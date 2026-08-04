#!/usr/bin/env python3
"""周报条目优先级自动打分引擎 v3.0（2026-07-28 8维重构）

法律条目从 4 维升级为 7 维：
  case_density        案例密度 — 有没有具体案子？只抛现象不谈案子，分就下来
  norm_anchoring      规范锚定 — 有没有回到法条和司法解释？最高档是引到入库案例
  actionability       可操作性 — 读完能不能拿走能直接用的规则？
  author_empirical_depth  作者实证深度 — 不看「法官」头衔，看审级和论证的真功底
  framework_quality   框架定性 — 好文章先定法域框架再填内容，差文章直接堆材料
  relevance_halflife  时效半衰期 — 基础方法永不过时 vs 前沿快过时
  jurisdictional_proximity 地域管辖贴近度 — 浙江/金华本地法官=预判价值

用法：
    echo '{"features":{"case_density":1,...}}' | python3 scoring_engine.py legal
    echo '{"features":{"signal_strength":1,...}}' | python3 scoring_engine.py ai-legal
"""

import json, sys, math
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config" / "settings.yaml"

# 默认值（config 缺失时回退，保证单文件可用）
DEFAULT_LEGAL_WEIGHTS = {
    'case_density': 0.18, 'norm_anchoring': 0.18, 'actionability': 0.18,
    'author_empirical_depth': 0.16, 'framework_quality': 0.12,
    'relevance_halflife': 0.10, 'jurisdictional_proximity': 0.08,
    # deprecated（保留兼容旧训练集）
    'author_tier': 0.00, 'platform_tier': 0.00, 'depth': 0.00, 'relevance': 0.00,
}
DEFAULT_AI_LEGAL_WEIGHTS = {'signal_strength': 0.50, 'depth': 0.25, 'relevance': 0.15, 'domestic_relevance': 0.10, 'author_tier': 0.00, 'platform_tier': 0.00}
DEFAULT_INTEREST_KW = ['婚姻', '家事', '抚养', '继承', '离婚', '恋爱', '公司', '股东', '股权', '法人', '商标', '医疗', '诊疗', '知情']
DEFAULT_TRAINING = BASE / ".workbuddy" / "memory" / "scoring-training.jsonl"

# ── v3 旧→新 特征映射（训练集向后兼容）──
# 62 条训练集仍是老四维，运行时动态映射为新七维近似值
_OLD_TO_NEW_MAP = {
    # author_tier: 1最高法→1, 2省高院/中院→2, 3基层→3
    'author_empirical_depth': lambda f: f.get('author_tier', 2),
    # platform_tier: 1入库案例/公报→1, 2人民法院报→2, 3品牌栏目→2, 4一般→3, 5媒体→3
    'norm_anchoring': lambda f: {1: 1, 2: 2, 3: 2, 4: 3, 5: 3}.get(f.get('platform_tier', 3), 2),
    # depth: 1体系分析→1(好框架), 2有分析→2, 3新闻→3
    'framework_quality': lambda f: f.get('depth', 2),
    # depth → case_density: 1→1(有案例), 2→2, 3→3(无案例)
    'case_density': lambda f: f.get('depth', 2),
    # relevance → actionability: 1→1(直接可用), 2→2, 3→3
    'actionability': lambda f: f.get('relevance', 2),
    # relevance → relevance_halflife: 1→1(基础方法), 2→2, 3→2
    'relevance_halflife': lambda f: min(f.get('relevance', 2), 2),
    # jurisdictional_proximity: 老数据默认 0（无浙江/金华标签）
    'jurisdictional_proximity': lambda f: 0,
}


def _map_old_features_to_v3(feat):
    """将老四维特征映射为 v3 七维特征。已有新维度则不覆盖。"""
    f = dict(feat)
    # 检查是否已经是 v3 特征（有任一新维度键）
    v3_keys = {'case_density', 'norm_anchoring', 'actionability', 'author_empirical_depth',
               'framework_quality', 'relevance_halflife', 'jurisdictional_proximity'}
    already_v3 = any(k in f for k in v3_keys)
    if already_v3:
        return f  # 已经是 v3，不映射
    # 老四维 → 新七维
    for new_key, mapper in _OLD_TO_NEW_MAP.items():
        f[new_key] = mapper(f)
    return f


def normalize_features(feat, category):
    """字段兼容：补齐 v2 新增维度，旧训练集/候选缺字段时填中性默认。

    - signal_strength: 缺则按 first_hand 映射（1→2 应用落地, 0→3 融资动态），均缺默认 2
    - domestic_relevance: 缺默认 0
    - author_tier/platform_tier: 保留（权重已置 0，不影响距离）
    """
    f = dict(feat)
    if category == 'ai-legal':
        if 'signal_strength' not in f:
            fh = f.get('first_hand')
            if fh == 1:
                f['signal_strength'] = 2
            elif fh == 0:
                f['signal_strength'] = 3
            else:
                f['signal_strength'] = 2  # 中性默认：应用落地级
        if 'domestic_relevance' not in f:
            f['domestic_relevance'] = 0
    return f


def coalesce_vectors(data):
    """训练集加载后合并相同特征向量：同向量多条 → 1 条，分数取均值。

    防 k-NN 同向量多重命中（1/dist 权重虚高绑架预测）。
    训练集文件全量保留（不物理删除），仅此处运行时合并。
    返回新 list，每条含合并后的 'features' 与 'score'（均值）。
    """
    groups = {}
    for d in data:
        cat = d.get('category', d.get('type', ''))
        f = normalize_features(d.get('features', {}), cat)
        key = (cat, tuple(sorted(f.items())))
        groups.setdefault(key, []).append(d)
    out = []
    for (cat, _), items in groups.items():
        scores = [it.get('score', it.get('manual', it.get('predicted', 5.0))) for it in items]
        merged = dict(items[0])
        merged['features'] = normalize_features(items[0].get('features', {}), cat)
        merged['score'] = round(sum(scores) / len(scores), 2)
        merged['_merged_count'] = len(items)
        out.append(merged)
    return out


def load_settings():
    if yaml is None or not CONFIG.exists():
        return {}
    cfg = yaml.safe_load(open(CONFIG)) or {}
    # 版本化 merge：旧 config（无 schema_version）自动补全缺失字段，不全量覆盖
    if 'schema_version' not in cfg.get('scoring', {}):
        sc = cfg.setdefault('scoring', {})
        sc.setdefault('legal_weights', DEFAULT_LEGAL_WEIGHTS)
        sc.setdefault('ai_legal_weights', DEFAULT_AI_LEGAL_WEIGHTS)
        sc.setdefault('schema_version', 1)
    return cfg


def get_weights(category, settings):
    sc = settings.get('scoring', {})
    if category == 'legal':
        return sc.get('legal_weights', DEFAULT_LEGAL_WEIGHTS)
    return sc.get('ai_legal_weights', DEFAULT_AI_LEGAL_WEIGHTS)


def get_interest_kw(settings):
    sc = settings.get('scoring', {})
    return sc.get('interest_keywords', DEFAULT_INTEREST_KW)


def get_training_path(settings):
    sc = settings.get('scoring', {})
    p = sc.get('training_path', str(DEFAULT_TRAINING))
    return Path(p) if Path(p).is_absolute() else BASE / p


def load_training(path):
    """返回训练集 list；文件缺失/空返回 []（冷启动）。"""
    if not path.exists():
        return []
    data = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return data


def feature_distance(a_feat, b_feat, weights):
    dist = 0.0
    total_w = 0.0
    for k, w in weights.items():
        if k in a_feat and k in b_feat:
            dist += w * abs(a_feat[k] - b_feat[k])
            total_w += w
    return dist / max(total_w, 0.001)


def linear_fallback(entry, category, weights):
    """冷启动：无训练集时按特征权重线性映射到 1-10 分。"""
    feat = entry.get('features', {})
    if category == 'legal':
        # v3 七维：每维 1-3（越小越好），jurisdictional_proximity 0/1 加成
        score = 10.0
        score -= (feat.get('case_density', 2) - 1) * 0.9
        score -= (feat.get('norm_anchoring', 2) - 1) * 0.9
        score -= (feat.get('actionability', 2) - 1) * 0.9
        score -= (feat.get('author_empirical_depth', 2) - 1) * 0.8
        score -= (feat.get('framework_quality', 2) - 1) * 0.6
        score -= (feat.get('relevance_halflife', 2) - 1) * 0.5
        # 地域贴近加成：浙江/金华法官 +0.8（2026-08-01 随权重上调，本地规则预判价值高）
        if feat.get('jurisdictional_proximity', 0) == 1:
            score += 0.8
    else:
        # AI+法律冷启动：signal_strength 1格局/2落地/3融资（越小越高），depth/relevance 越小越高
        ss = feat.get('signal_strength', feat.get('first_hand', 1))
        # signal_strength 映射：1→9分基准, 2→7分, 3→5分
        base = {1: 9.0, 2: 7.0, 3: 5.0}.get(ss, 7.0)
        score = base
        score -= (feat.get('depth', 2) - 1) * 0.5
        score -= (feat.get('relevance', 2) - 1) * 0.3
    return max(1.0, min(10.0, score))


def predict(entry, category='legal'):
    """Predict score and confidence for a single entry."""
    settings = load_settings()
    weights = get_weights(category, settings)
    training_path = get_training_path(settings)
    data = load_training(training_path)

    # 冷启动降级
    if not data:
        score = linear_fallback(entry, category, weights)
        bonus = 0.0
        if category == 'legal' and 'title' in entry:
            for kw in get_interest_kw(settings):
                if kw in entry['title']:
                    bonus = 0.3
                    break
        return round(score + bonus, 1), 0.0  # confidence=0 标记冷启动

    pool = [d for d in data if d.get('category', d.get('type', '')) == category]
    if not pool:
        pool = data

    # 训练集 coalesce：同特征向量合并取均值（防权重虚高）
    pool = coalesce_vectors(pool)

    # v3: 法律条目老训练集特征映射为新七维
    if category == 'legal':
        for d in pool:
            old_feat = d.get('features', {})
            d['features'] = _map_old_features_to_v3(old_feat)

    entry_feat = normalize_features(entry.get('features', {}), category)
    # v3: 候选条目特征也映射（如果是老四维）
    if category == 'legal':
        entry_feat = _map_old_features_to_v3(entry_feat)

    scored = []
    for d in pool:
        dist = feature_distance(entry_feat, d.get('features', {}), weights)
        scored.append((dist, d.get('score', d.get('manual', d.get('predicted', 5.0)))))
    scored.sort()

    k = min(5, len(scored))
    neighbors = scored[:k]

    total_w = 0.0
    weighted_sum = 0.0
    for dist, score in neighbors:
        w = 1.0 / max(dist, 0.001)
        weighted_sum += w * score
        total_w += w
    predicted = weighted_sum / max(total_w, 0.001)

    nscores = [s for _, s in neighbors]
    score_range = max(nscores) - min(nscores)
    avg_dist = sum(d for d, _ in neighbors) / len(neighbors)
    agreement = 1.0 - (score_range / 5.0)
    proximity = max(0, 1.0 - avg_dist * 2)
    confidence = (agreement * 0.6 + proximity * 0.4)
    if score_range == 0 and avg_dist < 0.3:
        confidence = max(confidence, 0.85)

    bonus = 0.0
    if category == 'legal' and 'title' in entry:
        for kw in get_interest_kw(settings):
            if kw in entry['title']:
                bonus = 0.3
                break

    # 2026-08-01 用户裁定：不设封顶线，恢复引擎自然打分（k-NN 距离加权 + 兴趣加成），
    # 差异化来自特征标注粒度与训练集锚点；同特征条目同分属 k-NN 正常行为（相同输入=相同输出）
    return round(predicted + bonus, 1), round(min(1.0, confidence), 2)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: echo '{...}' | python3 scoring_engine.py <legal|ai-legal>", file=sys.stderr)
        sys.exit(1)
    cat = sys.argv[1]
    inp = json.loads(sys.stdin.read())
    score, conf = predict(inp, cat)
    print(json.dumps({"predicted_score": score, "confidence": conf, "need_review": conf < 0.8}, ensure_ascii=False))
