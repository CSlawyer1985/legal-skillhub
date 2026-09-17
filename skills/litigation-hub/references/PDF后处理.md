<!-- Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm. -->
# PDF 后处理（第六步做法层）

SKILL.md 只留「不默认启用 + 触发阈值 + 用户确认」，本文件放合并策略、A4 标准化与重命名规则的完整做法。

## 读取用户偏好

读取 `config/user-preferences.json`。如文件不存在，使用默认值（参考 `config/user-preferences.example.json`）。

| 偏好 | 默认值 | 说明 |
| --- | --- | --- |
| `merge_strategy` | `per_evidence` | 合并策略：`per_evidence`（按编号分别合并）或 `unified`（统一合并） |
| `merge_options.unified.bookmarks.enabled` | `true` | 统一合并时是否添加 PDF 书签 |
| `rename.enabled` | `true` | 是否精简文件名 |

## 触发检测

读取 `references/sms-patterns.json` → `post_processing.trigger` 配置，按以下规则分组：

```text
分组规则：
1. 证据类：文件名以"证据"开头 → 按编号分组（证据1、证据2、证据3…）
2. 其他文书：按文书类型分组（传票、起诉状、应诉通知书…）
3. 如任一组内文件数 > 3（threshold），触发提示
```

**示例**：证据3 下有 10 个 PDF → 触发。

## 用户确认话术

```text
检测到以下文书被拆分为多个 PDF：
- 证据3：10 个文件
- 证据5：4 个文件

是否执行 PDF 后处理（合并 + 重命名）？
  → 是，合并所有
  → 让我选择（逐个确认）
  → 跳过
```

## 合并策略

**策略一：per_evidence（默认）**——按单个证据编号分别合并，每个证据独立保留：

```text
- 证据3 有 10 个拆分文件 → 合并为「证据3：打印截图.pdf」
- 证据5 有 4 个拆分文件 → 合并为「证据5：电脑截图.pdf」
- 未被拆分的证据（如证据1 只有 1 个文件）保持不动
```

**策略二：unified**——将证据目录 + 所有证据合并为一个「原告证据.pdf」，并添加 PDF 书签：

```text
合并顺序：证据目录 → 证据1 → 证据2 → … → 证据N
书签格式：
  📑 证据目录
  📑 证据1：仲裁申请书、不予受理通知书
  📑 证据2：劳动合同、保密协议
  📑 证据3：被告工资表
  📑 证据4：泄露账号密码的电脑截图
  📑 证据5：打印及拷贝资料的电脑截图
  📑 证据6：删除电脑操作痕迹的截图
```

书签名称使用简洁版：证据编号 + 冒号 + 证据标题（去除当事人和日期后缀）。使用 pypdf 的 `add_outline_item` 添加书签。

## 页面尺寸标准化（A4）

合并过程中同时标准化页面尺寸为 A4（210×297mm）。使用 pypdf 逐页处理：

```python
from pypdf import PdfReader, PdfWriter, Transformation

A4_W = 595.27  # 210mm in points
A4_H = 841.89  # 297mm in points

for page in reader.pages:
    pw, ph = float(page.mediabox.width), float(page.mediabox.height)
    is_landscape = pw > ph

    # 保持原始方向：纵向→A4纵向，横向→A4横向
    target_w = A4_H if is_landscape else A4_W
    target_h = A4_W if is_landscape else A4_H

    # 等比缩放并居中
    scale = min(target_w / pw, target_h / ph)
    offset_x = (target_w - pw * scale) / 2
    offset_y = (target_h - ph * scale) / 2

    new_page = writer.add_blank_page(width=target_w, height=target_h)
    page.add_transformation(Transformation().scale(scale).translate(offset_x, offset_y))
    new_page.merge_page(page)
```

**规则**：

- 纵向页面 → A4 纵向（210×297mm）
- 横向页面 → A4 横向（297×210mm），不强制旋转为纵向
- 等比缩放、居中放置，不裁剪、不拉伸

## 精简文件名

根据 `user-preferences.json` → `rename` 配置对所有文件统一重命名：

```text
去除规则（strip_patterns）：
- 去掉括号内的当事人信息：（张三与李四合同纠纷）
- 去掉日期后缀：_20260405收
- 去掉平台标记：（合并）、（自贸法庭）、（素）-

特殊映射（special_mappings）：
- 起诉状（素）… → 起诉状（要素式）.pdf
- 开庭传票 → 传票.pdf
```

| 原始 | 重命名后 |
| --- | --- |
| `传票（张三与李四合同纠纷）_20260405收.pdf` | `传票.pdf` |
| `起诉状（合并）.pdf` | `起诉状.pdf` |
| `起诉状（素）-要素式起诉状（合并）.pdf` | `起诉状（要素式）.pdf` |
| `应诉通知书（自贸法庭）.pdf` | `应诉通知书.pdf` |
| `E法桥平台使用告知书（xxx）_20260405收.pdf` | `E法桥平台使用告知书.pdf` |
