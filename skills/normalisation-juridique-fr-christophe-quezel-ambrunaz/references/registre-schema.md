# JSON 登记表模式

文件写入 `.normjur/registre.json`，位于文档旁。**绝不倾倒进对话**：只有 `recap` 表格出现在其中。

```jsonc
{
  "version": "1.0",
  "document_original": "/chemin/abs/original.docx",   // 完整来源，重建的基础
  "document_corrige":  "/chemin/abs/normalise.docx",
  "horodatage": "2026-06-18T10:30:00Z",
  "auteur_revisions": "Claude — normalisation",
  "scope": "all",                                       // all | body | body+notes

  "groupes": [                                          // 汇总表的一行 = 一个组
    {
      "n": 1,                                            // 显示编号，稳定
      "cle": "apostrophes",
      "libelle": "Apostrophes droites → courbes",
      "categorie": "typographie",                        // typographie|lexique|citation|ia|stylistique
      "regime": "determin",                              // determin | jugement
      "type_edition": "direct",                          // direct | tracked
      "actif": true,
      "occurrences": 42,
      "exemples": ["l'article → l’article"]              // 1 至 3 个截断示例（约 40 字符）
    }
  ],

  "editions": [                                          // 一次原子修改
    {
      "n": 1, "i": 1,                                    // 组 n，出现 i（→“撤销 1.1”）
      "cle": "apostrophes",
      "regime": "determin",
      "partie": "document",                              // document | footnotes | endnotes
      "actif": true,
      "avant": "l'",
      "apres": "l’",
      "contexte": "…dans l'article 9…",                  // 可选，截断
      "w_ids": []                                        // Word 修订的 ids（judgment/tracked 制度）
    }
  ],

  "regles_desactivees": [],                              // ["anglicismes_surs", ...] — 确定性重建
  "occurrences_desactivees": []                          // ["7.2", "9.1"] — 精细排除
}
```

## 约定

- **编号**：确定性组按规则固定顺序获得 `n` = 1…k；判断组按 `registre.py add-jugement` 添加的顺序紧随其后（`k+1`、`k+2`…）。
- **确定性制度**：可逆性通过**重建**实现——从 `document_original` 重新应用仍然活跃的规则/出现项（`regles_desactivees`、`occurrences_desactivees`）。无原地重写：无漂移。
- **判断制度**：可逆性通过**拒绝**由 `w_ids` 标识的修订实现。如用户已在 Word 中接受它们，切换为 `apres → avant` 替换。
- **幂等性**：已停用的组不会被重新应用；已符合的出现项不会被重新计数。
