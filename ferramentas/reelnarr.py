"""Narrated Reels (VSL style): karaoke captions + animated cards over Juliano's videos, synced to his voice.
Usage: python3 reelnarr.py narr_semana4.json [ids] [--stills ID t1 t2 ...]
A voice file voice/<id>.(m4a|mp3|wav|ogg|aac) is used when present; otherwise timings are estimated (silent preview).
"""
import json, sys, re, subprocess, pathlib, copy
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import reelae

ROOT = pathlib.Path(__file__).parent
VOICE = ROOT / "voice"
TRS = ["zoom", "whipL", "glitch", "whipU", "spin", "whipR", "cube", "whipD"]

def find_voice(rid):
    for ext in ("wav", "m4a", "mp3", "ogg", "aac", "opus", "mp4"):
        p = VOICE / f"{rid}.{ext}"
        if p.exists(): return p
    return None

def speech_segments(path, noise="-34dB", d=0.28):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip())
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    segs, cur = [], 0.0
    for s0, e0 in zip(starts, ends + [dur] * (len(starts) - len(ends))):
        if s0 - cur > .12: segs.append([cur, s0])
        cur = e0
    if dur - cur > .12: segs.append([cur, dur])
    return segs, dur

def fit_segments(segs, n):
    """Merge speech segments (smallest gaps first) until there is one per script line."""
    segs = [list(s) for s in segs]
    while len(segs) > n:
        gaps = [segs[i + 1][0] - segs[i][1] for i in range(len(segs) - 1)]
        i = gaps.index(min(gaps)); segs[i][1] = segs[i + 1][1]; del segs[i + 1]
    while len(segs) < n:  # split the longest segment
        i = max(range(len(segs)), key=lambda k: segs[k][1] - segs[k][0]); a, b = segs[i]; m = (a + b) / 2
        segs[i:i + 1] = [[a, m], [m, b]]
    return segs

def line_words(text):
    return text.split()

def asr_chunks(rid):
    import glob
    for f in sorted(glob.glob(str(ROOT / "asr" / "chunks_*.json")), key=lambda f: -pathlib.Path(f).stat().st_mtime):
        d = json.load(open(f))
        if rid in d: return d[rid]
    return None

def timings(lines, rid):
    import align
    voice = find_voice(rid); texts = [L["text"] for L in lines]
    chunks = asr_chunks(rid) if voice else None
    if voice and chunks:  # transcription-assisted: each line gets the chunks whose words match it
        segs = [[a, b] for a, b, _ in align.align_text(chunks, texts)]
        inner = [(chunks[i][1], chunks[i + 1][0]) for i in range(len(chunks) - 1)]
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(voice)], capture_output=True, text=True).stdout.strip())
    elif voice:
        segs, inner, dur, _ = align.align(voice, texts)
    else:
        segs, t, inner = [], 0.35, []
        for L in lines:
            n = sum(len(w) + 3 for w in line_words(L["text"])); d = n * 0.044
            segs.append([t, t + d]); t += d + 0.42
        dur = t
    words = []
    for li, (L, (a, b)) in enumerate(zip(lines, segs)):
        wt = align.word_times(L["text"], a, b, inner); last = len(wt) - 1
        for j, (w, t0, t1) in enumerate(wt):
            words.append({"w": w, "t0": t0, "t1": t1, "line": li, "eol": j == last})
    return words, segs, voice, dur

def build_reel(N):
    lines = N["lines"]; rid = N["id"]
    words, segs, voice, vdur = timings(lines, rid)
    starts = [0.0] + [segs[i][0] - 0.12 for i in range(1, len(lines))]
    end_speech = segs[-1][1]; duration = round(end_speech + N.get("tail", 2.6), 2)
    ends = starts[1:] + [duration]
    shots, cards, scenes = [], [], {}
    vids = N["videos"]
    for i, L in enumerate(lines):
        st, en = starts[i], ends[i]
        v = L.get("video") or vids[i % len(vids)]
        shot = {"start": round(st, 3), "video": v[0], "from": v[1], "vol": 0.12, "plate": L.get("plate", N.get("plate", [0, 0.58]))}
        if i: shot["tr"] = L.get("tr", TRS[i % len(TRS)]); shot["td"] = 0.28
        if L.get("photo"): shot = {"start": round(st, 3), "img": L["photo"], "card": True, "tr": "slab", "td": 0.5}
        shots.append(shot)
        # extra cuts inside long lines: new footage every ~2.4 s, like the reference
        if not L.get("photo"):
            k, tt = 1, st + 2.4
            while en - tt > 1.6:
                vv = vids[(i * 3 + k + 7) % len(vids)]
                shots.append({"start": round(tt, 3), "video": vv[0], "from": vv[1] + 0.5 * k, "vol": 0.1, "plate": shot["plate"], "tr": "zoom" if k % 2 else "whipL", "td": 0.22})
                k += 1; tt += 2.4
        lw = [w for w in words if w["line"] == i]
        if "card" in L:
            C = copy.deepcopy(L["card"]); C["t0"] = round(st + 0.05, 3) if i else -1.0; C["t1"] = round(en, 3)
            for key in ("at",):  # item times keyed to spoken words
                if key in C and C[key] and isinstance(C[key][0], str):
                    C[key] = [round(next((w["t0"] for w in lw if w["w"].lower().strip('.,:;?!"').startswith(k.lower())), st + 0.5) - C["t0"], 3) for k in C[key]]
            for key in ("stampAt", "strikeAt", "lit"):
                if isinstance(C.get(key), str):
                    C[key] = round(next((w["t0"] for w in lw if w["w"].lower().strip('.,:;?!"').startswith(C[key].lower())), st + 0.8) - C["t0"], 3)
            cards.append(C)
        if "scene" in L:
            S = copy.deepcopy(L["scene"]); typ = S.pop("type"); S.update({"t0": round(st + 0.05, 3), "t1": round(en, 3)}); scenes[typ] = S
    R = {"id": rid, "duration": duration, "bpm": N.get("bpm", 96), "cover_t": 0.4, "words": words, "cards": cards, "scenes": scenes,
         "shots": shots, "caps": [], "drops": [0.0, starts[-1]], "pulse_bar": .012, "pulse": .005, "tema": N["tema"], "caption": N["caption"],
         "voice": str(voice) if voice else None, "cta_t": starts[-1]}
    return R

def render(R):
    import json as js
    rid = R["id"]; page = reelae.build(R)
    OUT = reelae.OUT; FPS = reelae.FPS
    silent = OUT / f"reel{rid}_silent.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b, pg = reelae.open_page(pw, page)
        for i in range(int(R["duration"] * FPS)):
            t = i / FPS; pg.evaluate(f"render({t})")
            shot = pg.screenshot(type="jpeg", quality=92); ff.stdin.write(shot)
            if abs(t - R.get("cover_t", .4)) < 1 / (2 * FPS): (OUT / f"reel{rid}_cover.jpg").write_bytes(shot)
        b.close()
    ff.stdin.close(); ff.wait()
    sh = R["shots"]; clips = []
    for i, s in enumerate(sh):
        if "video" not in s: continue
        end = sh[i + 1]["start"] if i + 1 < len(sh) else R["duration"]; td = reelae.td_of(s)
        clips.append({"t": s["start"] - td, "dur": end - s["start"] + td, "src": str(reelae.reelc.find_video(s["video"])), "from": s.get("from", 0), "vol": s.get("vol", .12)})
    fx = [{"t": s["start"] - reelae.td_of(s), "dur": reelae.td_of(s), "kind": s["tr"]} for s in sh if s.get("tr")]
    fx += [{"t": c["t0"], "dur": .2, "kind": "pin"} for c in R["cards"]]
    cfg = {"duration": R["duration"], "bpm": R["bpm"], "cta": R["cta_t"], "clips": clips, "fx": fx, "voice": R.get("voice"), "bed": 0.22}
    cj = OUT / f"reel{rid}_audio.json"; cj.write_text(js.dumps(cfg)); wav = OUT / f"reel{rid}.wav"
    subprocess.run([sys.executable, str(ROOT / "audio3.py"), str(wav), str(cj)], check=True)
    final = OUT / f"reel{rid}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final)], check=True)
    if final.stat().st_size > 19.0 * 1024 * 1024:  # jsDelivr serves files up to 20 MB: re-encode at a target bitrate (2-pass)
        vb = int(18.2 * 8 * 1024 * 1024 / R["duration"] - 160000)
        common = ["-i", str(silent), "-c:v", "libx264", "-preset", "slow", "-b:v", str(vb), "-maxrate", str(int(vb * 1.4)), "-bufsize", str(vb * 2), "-pix_fmt", "yuv420p"]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + common + ["-pass", "1", "-passlogfile", f"/tmp/claude-0/x264_{rid}", "-an", "-f", "null", "/dev/null"], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav)] + common + ["-pass", "2", "-passlogfile", f"/tmp/claude-0/x264_{rid}",
                        "-map", "1:v", "-map", "0:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(final)], check=True)
    return final

if __name__ == "__main__":
    cfgs = json.load(open(sys.argv[1]))
    if len(sys.argv) > 2 and sys.argv[2] == "--stills":
        N = next(x for x in cfgs if x["id"] == sys.argv[3]); R = build_reel(N)
        reelae.stills(R, [float(x) for x in sys.argv[4:]], f"/tmp/claude-0/stills_{R['id']}.png")
        json.dump(R, open(f"/tmp/claude-0/narr_{R['id']}.json", "w"), ensure_ascii=False, indent=1); sys.exit()
    ids = sys.argv[2:]
    for N in cfgs:
        if ids and N["id"] not in ids: continue
        R = build_reel(N); json.dump(R, open(reelae.OUT / f"narr_{R['id']}.json", "w"), ensure_ascii=False, indent=1)
        print(render(R), R["duration"], "voz" if R.get("voice") else "sem voz")
