"""Synthesize a two-voice test recording (vowel-like speech from a pulse source through formant filters)."""
import numpy as np, scipy.signal as sg, scipy.io.wavfile as wf, sys

SR = 48000
rng = np.random.default_rng(7)
VOWELS = [(730, 1090, 2440, 3400), (270, 2290, 3010, 3700), (300, 870, 2240, 3300),
          (530, 1840, 2480, 3500), (570, 840, 2410, 3400), (660, 1720, 2410, 3500)]

def voice(dur, f0, fscale, seed):
    r = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.08 * np.sin(2 * np.pi * 0.7 * t + r.uniform(0, 6)) + 0.01 * r.standard_normal(n).cumsum() / np.sqrt(n))
    phase = np.cumsum(f) / SR
    src = np.diff(np.floor(phase), prepend=0.0)              # one impulse per glottal cycle
    src = sg.lfilter([1], [1, -0.97], src)                   # spectral tilt
    out = np.zeros(n); seg = int(0.17 * SR)
    for s in range(0, n, seg):
        e = min(n, s + seg); v = VOWELS[r.integers(len(VOWELS))]
        x = src[max(0, s - 400):e]
        y = x.copy()
        for fc, bw in zip([fi * fscale for fi in v], (80, 100, 140, 180)):
            rr = np.exp(-np.pi * bw / SR); th = 2 * np.pi * fc / SR
            y = sg.lfilter([1 - rr], [1, -2 * rr * np.cos(th), rr * rr], y)
        out[s:e] = y[-(e - s):]
    env = 0.55 + 0.45 * np.sin(2 * np.pi * 4.2 * t + r.uniform(0, 6)) ** 2  # syllable rhythm
    ramp = np.minimum(1, np.minimum(t, dur - t) / 0.04)
    out = out * env * ramp
    return out / (np.abs(out).max() + 1e-9) * 0.35

A = dict(f0=112, fscale=1.0); B = dict(f0=208, fscale=1.17)
plan = [(1.0, 4.5, A), (5.3, 7.8, A), (9.8, 12.8, B), (13.4, 15.4, A), (21.5, 24.0, B), (25.0, 27.0, B), (27.35, 29.5, A)]
total = 31.0
x = rng.standard_normal(int(total * SR)) * 0.0015            # room noise
for i, (a, b, v) in enumerate(plan):
    s = int(a * SR); y = voice(b - a, v['f0'], v['fscale'], 100 + i); x[s:s + len(y)] += y
wf.write(sys.argv[1], SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
print('wrote', sys.argv[1], total, 's')
