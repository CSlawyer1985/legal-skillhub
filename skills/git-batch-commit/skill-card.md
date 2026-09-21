## Description: <br>
Helps agents split staged Git changes into focused commits and generate Conventional Commit messages while leaving push, merge, PR, and issue-closing decisions to a separate Git workflow. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[cat-xierluo](https://clawhub.ai/user/cat-xierluo) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and engineers use this skill when staged changes span multiple logical categories and they want an agent to propose grouped commits, generate commit messages, and optionally run the included commit helper. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill may prompt for ClawHub publishing or sync-state changes when a `skills/clawhub-sync/` workflow is present. <br>
Mitigation: Approve sync or publish prompts only after inspecting the publish directory, confirming no secrets or private files are included, and intentionally accepting allowlist or sync-record updates. <br>
Risk: The helper creates Git commits and can reorganize the staged state through local Git commands. <br>
Mitigation: Review proposed groups first, use dry-run mode when uncertain, and keep only intended files staged before creating commits. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/cat-xierluo/git-batch-commit) <br>
- [Publisher profile](https://clawhub.ai/user/cat-xierluo) <br>
- [Homepage](https://github.com/cat-xierluo/legal-skills) <br>
- [Commit Types](references/commit-types.md) <br>
- [Conventional Commits](references/conventional-commits.md) <br>
- [ClawHub Sync Check](references/clawhub-sync-check.md) <br>
- [Subtree Push Check](references/subtree-push-check.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, guidance] <br>
**Output Format:** [Markdown with inline shell commands and generated commit message text] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May invoke local Python helper scripts and Git commands after user review.] <br>

## Skill Version(s): <br>
1.4.1 (source: server release metadata and SKILL.md frontmatter) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
