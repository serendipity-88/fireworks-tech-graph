#!/usr/bin/env python3
"""layout_engine.py — layout-driven JSON → coordinate fixture 转换器。

LLM 只产结构(layout 原语:row/col/grid/stack + children),本引擎算出每个
node/container 的绝对坐标,转成 generate-from-template.py 能吃的 fixture 格式
(containers/nodes/arrows 带 x/y/width/height)。纯 stdlib,零依赖。

这是 fireworks-tech-graph 改造路线2 的核心:让坐标由确定性引擎算,根除"LLM 手算
坐标导致错位/串行"。语义源自 ~/Desktop/fireworks-schema/render.py 的 flex 逻辑,
但用 Python 重写(不依赖浏览器)。

用法(由 generate-from-template.py main() 自动调用,无需手动跑):
    import layout_engine
    fixture = layout_engine.convert(layout_json)
"""
import json
import sys

# spacing scale —— single source,见 references/spacing-scale.md
SPACING = {'xs': 8, 'sm': 16, 'md': 24, 'lg': 32, 'xl': 48, '2xl': 64, '3xl': 96}

# style 名 → generate-from-template.py 的 style int。
# 注意:claude-lite/dark-luxury 是 AI-authored(style 8/9 被原引擎拒绝渲染),
# 但本引擎自己按 role/styleHook 给 fill/stroke 写进 node,原引擎只管几何,所以能走。
STYLE_MAP = {
    'flat-icon': 1, 'dark-terminal': 2, 'blueprint': 3, 'notion-clean': 4,
    'glassmorphism': 5, 'claude-official': 6, 'openai': 7,
    'claude-lite': 1, 'dark-luxury': 1,  # AI-authored:用 style1 做(背景/连线)基底,卡片色由本引擎给
}

# role → (fill, stroke, text_fill)。flat-icon 色板作默认;Phase2 按 style 选不同色板。
ROLE_COLOR = {
    'default':  ('#eff6ff', '#bfdbfe', '#1e3a8a'),
    'primary':  ('#1e3a8a', '#1e3a8a', '#ffffff'),
    'data':     ('#ffffff', '#3b82f6', '#1e40af'),
    'success':  ('#ecfdf5', '#a7f3d0', '#065f46'),
    'muted':    ('#f1f5f9', '#e2e8f0', '#475569'),
    'warning':  ('#fffbeb', '#fde68a', '#92400e'),
    'danger':   ('#fef2f2', '#fecaca', '#991b1b'),
    'info':     ('#eff6ff', '#93c5fd', '#1e40af'),
    'accent':   ('#f5f3ff', '#ddd6fe', '#5b21b6'),
}
# styleHook(hook) → (fill, stroke) 用于 container 背景
HOOK_COLOR = {
    'darkBar':       ('#0f172a', '#0f172a'),
    'solidPrimary':  ('#1e3a8a', '#1e3a8a'),
}

# shape → generate-from-template.py 的 kind
SHAPE_KIND = {
    'rect': 'rect', 'diamond': 'rect', 'cylinder': 'cylinder', 'hex': 'hexagon',
    'cloud': 'circle_cluster', 'ellipse': 'circle_cluster', 'actor': 'user_avatar',
    'forkbar': 'rect', 'mergebar': 'rect', 'document': 'document',
}

# relType → generate-from-template.py 的 flow(连线色/语义)
RELTYPE_FLOW = {
    'association': 'control', 'dependency': 'control', 'call': 'control',
    'composition': 'data', 'aggregation': 'data', 'realization': 'data',
    'inheritance': 'feedback', 'transition': 'control', 'message': 'read',
}


def snap8(v):
    """坐标/尺寸 round 到 8 的倍数,最小 8。"""
    return max(8, round(v / 8) * 8)


def measure_node(n):
    """估算单个 node 的 (width, height)。基于 title/subtitle/badge 行数。"""
    title = n.get('title', '')
    sub = n.get('subtitle', '')
    badge = n.get('badge')
    longest = max(len(title), len(sub) if sub else 0, len(badge) if badge else 0, 8)
    w = snap8(max(120, longest * 9 + SPACING['sm'] * 2))
    if w > 280:
        w = 280
    h = SPACING['sm']  # top pad
    h += 20  # title
    if sub:
        h += 18
    if badge:
        h += 16
    h += SPACING['sm']  # bottom pad
    return w, snap8(h)


def _gap_for(layout):
    if layout in ('row', 'grid'):
        return SPACING['sm']
    if layout == 'stack':
        return SPACING['sm']
    return SPACING['md']  # col


def measure_box(node_or_group, avail_w):
    """递归估算 group 或 node 的 (w, h)。group 按其 layout 聚合 children。"""
    if node_or_group.get('type') == 'node':
        return measure_node(node_or_group)
    g = node_or_group
    layout = g.get('layout', 'col')
    children = g.get('children', [])
    gap = g.get('gap') or _gap_for(layout)
    title_h = 40 if g.get('title') else 0  # generate 把 container label 画在 y+24,header 区到 y+30,故 node 起始 +40
    if not children:
        return snap8(avail_w), snap8(SPACING['md'] + title_h)
    sizes = [measure_box(c, avail_w) for c in children]
    bot = SPACING['sm']  # bottom padding:node 不得贴/超 container 底
    if layout == 'row':
        h = max(s[1] for s in sizes)
        return snap8(avail_w), snap8(h + title_h + bot)
    if layout == 'grid':
        cols = g.get('cols', 2)
        rows = (len(children) + cols - 1) // cols
        cell_h = max(s[1] for s in sizes)
        return snap8(avail_w), snap8(rows * cell_h + (rows - 1) * gap + title_h + bot)
    # col / stack
    h = sum(s[1] for s in sizes) + gap * (len(children) - 1) + title_h + bot
    return snap8(avail_w), snap8(h)


def layout_box(item, x, y, avail_w):
    """给 item(group/node)及其后代填绝对坐标。返回 (w, h)。
    node 撑满父分配宽(像 flex:1)——同行卡片等宽,治"有的宽有的窄"。高按内容估。"""
    _mw, h = measure_box(item, avail_w)
    w = snap8(avail_w)
    item['_box'] = {'x': snap8(x), 'y': snap8(y), 'w': w, 'h': h}

    if item.get('type') == 'node':
        return w, h

    g = item
    layout = g.get('layout', 'col')
    children = g.get('children', [])
    gap = g.get('gap') or _gap_for(layout)
    inner_x = snap8(x + SPACING['sm'])
    inner_y = snap8(y + (40 if g.get('title') else SPACING['sm']))
    inner_w = snap8(w - SPACING['sm'] * 2)

    if layout == 'grid':
        cols = g.get('cols', 2)
        cell_w = snap8((inner_w - gap * (cols - 1)) / cols)
        cell_h = snap8(max((measure_box(c, cell_w)[1] for c in children), default=SPACING['md']))
        for i, c in enumerate(children):
            r, col = divmod(i, cols)
            cx = inner_x + col * (cell_w + gap)
            cy = inner_y + r * (cell_h + gap)
            layout_box(c, cx, cy, cell_w)
            c['_box']['h'] = cell_h  # 同行等高
        return w, h
    if layout == 'row':
        n = len(children)
        cell_w = snap8((inner_w - gap * (n - 1)) / n) if n else inner_w
        max_h = snap8(max((measure_box(c, cell_w)[1] for c in children), default=SPACING['md']))
        cx = inner_x
        for c in children:
            layout_box(c, cx, inner_y, cell_w)
            c['_box']['h'] = max_h  # 同行等高(像 flex align-items:stretch)
            cx = snap8(cx + cell_w + gap)
        return w, h
    # col / stack:每个 child 宽 = inner_w,沿 y 累加
    cy = inner_y
    for c in children:
        cw, ch = layout_box(c, inner_x, cy, inner_w)
        cy = snap8(cy + ch + gap)
    return w, h


def _node_to_fixture(n):
    role = n.get('role', 'default')
    fill, stroke, text = ROLE_COLOR.get(role, ROLE_COLOR['default'])
    kind = SHAPE_KIND.get(n.get('shape', 'rect'), 'rect')
    box = n['_box']
    node = {
        'id': n.get('id'),
        'kind': kind,
        'x': box['x'], 'y': box['y'], 'width': box['w'], 'height': box['h'],
        'label': n.get('title', ''),
        'fill': fill, 'stroke': stroke,
        'text_fill': text,  # 深底 role → 浅字(default→深字,primary/darkBar→白)
    }
    if n.get('subtitle'):
        node['sublabel'] = n['subtitle']
    if n.get('badge'):
        node['type_label'] = n['badge']
    return node


def _group_to_fixture(g, containers, nodes):
    box = g['_box']
    hook = (g.get('styleHook') or {}).get('hook')
    cfill, cstroke = HOOK_COLOR.get(hook, ('#ffffff', '#e2e8f0'))
    containers.append({
        'x': box['x'], 'y': box['y'], 'width': box['w'], 'height': box['h'],
        'label': g.get('title', ''), 'fill': cfill, 'stroke': cstroke,
        'stroke_dasharray': '4,3' if hook is None else '',
    })
    for ch in g.get('children', []):
        if ch.get('type') == 'node':
            nodes.append(_node_to_fixture(ch))
        else:
            _group_to_fixture(ch, containers, nodes)


def _guess_port(fb, tb):
    """根据 from/to 相对位置猜 source_port/target_port(让 build_orthogonal_route 有好起点)。"""
    if tb['y'] >= fb['y'] + fb['h']:
        return 'bottom', 'top'
    if fb['y'] >= tb['y'] + tb['h']:
        return 'top', 'bottom'
    if tb['x'] >= fb['x'] + fb['w']:
        return 'right', 'left'
    return 'left', 'right'


def convert(layout_json):
    """layout-driven JSON(schema v1.1) → coordinate fixture(generate-from-template.py 格式)。"""
    style_name = layout_json.get('style', 'flat-icon')
    canvas = layout_json.get('canvas', {})
    width = canvas.get('w', 1080)
    margin = SPACING['xl']

    root = layout_json['root']
    root_w = width - margin * 2
    layout_box(root, margin, margin, root_w)
    total_h = root['_box']['y'] + root['_box']['h'] + margin
    height = snap8(max(total_h, canvas.get('h', 0) or 0, 400))

    containers, nodes = [], []
    _group_to_fixture(root, containers, nodes)

    # node id → box,供 edges 解析
    box_by_id = {}
    for n in nodes:
        if n.get('id'):
            box_by_id[n['id']] = {'x': n['x'], 'y': n['y'], 'w': n['width'], 'h': n['height']}

    arrows = []
    for e in layout_json.get('edges', []):
        f, t = e.get('from'), e.get('to')
        if f not in box_by_id or t not in box_by_id:
            continue  # group↔group 的层间关系由布局表达,不画显式箭头
        sp, tp = _guess_port(box_by_id[f], box_by_id[t])
        arr = {
            'source': f, 'target': t,
            'source_port': sp, 'target_port': tp,
            'flow': RELTYPE_FLOW.get(e.get('relType', 'association'), 'control'),
        }
        if e.get('label'):
            arr['label'] = e['label']
        dec = e.get('decorators') or {}
        if dec.get('dashed') or e.get('relType') in ('dependency', 'realization'):
            arr['dashed'] = True
        arrows.append(arr)

    return {
        'template_type': layout_json.get('template_type', 'architecture'),
        'style': STYLE_MAP.get(style_name, 1),
        'width': width,
        'height': height,
        'title': layout_json.get('title', ''),
        'containers': containers,
        'nodes': nodes,
        'arrows': arrows,
        'legend': [],
        'footer': '',
    }


if __name__ == '__main__':
    # 手动测试:python3 layout_engine.py input.json [output.json]
    src = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else json.load(sys.stdin)
    out = convert(src)
    tgt = sys.argv[2] if len(sys.argv) > 2 else None
    if tgt:
        json.dump(out, open(tgt, 'w'), ensure_ascii=False, indent=2)
        print(f'✓ {len(out["nodes"])} nodes, {len(out["containers"])} containers, {len(out["arrows"])} arrows → {tgt}')
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))
