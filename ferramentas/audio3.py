"""Beat-locked soundtrack for the sync Reels + the clips' own sound.
Usage: python3 audio2.py out.wav config.json
config: {"duration": 20, "bpm": 120, "cta": 16.0,
         "clips": [{"t": 0.0, "dur": 2.3, "src": "/path/IMG.mov", "from": 2.0, "vol": 0.9}]}
"""
import sys, json, wave, subprocess, numpy as np

SR = 44100
out, cfg = sys.argv[1], json.load(open(sys.argv[2]))
dur, bpm = cfg["duration"], cfg.get("bpm", 120)
N = int(SR * (dur + 0.1)); t = np.arange(N) / SR
beat = 60 / bpm; bar = 4 * beat
rng = np.random.default_rng(11)

def add(buf, at, sig, g=1.0):
    i = int(round(at * SR))
    if i >= len(buf) or i + len(sig) <= 0: return
    a = max(0, -i); i = max(0, i); j = min(len(buf), i + len(sig) - a)
    buf[i:j] += sig[a:a + (j - i)] * g

def onepole(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for k in range(len(x)): s = (1 - a) * x[k] + a * s; y[k] = s
    return y

def hz(m): return 440 * 2 ** ((m - 69) / 12)

# ---------- instruments ----------
def kick():
    L = int(.42 * SR); k = np.arange(L) / SR
    f = 46 + 110 * np.exp(-k * 38)
    ph = 2 * np.pi * np.cumsum(f) / SR
    click = np.exp(-k * 900) * .6
    return (np.sin(ph) * np.exp(-k * 7.5) + click) * .95

def clap():
    L = int(.28 * SR); k = np.arange(L) / SR
    n = rng.standard_normal(L)
    env = np.exp(-k * 28) + .55 * np.exp(-np.maximum(k - .012, 0) * 30) * (k > .012) + .4 * np.exp(-np.maximum(k - .024, 0) * 22) * (k > .024)
    bp = n - onepole(n, 900); bp = onepole(bp, 5200)
    return bp * env * 1.6

def hat(open_=False):
    L = int((.18 if open_ else .05) * SR); k = np.arange(L) / SR
    n = rng.standard_normal(L); hp = n - onepole(n, 7000)
    return hp * np.exp(-k * (14 if open_ else 80)) * .5

def bass_note(m, length):
    L = int(length * SR); k = np.arange(L) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * k) + .35 * np.sin(4 * np.pi * f * k) + .12 * np.sin(6 * np.pi * f * k)
    env = np.minimum(1, k / .008) * np.exp(-k * 5)
    return s * env * .8

def pad_chord(notes, length):
    L = int(length * SR); k = np.arange(L) / SR
    s = np.zeros(L)
    for m in notes:
        for det in (-.08, .08):
            f = hz(m) * 2 ** (det / 12)
            s += np.sin(2 * np.pi * f * k + rng.uniform(0, 6)) + .3 * np.sin(4 * np.pi * f * k)
    env = np.minimum(1, k / .25) * np.minimum(1, (length - k) / .3).clip(0, 1)
    return s * env / len(notes)

def riser(length):
    L = int(length * SR); k = np.arange(L) / SR
    n = rng.standard_normal(L)
    out = np.zeros(L); s = 0.0
    fc = 400 + 7000 * (k / length) ** 2
    for i in range(L):
        a = np.exp(-2 * np.pi * fc[i] / SR); s = (1 - a) * n[i] + a * s; out[i] = s
    return out * (k / length) ** 1.5 * 1.4

def impact():
    L = int(1.6 * SR); k = np.arange(L) / SR
    boom = np.sin(2 * np.pi * (38 + 60 * np.exp(-k * 9)) * k) * np.exp(-k * 2.2)
    n = rng.standard_normal(L); air = onepole(n, 2500) * np.exp(-k * 4) * .5
    return (boom + air) * .9

# ---------- arrangement ----------
prog = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 55, 60, 64], [55, 59, 62, 67]]   # Am7 F C G
roots = [45, 41, 36, 43]
drums = np.zeros(N); bass = np.zeros(N); pad = np.zeros(N); fx = np.zeros(N)
nbars = int(np.ceil(dur / bar))
cta = cfg.get("cta", dur - 4)
K, C, H, HO = kick(), clap(), hat(), hat(True)
for b in range(nbars):
    t0 = b * bar
    ch = prog[b % 4]
    add(pad, t0, pad_chord(ch, bar + .3))
    intro = b == 0
    for q in range(4):
        tb = t0 + q * beat
        if tb >= dur - .3: break
        if not intro: add(drums, tb, K, 1.0 if q == 0 else .85)
        if q in (1, 3) and not intro: add(drums, tb, C, .55)
        add(drums, tb + beat / 2, HO if (q == 3 and b % 2) else H, .5 if intro else .8)
        if not intro:
            add(bass, tb + beat / 2, bass_note(roots[b % 4], beat * .45), .9)
            add(bass, tb, bass_note(roots[b % 4] + 12, beat * .25), .25)
add(fx, bar - beat, riser(beat), .6)            # into the first drop
add(fx, cta - 2 * beat, riser(2 * beat), .7)     # into the CTA
add(fx, cta, impact(), .9)
add(fx, bar, impact()[:int(.6 * SR)], .45)

pad = onepole(pad, 1800)
music = drums * .55 + bass * .42 + pad * .22 + fx * .5
# CTA: drums drop out, pad swells (breathing ending)
ctai = int(cta * SR)
fade = np.ones(N); fade[ctai:] = np.linspace(1, .0, N - ctai) ** .5
music = (drums * .55 * fade + bass * .42 * fade + pad * .22 * (1 + .6 * (t >= cta)) + fx * .5)


# ---------- sound design for the transitions ----------
def whoosh(length, up=True):
    L = int(length * SR); k = np.arange(L) / SR; u = k / length
    n = rng.standard_normal(L); out = np.zeros(L); s1 = s2 = 0.0
    fc = 300 + 5200 * (np.sin(np.pi * u) ** 1.5)
    for i in range(L):
        a = np.exp(-2 * np.pi * fc[i] / SR); s1 = (1 - a) * n[i] + a * s1
        b = np.exp(-2 * np.pi * fc[i] * .25 / SR); s2 = (1 - b) * n[i] + b * s2
        out[i] = s1 - s2
    env = np.sin(np.pi * u) ** 2
    return out * env * 2.2

def glitch_snd(length):
    L = int(length * SR); out = np.zeros(L); k = np.arange(L) / SR
    for j in range(7):
        i0 = int(rng.uniform(0, .8) * L); ln = int(rng.uniform(.01, .04) * SR)
        f = rng.uniform(300, 2400)
        seg = np.sign(np.sin(2 * np.pi * f * np.arange(ln) / SR)) * .35 + rng.standard_normal(ln) * .25
        out[i0:i0 + ln] += seg[:max(0, min(ln, L - i0))]
    return out

def blip():
    L = int(.18 * SR); k = np.arange(L) / SR
    return (np.sin(2 * np.pi * 1320 * k) + .5 * np.sin(2 * np.pi * 1980 * k)) * np.exp(-k * 28) * .5

def swell(length):
    L = int(length * SR); k = np.arange(L) / SR; u = k / length
    s = sum(np.sin(2 * np.pi * hz(m) * k + rng.uniform(0, 6)) for m in (69, 76, 81))
    return s / 3 * (u ** 2) * np.exp(-(u > .85).astype(float) * (u - .85) * 30) * .6

fxbus = np.zeros(N)
for e in cfg.get("fx", []):
    kd, t0, d = e["kind"], e["t"], max(e["dur"], .25)
    if kd in ("whipL", "whipR", "whipU", "whipD", "spin", "slab", "cube"):
        add(fxbus, t0 - .12, whoosh(d + .25), .55)
    elif kd == "zoom":
        add(fxbus, t0 - .15, whoosh(d + .3), .6); add(fxbus, t0 + d * .5, impact()[:int(.5 * SR)], .35)
    elif kd == "glitch":
        add(fxbus, t0, glitch_snd(d + .1), .5)
    elif kd == "pin":
        add(fxbus, t0, blip(), .45)
    elif kd in ("leak", "dissolve"):
        add(fxbus, t0 - .3, swell(d + .3), .35)
music = music + fxbus

# ---------- the clips' own sound ----------
clipbus = np.zeros(N); duck = np.ones(N)
for c in cfg.get("clips", []):
    wav = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(c["from"]), "-t", str(c["dur"] + .2), "-i", c["src"],
                          "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(wav, dtype=np.int16).astype(np.float32) / 32768
    if len(a) == 0: continue
    L = len(a); k = np.arange(L) / SR
    env = np.minimum(1, k / .08) * np.minimum(1, (L / SR - k) / .12).clip(0, 1)
    a = a * env
    rms = np.sqrt(np.mean(a ** 2)) + 1e-6
    a = a / rms * .12                     # normalise clip loudness
    v = c.get("vol", .35)
    add(clipbus, c["t"], a, v)
    if v > .6:
        i0 = int(c["t"] * SR); i1 = min(N, i0 + L)
        duck[i0:i1] = np.minimum(duck[i0:i1], .45)
duck = np.convolve(duck, np.ones(2205) / 2205, mode="same")
mix = music * duck + clipbus
mix[-int(.8 * SR):] *= np.linspace(1, 0, int(.8 * SR))
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix /= np.max(np.abs(mix)) / .9
st = np.stack([mix, np.roll(mix, int(.011 * SR))], 1)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
