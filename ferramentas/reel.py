"""Render a 9:16 Reel (1080x1920, 30 fps) in the AMG Carbon standard.

Usage: REEL=reels.json python3 reel.py 03
Each reel is a list of scenes; every frame is drawn deterministically by render(t)
in the page, captured with Playwright and piped to ffmpeg. Audio is synthesised
(audio.py) and muxed at the end.
"""
import json, os, sys, subprocess, pathlib, base64
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
F = ROOT / "node_modules/@fontsource"
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
FPS = 30

def B(p):
    return base64.b64encode((F / p).read_bytes()).decode()

FONTS = "".join(
    f"@font-face{{font-family:{fam};font-weight:{w};src:url(data:font/woff2;base64,{B(path)})}}"
    for fam, w, path in [
        ("Barlow", 400, "barlow/files/barlow-latin-400-normal.woff2"),
        ("Barlow", 600, "barlow/files/barlow-latin-600-normal.woff2"),
        ("Barlow", 700, "barlow/files/barlow-latin-700-normal.woff2"),
        ("BarlowC", 700, "barlow-condensed/files/barlow-condensed-latin-700-normal.woff2"),
        ("BarlowC", 800, "barlow-condensed/files/barlow-condensed-latin-800-normal.woff2"),
    ])

PAGE = (ROOT / "reel_template.html").read_text()


def build(reel):
    html = PAGE.replace("/*FONTS*/", FONTS).replace("/*REEL*/", json.dumps(reel, ensure_ascii=False))
    return html


def render(reel, name):
    dur = reel["duration"]
    n = int(dur * FPS)
    silent = OUT / f"{name}_silent.mp4"
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
        "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)], stdin=subprocess.PIPE)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.set_content(build(reel))
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        pg.evaluate("fit()")
        for i in range(n):
            t = i / FPS
            pg.evaluate(f"render({t})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=95))
            if i == int(reel.get("cover_t", 2.6) * FPS):
                pg.screenshot(path=str(OUT / f"{name}_cover.jpg"), type="jpeg", quality=92)
        b.close()
    ff.stdin.close(); ff.wait()
    # audio
    wav = OUT / f"{name}.wav"
    subprocess.run([sys.executable, str(ROOT / "audio.py"), str(wav), str(dur),
                    json.dumps(reel.get("cues", []))], check=True)
    final = OUT / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", str(final)], check=True)
    return final


if __name__ == "__main__":
    reels = json.load(open(ROOT / os.environ.get("REEL", "reels.json")))
    ids = sys.argv[1:]
    for r in reels:
        if ids and r["id"] not in ids:
            continue
        print("rendering", r["id"])
        print(render(r, f"reel{r['id']}"))
