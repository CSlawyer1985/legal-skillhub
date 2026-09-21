# Design Languages

Read this file after the user chooses a design language. Apply the selected system consistently across cover, part transitions, content slides, notes, and navigation. Never mix systems on a single deck.

## Global expectations

- Match or exceed the user's approved reference deck in visual quality and interaction quality.
- Build a full design system, not isolated pretty slides.
- Keep typography, spacing, card treatment, navigation, and motion coherent.
- Use CSS variables in `:root` for the complete palette and font stack.
- Avoid generic defaults.

## A 路 Warm Editorial / 鏆栫焊缂栬緫

Asset starting point: `assets/template-a-warm-editorial.html` or `assets/slides-template-v3.html`

```css
:root {
  --bg:        #F0EBE0;
  --bg-2:      #E8E3D8;
  --accent:    #0E7A75;
  --accent-2:  #CB5F3D;
  --text-main: #1A2A28;
  --text-sub:  #4A5A58;
  --text-faint:#8A9A98;
  --line:      rgba(14,122,117,0.18);
  --f-display: 'Playfair Display', Georgia, serif;
  --f-body:    'Source Sans 3', 'Helvetica Neue', sans-serif;
  --f-mono:    'JetBrains Mono', monospace;
}
```

Use a warm paper field, serif cover typography, editorial cards, and soft contrast. Keep the result trustworthy, warm, and polished.

Required cues:
- Large serif title on the cover.
- Fine monospace or light sans subtitle.
- Kicker label with soft green background and left accent line.
- Standard card with left accent border.
- `card-highlight` in the primary color family.
- `card-warning` in the orange-red family.
- Dark part-transition slide with a restrained green accent line.
- Dark code blocks with a 3px green edge.

## B 路 Dark Terminal / 娣辩┖缁堢

Asset starting point: `assets/template-b-terminal.html`

```css
:root {
  --bg:          #0A0E0D;
  --bg-panel:    #141A18;
  --green:       #00FF88;
  --green-dim:   #00CC6A;
  --green-faint: rgba(0,255,136,0.12);
  --amber:       #FFB340;
  --red:         #FF4F4F;
  --text-main:   #D4E8D4;
  --text-sub:    #7A9E88;
  --text-faint:  #3A5040;
  --f-mono:      'JetBrains Mono', 'Fira Code', monospace;
  --f-sans:      'IBM Plex Sans', sans-serif;
}
```

Use a technical, machine-like presentation language with terminal chrome and restrained glow.

Required cues:
- CRT scanline overlay at low opacity.
- Terminal title bar at the top of each slide.
- Code blocks with prompt, parameter, and comment color hierarchy.
- Kicker labels prefixed with `//`.
- Card left borders: green for standard, amber for caution, red for warning.
- Session status indicator in a corner.
- Part-transition slide with module progress states.

## C 路 Swiss Grid / 鍖呰豹鏂綉鏍?
Asset starting point: `assets/template-c-swiss.html`

```css
:root {
  --bg:        #F2F0EB;
  --ink:       #0D0D0D;
  --mid:       #555555;
  --faint:     #AAAAAA;
  --accent:    #E63329;
  --f-display: 'Bebas Neue', Impact, sans-serif;
  --f-body:    'DM Sans', 'Helvetica Neue', sans-serif;
  --f-mono:    'Space Mono', monospace;
}
```

Use strict grid logic, bold display type, strong horizontal divisions, and confident structural contrast.

Required cues:
- Light grid overlay in the background.
- Clear horizontal divider separating title and content zones.
- Large faint page number as a composition element.
- Custom red cursor treatment if the deck uses pointer effects.
- Content rows with index, heading, and body rhythm.
- Part-transition slide with oversized number and progress bar.
- Prefer line-based separation over filled rounded cards.

## D 路 Japanese Ink / 鏃ュ紡澧ㄧ

Asset starting point: `assets/template-d-ink.html`

```css
:root {
  --paper:     #F7F4EE;
  --ink:       #1A1410;
  --ink-mid:   #4A4540;
  --ink-soft:  #8A8480;
  --ink-faint: #C8C4BC;
  --red:       #C0392B;
  --f-serif:   'Cormorant Garamond', 'Noto Serif SC', Georgia, serif;
  --f-sans:    'Noto Sans Mono', monospace;
}
```

Use large breathing room, paper texture, restrained movement, and a mature narrative tone.

Required cues:
- Subtle paper/noise texture.
- Vertical page marker on the right side with a red dot.
- Serif titles with mono labels.
- Lower information density than the other systems.
- Red italic emphasis instead of bold.
- Very quiet part-transition slide with oversized near-invisible number.
- Fade-only reveal motion.
- Quote blocks with a thin red vertical rule.