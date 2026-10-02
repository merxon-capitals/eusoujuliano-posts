"""Render Instagram carousel slides in the AMG Carbon standard (1080x1350, 4:5)."""
import json, sys, html, pathlib, base64
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).parent
F = ROOT / "node_modules/@fontsource"
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

def B(p):
    return base64.b64encode((F / p).read_bytes()).decode()

BRAND = "Duplicando Milhas"
HANDLE = "@eusoujuliano"

CSS = f"""
@font-face {{font-family:Barlow;font-weight:400;src:url(data:font/woff2;base64,{B('barlow/files/barlow-latin-400-normal.woff2')})}}
@font-face {{font-family:Barlow;font-weight:500;src:url(data:font/woff2;base64,{B('barlow/files/barlow-latin-500-normal.woff2')})}}
@font-face {{font-family:Barlow;font-weight:600;src:url(data:font/woff2;base64,{B('barlow/files/barlow-latin-600-normal.woff2')})}}
@font-face {{font-family:Barlow;font-weight:700;src:url(data:font/woff2;base64,{B('barlow/files/barlow-latin-700-normal.woff2')})}}
@font-face {{font-family:BarlowC;font-weight:600;src:url(data:font/woff2;base64,{B('barlow-condensed/files/barlow-condensed-latin-600-normal.woff2')})}}
@font-face {{font-family:BarlowC;font-weight:700;src:url(data:font/woff2;base64,{B('barlow-condensed/files/barlow-condensed-latin-700-normal.woff2')})}}
@font-face {{font-family:BarlowC;font-weight:800;src:url(data:font/woff2;base64,{B('barlow-condensed/files/barlow-condensed-latin-800-normal.woff2')})}}
:root{{--carbon:#15171A;--graphite:#3B4048;--steel:#8B9098;--silver:#C4C8CE;--mist:#F1F2F4;--ink:#1C1E21;--pos:#2F6B4F;--neg:#9E2F2F}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;font-family:Barlow;color:var(--ink);-webkit-font-smoothing:antialiased}}
.c{{font-family:BarlowC;text-transform:uppercase}}
.ln{{display:block;white-space:nowrap}}
.compact .row{{padding:20px 24px}} .compact .row .k{{font-size:37px}} .compact .row .v{{font-size:42px}} .compact .head{{margin:48px 0 30px}} .compact .note{{margin-top:24px}}
.slide{{position:relative;width:1080px;height:1350px;overflow:hidden}}
.dark{{background:var(--carbon);color:#fff}}
.light{{background:#fff}}
.top{{position:absolute;left:88px;right:88px;top:72px;display:flex;justify-content:space-between;align-items:center}}
.brand{{font-weight:700;font-size:30px;letter-spacing:.24em;color:var(--steel)}}
.pg{{font-weight:700;font-size:30px;letter-spacing:.12em;color:var(--steel)}}
.rule-d{{position:absolute;left:88px;right:88px;top:124px;height:2px;background:var(--graphite)}}
.foot{{position:absolute;left:88px;right:88px;bottom:64px;display:flex;justify-content:space-between;align-items:center}}
.handle{{font-weight:700;font-size:30px;letter-spacing:.16em;color:var(--steel)}}
.swipe{{font-weight:700;font-size:30px;letter-spacing:.16em;color:#fff}}
/* cover */
.cov{{position:absolute;left:88px;right:88px;top:300px}}
.eyebrow{{font-weight:700;font-size:30px;letter-spacing:.2em;color:var(--silver);margin-bottom:34px}}
.ttl{{font-weight:800;font-size:164px;line-height:.94;letter-spacing:-.005em;color:#fff}}
.bar{{width:120px;height:6px;background:#fff;margin:52px 0 44px}}
.sub{{font-size:40px;line-height:1.38;color:var(--silver);max-width:860px}}
/* light slides */
.band{{position:absolute;left:0;right:0;top:0;height:196px;background:var(--carbon)}}
.band .top{{top:78px}}
.body{{position:absolute;left:88px;right:88px;top:280px}}
.sec{{display:flex;align-items:baseline;gap:26px;padding-bottom:22px;border-bottom:4px solid var(--carbon)}}
.sec .n{{font-weight:700;font-size:32px;letter-spacing:.2em;color:var(--steel)}}
.sec .l{{font-weight:800;font-size:46px;letter-spacing:.08em;color:var(--carbon)}}
.head{{font-weight:700;font-size:66px;line-height:1.12;margin:60px 0 48px;color:var(--ink)}}
.wm{{position:absolute;right:64px;bottom:150px;font-family:BarlowC;font-weight:800;font-size:420px;line-height:.8;color:var(--mist)}}
.row{{display:flex;justify-content:space-between;align-items:center;gap:30px;padding:30px 24px;border-bottom:2px solid var(--silver)}}
.row.hl{{background:var(--mist)}}
.row .k{{font-size:40px;line-height:1.25;color:var(--ink)}}
.row .v{{font-weight:700;font-size:46px;white-space:nowrap;color:var(--ink);font-variant-numeric:tabular-nums}}
.pos{{color:var(--pos)!important}} .neg{{color:var(--neg)!important}}
.note{{font-size:31px;line-height:1.45;color:var(--steel);margin-top:36px}}
.para{{display:flex;gap:28px;margin-bottom:34px}}
.para .m{{flex:none;width:14px;height:14px;background:var(--carbon);margin-top:22px}}
.para p{{font-size:48px;line-height:1.4;color:var(--ink)}}
.statv{{font-family:BarlowC;font-weight:800;font-size:230px;line-height:.9;color:var(--pos);letter-spacing:-.01em}}
.statu{{font-family:BarlowC;font-weight:700;font-size:36px;letter-spacing:.14em;text-transform:uppercase;color:var(--steel);margin-top:22px}}
.li{{display:flex;gap:30px;padding:30px 0;border-bottom:2px solid var(--silver)}}
.li .n{{flex:none;width:70px;font-family:BarlowC;font-weight:800;font-size:44px;color:var(--steel);line-height:1.2}}
.li p{{font-size:42px;line-height:1.35}}
.lfoot{{position:absolute;left:88px;right:88px;bottom:64px;display:flex;justify-content:space-between;border-top:2px solid var(--silver);padding-top:26px}}
.lfoot span{{font-family:BarlowC;font-weight:700;font-size:28px;letter-spacing:.18em;text-transform:uppercase;color:var(--steel)}}
/* light cover + solo */
.lc{{background:#fff}}
.lc .brand,.lc .pg,.lc .handle{{color:var(--steel)}} .lc .rule-d{{background:var(--silver)}} .lc .eyebrow{{color:var(--steel)}} .lc .ttl{{color:var(--carbon)}} .lc .bar{{background:var(--carbon)}} .lc .sub{{color:var(--graphite)}} .lc .swipe{{color:var(--carbon)}}
.solov{{font-family:BarlowC;font-weight:800;font-size:250px;line-height:.9;color:var(--pos);white-space:nowrap;margin-top:10px}}
.solou{{font-family:BarlowC;font-weight:700;font-size:40px;letter-spacing:.14em;text-transform:uppercase;color:var(--steel);margin-top:26px}}
/* cta */
.ctab{{position:absolute;left:88px;right:88px;top:400px}}
.ctat{{font-weight:800;font-size:140px;line-height:.95;color:#fff}}
.ctab p{{font-size:42px;line-height:1.4;color:var(--silver);max-width:860px}}
.big-handle{{position:absolute;left:88px;bottom:150px;font-family:BarlowC;font-weight:800;font-size:64px;letter-spacing:.06em;color:#fff}}
"""

e = html.escape

def top(i, n):
    return f'<div class="top"><span class="c brand">{e(BRAND)}</span><span class="c pg">{i:02d} / {n:02d}</span></div>'

def sec(s):
    return f'<div class="sec"><span class="c n">Seção {e(s["sec"])}</span><span class="c l">{e(s["label"])}</span></div>'

def light(inner, i, n, wm='', cls=''):
    return (f'<div class="slide light"><div class="wm">{e(wm)}</div><div class="band">{top(i,n)}</div><div class="body{cls}">{inner}</div>'
            f'<div class="lfoot"><span>{e(HANDLE)}</span><span>Arraste →</span></div></div>')

def slide_html(s, i, n):
    t = s["t"]
    if t == "solo":
        return (f'<div class="slide lc">{top(i,n)}<div class="rule-d"></div><div class="cov" style="top:330px">'
                f'<div class="c eyebrow">{e(s["eyebrow"])}</div><div class="c ttl" style="font-size:96px"><span class="ln">{e(s["head"])}</span></div>'
                f'<div class="solov">{e(s["value"])}</div><div class="solou">{e(s["unit"])}</div>'
                f'<div class="bar"></div><div class="sub">{e(s["sub"])}</div></div>'
                f'<div class="foot"><span class="c handle">{e(HANDLE)}</span><span class="c swipe">Salve</span></div></div>')
    if t == "cover":
        title = "".join(f'<span class="ln">{e(x)}</span>' for x in s["title"])
        return (f'<div class="slide {"lc" if s.get("theme")=="light" else "dark"}">{top(i,n)}<div class="rule-d"></div><div class="cov">'
                f'<div class="c eyebrow">{e(s["eyebrow"])}</div><div class="c ttl">{title}</div>'
                f'<div class="bar"></div><div class="sub">{e(s["sub"])}</div></div>'
                f'<div class="foot"><span class="c handle">{e(HANDLE)}</span><span class="c swipe">Arraste →</span></div></div>')
    if t == "cta":
        title = "".join(f'<span class="ln">{e(x)}</span>' for x in s["title"])
        return (f'<div class="slide dark">{top(i,n)}<div class="rule-d"></div><div class="ctab">'
                f'<div class="c ctat">{title}</div><div class="bar"></div><p>{e(s["body"])}</p></div>'
                f'<div class="big-handle">{e(HANDLE)}</div></div>')
    inner = sec(s) + f'<div class="head">{e(s["head"])}</div>'
    if t == "table":
        for k, v, tone in s["rows"]:
            hl = " hl" if tone == "pos" else ""
            cls = f' {tone}' if tone else ""
            inner += f'<div class="row{hl}"><span class="k">{e(k)}</span><span class="v{cls}">{e(v)}</span></div>'
        if s.get("note"):
            inner += f'<div class="note">{e(s["note"])}</div>'
    elif t == "point":
        for p in s["body"]:
            inner += f'<div class="para"><span class="m"></span><p>{e(p)}</p></div>'
    elif t == "stat":
        inner += f'<div class="statv">{e(s["value"])}</div><div class="statu">{e(s["unit"])}</div>'
        if s.get("note"):
            inner += f'<div class="note" style="margin-top:56px;font-size:34px">{e(s["note"])}</div>'
    elif t == "list":
        start = s.get("start", 1)
        for j, it in enumerate(s["items"]):
            inner += f'<div class="li"><span class="n">{start+j:02d}</span><p>{e(it)}</p></div>'
    cls = ' compact' if t == 'table' and len(s['rows']) > 4 else ''
    return light(inner, i, n, s['sec'] if t in ('point','stat','list') else '', cls)

def main(ids=None):
    import os
    posts = json.load(open(ROOT / os.environ.get("POSTS", "posts.json")))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for post in posts:
            if ids and post["id"] not in ids:
                continue
            n = len(post["slides"])
            for i, s in enumerate(post["slides"], 1):
                doc = f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{slide_html(s,i,n)}</body></html>'
                pg.set_content(doc)
                pg.evaluate("document.fonts.ready")
                pg.evaluate("""() => { for (const el of document.querySelectorAll('.ttl,.ctat,.solov')) { let fs=parseFloat(getComputedStyle(el).fontSize); const w=el.clientWidth; const lines=el.querySelectorAll('.ln').length?[...el.querySelectorAll('.ln')]:[el]; while (fs>60 && lines.some(l=>l.scrollWidth>w)) { fs-=2; el.style.fontSize=fs+'px'; } } }""")
                pg.wait_for_timeout(120)
                png = OUT / f"post{post['id']}_{i:02d}.png"
                pg.screenshot(path=str(png), full_page=False)
                Image.open(png).convert("RGB").save(png.with_suffix(".jpg"), quality=92)
                # overflow check
                over = pg.evaluate("""() => { const b=document.querySelector('.body'); if(!b) return 0; const r=b.getBoundingClientRect(); return r.bottom; }""")
                if over and over > 1250:
                    print("OVERFLOW", post["id"], i, over)
        b.close()

if __name__ == "__main__":
    main(sys.argv[1:] or None)
