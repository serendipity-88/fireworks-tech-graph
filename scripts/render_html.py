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

# design token —— 视觉细节全在这张表里,改配色/边距只改这里。9 套风格。
STYLES = {
 'flat-icon': {'BG':'#fff','RADIUS':'10px','TITLE':'#0f172a','EDGE':'#3b82f6',
   'ROLE':{'default':'background:#eff6ff;border:1px solid #bfdbfe;color:#1e3a8a','primary':'background:#1e3a8a;color:#fff',
           'data':'background:#fff;border:1.5px solid #3b82f6;color:#1e40af','success':'background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46',
           'muted':'background:#f1f5f9;border:1px solid #e2e8f0;color:#475569','warning':'background:#fffbeb;border:1px solid #fde68a;color:#92400e',
           'danger':'background:#fef2f2;border:1px solid #fecaca;color:#991b1b','info':'background:#eff6ff;border:1px solid #93c5fd;color:#1e40af','accent':'background:#f5f3ff;border:1px solid #ddd6fe;color:#5b21b6'},
   'HOOK':{'darkBar':'#0f172a','solidPrimary':'#1e3a8a'},'GBORDER':'#cbd5e1'},
 'dark-terminal': {'BG':'#0f0f1a','RADIUS':'6px','TITLE':'#e2e8f0','EDGE':'#a855f7',
   'ROLE':{'default':'background:#0f172a;border:1px solid #334155;color:#e2e8f0','primary':'background:#7c3aed;color:#fff',
           'data':'background:#1e3a5f;border:1.5px solid #3b82f6;color:#bfdbfe','success':'background:#052e16;border:1px solid #059669;color:#a7f3d0',
           'muted':'background:#1c1917;border:1px solid #44403c;color:#a8a29e','warning':'background:#1c1917;border:1px solid #ea580c;color:#fdba74',
           'danger':'background:#450a0a;border:1px solid #dc2626;color:#fecaca','info':'background:#1e3a5f;border:1px solid #3b82f6;color:#bfdbfe','accent':'background:#1e1b4b;border:1px solid #a855f7;color:#ddd6fe'},
   'HOOK':{'darkBar':'#0f172a','solidPrimary':'#7c3aed'},'GBORDER':'#334155'},
 'blueprint': {'BG':'#0a1628','RADIUS':'2px','TITLE':'#caf0f8','EDGE':'#00b4d8',
   'ROLE':{'default':'background:#0d1f3c;border:1px solid #00b4d8;color:#caf0f8','primary':'background:#00b4d8;color:#0a1628',
           'data':'background:#0d1f3c;border:1.5px solid #48cae4;color:#caf0f8','success':'background:#0d1f3c;border:1px solid #06d6a0;color:#caf0f8',
           'muted':'background:#0d1f3c;border:1px solid #48cae4;color:#90e0ef','warning':'background:#0d1f3c;border:1px solid #f77f00;color:#ffedd5',
           'danger':'background:#0d1f3c;border:1px solid #ef4444;color:#fecaca','info':'background:#0d1f3c;border:1px solid #48cae4;color:#90e0ef','accent':'background:#0d1f3c;border:1px solid #00b4d8;color:#ffffff'},
   'HOOK':{'darkBar':'#0a1628','solidPrimary':'#00b4d8'},'GBORDER':'#112240'},
 'notion-clean': {'BG':'#ffffff','RADIUS':'4px','TITLE':'#111827','EDGE':'#3b82f6',
   'ROLE':{'default':'background:#f9fafb;border:1px solid #e5e7eb;color:#111827','primary':'background:#3b82f6;color:#fff',
           'data':'background:#ffffff;border:1.5px solid #3b82f6;color:#1e40af','success':'background:#f0fdf4;border:1px solid #bbf7d0;color:#166534',
           'muted':'background:#f9fafb;border:1px solid #e5e7eb;color:#9ca3af','warning':'background:#fffbeb;border:1px solid #fde68a;color:#92400e',
           'danger':'background:#fef2f2;border:1px solid #fecaca;color:#991b1b','info':'background:#eff6ff;border:1px solid #93c5fd;color:#1e40af','accent':'background:#f5f3ff;border:1px solid #ddd6fe;color:#5b21b6'},
   'HOOK':{'darkBar':'#111827','solidPrimary':'#3b82f6'},'GBORDER':'#e5e7eb'},
 'glassmorphism': {'BG':'#0d1117','RADIUS':'12px','TITLE':'#f0f6fc','EDGE':'#58a6ff',
   'ROLE':{'default':'background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.15);color:#f0f6fc','primary':'background:#58a6ff;color:#0d1117',
           'data':'background:rgba(88,166,255,0.15);border:1.5px solid #58a6ff;color:#cae8ff','success':'background:rgba(63,185,80,0.15);border:1px solid #3fb950;color:#a7f3c4',
           'muted':'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);color:#8b949e','warning':'background:rgba(247,129,102,0.15);border:1px solid #f78166;color:#ffb39e',
           'danger':'background:rgba(247,129,102,0.2);border:1px solid #f78166;color:#ffd0c2','info':'background:rgba(88,166,255,0.12);border:1px solid #58a6ff;color:#cae8ff','accent':'background:rgba(188,140,255,0.15);border:1px solid #bc8cff;color:#e0c7ff'},
   'HOOK':{'darkBar':'#161b22','solidPrimary':'#58a6ff'},'GBORDER':'rgba(255,255,255,0.12)'},
 'claude-official': {'BG':'#f8f6f3','RADIUS':'12px','TITLE':'#1a1a1a','EDGE':'#5a5a5a',
   'ROLE':{'default':'background:#e8e6e3;border:1px solid #4a4a4a;color:#1a1a1a','primary':'background:#9dd4c7;border:2px solid #4a4a4a;color:#1a1a1a',
           'data':'background:#a8c5e6;border:2px solid #4a4a4a;color:#1a1a1a','success':'background:#9dd4c7;border:2px solid #4a4a4a;color:#1a1a1a',
           'muted':'background:#e8e6e3;border:1px solid #4a4a4a;color:#6a6a6a','warning':'background:#f4e4c1;border:2px solid #4a4a4a;color:#1a1a1a',
           'danger':'background:#e8b4b4;border:2px solid #4a4a4a;color:#1a1a1a','info':'background:#a8c5e6;border:2px solid #4a4a4a;color:#1a1a1a','accent':'background:#f4e4c1;border:2px solid #4a4a4a;color:#1a1a1a'},
   'HOOK':{'darkBar':'#1a1a1a','solidPrimary':'#9dd4c7'},'GBORDER':'#4a4a4a'},
 'openai': {'BG':'#ffffff','RADIUS':'8px','TITLE':'#0d0d0d','EDGE':'#10a37f',
   'ROLE':{'default':'background:#ffffff;border:1.5px solid #e5e5e5;color:#0d0d0d','primary':'background:#10a37f;color:#fff',
           'data':'background:#ffffff;border:1.5px solid #1d4ed8;color:#1d4ed8','success':'background:#ffffff;border:1.5px solid #10a37f;color:#0d6e54',
           'muted':'background:#ffffff;border:1px solid #e5e5e5;color:#6e6e80','warning':'background:#ffffff;border:1.5px solid #f97316;color:#9a3412',
           'danger':'background:#ffffff;border:1.5px solid #ef4444;color:#991b1b','info':'background:#ffffff;border:1.5px solid #1d4ed8;color:#1d4ed8','accent':'background:#f0fdf4;border:1.5px solid #10a37f;color:#0d6e54'},
   'HOOK':{'darkBar':'#0d0d0d','solidPrimary':'#10a37f'},'GBORDER':'#e5e5e5'},
 'dark-luxury': {'BG':'#0a0a0a','RADIUS':'6px','TITLE':'#f5f0eb','EDGE':'#d4a574',
   'ROLE':{'default':'background:#111111;border:1.5px solid #d4a574;color:#f5f0eb','primary':'background:#d4a574;color:#0a0a0a',
           'data':'background:#111111;border:1.5px solid #38bdf8;color:#7dd3fc','success':'background:#111111;border:1.5px solid #5a9e6f;color:#86efac',
           'muted':'background:#1a1a1a;border:1px solid #6b5f53;color:#a39787','warning':'background:#111111;border:1.5px solid #fbbf24;color:#fcd34d',
           'danger':'background:#111111;border:1.5px solid #f87171;color:#fca5a5','info':'background:#111111;border:1.5px solid #38bdf8;color:#7dd3fc','accent':'background:#111111;border:1.5px solid #a78bfa;color:#c4b5fd'},
   'HOOK':{'darkBar':'#1a1a1a','solidPrimary':'#d4a574'},'GBORDER':'#6b5f53'},
 'claude-lite': {'BG':'#FAF9F5','RADIUS':'6px','TITLE':'#141413','EDGE':'#D97757',
   'ROLE':{'default':'background:#F5F4ED;border:1px solid #E8E6DC;color:#141413','primary':'background:#D97757;color:#FFFFFF',
           'data':'background:#FAF9F5;border:1.5px solid #6A9BCC;color:#141413','success':'background:#FAF9F5;border:1.5px solid #788C5D;color:#141413',
           'muted':'background:#F5F4ED;border:1px dashed #B0AEA5;color:#3D3D3A','warning':'background:#F6EEDF;border:1px solid #D97757;color:#A94F35',
           'danger':'background:#FAF9F5;border:1.5px solid #C0504D;color:#141413','info':'background:#D6E4F6;border:1px solid #6A9BCC;color:#141413','accent':'background:#F6EEDF;border:1px solid #D97757;color:#141413'},
   'HOOK':{'darkBar':'#141413','solidPrimary':'#D97757'},'GBORDER':'#C9C4B5'},
}
S = STYLES.get(data.get('style', 'claude-lite'), STYLES['claude-lite'])
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
