"""Connection-style Reels: fast cuts of Juliano's photos/videos + native-looking captions.

Usage: python3 reelc.py reels_conexao.json [id ...]
shots: [{"start": 0, "img": "IMG_0455", "kb": [...]}, {"start": 1.2, "video": "IMG_1914.mov", "from": 0.5}]
caps:  [{"start": 0, "end": 2, "text": "texto com [[destaque]]", "small": "...", "quote": true}]
"""
import json, sys, subprocess, pathlib
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from reel import FONTS
import reelm

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out"
FPS = 30
TPL = (ROOT / "reel_conexao.html").read_text()
VIDDIRS = [pathlib.Path("/home/claude/midia/video"), pathlib.Path("/home/claude/midia/raw")]


def find_video(name):
    for d in VIDDIRS:
        if (d / name).exists(): return d / name
    raise FileNotFoundError(name)


def prep_video(name, start, dur):
    src = find_video(name)
    d = reelm.WORK / f"c_{src.stem}_{start}_{dur:.1f}"
    if not d.exists():
        d.mkdir()
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur + .3), "-i", str(src),
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                        "-an", "-q:v", "3", str(d / "%04d.jpg")], check=True)
    return [f"{d.name}/{f.name}" for f in sorted(d.iterdir())]


def build(reel):
    sh = reel["shots"]
    for i, s in enumerate(sh):
        end = sh[i + 1]["start"] if i + 1 < len(sh) else reel["duration"]
        if "img" in s and not s["img"].endswith(".jpg"): s["img"] = reelm.prep_img(s["img"])
        if "video" in s and "frames" not in s:
            td = s.get("td", .5 if s.get("tr") == "dissolve" else .42) if s.get("tr") else 0
            s["frames"] = prep_video(s["video"], s.get("from", 0), (end - s["start"] + td) * s.get("speed", 1))
    page = reelm.WORK / f"conexao{reel['id']}.html"
    page.write_text(TPL.replace("/*FONTS*/", FONTS).replace("/*REEL*/", json.dumps(reel, ensure_ascii=False)))
    return page


def open_page(pw, page):
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto(page.as_uri())
    pg.evaluate("document.fonts.ready"); pg.evaluate("ready()"); pg.wait_for_timeout(300); pg.evaluate("fit()")
    return b, pg


def render(reel):
    rid = reel["id"]
    page = build(reel)
    silent = OUT / f"reel{rid}_silent.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", str(silent)], stdin=subprocess.PIPE)
    with sync_playwright() as pw:
        b, pg = open_page(pw, page)
        for i in range(int(reel["duration"] * FPS)):
            t = i / FPS
            pg.evaluate(f"render({t})")
            shot = pg.screenshot(type="jpeg", quality=94)
            ff.stdin.write(shot)
            if abs(t - reel.get("cover_t", 0.5)) < 1 / (2 * FPS):
                (OUT / f"reel{rid}_cover.jpg").write_bytes(shot)
        b.close()
    ff.stdin.close(); ff.wait()
    cues = [{"t": c["start"], "type": "tick"} for c in reel["caps"][1:]]
    cues += [{"t": s["start"] - .25, "type": "whoosh"} for s in reel["shots"] if s.get("flash")]
    wav = OUT / f"reel{rid}.wav"
    subprocess.run([sys.executable, str(ROOT / "audio.py"), str(wav), str(reel["duration"]), json.dumps(cues)], check=True)
    final = OUT / f"reel{rid}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final)], check=True)
    return final


def stills(reel, times, out):
    from PIL import Image
    page = build(reel)
    ims = []
    with sync_playwright() as pw:
        b, pg = open_page(pw, page)
        for t in times:
            pg.evaluate(f"render({t})"); p = f"/tmp/claude-0/s_{reel['id']}_{t}.png"; pg.screenshot(path=p)
            ims.append(Image.open(p).resize((240, 427)))
        b.close()
    cols = min(8, len(ims)); rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cols * 248, rows * 435), "#777")
    for i, im in enumerate(ims): sh.paste(im, ((i % cols) * 248 + 4, (i // cols) * 435 + 4))
    sh.save(out)


if __name__ == "__main__":
    reels = json.load(open(sys.argv[1]))
    ids = sys.argv[2:]
    for r in reels:
        if ids and r["id"] not in ids: continue
        print(render(r))
