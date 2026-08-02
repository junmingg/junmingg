"""Renders portrait.txt — the ASCII portrait used by build.py.

Usage: python portrait.py [cols] [gamma] > portrait.txt

portrait-source.png is a studio shot on a flat blue key, so the subject comes
out with a plain chroma-key: distance from the background colour gives a soft
alpha that keeps individual hair strands, and everything is composited onto
white before the luminance -> character-ramp mapping. Cells outside the subject
become blanks.
"""
from PIL import Image
import numpy as np
from scipy import ndimage
import sys

COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 96
GAMMA = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5   # >1 darkens the skin midtones
DETAIL = float(sys.argv[3]) if len(sys.argv) > 3 else 1.4  # local-contrast boost
RAMP = "@%#*+=-:."          # dark -> light; no space, so build.py can mirror it

SRC = "portrait-source.png"
CROP = (295, 190, 955, 950)
SOFT, SOLID = 55.0, 135.0   # colour distance from the key: fully background -> fully subject

im = Image.open(SRC).convert("RGB").crop(CROP)
a = np.asarray(im, dtype=np.float32)

corners = np.concatenate([a[:40, :40].reshape(-1, 3), a[:40, -40:].reshape(-1, 3)])
key = np.median(corners, axis=0)
dist = np.linalg.norm(a - key, axis=2)
alpha = np.clip((dist - SOFT) / (SOLID - SOFT), 0, 1)

# drop specks of leftover key noise; the head is one blob
solid = ndimage.binary_fill_holes(ndimage.binary_opening(alpha > 0.5, np.ones((5, 5))))
lab, n = ndimage.label(solid)
if n:
    solid = lab == np.argmax(np.bincount(lab.ravel())[1:]) + 1
alpha *= ndimage.binary_dilation(solid, np.ones((9, 9)))

# composite onto white, then grade using the subject's own range
gray = np.asarray(im.convert("L"), dtype=np.float32) * alpha + 255 * (1 - alpha)
lo, hi = np.percentile(gray[alpha > 0.5], (1, 99))
gray = np.clip((gray - lo) / max(1.0, hi - lo), 0, 1)

# cells are generated at a 0.5 aspect ratio: build.py renders them at a line
# height of 2 x character width
rows = max(1, round(COLS * im.height / im.width * 0.5))

# The hair is dark enough to clip to a single ramp character across the whole
# mass. Unsharp at ~2 cells (finer detail just averages away in the downsample)
# puts the strands back without disturbing the overall tonality.
blur = ndimage.gaussian_filter(gray, sigma=2.0 * im.width / COLS)
gray = np.clip(gray + DETAIL * (gray - blur), 0, 1)
cells = np.asarray(Image.fromarray((gray * 255).astype(np.uint8))
                   .resize((COLS, rows), Image.LANCZOS), dtype=np.float32)
keep = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8))
                  .resize((COLS, rows), Image.LANCZOS)) > 70

n = len(RAMP)
for y in range(rows):
    line = ""
    for x in range(COLS):
        if not keep[y, x]:
            line += " "
            continue
        v = min(255, int(255 * (cells[y, x] / 255) ** GAMMA))
        line += RAMP[min(n - 1, v * n // 256)]
    print(line.rstrip())
