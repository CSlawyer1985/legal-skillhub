## Description: <br>
Discover and classify a live website's legal and compliance pages by triangulating sitemap.xml, robots.txt, footer and navigation links, and common compliance path guesses, then recording verbatim-grounded page classifications, controlling entities, mismatches, and observations for downstream routing. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[dangsllc](https://clawhub.ai/user/dangsllc) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Compliance, legal operations, and engineering users can use this skill to discover posted legal and compliance documents on a public website and prepare a manifest for later review or routing. It helps identify candidate privacy, HIPAA, terms, consent, accessibility, and similar pages without performing a compliance assessment. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill fetches public pages from a user-provided domain and tries common legal-page paths, including public robots.txt-disallowed paths. <br>
Mitigation: Run it only against domains you are authorized to inspect and review the generated manifest before relying on it. <br>
Risk: The skill is designed for discovery and classification, not legal or compliance judgment. <br>
Mitigation: Use the manifest as routing evidence for a qualified downstream review rather than as a compliance conclusion. <br>


## Reference(s): <br>
- [ClawHub listing](https://clawhub.ai/dangsllc/skills/legal-page-discovery) <br>


## Skill Output: <br>
**Output Type(s):** [Markdown, JSON, Shell commands, Guidance] <br>
**Output Format:** [Markdown manifest and JSON manifest] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Writes local discovery manifests and includes URLs, source signals, classifications, controlling entities, mismatch flags, salient observations, and discoverability notes.] <br>

## Skill Version(s): <br>
1.0.0 (source: ClawHub release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
