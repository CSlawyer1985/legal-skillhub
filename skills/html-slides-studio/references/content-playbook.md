# Content Workflow

Use this file to collect inputs and plan the deck before writing code.

## Source-of-truth rule

- Prefer a detailed outline or manuscript.
- Do not create an entire talk from nothing unless the user explicitly asks.
- If the outline is thin, ask for the missing chapter goals, core claims, examples, and demo moments.

## Required inputs

Collect only the fields the user has not already provided:

1. Talk title
2. Subtitle or keywords (optional)
3. Speaker name, organization, and date
4. Audience profile
5. Duration
6. Detailed outline: chapter titles plus core points
7. Special requirements: must-include content, code blocks, tables, screenshots, demos, or fixed assets

## Send this template first when style is not yet confirmed

```text
椋庢牸閫夋嫨锛歔A / B / C / D]

婕旇鏍囬锛?鍓爣棰?鍏抽敭璇嶏細
婕旇鑰咃細
鏃堕暱锛?鍚紬锛?
澶х翰锛?Part 1 - [鏍囬]
  1.1 [灏忚妭]
  1.2 [灏忚妭]
Part 2 - [鏍囬]
  2.1 [灏忚妭]
  ...

鐗规畩瑕佹眰锛?```

## Page-planning rules

Use roughly 90 seconds per slide unless the content or demo format clearly requires a different rhythm.

| Duration | Target slide count | Rhythm |
| --- | --- | --- |
| 30 minutes | 18-22 slides | About 90 seconds per slide |
| 45 minutes | 24-30 slides | About 90 seconds per slide |
| 60 minutes | 32-40 slides | About 90 seconds per slide |

## Required slide types

Every planned deck must include:

- Cover: 1 slide
- Self-introduction or icebreaker: 1-2 slides
- Background or problem framing: 1-2 slides
- Roadmap / today's agenda: 1 slide
- Part-transition slides: 1 slide per major section
- Content slides: the main body
- Closing / takeaway: 1 slide
- Q&A: 1 slide

## Planning output format

Before writing any HTML, list the full deck structure slide by slide. Use concise one-line descriptions such as:

1. Cover
2. Why this matters now
3. Today's roadmap
4. Part 1 transition
5. Chatbot pain points
6. IDE working model
7. Demo: CLI flow
...

Then wait for explicit confirmation before generating code.

## Density rules

- Keep each slide under 7 independent information blocks.
- Split dense frameworks, matrices, or SOPs across multiple slides.
- Use slides for structure and emphasis, not paragraphs.
- Move long phrasing to speaker notes whenever possible.