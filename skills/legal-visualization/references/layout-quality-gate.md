# Layout Quality Gate

Use this reference when generating or revising legal diagrams.

## Failure Modes

Common unacceptable outputs:

- connector line crosses a node that is not its source or target
- connector label overlaps node text
- multiple relationship lines run through the same corridor
- long outer-loop arrows make the diagram feel like a wiring diagram
- hachure/cross-hatch fills make legal diagrams look noisy or unprofessional
- a node contains a full sentence instead of a legal label
- one diagram mixes contract chain, payment chain, guarantee chain, and litigation consequence without visual separation

## Revision Rules

1. **Add a hub**
   - If many arrows point to the same legal consequence, create a hub such as `责任承担结构`, `核心风险结构`, or `争议焦点`.
   - Connect detailed items to the hub instead of drawing all pairwise connections.

2. **Split the diagram**
   - If a construction dispute has more than 6 actors and more than 8 relationships, split it.
   - Suggested split: `合同与履约关系图` + `付款断裂与索赔路径图`.

3. **Use lanes**
   - Put legal actors in a top lane.
   - Put breach/payment break in a middle lane.
   - Put claims and consequences in a bottom lane.
   - Do not draw vertical lines through unrelated middle-lane nodes.

4. **Use side notes**
   - If a relationship is legally important but visually secondary, put it in a side note or legend rather than drawing another crossing arrow.

5. **Prefer one legal meaning per line**
   - A line should represent one relationship: contract, payment, guarantee, supervision, claim, or risk.
   - Do not use one line to imply two legal meanings.

6. **For Excalidraw legal diagrams, prefer clean whiteboard style**
   - Use solid light fills, not hachure/cross-hatch.
   - Keep roughness low.
   - Use straight or orthogonal arrows whenever possible.
   - Use color to express legal meaning, not heavy shading.

## Draw.io Validation Script

For `.drawio` files, run:

```bash
# Run from the legal-visualization skill root (the folder that contains SKILL.md)
python3 scripts/validate_drawio_layout.py diagram.drawio
```

The script detects common geometry problems where an edge segment crosses a non-endpoint vertex box. It is an approximation, not a replacement for visual review.

Interpretation:

- `PASS`: no obvious edge-through-node issue detected.
- `WARN`: inspect and revise the named edge or node.

When the script warns, revise by:

- moving the crossed node
- routing the edge around the outside
- adding a hub
- splitting the diagram

For `.excalidraw` files, run:

```bash
python3 scripts/validate_excalidraw_layout.py diagram.excalidraw
```

This script checks for:

- arrows crossing rectangle nodes
- hachure/cross-hatch fills
- high roughness on legal nodes

Warnings must be fixed before final delivery unless the user explicitly wants a rough sketch.
