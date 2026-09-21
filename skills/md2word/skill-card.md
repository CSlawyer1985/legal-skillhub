## Description: <br>
Markdown转Word文档技能，将 Markdown 文档转换为符合中文排版标准的专业 Word 文档，并支持多种预设格式。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[cat-xierluo](https://clawhub.ai/user/cat-xierluo) <br>

### License/Terms of Use: <br>
MIT <br>


## Use Case: <br>
Agents use this skill to convert Markdown drafts into Chinese-formatted Word documents for legal documents, service plans, academic papers, reports, and book manuscripts. It applies preset or custom formatting for headings, body text, tables, images, footnotes, and basic document structure. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The security evidence reports that the skill can fetch arbitrary external image URLs while processing Markdown. <br>
Mitigation: Use trusted local Markdown when possible, pre-download and review remote images, and run conversions with network access controlled for untrusted inputs. <br>
Risk: The security evidence reports that user-supplied SVG and diagram content may be rendered through local tools. <br>
Mitigation: Avoid untrusted inline SVG or Mermaid content unless the renderer is isolated and optional rendering tools are installed in a constrained environment. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/cat-xierluo/skills/md2word) <br>
- [ClawDIS Homepage](https://github.com/cat-xierluo/legal-skills) <br>
- [Configuration Reference](references/config-reference.md) <br>
- [Style Mappings](references/style-mappings.md) <br>
- [Usage Examples](references/examples.md) <br>


## Skill Output: <br>
**Output Type(s):** [files, markdown, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with shell commands and generated .docx Word document files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Supports preset and custom YAML configuration; may create companion image files when rendering diagrams or inline SVG.] <br>

## Skill Version(s): <br>
1.1.8 (source: frontmatter, CHANGELOG, server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
