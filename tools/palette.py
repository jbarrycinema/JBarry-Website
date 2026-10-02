#!/usr/bin/env python3
"""Extract a per-second 3-colour palette timeline from a video.

Usage: palette.py <video> -> prints JSON {"d": duration, "p": [[c1,c2,c3], ...]}
Each entry is one second; colours are hex strings ordered by visual weight.
"""
import itertools, json, subprocess, sys
import numpy as np

W, H = 64, 36
src = sys.argv[1]
dur = float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).strip())
raw = subprocess.check_output(
    ["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=1,scale={W}:{H}:flags=area",
     "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
frames = np.frombuffer(raw, np.uint8).reshape(-1, W * H, 3).astype(np.float32) / 255.0


def hsv(px):
    mx, mn = px.max(1), px.min(1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    return s, mx


def kmeans(px, w, k=3, iters=12):
    # deterministic init: spread along luminance-weighted ordering
    order = np.argsort((px * [0.3, 0.59, 0.11]).sum(1))
    c = px[order[np.linspace(0, len(px) - 1, k).astype(int)]].copy()
    for _ in range(iters):
        lab = ((px[:, None, :] - c[None]) ** 2).sum(2).argmin(1)
        for j in range(k):
            m = lab == j
            if w[m].sum() > 0:
                c[j] = (px[m] * w[m, None]).sum(0) / w[m].sum()
    lab = ((px[:, None, :] - c[None]) ** 2).sum(2).argmin(1)
    weight = np.array([w[lab == j].sum() for j in range(k)])
    return c[np.argsort(-weight)]


def lift(c):
    """Push a colour into a usable range for a glow on near-black:
    keep hue, ensure some value, cap saturation blowout."""
    mx = c.max()
    if mx < 0.35:
        c = c * (0.35 / max(mx, 1e-3))
    return np.clip(c, 0, 1)


out = []
prev = None
for f in frames:
    s, v = hsv(f)
    # favour colourful, mid-to-bright pixels; near-black contributes little
    w = (0.15 + s) * np.clip(v - 0.06, 0, 1) ** 0.8
    if w.sum() < 1e-3:
        w = np.ones(len(f))
    c = kmeans(f, w)
    c = np.array([lift(x) for x in c])
    if prev is not None:
        # keep each slot tracking its nearest colour so blobs don't swap hues,
        # then smooth lightly so hard cuts don't strobe
        perm = min(itertools.permutations(range(3)),
                   key=lambda p: ((c[list(p)] - prev) ** 2).sum())
        c = 0.65 * c[list(perm)] + 0.35 * prev
    prev = c
    out.append(["#%02x%02x%02x" % tuple((x * 255).round().astype(int)) for x in c])

print(json.dumps({"d": round(dur, 2), "p": out}, separators=(",", ":")))
