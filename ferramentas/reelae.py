"""Beat-synced connection Reels (reel_sync.html + audio2.py).
Usage: python3 reelsync.py reels_sync.json [id ...]   |   python3 reelsync.py reels_sync.json --stills ID t1 t2 ...
"""
import json, sys, subprocess, pathlib
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from reel import FONTS
import reelm, reelc

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out"; FPS = 30
TPL = (ROOT / "reel_ae.html").read_text()
FAST = ("whipL", "whipR", "whipU", "whipD", "zoom", "spin", "glitch")

def td_of(s):
    return s.get("td", .42) if s.get("tr") else 0

def auto_ramps(sh):
    for i, s in enumerate(sh):
        if "video" not in s: continue
        nx = sh[i + 1] if i + 1 < len(sh) else None
        if s.get("tr") in FAST: s.setdefault("ramp_in", .45)
        if nx and nx.get("tr") in FAST: s.setdefault("ramp_out", .45)

def src_len(s, L):
    V = s.get("ramp_v", 2.6)
    return s.get("speed", 1) * (L + (V - 1) * .5 * (s.get("ramp_in", 0) + s.get("ramp_out", 0))) + .25

def build(reel):
    sh = reel["shots"]
    auto_ramps(sh)
    for i, s in enumerate(sh):
        end = sh[i + 1]["start"] if i + 1 < len(sh) else reel["duration"]
        if "img" in s and not s["img"].endswith(".jpg"): s["img"] = reelm.prep_img(s["img"])
        if "video" in s and "frames" not in s:
            s["frames"] = reelc.prep_video(s["video"], s.get("from", 0), src_len(s, end - s["start"] + td_of(s)))
    page = reelm.WORK / f"ae{reel['id']}.html"
    extra = ""
    if reel.get("globe"):
        nm = ROOT / "node_modules"
        for f in ["d3-array/dist/d3-array.min.js", "d3-geo/dist/d3-geo.min.js", "topojson-client/dist/topojson-client.min.js"]:
            extra += "<script>" + (nm / f).read_text() + "</script>"
        extra += "<script>window.WORLD=" + (nm / "world-atlas/land-50m.json").read_text() + ";</script>"
    page.write_text(TPL.replace("/*EXTRA*/", extra).replace("/*FONTS*/", FONTS).replace("/*REEL*/", json.dumps(reel, ensure_ascii=False)))
    return page

def open_page(pw, page):
    b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto(page.as_uri()); pg.evaluate("document.fonts.ready"); pg.evaluate("ready()"); pg.wait_for_timeout(300); pg.evaluate("fit()")
    return b, pg

def render(reel):
    rid = reel["id"]; page = build(reel)
    silent = OUT / f"reel{rid}_silent.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)],
                          stdin=subprocess.PIPE)
    with sync_playwright() as pw:
        b, pg = open_page(pw, page)
        for i in range(int(reel["duration"] * FPS)):
            t = i / FPS; pg.evaluate(f"render({t})")
            shot = pg.screenshot(type="jpeg", quality=94); ff.stdin.write(shot)
            if abs(t - reel.get("cover_t", .6)) < 1 / (2 * FPS): (OUT / f"reel{rid}_cover.jpg").write_bytes(shot)
        b.close()
    ff.stdin.close(); ff.wait()
    sh = reel["shots"]; clips = []
    for i, s in enumerate(sh):
        if "video" not in s: continue
        end = sh[i + 1]["start"] if i + 1 < len(sh) else reel["duration"]
        td = td_of(s)
        clips.append({"t": s["start"] - td, "dur": end - s["start"] + td, "src": str(reelc.find_video(s["video"])),
                      "from": s.get("from", 0), "vol": s.get("vol", .3)})
    fx = [{"t": s["start"] - td_of(s), "dur": td_of(s), "kind": s["tr"]} for s in sh if s.get("tr")]
    g = reel.get("globe")
    if g:
        fx += [{"t": g["start"] - .4, "dur": .4, "kind": "zoom"}, {"t": g["end"], "dur": .4, "kind": "zoom"}]
        fx += [{"t": p["at"], "dur": .2, "kind": "pin"} for p in g["pins"]]
    cfg = {"duration": reel["duration"], "bpm": reel.get("bpm", 120), "cta": reel["caps"][-1]["start"], "clips": clips, "fx": fx}
    cj = OUT / f"reel{rid}_audio.json"; cj.write_text(json.dumps(cfg))
    wav = OUT / f"reel{rid}.wav"
    subprocess.run([sys.executable, str(ROOT / "audio3.py"), str(wav), str(cj)], check=True)
    final = OUT / f"reel{rid}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", str(final)], check=True)
    return final

def stills(reel, times, out):
    from PIL import Image
    page = build(reel); ims = []
    with sync_playwright() as pw:
        b, pg = open_page(pw, page)
        for t in times:
            pg.evaluate(f"render({t})"); p = f"/tmp/claude-0/ae_{reel['id']}_{t}.png"; pg.screenshot(path=p)
            ims.append(Image.open(p).resize((216, 384)))
        b.close()
    cols = min(10, len(ims)); rows = (len(ims) + cols - 1) // cols
    s = Image.new("RGB", (cols * 222, rows * 390), "#777")
    for i, im in enumerate(ims): s.paste(im, ((i % cols) * 222 + 3, (i // cols) * 390 + 3))
    s.save(out)

if __name__ == "__main__":
    reels = json.load(open(sys.argv[1]))
    if len(sys.argv) > 2 and sys.argv[2] == "--stills":
        r = next(x for x in reels if x["id"] == sys.argv[3])
        stills(r, [float(x) for x in sys.argv[4:]], f"/tmp/claude-0/stills_{r['id']}.png"); sys.exit()
    ids = sys.argv[2:]
    for r in reels:
        if ids and r["id"] not in ids: continue
        print(render(r))
