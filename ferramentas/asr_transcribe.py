import sys, json, subprocess, numpy as np, sherpa_onnx
sys.path.insert(0, '/home/claude/ig'); import align
M = '/home/claude/models/dl/sherpa-onnx-whisper-base/'
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M+'base-encoder.onnx', decoder=M+'base-decoder.onnx', tokens=M+'base-tokens.txt', language='pt', task='transcribe', num_threads=4)
def load(p):
    raw = subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.int16).astype(np.float32)/32768
out = {}
for rid in sys.argv[1:]:
    p = f'/home/claude/ig/voice/{rid}.wav'; x = load(p)
    G, dur = align.gaps(p, '-32dB', 0.14)
    # speech chunks between gaps
    chunks = []; t = 0.0
    for a, b in G:
        if a - t > 0.12: chunks.append([t, a])
        t = b
    if dur - t > 0.12: chunks.append([t, dur])
    res = []
    for a, b in chunks:
        s = rec.create_stream(); s.accept_waveform(16000, x[int(max(0,a-0.08)*16000):int(min(dur,b+0.08)*16000)]); rec.decode_stream(s)
        res.append([round(a,3), round(b,3), s.result.text.strip()])
        print(rid, f'{a:6.2f}-{b:6.2f}', s.result.text.strip(), flush=True)
    out[rid] = res
json.dump(out, open('/home/claude/ig/asr/chunks_' + '_'.join(sys.argv[1:]) + '.json', 'w'), ensure_ascii=False, indent=1)
