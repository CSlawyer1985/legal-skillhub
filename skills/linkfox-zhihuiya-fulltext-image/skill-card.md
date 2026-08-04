## Description: <br>
Retrieves full-text patent images, drawings, diagrams, and related metadata from the Zhihuiya patent data service by patent ID or publication number. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers, patent analysts, and agents use this skill to fetch and present patent drawing metadata and image download paths for a specific patent. It is intended for targeted retrieval by patent ID or publication number, not broad patent search or legal-status analysis. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill makes authenticated external API calls and consumes paid LinkFox credits for patent image retrieval. <br>
Mitigation: Confirm the user wants to spend credits before repeated calls, constrain the gateway and API-key environment variables, and avoid automatic retries or pagination without approval. <br>
Risk: The script saves complete API responses and cache files under a local linkfox workspace path, which may include patent identifiers and returned image metadata. <br>
Mitigation: Run it from an appropriate workspace, review saved outputs before sharing, and avoid using sensitive project directories when local response retention is not desired. <br>
Risk: Security evidence marks the release suspicious because it includes feedback, onboarding, and remote installation flows beyond the core retrieval task. <br>
Mitigation: Require explicit approval before submitting feedback or installing onboarding assets, and review those flows separately from normal image retrieval. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-fulltext-image) <br>
- [智慧芽-全文附图 API reference](references/api.md) <br>


## Skill Output: <br>
**Output Type(s):** [guidance, shell commands, JSON, markdown] <br>
**Output Format:** [Markdown guidance with shell command examples, structured tables, and JSON response data or saved JSON files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires either patentId or patentNumber; limit and offset are string parameters; full responses are saved locally and large responses are summarized unless inline output is requested.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
