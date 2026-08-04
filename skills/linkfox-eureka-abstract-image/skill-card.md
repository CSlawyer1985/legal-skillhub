## Description: <br>
Retrieves patent abstract drawings from the Eureka patent data platform by patent ID or publication number and returns image paths and saved JSON results. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and developers use this skill to retrieve abstract drawings for one or more patents when they already have patent IDs or publication numbers. It is suited for patent illustration lookup, not full patent search, claims analysis, legal status checks, family analysis, citation review, valuation, or infringement analysis. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill uses an external API key and makes network calls to LinkFox and Eureka services. <br>
Mitigation: Run it only in workspaces where those outbound requests and credentials are acceptable, and review API-key handling before use. <br>
Risk: The skill writes complete API responses into a local linkfox session data directory. <br>
Mitigation: Use a dedicated workspace and avoid confidential patent lookups unless retention and redaction expectations are clear. <br>
Risk: The skill can send feedback data to a separate endpoint. <br>
Mitigation: Review feedback behavior and avoid including sensitive user or patent information in feedback content. <br>
Risk: Patent image retrieval consumes account credits and may cost more for larger result sets. <br>
Mitigation: Confirm the user wants to continue before repeated or high-volume lookups, and rely on the 24-hour cache for repeated identical requests. <br>


## Reference(s): <br>
- [Eureka abstract image API reference](references/api.md) <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-eureka-abstract-image) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, Shell commands, Files, Guidance] <br>
**Output Format:** [Markdown summaries and image embeds, shell command examples, and JSON API responses saved to local files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Supports up to 100 patent identifiers per request; writes complete responses to a linkfox session data directory; uses a 24-hour local cache; large responses are summarized unless inline output is requested.] <br>

## Skill Version(s): <br>
1.0.5 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
