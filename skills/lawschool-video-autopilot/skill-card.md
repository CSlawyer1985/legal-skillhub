## Description: <br>
Automate online law course video watching on 律师云学院 (lawschool.lawyerpass.com), including course enrollment, video completion checks, course switching, progress state, and notifications. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[vanishedzhou](https://clawhub.ai/user/vanishedzhou) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and agents use this skill to automate a logged-in lawschool.lawyerpass.com Chrome session for course enrollment, video playback monitoring, completion tracking, and progress notifications. <br>

### Deployment Geography for Use: <br>
China <br>

## Known Risks and Mitigations: <br>
Risk: The skill gives an automated agent control of a logged-in Chrome tab and can enroll in courses and advance course-completion records. <br>
Mitigation: Use a dedicated browser profile, review the course queue before execution, and supervise initial operation. <br>
Risk: A recurring background cron job can continue controlling playback after the desired courses are complete. <br>
Mitigation: Manually disable or delete the video-check-loop cron job when finished. <br>
Risk: Progress state and notifications can expose course activity to the configured WeCom/OpenClaw message group. <br>
Mitigation: Use the intended notification group only and avoid placing unnecessary sensitive data in video_state.json. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/vanishedzhou/sh-lawschool-video-autopilot) <br>
- [Workflow](references/workflow.md) <br>
- [Known Issues](references/known-issues.md) <br>
- [State Schema](references/state-schema.md) <br>
- [State Initialization Script](scripts/lawschool_init_state.py) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with JavaScript, JSON, and shell command snippets] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces browser automation steps, cron setup guidance, and a local state-file schema; it does not produce media content.] <br>

## Skill Version(s): <br>
1.0.0 (source: ClawHub release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
