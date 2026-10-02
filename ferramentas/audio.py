"""Synthesised bed for the Reels: soft pad + light pulse + whooshes/ticks on cues.
Usage: python3 audio.py out.wav DURATION '[{"t":3.2,"type":"whoosh"}]'"""
import sys, json, wave, numpy as np

SR = 44100
path, dur, cues = sys.argv[1], float(sys.argv[2]), json.loads(sys.argv[3])
N = int(SR * (dur + 0.05))
t = np.arange(N) / SR
rng = np.random.default_rng(7)
BPM = 100; beat = 60 / BPM

def lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def hz(m): return 440 * 2 ** ((m - 69) / 12)

# --- pad: Am9 -> Fmaj7 -> Cadd9 -> G6, 4 bars each chord ---
chords = [[45, 57, 60, 64, 67, 71], [41, 53, 57, 60, 64, 69], [48, 55, 60, 62, 64, 67], [43, 55, 59, 62, 64, 66]]
bar = 4 * beat; seg = 2 * bar
pad = np.zeros(N)
for ci in range(int(dur // seg) + 2):
    ch = chords[ci % len(chords)]
    s0, s1 = ci * seg, (ci + 1) * seg
    i0, i1 = int(s0 * SR), min(int((s1 + 0.8) * SR), N)
    if i0 >= N: break
    tt = t[i0:i1] - s0
    env = np.minimum(1, tt / 0.9) * np.clip((s1 - s0 + 0.8 - tt) / 0.8, 0, 1)
    sig = np.zeros(i1 - i0)
    for m in ch:
        f = hz(m)
        for det in (-0.12, 0.12):
            ff = f * 2 ** (det / 12)
            for h, amp in ((1, 1), (2, .35), (3, .15)):
                sig += amp * np.sin(2 * np.pi * ff * h * tt + rng.uniform(0, 6.28))
    pad[i0:i1] += sig * env
pad = lp(pad, 1400)
pad *= 1 + 0.15 * np.sin(2 * np.pi * t * 0.25)          # slow breathing

# --- pulse: soft kick on 1 and 3, closed tick on off-beats (from 0.4 s) ---
drums = np.zeros(N)
def add(buf, at, sig):
    i = int(at * SR)
    if i >= N: return
    j = min(N, i + len(sig)); buf[i:j] += sig[:j - i]
kt = np.arange(int(.35 * SR)) / SR
kick = np.sin(2 * np.pi * (48 * kt + 60 * (1 - np.exp(-kt * 30)) / 30)) * np.exp(-kt * 9)
ht = np.arange(int(.05 * SR)) / SR
hat = np.diff(rng.standard_normal(len(ht) + 1)) * np.exp(-ht * 90) * .5
n_beats = int(dur / beat) + 1
for b in range(n_beats):
    at = b * beat
    if at > dur - 0.6: break
    if b % 2 == 0: add(drums, at, kick * (.9 if b % 4 == 0 else .6))
    add(drums, at + beat / 2, hat * (.7 if b % 2 else .45))

# --- cues ---
fx = np.zeros(N)
for c in cues:
    if c["type"] == "whoosh":
        L = int(.6 * SR); wt = np.arange(L) / SR
        nz = rng.standard_normal(L)
        env = np.sin(np.pi * np.clip(wt / .6, 0, 1)) ** 2
        sweep = lp(nz, 900) * .8 + np.diff(np.concatenate([[0], lp(nz, 5000)])) * 2
        add(fx, c["t"] - .3, sweep * env * .9)
    elif c["type"] == "tick":
        L = int(.08 * SR); tk = np.arange(L) / SR
        add(fx, c["t"], np.sin(2 * np.pi * 1850 * tk) * np.exp(-tk * 70) * .35)
    elif c["type"] == "hit":
        L = int(1.2 * SR); hh = np.arange(L) / SR
        s = sum(np.sin(2 * np.pi * hz(m) * hh) for m in (57, 64, 69, 76)) / 4
        add(fx, c["t"], (s * np.exp(-hh * 3) + kick[:L] if L <= len(kick) else s * np.exp(-hh * 3)) * .7)
        add(fx, c["t"], kick * .8)

mix = pad / np.max(np.abs(pad)) * .30 + drums * .32 + fx * .55
fade = np.ones(N); fl = int(1.2 * SR); fade[-fl:] = np.linspace(1, 0, fl)
fade[:int(.03 * SR)] = np.linspace(0, 1, int(.03 * SR))
mix *= fade
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix /= np.max(np.abs(mix)) / 0.89
st = np.stack([mix, np.roll(mix, int(.012 * SR)) * .97 + mix * .03], axis=1)
with wave.open(path, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
