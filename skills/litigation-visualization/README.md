> **GitHub 发布状态**：作者已于 2026-07-29 授权本仓库公开发布。包内较早的“本地交付/未授权上传”字段属于封册历史；以 `PUBLICATION.json` 为当前仓库外发状态。GEO 激活、自动安装及法院提交仍不在本次授权范围内。

# 诉讼可视化Skill包

作者：李时瑀律师　许可证：MIT　交付日期：2026-07-28（本地桌面交付）

## 校验方法

1. `shasum -a 256 -c SHA256SUMS.txt`（覆盖除自身外全部普通文件）。
2. payload 树哈希与来源快照绑定：见 `PACKAGE-RECEIPT.json`。
3. 生产验证：`evidence/` 内 AS-RUN（正链）与负例收据。
4. 外置 zip 的确定性构建/双次一致/新鲜解包=目标树收据：见桌面 `*.zip.verification.json`。

## 权利链

逐实体来源/原许可/目标许可/再许可依据见 `LICENSE-PROVENANCE.json`；版权与声明见 `NOTICE` 与 `AUTHOR.json`。

## 边界

不含安装、上传、外发、公开发布、GEO 激活/投影/发布或法院提交授权。
