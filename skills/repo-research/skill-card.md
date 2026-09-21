## Description: <br>
Analyzes one or more GitHub repositories, compares them with local projects, and generates structured research reports with architecture, dependency, quality, security, and integration insights. <br>

This skill is for research and development only. <br>

## Publisher: <br>
[cat-xierluo](https://clawhub.ai/user/cat-xierluo) <br>

### License/Terms of Use: <br>
CC BY-NC-SA 4.0 <br>


## Use Case: <br>
Developers and engineers use Repo Research to study GitHub repositories, compare multiple projects or a local codebase, and produce Markdown reports with practical improvement ideas. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill can clone arbitrary GitHub repositories into local research folders. <br>
Mitigation: Review repository URLs before cloning and run analysis in a workspace where cloned content can be inspected or removed. <br>
Risk: Topic search mode can install or invoke the optional find-skills dependency. <br>
Mitigation: Require explicit approval before installing find-skills or using topic-driven search. <br>
Risk: The bundled config.yaml contains a user-specific absolute output path. <br>
Mitigation: Edit or remove artifact/assets/config.yaml so reports are written only to an approved local directory. <br>


## Reference(s): <br>
- [Repo Research ClawHub listing](https://clawhub.ai/cat-xierluo/repo-research) <br>
- [Publisher profile](https://clawhub.ai/user/cat-xierluo) <br>
- [Source homepage from ClawHub metadata](https://github.com/cat-xierluo/legal-skills) <br>
- [Optional find-skills dependency](https://skills.sh/vercel-labs/skills/find-skills) <br>
- [Single repository report template](artifact/assets/report-template.md) <br>
- [Topic research report template](artifact/assets/topic-research-template.md) <br>
- [Comparison report template](artifact/assets/comparison-template.md) <br>
- [Configuration example](artifact/assets/config.example.yaml) <br>


## Skill Output: <br>
**Output Type(s):** [Markdown, Shell commands, Configuration, Guidance] <br>
**Output Format:** [Markdown reports, Markdown summaries, inline shell commands, and YAML configuration guidance] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Reports are written under a configurable research output directory; the bundled config.yaml contains a local absolute path that should be changed before use.] <br>

## Skill Version(s): <br>
0.7.0 (source: SKILL.md frontmatter, CHANGELOG, ClawHub release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
