"""Reels with Juliano's own photos/videos as background (AMG Carbon overlays).

Usage: python3 reelm.py reels_midia.json [id ...]
Scene bg: {"img": "IMG_0455"} (from /home/claude/midia/jpg) with optional
"kb": [scale0, scale1, x0, x1, y0, y1], or {"video": "IMG_1914.mov", "from": 0.0}.
"""
import json, sys, subprocess, pathlib, shutil
from PIL import Image
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from reel import FONTS

ROOT = pathlib.Path(__file__).parent
MID = pathlib.Path("/home/claude/midia")
WORK = MID / "work"; WORK.mkdir(exist_ok=True)
OUT = ROOT / "out"
FPS = 30
TPL = (ROOT / "reel_media.html").read_text()


def prep_img(name):
    dst = WORK / f"{name}.jpg"
    if not dst.exists():
        im = Image.open(MID / "jpg" / f"{name}.jpg").convert("RGB")
        s = max(1300 / im.width, 2310 / im.height)
        im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS).save(dst, quality=90)
    return dst.name


def prep_video(name, start, dur):
    d = WORK / f"v_{pathlib.Path(name).stem}_{start}"
    if not d.exists():
        d.mkdir()
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur + .5), "-i", str(MID / "raw" / name),
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                        "-q:v", "3", str(d / "%04d.jpg")], check=True)
    return [f"{d.name}/{f.name}" for f in sorted(d.iterdir())]


def render(reel):
    rid = reel["id"]
    for i, s in enumerate(reel["scenes"]):
        bg = s.get("bg")
        if not bg: continue
        if "img" in bg: bg["img"] = prep_img(bg["img"])
        if "video" in bg:
            end = reel["scenes"][i + 1]["start"] if i + 1 < len(reel["scenes"]) else reel["duration"]
            bg["frames"] = prep_video(bg["video"], bg.get("from", 0), end - s["start"] + .5)
    page = WORK / f"reel{rid}.html"
    page.write_text(TPL.replace("/*FONTS*/", FONTS).replace("/*REEL*/", json.dumps(reel, ensure_ascii=False)))
    silent = OUT / f"reel{rid}_silent.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", str(silent)], stdin=subprocess.PIPE)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(page.as_uri())
        pg.evaluate("document.fonts.ready"); pg.evaluate("ready()"); pg.wait_for_timeout(300)
        pg.evaluate("fit()")
        n = int(reel["duration"] * FPS)
        for i in range(n):
            t = i / FPS
            pg.evaluate(f"render({t})")
            shot = pg.screenshot(type="jpeg", quality=94)
            ff.stdin.write(shot)
            if abs(t - reel.get("cover_t", 1.5)) < 1 / (2 * FPS):
                (OUT / f"reel{rid}_cover.jpg").write_bytes(shot)
        b.close()
    ff.stdin.close(); ff.wait()
    cues = [{"t": s["start"] + .05, "type": "tick"} for s in reel["scenes"][1:]]
    cues += [{"t": reel["scenes"][-1]["start"] + .15, "type": "hit"}]
    wav = OUT / f"reel{rid}.wav"
    subprocess.run([sys.executable, str(ROOT / "audio.py"), str(wav), str(reel["duration"]), json.dumps(cues)], check=True)
    final = OUT / f"reel{rid}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final)], check=True)
    return final


if __name__ == "__main__":
    reels = json.load(open(sys.argv[1]))
    ids = sys.argv[2:]
    for r in reels:
        if ids and r["id"] not in ids: continue
        print(render(r))
