# Style 9: Claude Lite

Warm paper aesthetic with Claude orange accent. Inspired by Anthropic's editorial design — restrained, paper-like, with one accent color for the core idea.

## Colors

```
Background:     #FAF9F5  (paper)
Surface:        #F5F4ED  (box default fill)
Line:           #E8E6DC  (box border, dividers)
Text primary:   #141413  (near black)
Text soft:      #3D3D3A  (body text)
Text muted:     #73726C  (labels, annotations)
Gray:           #B0AEA5  (normal connection lines)

Claude Orange:
  orange:       #D97757  (main accent — core module border/fill, primary path)
  orange-soft:  #F6EEDF  (light orange background)
  orange-deep:  #A94F35  (deep orange text or dark emphasis)

Supporting:
  blue:         #6A9BCC  (data flow, information, external input)
  blue-soft:    #D6E4F6  (light blue background)
  green:        #788C5D  (verification, success, completed state)
  green-soft:   #E9F1DC  (light green background)
```

## Color Semantics (IMPORTANT)

- **Orange** = core focus / primary path / current module
- **Blue** = data, context, input/output
- **Green** = verified, completed, correct result
- **Gray** = normal path, secondary module, background info

Do NOT make the whole page orange. Orange fill is reserved for 1-2 truly important modules per diagram.

## Typography

```
font-family: 'Anthropic Sans', 'Inter', 'Aptos', 'Helvetica Neue',
             'PingFang SC', 'Noto Sans SC', 'Source Han Sans SC',
             'Microsoft YaHei', sans-serif
font-size:   14px labels, 12px sub-labels, 18px titles
font-weight: 500-600 for titles, 400 for body, 500 for labels

Do NOT use 800/900 weight.
```

## Box Styles

### Default Box (most nodes)

```xml
<rect rx="6" fill="#F5F4ED" stroke="#E8E6DC" stroke-width="1"/>
<text fill="#141413" font-size="14" font-weight="500"/>
```

### Important Outline Box (key but not primary)

```xml
<rect rx="6" fill="#FAF9F5" stroke="#D97757" stroke-width="2"/>
<text fill="#141413" font-size="14" font-weight="500"/>
```

### Orange Fill Box (THE core module — max 1-2 per diagram)

```xml
<rect rx="6" fill="#D97757" stroke="#D97757" stroke-width="1"/>
<text fill="#FFFFFF" font-size="14" font-weight="500"/>
```

### Soft Orange Box (highlighted secondary)

```xml
<rect rx="6" fill="#F6EEDF" stroke="#D97757" stroke-width="1"/>
<text fill="#141413" font-size="14" font-weight="500"/>
```

### Data Box (memory, database, context)

```xml
<rect rx="6" fill="#FAF9F5" stroke="#6A9BCC" stroke-width="1.5"/>
<text fill="#141413" font-size="14" font-weight="500"/>
```

### Verified Box (success, validated output)

```xml
<rect rx="6" fill="#FAF9F5" stroke="#788C5D" stroke-width="1.5"/>
<text fill="#141413" font-size="14" font-weight="500"/>
```

### Muted Box (external, optional, secondary)

```xml
<rect rx="6" fill="#F5F4ED" stroke="#B0AEA5" stroke-width="1" stroke-dasharray="4,3"/>
<text fill="#3D3D3A" font-size="14" font-weight="500"/>
```

## Arrows

```xml
<defs>
  <marker id="arrow-orange" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#D97757"/>
  </marker>
  <marker id="arrow-blue" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#6A9BCC"/>
  </marker>
  <marker id="arrow-green" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#788C5D"/>
  </marker>
  <marker id="arrow-gray" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#B0AEA5"/>
  </marker>
</defs>
```

| Line Type | Color | Width | Style | Usage |
|-----------|-------|-------|-------|-------|
| Primary path | `#D97757` | 2px | solid | Core flow, main request/response |
| Data flow | `#6A9BCC` | 1.5px | solid | Data, context, read/write |
| Verified path | `#788C5D` | 1.5px | solid | Validation, success output |
| Normal link | `#B0AEA5` | 1.5px | solid | Secondary connections |
| Optional/external | `#B0AEA5` | 1.5px | dashed | External, optional, return |

## Arrow Labels

```xml
<text fill="#73726C" font-size="12" text-anchor="middle">label</text>
```

Labels use `text-muted` color, 12px. No background rect needed on paper background.

## Layer / Container

```xml
<rect rx="6" fill="#F5F4ED" fill-opacity="0.5" stroke="#E8E6DC" stroke-width="1"/>
<text fill="#73726C" font-size="11" font-weight="500" letter-spacing="0.06em">LAYER NAME</text>
```

Layer containers use semi-transparent surface fill with line-color border.
Layer labels in muted text, ALL CAPS, 11px, letter-spacing 0.06em.

## Legend (On-Demand)

Include a legend **only when** the diagram uses 3+ distinct arrow colors or line styles that readers cannot infer from context. Legend entries must be **arrow types only** — do NOT add entries for box fill colors (orange fill = core, blue border = data, etc. is self-explanatory from the diagram).

```xml
<!-- Example: arrow-only legend (only add if 3+ arrow semantics exist) -->
<g transform="translate(x, y)">
  <!-- Orange line -->
  <line x1="0" y1="0" x2="24" y2="0" stroke="#D97757" stroke-width="2"
        marker-end="url(#arrow-orange)"/>
  <text x="30" y="4" fill="#73726C" font-size="11">主路径</text>

  <!-- Blue line -->
  <line x1="100" y1="0" x2="124" y2="0" stroke="#6A9BCC" stroke-width="1.5"
        marker-end="url(#arrow-blue)"/>
  <text x="130" y="4" fill="#73726C" font-size="11">数据流</text>

  <!-- Gray dashed -->
  <line x1="200" y1="0" x2="224" y2="0" stroke="#B0AEA5" stroke-width="1.5"
        stroke-dasharray="4,3" marker-end="url(#arrow-gray)"/>
  <text x="230" y="4" fill="#73726C" font-size="11">返回</text>
</g>
```

## SVG Template

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 600" width="960" height="600">
  <style>
    text { font-family: 'Anthropic Sans', 'Inter', 'Aptos', 'Helvetica Neue',
           'PingFang SC', 'Noto Sans SC', 'Source Han Sans SC',
           'Microsoft YaHei', sans-serif; }
  </style>
  <defs>
    <!-- arrow markers -->
  </defs>
  <!-- Paper background -->
  <rect width="960" height="600" fill="#FAF9F5"/>
  <!-- diagram content -->
</svg>
```

## Design Philosophy

- **Warm paper feel**: `#FAF9F5` background, not pure white
- **One accent**: Claude orange `#D97757` is THE hero color — use sparingly
- **Semantic color**: blue=data, green=verified, gray=secondary
- **Thin strokes**: 1-2px, never heavy 2.5px borders
- **Small radius**: 6px, not 12px
- **Medium weight**: 400-600, never 800/900
- **Clear hierarchy**: orange fill > orange outline > data border > default > muted

## Arrow Routing Rules (CRITICAL)

### No Arrow-Through-Box

Arrows MUST NOT pass through the interior of any component box. When a source node needs to connect to multiple non-adjacent targets in the same row:

1. **Chain pattern** (preferred): Connect source → first target, then first → second, second → third. Use orange for the primary link, gray for subsequent links.
2. **Bus pattern**: Route a horizontal line below the row, with vertical drops up to each target.
3. **Omit arrows**: If spatial arrangement + visual hierarchy (fill color, border) already conveys the relationship, skip intra-layer arrows entirely.

**NEVER** draw a straight arrow from a leftmost source to a rightmost target that crosses over intermediate boxes.

### Inter-Layer Arrows

Use a single centered vertical arrow between layers. Direction is always top-to-bottom (request flow). Color by semantic:
- Orange `#D97757`: Primary orchestration flow (L1→L2, L2→L3)
- Blue `#6A9BCC`: Data flow (L3→L4)
- Gray `#B0AEA5`: Secondary / return paths

Avoid: purple gradients, neon, glassmorphism, heavy shadows, decorative AI visuals, overly saturated fills.
