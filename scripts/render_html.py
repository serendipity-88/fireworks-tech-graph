#!/usr/bin/env python3
"""render_html.py — layout-driven JSON → HTML/CSS(flex)→ PNG。

主线渲染器(架构图 A 路线)。直接吃 schema v1.1 的 layout JSON,浏览器 flex 算坐标
(不错位、同行等宽等高、文字自适应),连线从 DOM 实际位置读 + 正交避障(不穿卡)。
文字色/配色/边距全在本文件 STYLES 控制(视觉细节零摩擦,区别于 generate-from-template)。

依赖:playwright + 系统 Chrome(自用/预览;无 chrome 环境改走 generate-from-template B 路线)。

用法:
    python3 render_html.py input.json [output.png]      # 文件
    cat input.json | python3 render_html.py - out.png    # stdin
"""
import json, math, sys
from playwright.sync_api import sync_playwright

src = sys.argv[1] if len(sys.argv) > 1 else '-'
data = json.load(open(src) if src != '-' else sys.stdin)
out = sys.argv[2] if len(sys.argv) > 2 else f'/tmp/rendered-{data.get("style","flat")}.png'

# design token —— 视觉细节全在这张表里,改配色/边距只改这里
STYLES = {
 'flat-icon': {'BG':'#fff','RADIUS':'10px','TITLE':'#0f172a','EDGE':'#3b82f6',
   'ROLE':{'default':'background:#eff6ff;border:1px solid #bfdbfe;color:#1e3a8a','primary':'background:#1e3a8a;color:#fff',
           'data':'background:#fff;border:1.5px solid #3b82f6;color:#1e40af','success':'background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46',
           'muted':'background:#f1f5f9;border:1px solid #e2e8f0;color:#475569','warning':'background:#fffbeb;border:1px solid #fde68a;color:#92400e',
           'danger':'background:#fef2f2;border:1px solid #fecaca;color:#991b1b','info':'background:#eff6ff;border:1px solid #93c5fd;color:#1e40af','accent':'background:#f5f3ff;border:1px solid #ddd6fe;color:#5b21b6'},
   'HOOK':{'darkBar':'#0f172a','solidPrimary':'#1e3a8a'},'GBORDER':'#cbd5e1'},
 'claude-lite': {'BG':'#FAF9F5','RADIUS':'6px','TITLE':'#141413','EDGE':'#D97757',
   'ROLE':{'default':'background:#F5F4ED;border:1px solid #E8E6DC;color:#141413','primary':'background:#D97757;color:#FFFFFF',
           'data':'background:#FAF9F5;border:1.5px solid #6A9BCC;color:#141413','success':'background:#FAF9F5;border:1.5px solid #788C5D;color:#141413',
           'muted':'background:#F5F4ED;border:1px dashed #B0AEA5;color:#3D3D3A','warning':'background:#F6EEDF;border:1px solid #D97757;color:#A94F35',
           'danger':'background:#FAF9F5;border:1.5px solid #C0504D;color:#141413','info':'background:#D6E4F6;border:1px solid #6A9BCC;color:#141413','accent':'background:#F6EEDF;border:1px solid #D97757;color:#141413'},
   'HOOK':{'darkBar':'#141413','solidPrimary':'#D97757'},'GBORDER':'#C9C4B5'}
}
S = STYLES.get(data.get('style', 'flat-icon'), STYLES['flat-icon'])
ROLE, HOOK, BG, RADIUS, TITLE, EDGE, GBORDER = S['ROLE'], S['HOOK'], S['BG'], S['RADIUS'], S['TITLE'], S['EDGE'], S['GBORDER']

def node(n, extra=''):
    nid = n.get('id', '')
    s = ROLE.get(n.get('role', 'default'), ROLE['default']) + f';border-radius:{RADIUS};padding:16px;text-align:center;min-width:max-content' + extra
    h = f'<div data-nid="{nid}" style="{s}">'
    if n.get('badge'): h += f'<div style="font-size:10px;opacity:.6;margin-bottom:4px">{n["badge"]}</div>'
    h += f'<div style="font-size:14px;font-weight:600;white-space:nowrap">{n["title"]}</div>'
    if n.get('subtitle'): h += f'<div style="font-size:11px;opacity:.78;margin-top:5px;white-space:nowrap">{n["subtitle"]}</div>'
    return h + '</div>'

def group(g, extra=''):
    lay = g['layout']; hook = (g.get('styleHook') or {}).get('hook')
    disp = {'row':'display:flex;flex-direction:row','col':'display:flex;flex-direction:column','stack':'display:flex;flex-direction:column',
            'grid':f'display:grid;grid-template-columns:repeat({g.get("cols",2)},minmax(max-content,1fr))'}.get(lay, 'display:block')
    style = disp + f';gap:{"16px" if lay in ("row","grid") else ("8px" if lay=="stack" else "18px")}'
    if lay in ('row', 'grid'): style += ';align-items:center'  # node 不等高拉伸(各按内容高,padding 四边固定16),同行垂直居中对齐
    if hook and hook in HOOK:
        style += f';background:{HOOK[hook]};border-radius:{RADIUS};padding:16px'   # 实心分组(知识库/基础层)
    else:
        style += f';border:1px dashed {GBORDER};border-radius:{RADIUS};padding:16px'  # 虚线框分组(模块分隔感)
    h = f'<div style="{style}{extra}">'
    if g.get('title'):
        tc = '#FFFFFF' if hook == 'solidPrimary' else ('#F5F4ED' if hook == 'darkBar' else TITLE)
        h += f'<div style="font-size:13px;font-weight:700;color:{tc};margin-bottom:10px">{g["title"]}</div>'
    ce = ';flex:1;min-width:0' if lay in ('row', 'grid') else ''
    for ch in g.get('children', []): h += node(ch, ce) if ch['type'] == 'node' else group(ch, ce)
    return h + '</div>'

root = data['root']; kids = root.get('children', [])
pairs = {(e['from'], e['to']) for e in data.get('edges', []) if 'from' in e and 'to' in e}
body = ''
for i, ch in enumerate(kids):
    body += group(ch) if ch['type'] == 'group' else node(ch)
    if i < len(kids) - 1 and (ch.get('id'), kids[i+1].get('id')) in pairs:
        body += f'<div style="text-align:center;margin:6px 0"><svg width="20" height="38" style="display:block;margin:0 auto"><line x1="10" y1="2" x2="10" y2="24" stroke="{EDGE}" stroke-width="2.5" stroke-linecap="round"/><polygon points="3,21 17,21 10,34" fill="{EDGE}"/></svg></div>'
w = data.get('canvas', {}).get('w', 1080)
html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:"Anthropic Sans","Inter","PingFang SC","Helvetica Neue",Arial,sans-serif}}
body{{background:{BG};padding:40px;width:{w}px}}</style></head>
<body><div style="display:flex;flex-direction:column">{body}</div></body></html>'''

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport={"width": w+80, "height": 2000}, device_scale_factor=2)
    pg.set_content(html)
    boxes = pg.evaluate("""()=>{const m={};document.querySelectorAll('[data-nid]').forEach(el=>{
      if(!el.dataset.nid)return;const r=el.getBoundingClientRect();m[el.dataset.nid]={x:r.x,y:r.y,w:r.width,h:r.height}});return m}""")
    segs = [f'<defs><marker id="arr" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="{EDGE}"/></marker></defs>']
    drawn = 0
    for e in data.get('edges', []):
        f, t = e.get('from'), e.get('to')
        if f not in boxes or t not in boxes: continue
        fb, tb = boxes[f], boxes[t]
        fcx, fcy = fb['x']+fb['w']/2, fb['y']+fb['h']/2; tcx, tcy = tb['x']+tb['w']/2, tb['y']+tb['h']/2
        dx, dy = tcx-fcx, tcy-fcy
        if abs(dy) >= abs(dx):
            fy_s = fb['y']+fb['h'] if dy > 0 else fb['y']; ty_e = tb['y'] if dy > 0 else tb['y']+tb['h']
            mid_y = (fy_s+ty_e)/2
            pts = [(fcx, fy_s), (fcx, mid_y), (tcx, mid_y), (tcx, ty_e)]
        else:
            fx_s = fb['x']+fb['w'] if dx > 0 else fb['x']; tx_e = tb['x'] if dx > 0 else tb['x']+tb['w']
            mid_x = (fx_s+tx_e)/2
            pts = [(fx_s, fcy), (mid_x, fcy), (mid_x, tcy), (tx_e, tcy)]
        d = "M " + " L ".join(f"{x:.0f} {y:.0f}" for x, y in pts)
        segs.append(f'<path d="{d}" stroke="{EDGE}" stroke-width="2" fill="none" marker-end="url(#arr)"/>')
        if e.get('label'):
            mx, my = (pts[1][0]+pts[2][0])/2, (pts[1][1]+pts[2][1])/2
            segs.append(f'<rect x="{mx-22}" y="{my-9}" width="44" height="16" rx="3" fill="{BG}"/>')
            segs.append(f'<text x="{mx}" y="{my+3}" font-size="10" fill="#73726C" text-anchor="middle">{e["label"]}</text>')
        drawn += 1
    overlay = f'<div style="position:absolute;top:0;left:0;width:{w+80}px;height:2000px;pointer-events:none"><svg width="{w+80}" height="2000" style="position:absolute;top:0;left:0">' + ''.join(segs) + '</svg></div>'
    pg.evaluate("document.body.insertAdjacentHTML('beforeend'," + json.dumps(overlay) + ")")
    pg.screenshot(path=out, full_page=True); b.close()
print(f"✓ render_html → {out} (style={data.get('style')}, {drawn} 条连线)")
