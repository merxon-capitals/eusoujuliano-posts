"""Align script lines to a narration without ASR: DP over silence gaps, matching each line's length in characters."""
import re, subprocess, math

def gaps(path, noise="-32dB", d=0.14):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"], capture_output=True, text=True).stderr
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip())
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    en += [dur] * (len(st) - len(en))
    return [(max(0, a), b) for a, b in zip(st, en)], dur

def weight(text):
    # spoken length proxy: letters + digits; punctuation adds a pause
    return len(re.sub(r"[^\wÀ-ú]", "", text)) + 6 * len(re.findall(r"[.,:;?!]", text[:-1]))

def align(path, texts, noise="-32dB", d=0.14):
    G, dur = gaps(path, noise, d)
    s0 = G[0][1] if G and G[0][0] <= 0.05 else 0.0
    e0 = G[-1][0] if G and G[-1][1] >= dur - 0.05 else dur
    inner = [g for g in G if g[0] > s0 + 0.2 and g[1] < e0 - 0.2]
    W = [weight(t) for t in texts]; n = len(texts); m = len(inner)
    def speech(a, b):  # speech time between a and b, minus long internal pauses
        return (b - a) - sum(max(0, min(b, g[1]) - max(a, g[0])) for g in inner if g[1] - g[0] > 0.35)
    k = speech(s0, e0) / sum(W)
    for _ in range(3):
        INF = 1e18
        # best[j][g]: line j ends at gap g (g = m means the end)
        best = [[INF] * (m + 1) for _ in range(n)]; back = [[-1] * (m + 1) for _ in range(n)]
        def cost(j, a, b, glen):
            exp = k * W[j]; dd = speech(a, b)
            return ((dd - exp) / (exp + 0.6)) ** 2 * 10 - 1.2 * math.log(1 + glen * 8)
        for g in range(m + 1):
            b = inner[g][0] if g < m else e0; glen = inner[g][1] - inner[g][0] if g < m else 1.0
            best[0][g] = cost(0, s0, b, glen)
        for j in range(1, n):
            for g in range(j, m + 1):
                b = inner[g][0] if g < m else e0; glen = inner[g][1] - inner[g][0] if g < m else 1.0
                for p in range(j - 1, g):
                    if best[j - 1][p] >= INF: continue
                    c = best[j - 1][p] + cost(j, inner[p][1], b, glen)
                    if c < best[j][g]: best[j][g] = c; back[j][g] = p
        ends = [m]
        for j in range(n - 1, 0, -1): ends.append(back[j][ends[-1]])
        ends = ends[::-1]
        segs = []; a = s0
        for j, g in enumerate(ends):
            b = inner[g][0] if g < m else e0; segs.append([a, b]); a = inner[g][1] if g < m else e0
        k = sum(speech(a, b) for a, b in segs) / sum(W)
    return segs, inner, dur, k

def word_times(text, a, b, inner):
    """Spread words over the speech inside [a,b], skipping internal pauses; punctuation snaps to the nearest pause."""
    words = text.split(); wt = [weight(w) + 1 for w in words]
    pauses = [g for g in inner if g[0] > a and g[1] < b and g[1] - g[0] > 0.2]
    # timeline of speech pieces
    pieces = []; t = a
    for g in pauses: pieces.append((t, g[0])); t = g[1]
    pieces.append((t, b)); tot = sum(q - p for p, q in pieces)
    def at(x):  # speech-time x -> clock time
        for p, q in pieces:
            if x <= q - p: return p + x
            x -= q - p
        return b
    T = sum(wt); out = []; acc = 0
    for w, v in zip(words, wt):
        x0 = acc / T * tot; acc += v; x1 = acc / T * tot
        out.append([w, round(at(x0), 3), round(at(x1 - 1e-6), 3)])
    return out

# ---- text-assisted alignment (ASR chunks -> script lines) ----
import unicodedata
NUM = {"2026": "dois mil e vinte e seis", "10.10": "dez dez", "10": "dez", "20": "vinte", "37": "trinta e sete", "45": "quarenta e cinco",
       "100%": "cem por cento", "40%": "quarenta por cento", "11": "onze", "2939": "dois mil novecentos e trinta e nove", "2.939": "dois mil novecentos e trinta e nove"}
def norm_words(s):
    s = s.lower().replace("r$", " ")
    out = []
    for w in re.findall(r"[\w.%]+", s):
        w = w.strip(".")
        w = NUM.get(w, w)
        out += w.split()
    return [unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode() for w in out if w]

def sim(chunk_words, line_words):
    if not chunk_words: return 0.0
    from difflib import SequenceMatcher
    m = SequenceMatcher(None, chunk_words, line_words, autojunk=False)
    return sum(b.size for b in m.get_matching_blocks())

def align_text(chunks, texts):
    """chunks: [[a,b,text],...] in order; returns one [a,b] per line. Monotonic DP maximising word overlap
    minus a penalty for length mismatch (characters vs. seconds)."""
    C = [c for c in chunks if len(norm_words(c[2])) and not re.fullmatch(r"\W*(m[uú]sica)?\W*", c[2].lower())]
    n, m = len(texts), len(C)
    LW = [norm_words(t) for t in texts]; W = [weight(t) for t in texts]
    k = (C[-1][1] - C[0][0]) / sum(W)
    NEG = -1e18; best = [[NEG] * (m + 1) for _ in range(n + 1)]; back = [[0] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0
    for j in range(1, n + 1):
        for e in range(j, m + 1):
            for s in range(j - 1, e):
                if best[j - 1][s] <= NEG: continue
                cw = sum((norm_words(C[q][2]) for q in range(s, e)), [])
                ov = sim(cw, LW[j - 1]); extra = max(0, len(cw) - len(LW[j - 1]))
                d = C[e - 1][1] - C[s][0]; exp = k * W[j - 1]
                sc = best[j - 1][s] + ov - 0.5 * extra - 3 * abs(d - exp) / (exp + 0.5)
                if sc > best[j][e]: best[j][e] = sc; back[j][e] = s
    segs = []; e = m
    for j in range(n, 0, -1):
        s = back[j][e]; segs.append([C[s][0], C[e - 1][1], " | ".join(C[q][2] for q in range(s, e))]); e = s
    return segs[::-1]
