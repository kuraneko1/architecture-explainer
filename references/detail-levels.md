# Detail selection

Tier changes must explain more structure, not show more words on the same boxes.

Use consistent semantic colors at all three levels. Small/mid should use the same primary/KV/gate colors as large, with fewer solid-fill anchors and a smaller key. Only explicit residual wires get a residual dash; an equation summarizing them does not require invented wires. Stage bands belong where they help the density of the chosen layout, rather than being mandatory at every level.

| Tier | Local/global attention example | Common layer details |
|---|---|---|
| small | One inset with labeled fixed alternatives | Q/K norm, V-only blend, output gate may be compact; residual equations acceptable |
| mid | Separate local and global mechanisms; local Q/K RoPE vs global NoPE, window mask vs causal full history, explicit KV input | Shared input projections, gate and layer wrapper kept compact |
| large | Explicit Q/K/V, normalization and positions, cache write/read, GQA, masks, output gate and output projection | Distinct pre/post norm, both residual branches, evidenced clipped SwiGLU branch; separate embedding seed |

Always preserve true counts, branch meanings and layer order. Large must retain readable type by expanding the canvas, not by shrinking it. A tall figure may need a full-resolution PNG and preview. Do not imply cache eviction merely because local attention has a short visibility window. An inset showing both local and global is an explanation of two layer types; label their fixed nature so it cannot look like an adaptive runtime router.

Examples: “HFに貼る簡単な概要” -> small; “局所注意と全域注意の仕組みまで説明” -> mid; “キャッシュ・各Norm・FFNの分岐まで実装を追いたい” -> large. “このモデルの図を作って” with no purpose -> ask. “今のsmallを別パレットに” -> retain small, no detail question.
