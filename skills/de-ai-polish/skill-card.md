## Description: <br>
Detects AI-like expression patterns in Chinese drafts and helps remove template-like phrasing, empty summaries, mechanical transitions, exaggerated tone, and unnatural rhythm while preserving the writer's core meaning. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[cat-xierluo](https://clawhub.ai/user/cat-xierluo) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Writers, editors, and agent operators use this skill to review Chinese articles, reports, speeches, and public-facing drafts for common AI-writing patterns, then receive problem labels, rewrite guidance, and a more natural revision. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Rewrite suggestions can change the meaning, tone, or precision of legal, technical, or multilingual text. <br>
Mitigation: Review proposed changes before publishing and keep necessary legal terms, technical terms, citations, and author judgments intact. <br>
Risk: The punctuation helper can modify a Markdown file in place when no output path is provided. <br>
Mitigation: Use the helper's output option or work on a copy when the original file must be preserved. <br>


## Reference(s): <br>
- [ClawHub listing](https://clawhub.ai/cat-xierluo/de-ai-polish) <br>
- [Clawdis homepage](https://github.com/cat-xierluo/legal-skills) <br>
- [SKILL.md](SKILL.md) <br>
- [Expression transformations](reference/expression-transformations.md) <br>
- [Personal style guide](reference/personal-style-guide.md) <br>
- [Quality scoring](reference/quality-scoring.md) <br>
- [Sentence rhythm guide](reference/sentence-rhythm-guide.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, guidance, shell commands] <br>
**Output Format:** [Markdown with Chinese-language findings, rewrite suggestions, revised text, and optional shell command examples] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May propose direct text edits or run a local punctuation helper; users should review revisions before publishing.] <br>

## Skill Version(s): <br>
1.4.0 (source: server evidence release.version, target metadata, frontmatter, and changelog released 2026-06-22) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
