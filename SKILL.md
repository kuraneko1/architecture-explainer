---
name: architecture-explainer
description: Create source-backed model and system architecture explanation diagrams in the QSA figure style, with small/mid/large detail levels, semantic multicolor palettes, and text-aware arrow routing. Use for a single architecture, before/after migration, or explaining layer and data flows as PNG/SVG figures.
---

# Architecture Explainer

Create a quiet, structural figure: pale modules, thin rules, repeated-layer strips, split attention/FFN boxes and connected detail insets. Keep component names and meaningful quantities in the image; place prose, evidence and caveats in the accompanying notes. Primary deliverables are PNG and SVG. HTML is optional working material.

## Choose detail before drawing

- **small**: simplified overview, repeated groups, primary branches; internals can be collapsed. Use for quick overviews, model cards, presentation summaries, or explicit small requests.
- **mid**: mechanism explanation; expand the important alternatives separately (e.g. local and global attention), show their data inputs and outputs, keep common projections and FFN summarized. Use for explaining how an architecture works or explicit mid requests.
- **large**: implementation-oriented architecture; expand normalization, residual branches, projection-specific paths, cache read/update and FFN where evidenced. Use for a detailed technical explanation, an implementation diagram, or explicit large requests. This is not automatically a complete kernel-level execution graph.

If the query clearly states purpose/detail, choose it and briefly state the choice without asking. If purpose and desired detail are unclear, ask which of small/mid/large they need **before committing the layout**, and continue source inspection while waiting. Do not silently select mid. A reference to an existing tier inherits that tier. If several levels are requested, produce them from the same facts with increasing expansion, not by resizing fonts. See [detail-levels.md](references/detail-levels.md).

## Use the existing diagram skills

This is a wrapper around the installed `archify` and `benchmark-rebuild` workflows. Locate their SKILL.md through the current skills catalog; do not assume another host has this machine's absolute paths. For a fresh topology, use Archify for semantic topology and its applicable validation. For an image in the QSA visual grammar or reference reproduction, use benchmark-rebuild for the final figure, semantic palette and reusable geometry. Their artifacts and receipts cover their actual outputs only; do not claim an Archify HTML receipt validates a separately drawn PNG. User requests and this wrapper's image-first delivery/detail/palette decisions take priority over a base skill's default HTML output.

## Facts, levels and palette

Read the model/config/implementation (or supplied system facts), record source revision, and maintain a shared fact specification across tiers. Distinguish fixed layer types from routers; parallel execution from alternative diagrams; training weights from runtime caches; equations from explanatory simplifications. Never copy QSA-specific internals, freeze locks, MTP or image branches into an unrelated model. Shared layout is not shared architecture. Omit unsupported paths rather than inventing them.

Use [palettes.json](assets/palettes.json). Default: **jade-violet**, the green/purple QSA palette. Other presets: ocean, amber-indigo, accessible, monochrome. Bind named semantic roles (local/global, before/after, additions etc.) explicitly; do not assign by sorted index. Neutral modules stay neutral. More semantic roles use the preset's third/fourth colors only when that distinction helps reading. Users can request a palette by name or give colors. Keep a palette change independent of geometry and detail. See [rendering.md](references/rendering.md).

Visual anchors are bundled as `assets/reference-qsa.png` and `assets/examples/ripple-{small,mid,large}-ja-preview.png`; use them for visual grammar, not architectural facts. Mid/large scene JSON examples are editable. `assets/palette-preview.png` shows all five palette families.

For **all small/mid/large** figures, use color to guide reading, rather than giving every component equal gray weight. Keep the same role-to-color meaning across tiers; change how many components are expanded, not what a color means. Keep two independent meanings: primary local/global (or before/after) identity, and reusable auxiliary paths. With jade-violet, primary paths stay green/purple, KV/data paths are blue (`memory`, alias of fourth), learned gate/blend paths are amber (`modulation`, alias of third), and explicit residual bypasses are muted dashed lines. Reuse the same function mapping in every inset. A K normalization on the blue KV path can inherit blue; ordinary norms remain neutral. A combined Q/K box in small/mid can remain neutral while the outgoing Q and K paths use primary and memory colors. A node that combines V blending with projection can use memory fill and an amber incoming mixing path.

Limit solid accent fills to a few reading anchors (`emphasis: true`): attention alone is enough in small/mid; attention and FFN output projection work in large. Keep other fills pale. Main arrows can be slightly heavier (`width: 1.7`) while auxiliary paths stay around 1.2–1.3. Include a compact key for the roles actually visible at that tier. Do not draw residual wires or other operations merely to complete a color key when they are summarized as equations or omitted at the chosen detail. Quiet numbered stage bands are useful in a long large figure, but need not be added to simpler tiers. These are explanatory grouping, not new computational modules. Keep caption/route collision checks active. Palette changes preserve role bindings; don't promise that every preset uses literal blue/amber.

## Prevent arrow/text and arrow/arrow collisions

Use `scripts/diagram.py` for custom figure rendering or import its router into an existing renderer. Measure all labels in the final font first. Route arrows around measured text rectangles and node rectangles with clearance, including their arrowheads. Parent frames are not filled obstacles. Retain endpoints/ports, direction and meaning; route repair must not alter topology. The script checks resulting routes and refuses export if a collision or unroutable edge remains. Route geometry, evidence, and validation reports are saved next to the figure.

Reserve space around already routed wires and future ports as well. Route short connections first; retry competing connections in another order. Detect perpendicular crossings, collinear overlap and T-contacts. Only a short stem at a genuinely common port or an explicitly declared bus junction may be shared. Do not exempt whole edges just because they share a source: they may intersect again elsewhere. Preserve declared junction anchors during rerouting.

The renderer writes a routing-failure report and refuses export if unresolved wire crossings/overlaps remain. Repair placement/ports or add an explicit semantically valid bus and rerun; never turn off the check or disguise a crossing with a gap/bridge without the user's request. Avoid claiming universal planar routing: some graphs or fixed ports require a layout change. This check proves measured text/arrow, node/arrow and wire/wire clearance, not general visual quality. Inspect the final PNG for crowded detours and misleading intersections. Never hide a collision by drawing an opaque label background over a data arrow. Verify JP/EN exports separately because font metrics differ.

## Deliver

Return the selected figure(s), a short factual statement of their scope, and editable SVG/source plus spec/palette when useful. Keep source evidence and architecture caveats in notes. For bilingual requests keep topology and meaning identical, letting label widths affect routing. Do not add marketing copy, benchmark claims or explanation cards without a reason in the request.
