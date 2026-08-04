#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板管理器 v2：索引驱动 + 多级降级 + 源切换

优化点：
1. 模板索引：本地配置文件记录所有104个模板，精确匹配前先查索引确认存在
2. 模糊匹配降级：精确文件名不存在时，按doc_type前缀+案由关键词搜索
3. 通用模板兜底：找不到案由专属模板时，回退到同文书类型的"通用"模板
4. 源切换：Gitee→GitHub自动切换，403/404自动重试
5. 本地缓存：下载成功的模板缓存到本地，避免重复下载
"""

import os
import json
import shutil
import urllib.request
import urllib.parse
from typing import Optional, List, Dict


# 模板仓库配置（Gitee优先，GitHub备选）
GITEE_REPO = "hugeshark/element-lawsuit-templates"
GITEE_BRANCH = "main"
GITEE_RAW_BASE = f"https://gitee.com/{GITEE_REPO}/raw/{GITEE_BRANCH}"

GITHUB_REPO = "hugesharks/element-lawsuit-templates"
GITHUB_BRANCH = "main"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"

# 案由分类到模板目录的映射
CATEGORY_DIRS = {
    "01-刑事自诉": "01-刑事自诉",
    "02-婚姻家事": "02-婚姻家事",
    "03-合同纠纷": "03-合同纠纷",
    "04-劳动争议": "04-劳动争议",
    "05-交通事故": "05-交通事故",
    "06-保险纠纷": "06-保险纠纷",
    "07-知识产权": "07-知识产权",
    "08-行政纠纷": "08-行政纠纷",
    "09-国家赔偿": "09-国家赔偿",
    "10-公益诉讼": "10-公益诉讼",
    "11-海商海事": "11-海商海事",
}


class TemplateManager:
    """模板管理器 v2"""

    def __init__(self, cache_dir: str = None, config_dir: str = None, local_template_dir: str = None):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        if cache_dir is None:
            cache_dir = os.path.join(base_dir, 'template_cache')
        if config_dir is None:
            config_dir = os.path.join(base_dir, 'configs')
        
        self.cache_dir = cache_dir
        self.config_dir = config_dir
        self.local_template_dir = local_template_dir
        
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 加载案由分类映射
        self.case_to_category = self._load_case_category_mapping()
        
        # 加载模板索引
        self.template_index = self._load_template_index()
    
    def _load_case_category_mapping(self) -> Dict[str, str]:
        """从配置文件加载案由到分类的映射"""
        keywords_path = os.path.join(self.config_dir, 'case_keywords.json')
        if os.path.exists(keywords_path):
            with open(keywords_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return {
                name: info.get('category', '')
                for name, info in config.get('case_keywords', {}).items()
            }
        return {}
    
    def _load_template_index(self) -> Dict[str, List[Dict]]:
        """加载模板索引"""
        index_path = os.path.join(self.config_dir, 'template_index.json')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('templates', {})
        return {}
    
    def _index_has_template(self, doc_type: str, case_type: str) -> bool:
        """检查索引中是否存在指定模板"""
        templates = self.template_index.get(doc_type, [])
        for t in templates:
            if t['case_type'] == case_type:
                return True
        return False
    
    def _find_in_index(self, doc_type: str, case_type: str) -> Optional[str]:
        """在索引中查找模板，支持模糊匹配"""
        templates = self.template_index.get(doc_type, [])
        if not templates:
            return None
        
        # 1. 精确匹配
        for t in templates:
            if t['case_type'] == case_type:
                return t['filename']
        
        # 2. 案由关键词匹配（取案由的核心词在模板名中出现）
        # 把案由拆成关键词，在模板case_type中搜索
        keywords = self._extract_case_keywords(case_type)
        best_match = None
        best_score = 0
        
        for t in templates:
            score = 0
            for kw in keywords:
                if kw in t['case_type']:
                    score += len(kw)
            if score > best_score:
                best_score = score
                best_match = t['filename']
        
        if best_match and best_score >= 2:
            return best_match
        
        # 3. 通用模板兜底
        for t in templates:
            if '通用' in t['case_type']:
                return t['filename']
        
        # 4. 同文书类型的第一个模板（最后兜底）
        return templates[0]['filename'] if templates else None
    
    def _extract_case_keywords(self, case_type: str) -> List[str]:
        """从案由中提取关键词"""
        # 去掉常见后缀
        suffixes = ['纠纷', '案', '争议', '诉讼']
        core = case_type
        for s in suffixes:
            if core.endswith(s):
                core = core[:-len(s)]
                break
        
        # 拆分成2字以上的词组
        keywords = [case_type]  # 完整案由也作为一个关键词
        if len(core) >= 2:
            keywords.append(core)
        
        # 额外拆分
        extra_splits = [
            ('买卖合同', ['买卖', '合同']),
            ('房屋买卖', ['房屋', '买卖']),
            ('房屋租赁', ['房屋', '租赁']),
            ('建设工程', ['建设', '工程']),
            ('民间借贷', ['借贷', '民间']),
            ('金融借款', ['金融', '借款']),
            ('融资租赁', ['融资', '租赁']),
            ('交通事故', ['交通', '事故']),
            ('人身保险', ['人身', '保险']),
            ('财产损失保险', ['财产', '保险']),
            ('责任保险', ['责任', '保险']),
            ('保证保险', ['保证', '保险']),
            ('侵害商标权', ['商标']),
            ('侵害著作权', ['著作权', '版权']),
            ('侵害发明专利', ['发明', '专利']),
            ('侵害外观设计', ['外观', '专利']),
            ('侵害商业秘密', ['商业秘密']),
            ('侵害植物新品种', ['植物', '新品种']),
            ('不正当竞争', ['不正当', '竞争']),
            ('劳动争议', ['劳动']),
            ('环境污染', ['环境', '污染']),
            ('生态环境', ['生态', '环境']),
            ('生态破坏', ['生态', '破坏']),
            ('船舶碰撞', ['船舶', '碰撞']),
            ('海上、通海水域', ['海上', '通海']),
            ('工伤保险', ['工伤', '保险']),
            ('商标申请', ['商标']),
            ('商标撤销', ['商标', '撤销']),
            ('商标无效', ['商标', '无效']),
            ('专利申请', ['专利']),
            ('专利无效', ['专利', '无效']),
            ('刑事改判无罪', ['改判', '无罪', '刑事']),
            ('违法刑事拘留', ['拘留', '刑事']),
            ('怠于履行', ['怠于', '履行']),
            ('错误执行', ['错误', '执行']),
            ('不履行法定职责', ['不履行', '法定']),
            ('国有土地上房屋征收', ['房屋征收', '征收']),
            ('行政协议', ['协议']),
            ('政府信息公开', ['公开', '信息']),
            ('拒不执行判决裁定', ['拒不执行', '判决']),
        ]
        for full, parts in extra_splits:
            if full in case_type:
                keywords.extend(parts)
                break
        
        return keywords

    def get_template(self, case_type: str, doc_type: str, use_local: bool = True) -> Optional[str]:
        """
        获取模板文件路径（多级降级策略）
        
        优先级：
        1. 本地模板目录 → 精确匹配
        2. 本地模板目录 → 模糊匹配（同doc_type+案由关键词）
        3. 本地模板目录 → 通用模板兜底
        4. 远程缓存 → 精确匹配
        5. 远程下载（先查索引确认存在）→ 缓存
        6. 远程下载 → 模糊匹配（索引推荐的替代模板）
        """
        filename = f"{doc_type}-{case_type}.docx"
        
        # === 本地模板目录 ===
        if use_local and self.local_template_dir and os.path.isdir(self.local_template_dir):
            # 1. 精确匹配
            local_path = os.path.join(self.local_template_dir, filename)
            if os.path.exists(local_path):
                return local_path
            
            # 2. 模糊匹配：索引推荐
            alt_filename = self._find_in_index(doc_type, case_type)
            if alt_filename and alt_filename != filename:
                alt_path = os.path.join(self.local_template_dir, alt_filename)
                if os.path.exists(alt_path):
                    return alt_path
            
            # 3. 通用模板兜底
            for f in os.listdir(self.local_template_dir):
                if f.startswith(doc_type) and '通用' in f and f.endswith('.docx'):
                    return os.path.join(self.local_template_dir, f)
            
            # 4. 同doc_type的第一个模板
            for f in sorted(os.listdir(self.local_template_dir)):
                if f.startswith(doc_type) and f.endswith('.docx'):
                    return os.path.join(self.local_template_dir, f)
        
        # === 远程缓存 ===
        cached_path = os.path.join(self.cache_dir, filename)
        if os.path.exists(cached_path):
            return cached_path
        
        # === 远程下载 ===
        # 先查索引确认精确文件名是否存在
        exact_exists = self._index_has_template(doc_type, case_type)
        
        if exact_exists:
            # 精确文件名存在，直接下载
            if self._download_template(doc_type, case_type, filename):
                if os.path.exists(cached_path):
                    return cached_path
        
        # 模糊匹配：索引推荐的替代模板
        alt_filename = self._find_in_index(doc_type, case_type)
        if alt_filename and alt_filename != filename:
            # 解析替代模板的案由
            alt_name = alt_filename.replace('.docx', '')
            parts = alt_name.split('-', 1)
            alt_doc_type = parts[0]
            alt_case_type = parts[1] if len(parts) > 1 else ''
            
            alt_cached_path = os.path.join(self.cache_dir, alt_filename)
            if os.path.exists(alt_cached_path):
                return alt_cached_path
            
            if self._download_template(alt_doc_type, alt_case_type, alt_filename):
                if os.path.exists(alt_cached_path):
                    return alt_cached_path
        
        # 最后兜底：从本地缓存或本地目录找同类型的任意模板
        return self._find_any_template(doc_type)
    
    def _download_template(self, doc_type: str, case_type: str, filename: str) -> bool:
        """下载模板，自动源切换"""
        category = self.case_to_category.get(case_type, '')
        category_dir = CATEGORY_DIRS.get(category, '')
        
        if not category_dir:
            # 无法确定分类目录，尝试所有目录
            for cat_dir in CATEGORY_DIRS.values():
                if self._download_from_source(cat_dir, filename):
                    return True
            return False
        
        # Gitee优先，GitHub备选
        if self._download_from_source(category_dir, filename):
            return True
        
        return False
    
    def _download_from_source(self, category_dir: str, filename: str) -> bool:
        """从多个源尝试下载"""
        sources = [
            (GITEE_RAW_BASE, category_dir),
            (GITHUB_RAW_BASE, category_dir),
        ]
        
        for base_url, cat_dir in sources:
            if self._download_from_url(base_url, cat_dir, filename):
                return True
        
        return False

    def _download_from_url(self, base_url: str, category_dir: str, filename: str) -> bool:
        """从指定URL下载模板"""
        encoded_category = urllib.parse.quote(category_dir)
        encoded_filename = urllib.parse.quote(filename)
        url = f"{base_url}/templates/{encoded_category}/{encoded_filename}"
        
        cached_path = os.path.join(self.cache_dir, filename)
        temp_path = cached_path + '.tmp'
        
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'application/octet-stream'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            
            # 验证是否为有效的docx文件（ZIP格式以PK开头）
            if len(data) < 4 or data[:2] != b'PK':
                return False
            
            with open(temp_path, 'wb') as f:
                f.write(data)
            
            # 原子操作
            if os.path.exists(cached_path):
                os.remove(cached_path)
            os.rename(temp_path, cached_path)
            
            return True
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"下载模板失败: {filename}, 错误: {e}")
            return False
    
    def _find_any_template(self, doc_type: str) -> Optional[str]:
        """最后兜底：找同文书类型的任意模板"""
        # 搜索缓存目录
        if os.path.isdir(self.cache_dir):
            for f in sorted(os.listdir(self.cache_dir)):
                if f.startswith(doc_type) and f.endswith('.docx'):
                    return os.path.join(self.cache_dir, f)
        
        # 搜索本地目录
        if self.local_template_dir and os.path.isdir(self.local_template_dir):
            for f in sorted(os.listdir(self.local_template_dir)):
                if f.startswith(doc_type) and f.endswith('.docx'):
                    return os.path.join(self.local_template_dir, f)
        
        return None

    def list_local_templates(self) -> List[str]:
        """列出本地所有可用模板"""
        templates = set()
        
        if self.local_template_dir and os.path.isdir(self.local_template_dir):
            for f in os.listdir(self.local_template_dir):
                if f.endswith('.docx'):
                    templates.add(f)
        
        if os.path.isdir(self.cache_dir):
            for f in os.listdir(self.cache_dir):
                if f.endswith('.docx'):
                    templates.add(f)
        
        return sorted(templates)

    def get_template_info(self, filename: str) -> Dict:
        """解析模板文件名获取信息"""
        name = filename.replace('.docx', '')
        parts = name.split('-', 1)
        return {
            'doc_type': parts[0] if parts else '',
            'case_type': parts[1] if len(parts) > 1 else '',
            'filename': filename,
            'category': self.case_to_category.get(parts[1] if len(parts) > 1 else '', '')
        }

    def clear_cache(self):
        """清空远程模板缓存"""
        if os.path.isdir(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)

    def pre_download_all(self, local_dir: str = None) -> Dict:
        """预下载所有模板到缓存"""
        result = {"success": 0, "failed": 0, "errors": []}
        
        if local_dir and os.path.isdir(local_dir):
            for f in os.listdir(local_dir):
                if f.endswith('.docx') and not f.endswith('-实例.docx'):
                    src = os.path.join(local_dir, f)
                    dst = os.path.join(self.cache_dir, f)
                    try:
                        shutil.copy2(src, dst)
                        result["success"] += 1
                    except Exception as e:
                        result["failed"] += 1
                        result["errors"].append(f"复制 {f} 失败: {e}")
        else:
            for category_dir in CATEGORY_DIRS.values():
                try:
                    encoded_category = urllib.parse.quote(category_dir)
                    api_urls = [
                        f"https://gitee.com/api/v5/repos/{GITEE_REPO}/contents/templates/{encoded_category}",
                        f"https://api.github.com/repos/{GITHUB_REPO}/contents/templates/{encoded_category}",
                    ]
                    files = None
                    for api_url in api_urls:
                        try:
                            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                files = json.loads(resp.read().decode('utf-8'))
                            break
                        except Exception:
                            continue
                    
                    if not files:
                        result["errors"].append(f"列出 {category_dir} 目录失败: 所有源均不可用")
                        continue
                    
                    for file_info in files:
                        if file_info['name'].endswith('.docx'):
                            success = self._download_from_source(category_dir, file_info['name'])
                            if success:
                                result["success"] += 1
                            else:
                                result["failed"] += 1
                                result["errors"].append(f"下载 {file_info['name']} 失败")
                except Exception as e:
                    result["errors"].append(f"列出 {category_dir} 目录失败: {e}")
        
        return result


# 单独测试
if __name__ == '__main__':
    tm = TemplateManager(local_template_dir='/tmp/templates-blank')
    
    # 测试精确匹配
    path = tm.get_template("民间借贷纠纷", "民事起诉状")
    print(f"民间借贷→民事起诉状: {path}")
    
    # 测试模糊匹配（不存在的案由，应降级到同类模板）
    path = tm.get_template("保证合同纠纷", "民事起诉状")
    print(f"保证合同纠纷→民事起诉状: {path}")
    
    # 测试行政答辩状（只有2个模板，不存在的案由应降级到通用）
    path = tm.get_template("行政处罚", "行政答辩状")
    print(f"行政处罚→行政答辩状: {path}")
    
    # 测试国家赔偿答辩状（不存在的行政赔偿案由）
    path = tm.get_template("行政赔偿", "国家赔偿答辩状")
    print(f"行政赔偿→国家赔偿答辩状: {path}")
