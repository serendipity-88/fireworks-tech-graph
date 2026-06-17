# Spacing Scale (8-base grid)

**Single source of truth** for all spacing in this skill. Every gap / padding / margin / snap coordinate must take a value from this table. No `18 / 20 / 26 / 28 / 15` etc.

| token | px  | 用途 |
|------|-----|------|
| `xs`  | 8   | 最小间隙:badge↔title、icon 内距 |
| `sm`  | 16  | node 内 padding(四边)、row/grid 同级 gap、canvas 内细间距 |
| `md`  | 24  | stack 同级 gap、card 内 title↔subtitle 间距 |
| `lg`  | 32  | group/container 内 padding、同层内分组间距 |
| `xl`  | 48  | 画布 margin(左右)、箭头通道预留 |
| `2xl` | 64  | 跨层主间距(layer↔layer 纵向,含箭头+label 空间) |
| `3xl` | 96  | 大分区之间(独立子系统边界) |

## 规则

1. **取档**:所有 gap/padding/margin 必须是上表某档的值。禁止非 8 倍数(除特殊声明)。
2. **8px grid snap**:所有坐标 `round` 到 8 的倍数(`layout_engine.snap8`、Python `card_layout` 都遵守)。
3. **layer 间 = `2xl`(64)** = `sm`(16 上层 node padding)+ 32(箭头+label 空间)+ `sm`(16 下层 node padding)。统一取代旧的"content-driven 非固定 gap"说法。
4. **C 系列约束对齐**(见 `svg-layout-best-practices.md`):card padding = `sm`(16)、title_gap = `md`(24)、sub_gap = `md`(24)、detail_gap = `sm`(16)、inter-card gap = `sm`(16)。

## 在哪用

- `scripts/layout_engine.py`:`SPACING` 字典即本表,所有布局计算读它。
- `svg-layout-best-practices.md`:C1 `card_layout()` 参数、C2/C3 下限、C8 平衡、Universal Rules。
- `SKILL.md`:Layout Rules、Layer Diagram 公式。
- 各 `style-N.md`:不再各自述说 spacing,统一回查本表。
