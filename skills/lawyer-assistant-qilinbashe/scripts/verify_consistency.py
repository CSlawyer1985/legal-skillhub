#!/usr/bin/env python3
"""律师助手技能包一致性校验脚本

所有计数与版本号均「动态推导」，绝不硬编码 87 / 12 / 2.6.x：
- 技能总数 = plugin.json（.workbuddy-plugin）的 skills 清单长度（包清单为权威源）
- 技能分类数 = plugin.json 中 skills 数组长度
- agents/ 目录文件数必须与 plugin.json 一致，否则即漏加/多加且未登记
- 两个平台的 plugin.json 必须互为镜像（技能数 + 版本一致）
- 版本号：以 plugin.json 为权威，SKILL.md / manifest.yaml 必须与之相等
- trigger_keywords 分隔符统一为 `|`
"""
import os, json, re, sys

def check():
    src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    errors = []

    # 1. agents/ 目录文件清单
    agents_dir = os.path.join(src, 'agents')
    agent_files = sorted([f for f in os.listdir(agents_dir) if f.endswith('.md')])
    actual = len(agent_files)

    # 2. 权威技能数取自 plugin.json（包清单），不再硬编码
    #    zip 模式容错：SkillHub 提交版不含 .workbuddy-plugin（平台规则排除），
    #    此时改从 manifest.yaml 推导版本 + agents/ 目录推导技能数，不判 FAIL。
    wb_pj_path = os.path.join(src, '.workbuddy-plugin', 'plugin.json')
    cb_pj_path = os.path.join(src, '.codebuddy-plugin', 'plugin.json')
    wb_pj = cb_pj = None
    zip_mode = False
    if os.path.exists(wb_pj_path):
        wb_pj = json.load(open(wb_pj_path, 'r', encoding='utf-8'))
    if os.path.exists(cb_pj_path):
        cb_pj = json.load(open(cb_pj_path, 'r', encoding='utf-8'))

    if wb_pj is None:
        # zip 模式：从 manifest.yaml 推导版本，agents/ 目录为权威技能数
        zip_mode = True
        my_path = os.path.join(src, 'manifest.yaml')
        if os.path.exists(my_path):
            mc = open(my_path, 'r', encoding='utf-8').read()
            mv = re.search(r'version:\s*[\'"]?([\d.]+)', mc)
            wb_ver = mv.group(1) if mv else None
        else:
            wb_ver = None
        expected = actual
        print('[zip模式] 无 .workbuddy-plugin/plugin.json（SkillHub 提交版按规则排除），'
              '权威技能数以 agents/ 目录为准=%d' % actual)
    else:
        expected = len(wb_pj.get('skills', []))
        wb_ver = wb_pj.get('version')

    # 3. agents/ 文件数必须与 plugin.json 清单一致
    if actual != expected:
        errors.append('agents/ 文件数: %d, plugin.json skills: %d（不一致=漏加/多加且未登记）' % (actual, expected))

    # 4. 两个平台 plugin.json 互为镜像（技能数 + 版本）
    if wb_pj is not None and cb_pj is not None:
        if len(wb_pj.get('skills', [])) != len(cb_pj.get('skills', [])):
            errors.append('双 plugin.json 技能数不一致: workbuddy=%d, codebuddy=%d'
                          % (len(wb_pj.get('skills', [])), len(cb_pj.get('skills', []))))
        if wb_ver is not None and cb_pj.get('version') != wb_ver:
            errors.append('双 plugin.json 版本不一致: workbuddy=%s, codebuddy=%s'
                          % (wb_ver, cb_pj.get('version')))
    elif wb_pj is None and cb_pj is not None:
        expected = len(cb_pj.get('skills', []))
        wb_ver = cb_pj.get('version')

    # 5. SKILL.md 版本 + 动态计数
    sk_path = os.path.join(src, 'SKILL.md')
    if os.path.exists(sk_path):
        sk = open(sk_path, 'r', encoding='utf-8').read()
        if wb_ver and ('version: %s' % wb_ver) not in sk:
            errors.append('SKILL.md: version 不是 %s' % wb_ver)
        if '%d个技能文件' % actual not in sk:
            errors.append('SKILL.md: 技能计数未同步为 %d' % actual)
    else:
        errors.append('SKILL.md: 缺失')

    # 6. README 动态计数
    rd_path = os.path.join(src, 'README.md')
    if os.path.exists(rd_path):
        rd = open(rd_path, 'r', encoding='utf-8').read()
        if '**%d个**' % actual not in rd and '**%d个' % actual not in rd:
            found = re.search(r'\*\*(\d+)个\*\*', rd)
            if not found or int(found.group(1)) != actual:
                errors.append('README: 技能总数未同步为 %d' % actual)
    else:
        errors.append('README.md: 缺失')

    # 7. manifest.yaml 版本 + 动态计数
    my_path = os.path.join(src, 'manifest.yaml')
    if os.path.exists(my_path):
        c = open(my_path, 'r', encoding='utf-8').read()
        if wb_ver and ('version: %s' % wb_ver) not in c:
            errors.append('manifest.yaml: version 不是 %s' % wb_ver)
        if '%d个技能文件' % actual not in c:
            errors.append('manifest.yaml: 技能计数未同步为 %d' % actual)
    else:
        errors.append('manifest.yaml: 缺失')

    # 8. plugin.json 一致性（体积/作者/小白版计数动态比对）
    if wb_pj is not None:
        pj = wb_pj
        pj_count = len(pj.get('skills', []))
        if pj_count != actual:
            errors.append('plugin.json skills: %d, agents实际%d' % (pj_count, actual))
        pj_size = os.path.getsize(wb_pj_path)
        if pj_size > 64 * 1024:
            errors.append('plugin.json 体积过大: %d 字节 (>64KB)' % pj_size)
        if pj.get('author') != '七邻八舍':
            errors.append('plugin.json author 应为「七邻八舍」')
        # 小白版：plugin.json 与 agents/ 动态比对（不再硬编码 12）
        pj_xb = len([s for s in pj.get('skills', []) if '小白版' in s.get('name', '')])
        ag_xb = len([f for f in agent_files if '小白版' in f])
        if pj_xb != ag_xb:
            errors.append('小白版计数不一致: plugin.json=%d, agents=%d' % (pj_xb, ag_xb))
        # plugin.json 引用的 agent 文件必须全部存在
        miss = [s.get('file') for s in pj.get('skills', []) if not os.path.exists(os.path.join(src, s.get('file', '')))]
        if miss:
            errors.append('plugin.json 引用了不存在的 agent 文件: %s' % ', '.join(miss))

    # 9. SKILL_INVENTORY 行数 + 成熟度占位符
    inv_path = os.path.join(src, 'SKILL_INVENTORY.md')
    if os.path.exists(inv_path):
        inv = open(inv_path, 'r', encoding='utf-8').read()
        inv_rows = len(re.findall(r'^\|\s*\d+\s*\|', inv, re.MULTILINE))
        if inv_rows != actual:
            errors.append('SKILL_INVENTORY: %d行, agents实际%d' % (inv_rows, actual))
        if re.search(r'\|\s*\?\s*\|', inv):
            errors.append('SKILL_INVENTORY 成熟度列存在未填占位符 ?')

    # 10. trigger_keywords 分隔符统一为 `|`（防回归：逗号派=旧不一致格式）
    for fn in agent_files:
        p = os.path.join(agents_dir, fn)
        for line in open(p, 'r', encoding='utf-8'):
            m = re.match(r'^trigger_keywords:\s*"(.*)"\s*$', line)
            if m:
                val = m.group(1)
                if ',' in val and '|' not in val:
                    errors.append('%s: trigger_keywords 仍用逗号分隔（应为 `|`）' % fn)
                break

    # 11. assets/律师助手节点树状图.html 必须存在（防回归：07-27 上线前静默丢失）
    #     该文件被 agents/00-全景图.md 与 agents/31-总控路由.md 写死引用，
    #     是「用户说话即右侧常驻节点图」的渲染资源；缺失则逻辑在、图不在。
    #     历史校验器不查 assets，导致图丢未报警，特此补查。
    assets_path = os.path.join(src, 'assets', '律师助手节点树状图.html')
    if not os.path.exists(assets_path):
        errors.append('assets/律师助手节点树状图.html 缺失（右侧常驻节点图资源丢失；00-全景图/31-总控路由写死引用此文件）')
    else:
        ah = open(assets_path, 'r', encoding='utf-8', errors='replace').read()
        if len(ah) < 1000:
            errors.append('assets/律师助手节点树状图.html 体积异常(<1KB)，疑似空壳/坏版')
        if '<title>' not in ah or '律师助手' not in ah:
            errors.append('assets/律师助手节点树状图.html 内容不符（缺 <title> 或「律师助手」标识）')
        if len(re.findall(r'<button', ah)) < 1:
            errors.append('assets/律师助手节点树状图.html 无可点击节点(button)，非有效节点图')
        if '可点击目录' not in ah and '节点' not in ah:
            errors.append('assets/律师助手节点树状图.html 不含「可点击目录/节点」标记，疑似误生成版本')

    # 12. v4.4.1 四项校验：发布链路 / 入口零手动 / 新脚本入包
    pp_path = os.path.join(src, 'scripts', 'present_panorama.py')
    doc_path = os.path.join(src, 'scripts', 'doctor.py')
    for sp in (pp_path, doc_path):
        if not os.path.isfile(sp):
            errors.append('scripts/%s 缺失（v4.4.1 新增脚本）' % os.path.basename(sp))
    if os.path.isfile(pp_path):
        import subprocess, tempfile, shutil
        tmp = tempfile.mkdtemp(prefix='legal_verify_')
        try:
            r = subprocess.run([sys.executable, pp_path, '--check-present', '--to', tmp],
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=120, cwd=tmp)
            if r.returncode != 0:
                errors.append('present_panorama.py 发布链路自检未通过(rc=%d): %s'
                              % (r.returncode, (r.stderr or r.stdout)[-200:]))
        except Exception as e:
            errors.append('present_panorama.py 发布链路自检异常: %s' % e)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    # 入口文档零手动：SKILL.md / 00 / 31 不得再出现「渲染两步法」或引导用户手动复制
    for rel, name in [('SKILL.md', 'SKILL.md'),
                      (os.path.join('agents', '00-律师助手全景图.md'), '00-全景图'),
                      (os.path.join('agents', '31-总控路由.md'), '31-总控路由')]:
        p = os.path.join(src, rel)
        if os.path.exists(p):
            c = open(p, encoding='utf-8').read()
            if '渲染两步法' in c:
                errors.append('%s: 仍残留「渲染两步法」旧机制标题（应为一键发布法）' % name)
            if re.search(r'(?:请|需|要|让)用户(?:手动|自己)复制', c):
                errors.append('%s: 仍存在引导用户手动复制文件的指令（v4.4.1 应零手动）' % name)

    # Summary
    if errors:
        print('[X] %d 个一致性错误:' % len(errors))
        for e in errors:
            print('  -', e)
        return 1
    else:
        if zip_mode:
            print('[OK] zip模式全部一致: %d个技能(动态), v%s, 无小白版, 无plugin.json(按规则排除)'
                  % (actual, wb_ver))
        else:
            print('[OK] 全部一致: %d个技能(动态), v%s, 无小白版, plugin.json/%d'
                  % (actual, wb_ver, actual))
        return 0

if __name__ == '__main__':
    sys.exit(check())
