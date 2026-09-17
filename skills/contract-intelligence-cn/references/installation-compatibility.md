# 安装、兼容性与故障排查

## 一、最低环境

- Python 3.10及以上；
- `python-docx`；
- LibreOffice（`.doc`转换及DOCX转PDF）；
- Poppler的`pdfinfo`、`pdftoppm`（页数及预览核验）。

安装Python依赖：

```bash
python -m pip install python-docx
```

Linux（Debian/Ubuntu）可安装：

```bash
sudo apt-get install libreoffice poppler-utils
```

macOS可使用Homebrew安装LibreOffice和Poppler；Windows安装LibreOffice后，将其程序目录加入PATH。

## 二、平台中立导入

Skill核心为`SKILL.md`及`references/`，可复制到支持Markdown技能包或系统提示扩展的智能体中。若平台不支持脚本工具，仍可使用法律审查矩阵和输出模板，但无法自动生成Word红线和核验报告。

Hermes Agent示例：将整个`合同智审/`目录置于当前配置的skills目录，重新加载技能后调用。其他平台应保留目录结构，并允许读取references和调用本地Python脚本。

## 三、真实案件输入流程

1. 复制原合同到独立项目目录；
2. `.doc`先转换为`.docx`；
3. 执行`inspect`盘点正文、表格、金额和基础风险；
4. 法律专业人员结合材料形成结构化修改计划JSON；
5. 执行`apply-plan`生成红线版和清洁版；
6. 转PDF；
7. 执行`verify-pair`并逐页视觉检查；
8. 由承办律师审阅定稿。

## 四、常见问题

- **目标命中0次或多次：**JSON计划中的target必须是唯一、完整原文；先读取文档并增加上下文。
- **表格中找不到目标：**脚本会遍历正文和表格；嵌套表格或文本框属于已知限制，需人工处理。
- **中文字体错位：**设置东亚字体，并使用本机存在的宋体/微软雅黑等字体。
- **LibreOffice转换失败：**检查文件是否损坏、被占用或有密码保护。
- **扫描PDF无文本：**先OCR，再由律师复核识别结果；本脚本不直接修改PDF扫描件。
- **含修订模式/批注：**先列明并确认接受、拒绝或保留策略，避免与红色字体留痕混淆。

## 五、已知限制

1. 通用修改执行器以“唯一原文锚点”为基础，不自动理解任意合同；法律分析仍由Skill与律师共同完成；
2. 文本框、形状、复杂嵌套表格、域代码和特殊修订记录可能需专项处理；
3. PDF存在不等于版式无异常，仍须人工视觉核验；
4. 法律依据必须通过权威渠道另行检索并确认现行有效性。
