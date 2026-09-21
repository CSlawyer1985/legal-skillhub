# Implementation Rules

Read this file right before generating or revising the HTML deck.

## Core build requirements

- Produce a single-file HTML deck.
- Keep HTML, CSS, and JavaScript in the same file.
- Do not load Bootstrap, Tailwind, or other external CSS frameworks.
- Fonts may load from Google Fonts; keep the rest inline.
- Use 16:9 slides by default and support full-screen presentation.
- Make every slide fill the viewport and keep `overflow: hidden`.
- Use `clamp(min, viewport, max)` for type and spacing instead of fixed pixel typography.
- Keep internal skill paths relative so the skill folder can be copied into a GitHub repo without rewriting links.

## Motion and navigation

- Use staggered reveal only where sequencing improves comprehension.
- On entry, reveal items with fade and a slight upward motion unless the chosen style says fade-only.
- Use `0.3s-0.5s` transitions with `ease` or `cubic-bezier(0.4, 0, 0.2, 1)`.
- Do not replay reveal animations after the content has already appeared.
- Keyboard controls:
  - `ArrowRight` or `Space`: next
  - `ArrowLeft`: previous
- Show navigation state and current page / total page count.
- Keep page number visible at the bottom-right unless the chosen style uses a stronger placement convention.

## Shared layout rules

- Use clear title hierarchy for `h1`, `h2`, `h3`, body text, and annotations.
- Keep title line height around `1.1-1.2`.
- Keep body line height around `1.7-1.9`.
- Use only font weights `300`, `400`, `600`, and `700`.
- Avoid letter spacing for Chinese text. Use it sparingly for Latin display text when useful.
- Use content padding around `clamp(1.4rem, 3.2vw, 2.8rem)`.
- Use CSS Grid for two-column and three-column layouts.
- Give cards at least `0.8rem` internal padding.

## Shared component set

Implement each design language with its own component styling. Do not collapse all themes into a single generic card system.

Required classes:

- `.slide`
- `.slide.cover`
- `.slide.part-transition`
- `.kicker`
- `h1`, `h2`, `h3`
- `.card`
- `.card-highlight`
- `.card-warning`
- `.grid-2`
- `.grid-3`
- `.code-block`
- `.reveal`
- `.nav`

Optional when useful:

- table with zebra striping
- timeline or flow diagram in CSS
- data card with large number and caption
- quote / pull-quote slide

## Hard aesthetic constraints

Always obey:

- Define the full palette and font stack in `:root`.
- Limit a single slide to no more than 3 background colors.
- Keep four levels of text color hierarchy: primary, secondary, helper, placeholder.
- Reference colors through variables instead of hard-coded repeated values.
- Keep only one or two card languages per slide.

Never do:

- Do not use `#000000` or `#ffffff` as the dominant page color.
- Do not use rainbow palettes or casual multicolor gradients.
- Do not use more than 3 fonts on one slide.
- Do not exceed `0 4px 16px rgba(0,0,0,0.12)` for box shadows.
- Do not use `Inter`, `Roboto`, `Arial`, or `system-ui` as the main font.
- Do not bold more than 30% of a paragraph.
- Do not use emoji as decorative design substitutes.
- Do not use animation durations over `0.6s`.

## Editability and save stack

When the user wants an editable deck, include this save stack:

- Automatic local autosave to `localStorage` after edits.
- A visible save button that saves the full HTML document, not only the slide body.
- `Ctrl+S` / `Cmd+S` mapped to the same full-document save action.
- Full-document serialization so all current edits, notes, inserted images, and layout changes are written into the saved HTML.
- Direct overwrite through the File System Access API when the browser supports it and the user grants permission.
- Download fallback for browsers or contexts that cannot write back directly.
- Separate export / save-as action when the user wants a duplicate file.

Prefer this behavior:

1. Autosave silently to local draft storage on every meaningful edit.
2. If a writable file handle already exists, let autosave also sync the actual HTML file.
3. On manual save, try direct file save first.
4. If direct save is unavailable, download the serialized HTML so the user still gets a complete updated file.

When the user wants a clean delivery deck, provide a presentation-only variant without editor chrome.

## Print / PDF export

When the user asks for PDF export compatibility, include:

```css
@media print {
  .slide {
    break-after: page;
    width: 297mm;
    height: 167mm;
  }

  .nav,
  .slide-num-global {
    display: none;
  }
}
```

Ensure each slide prints as a separate 16:9 landscape page.
