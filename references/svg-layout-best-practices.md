# SVG Technical Diagram Layout Best Practices

## Universal Layout Rules (Apply to All Styles)

### 1. Component Spacing
> **所有 spacing 取自 `references/spacing-scale.md`(8 基数档位:s/sm/md/lg/xl/2xl/3xl),禁止裸数值。**

- **Minimum clearance between components**: `xl` 48px (edge to edge)
- **Minimum clearance for arrow paths**: `md` 24px from component edges
- **Layer vertical spacing**: `2xl` 64px between horizontal layers
- **Same-layer horizontal gap**: `sm` 16px between components

### 2. Arrow Routing & Connection Points

#### Connection Point Rules
- **Never connect arrows to component corners** - use midpoints of edges
- **Entry/exit points**: 
  - Top edge: `cx ± offset` where offset = 0 for single arrow, ±30px for multiple
  - Bottom edge: same rule
  - Left/right edges: `cy ± offset`
- **Clearance from corners**: minimum 20px

#### Arrow Path Routing
- **Avoid diagonal lines crossing components** - use orthogonal routing (L-shaped paths)
- **For curved arrows**: 
  - Control point should be at least 40px away from any component edge
  - Use intermediate waypoints for complex routing: `M x1,y1 L x2,y2 Q cx,cy x3,y3`
- **Multiple arrows between same layers**: stagger Y-coordinates by 15-20px to avoid overlap

#### Arrow Overlap Prevention
```svg
<!-- Bad: diagonal arrow crosses component -->
<path d="M 200,100 L 600,400"/>

<!-- Good: orthogonal routing around component -->
<path d="M 200,100 L 200,250 L 600,250 L 600,400"/>

<!-- Good: curved with safe control point -->
<path d="M 200,100 Q 400,200 600,400"/>
<!-- Control point (400,200) is 50px+ away from any component -->
```

### 3. Arrow Label Placement
- **Position**: midpoint of arrow path, offset by 5-10px perpendicular to arrow direction
- **Background rect**: ALWAYS include, with:
  - Padding: 4px horizontal, 2px vertical
  - Fill: match background color
  - Opacity: 0.9-0.95
- **Safety distance**: 15px minimum from any component edge
- **Multiple converging arrows**: stagger label positions vertically by 20px

### 4. Component Overlap Detection
Before finalizing SVG, check:
- No component bounding boxes overlap (8px safety margin)
- No arrow paths pass through component interiors (except intentional tunneling with dashed style)
- No text labels overlap with components or other labels

### 5. Z-Index Layering (SVG render order)
```svg
<!-- Render order (top to bottom = back to front): -->
1. Background rect
2. Grouping containers (dashed rects)
3. Arrow paths
4. Arrow label background rects
5. Components (boxes, cylinders, etc.)
6. Component text
7. Arrow label text
8. Legend
```

## Style-Specific Enhancements

### Style-1: Flat Icon Clean
- **Perfect alignment**: snap all coordinates to 8px grid
- **Sharp corners**: rx="8" ry="8" for rounded rects (consistent)
- **Arrows**: thin (1.5-2px), filled polygon markers
- **No shadows**: flat design principle

### Style-6: Claude Official Warm
- **Soft shadows**: `<feDropShadow dx="0" dy="2" stdDeviation="6" flood-color="#00000008"/>`
- **Rounded corners**: rx="12" ry="12" (more rounded than Style-1)
- **Arrows**: medium weight (2px), subtle markers

## Text-Rect Alignment Constraints (Critical)

These constraints prevent the most common recurring bug: text overflowing or clipping at the bottom of card/rect containers. **Every multi-card diagram MUST follow these rules.**

### C1: Computed Heights — Never Handwrite rect height
Never manually estimate or hardcode `<rect height="...">` for content cards. Use a `card_layout()` helper function that calculates height from content:
```python
def card_layout(y_start, lines_data, pad_top=16, pad_bottom=16, title_gap=24, sub_gap=24, detail_gap=16):
    """Returns (height, [(y, class, text, fill), ...])"""
    entries = []
    y = y_start + pad_top
    for i, (cls, txt, fill) in enumerate(lines_data):
        entries.append((y, cls, txt, fill))
        if i == 0:
            y += title_gap
        elif cls == 'node-detail':
            y += detail_gap
        else:
            y += sub_gap
    last_y = entries[-1][0]
    height = last_y + pad_bottom - y_start
    return height, entries
```

### C2: Minimum Bottom Padding
Every card rect must satisfy: `last_text_y + 16px ≤ rect_bottom`. This means `pad_bottom ≥ 16 (sm)` in the helper function (见 `spacing-scale.md`)。**Zero padding or negative padding (text below rect) is a bug.**

### C3: Minimum Inter-Card Gap
Cards in the same column must have `gap ≥ 16px (sm)`. Use chain calculation:
```python
next_card_y = prev_card_y + prev_card_h + GAP  # GAP ≥ 16 (sm)
```
Never place a card by guessing its y-coordinate independently.

### C4: Python Generation Required
For any diagram with 3+ content cards, **always generate SVG via Python script** using the `card_layout()` helper. Do not handwrite rect heights and text y-coordinates in raw SVG. The Python script is the source of truth.

### C5: Post-Generation Verification
After generating SVG, automatically print verification for every card:
```
Card Name: y=140 h=170 bottom=310 last_text=290 padding=20px OK
```
All padding values must be ≥ 16px (sm). All inter-card gaps must be ≥ 16px (sm). If any check fails, fix before exporting PNG.

### C6: Arrow Coordinates Reference Variables
Arrow y-coordinates must reference card variables (e.g., `di_mid`, `cw_bottom`), never hardcoded numbers. When a card moves or resizes, all connected arrows update automatically.

### C7: Legend — On-Demand, Arrow Types Only
Legend is **not required by default**. Add one **only when** the diagram uses 3+ distinct arrow colors or line styles that readers cannot infer from context. When included:
- Legend entries must be **arrow types only** (e.g., "主路径", "数据流", "返回"). Do NOT add entries for box fill colors — visual hierarchy is self-explanatory.
- Place below the bottom-most container with ≥ 20px clearance. Never overlap a legend with any container's bottom edge. The legend is a top-level element, not inside any container.

Verification: if legend is present, `legend_y ≥ last_container_bottom + 20`

### C8: Container Internal Padding Balance
Within a container, the distance from the top edge to the first element (title) and from the last element to the bottom edge must be **balanced**: `|top_padding - bottom_padding| ≤ 8px`.

Typical balanced padding: title at `container_y + 24 (md)`, last text at `container_y + container_h - 16 (sm)`. This gives ~24px top and ~16px bottom for single-line responsibility text, which is acceptable. If the container has no bottom text, center the content vertically.

### C9: Layout Table Completeness
Every visual element must appear in the layout table — including legends (if present), arrows between layers, and any standalone labels. If it's rendered in the SVG, it must be in the table with explicit (x, y) coordinates. This ensures canvas height accounts for all elements.

Verification: `canvas_height ≥ max_element_bottom + 30` (minimum 30px bottom margin)

### C10: No Arrow-Through-Box (Same-Row Multi-Target)
When a source node needs to connect to multiple non-adjacent targets in the same row, **NEVER** draw a straight arrow that crosses over intermediate boxes. Use one of these patterns:
1. **Chain pattern** (preferred for orchestration): Source → Target₁ → Target₂ → Target₃. Primary link in accent color, subsequent links in gray.
2. **Bus pattern**: Route a horizontal line below the row, with vertical drops up to each target.
3. **Omit arrows**: If spatial arrangement + visual hierarchy (fill color, border style) already conveys the relationship, skip intra-layer arrows entirely.

Verification: After placing any horizontal arrow, check that its line segment does not intersect any `<rect>` bounding box other than its source and target.

### Why These Constraints Exist
SVG is an absolute-positioning system with no auto-layout. Unlike HTML's CSS box model, `<text>` y-coordinates and `<rect>` height are independently declared with no binding. Manual "mental math" for 10+ cards inevitably produces overflow, clipping, or overlap. The `card_layout()` function creates a single source of truth that eliminates this class of bugs entirely.

## Validation Checklist

Before exporting PNG, verify:
- [ ] No arrow-component overlaps (visual inspection)
- [ ] All arrow labels have background rects
- [ ] Minimum 60px clearance for all arrow paths
- [ ] Component spacing ≥ 80px
- [ ] Arrow connection points avoid corners (≥20px from corner)
- [ ] Multiple arrows between layers are staggered
- [ ] Legend is readable and doesn't overlap content
- [ ] SVG renders cleanly via `cairosvg` (or `rsvg-convert` as fallback)

## Common Anti-Patterns to Avoid

| Anti-Pattern | Fix |
|--------------|-----|
| Arrow crosses component | Use orthogonal routing, increase control point distance |
| Label overlaps component | Add background rect + increase offset |
| Components too close | Increase spacing to 80px minimum |
| Arrow connects to corner | Move connection point to edge midpoint offset |
| No z-index planning | Follow render order: arrows -> components -> text |
