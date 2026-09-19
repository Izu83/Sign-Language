"""Draws a picture of each sign from its pose, in the app colours.

Pictures are saved to images/<slug>.png the first time they are needed. To use your own
picture for a sign, put a PNG with the same name in that folder; it will be used instead.
"""
import math
from pathlib import Path

import cv2
import numpy as np

# BGR colours
SAND = (229, 237, 240)       # #F0EDE5
CYPRUS = (67, 70, 0)         # #004643
SHINE = (117, 122, 22)       # lighter teal for highlights and creases
SLEEVE = (138, 142, 92)      # soft teal cuff
BACKDROP = (210, 223, 228)   # slightly darker sand disc behind the hand
SHADOW = (170, 185, 190)

SIZE = 800
IMAGES = Path(__file__).resolve().parent.parent / "images"

CENTERS = [302, 368, 434, 500]         # finger x positions (index .. pinky)
WIDTHS = [58, 58, 56, 50]
LENGTHS = [200, 225, 205, 160]         # total finger lengths
SPLIT = (0.45, 0.30, 0.25)             # proximal, middle, distal share of a finger
BASE_Y = 455
PALM = (262, 440, 538, 690)            # left, top, right, bottom
THUMB_BASE = (275, 610)


# ---------- drawing helpers ----------
def _chain(img, pts, width, color):
    for a, b in zip(pts, pts[1:]):
        cv2.line(img, a, b, color, width, cv2.LINE_AA)
    for p in pts:
        cv2.circle(img, p, width // 2, color, -1, cv2.LINE_AA)


def _shine(img, pts, width):
    """A thin lighter stripe along the left side of a limb, for a bit of volume."""
    off = int(width * 0.2)
    _chain(img, [(x - off, y) for x, y in pts], max(4, int(width * 0.14)), SHINE)


def _limb(img, pts, width, outline=True):
    if outline:
        _chain(img, pts, width + 16, SAND)   # keeps overlapping parts readable
    _chain(img, pts, width, CYPRUS)
    _shine(img, pts, width)


def _creases(img, pts, width):
    """Small joint lines across a straight finger."""
    for x, y in pts[1:3]:
        cv2.line(img, (x - int(width * 0.28), y), (x + int(width * 0.28), y), SHINE, 4, cv2.LINE_AA)


def _rounded_rect(img, box, r, color):
    l, t, rt, b = box
    cv2.rectangle(img, (l + r, t), (rt - r, b), color, -1)
    cv2.rectangle(img, (l, t + r), (rt, b - r), color, -1)
    for cx, cy in ((l + r, t + r), (rt - r, t + r), (l + r, b - r), (rt - r, b - r)):
        cv2.circle(img, (cx, cy), r, color, -1, cv2.LINE_AA)


def _sleeve(img, cx, top, half_w=100):
    _rounded_rect(img, (cx - half_w, top, cx + half_w, 790), 22, SLEEVE)
    cv2.line(img, (cx - half_w + 14, top + 24), (cx + half_w - 14, top + 24), SAND, 5, cv2.LINE_AA)


def _finger_points(f, curl, tilt):
    """Project the finger's three segments onto the picture (it curls toward the viewer)."""
    total = LENGTHS[f]
    a1, a2, a3 = curl * 60, curl * 70, curl * 50
    thetas = [a1, a1 + a2, a1 + a2 + a3]
    x, y = float(CENTERS[f]), float(BASE_Y)
    sx, sy = math.sin(math.radians(tilt)), math.cos(math.radians(tilt))
    pts = [(int(x), int(y))]
    for share, th in zip(SPLIT, thetas):
        step = total * share * math.cos(math.radians(th))
        x += sx * step
        y -= sy * step
        pts.append((int(x), int(y)))
    return pts


def _thumb_points(thumb, tips):
    bx, by = THUMB_BASE
    if thumb == "out":
        return [(bx + 40, by + 20), (bx - 70, by - 55), (bx - 185, by - 120)]
    if thumb == "in":
        return [(bx, by - 20), (bx + 70, by - 60), (bx + 175, by - 85)]
    k = int(thumb.split(":")[1])
    tx, ty = tips[k]
    mx, my = (bx + tx) // 2 - 45, (by + ty) // 2
    return [(bx, by), (mx, my), (tx, ty + 12)]


# ---------- the three kinds of picture ----------
def _open_hand(sign):
    img = np.full((SIZE, SIZE, 3), SAND, np.uint8)
    tilt = sign.get("tilt", [0, 0, 0, 0])
    curls = sign["curl"]
    pts = [_finger_points(f, curls[f], tilt[f]) for f in range(4)]

    # straight fingers go behind the palm, curled ones lie over it
    for f in (3, 2, 1, 0):
        if curls[f] < 0.4:
            _limb(img, pts[f], WIDTHS[f])
            _creases(img, pts[f], WIDTHS[f])
    _rounded_rect(img, PALM, 40, CYPRUS)
    cv2.rectangle(img, (325, PALM[3] - 30), (475, 780), CYPRUS, -1)
    cv2.ellipse(img, (400, 610), (95, 38), 0, 15, 165, SHINE, 5, cv2.LINE_AA)   # palm crease
    for f in (3, 2, 1, 0):
        if curls[f] >= 0.4:
            _limb(img, pts[f], WIDTHS[f])

    thumb = _thumb_points(sign["thumb"], [p[-1] for p in pts])
    # beside the palm the thumb has no outline, so it joins the hand
    _limb(img, thumb, 62, outline=sign["thumb"] != "out")
    _sleeve(img, 400, 730)
    return img


def _thumbs_fist(down):
    """Side view of a fist with the thumb straight up (or down, when flipped)."""
    img = np.full((SIZE, SIZE, 3), SAND, np.uint8)
    cv2.rectangle(img, (325, 640), (485, 780), CYPRUS, -1)                     # wrist
    _rounded_rect(img, (255, 370, 550, 700), 55, CYPRUS)                       # fist
    _chain(img, [(350, 420), (335, 205)], 104, CYPRUS)                         # thumb
    _shine(img, [(350, 420), (335, 205)], 104)
    for y in (455, 520, 585, 650):                                             # curled fingers
        _limb(img, [(305, y), (500, y)], 60)
    _sleeve(img, 405, 730)
    return cv2.flip(img, 0) if down else img


def _curved_hand(open_c):
    """Side view of a curved hand: an open C, or a closed O (thumb meets the fingertips)."""
    img = np.full((SIZE, SIZE, 3), SAND, np.uint8)
    cx, cy, r, w = 400, 340, 160, 88
    cv2.rectangle(img, (335, 500), (465, 780), CYPRUS, -1)                     # wrist
    if open_c:
        cv2.ellipse(img, (cx, cy), (r, r), 0, 45, 315, CYPRUS, w, cv2.LINE_AA)
        for a in (45, 315):
            x = int(cx + r * math.cos(math.radians(a)))
            y = int(cy + r * math.sin(math.radians(a)))
            cv2.circle(img, (x, y), w // 2, CYPRUS, -1, cv2.LINE_AA)
        cv2.ellipse(img, (cx - 22, cy), (r, r), 0, 110, 250, SHINE, 8, cv2.LINE_AA)
    else:
        cv2.circle(img, (cx, cy), r, CYPRUS, w, cv2.LINE_AA)
        cv2.line(img, (cx + r - w // 2 - 4, cy), (cx + r + w // 2 + 4, cy), SAND, 8, cv2.LINE_AA)
        cv2.ellipse(img, (cx - 22, cy), (r, r), 0, 110, 250, SHINE, 8, cv2.LINE_AA)
    _sleeve(img, 400, 730, 95)
    return img


# ---------- finishing ----------
def _fit(img, size):
    """Crop to the hand, centred in a square with a margin, and scale to `size`."""
    ys, xs = np.where(np.any(img != SAND, axis=2))
    cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
    half = max(xs.max() - xs.min(), ys.max() - ys.min()) // 2 + 50
    canvas = np.full((half * 2, half * 2, 3), SAND, np.uint8)
    x0, y0 = cx - half, cy - half
    sx0, sy0 = max(x0, 0), max(y0, 0)
    sx1, sy1 = min(x0 + 2 * half, SIZE), min(y0 + 2 * half, SIZE)
    canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
    return cv2.resize(canvas, (size, size), interpolation=cv2.INTER_AREA)


def _finish(layer, size):
    """Put the hand on a soft sand disc with a blurred drop shadow."""
    big = _fit(layer, size * 2)
    ink = np.any(big != SAND, axis=2).astype(np.uint8)
    k = (size // 12) | 1                                     # fill the outline gaps in the hand
    body = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))

    out = np.full_like(big, SAND)
    cv2.circle(out, (size, size), int(size * 0.94), BACKDROP, -1, cv2.LINE_AA)

    shadow = np.roll(body, (size // 22, size // 30), axis=(0, 1)).astype(np.float32)
    shadow = cv2.GaussianBlur(shadow, (0, 0), size / 26)[..., None] * 0.55
    out = (out * (1 - shadow) + np.array(SHADOW, np.float32) * shadow).astype(np.uint8)

    out[body > 0] = big[body > 0]
    return cv2.resize(out, (size, size), interpolation=cv2.INTER_AREA)


def render(sign, size=320):
    if sign["name"] in ("Letter C", "Letter O"):
        layer = _curved_hand(sign["name"] == "Letter C")
    elif sign["thumb"] in ("up", "down"):
        layer = _thumbs_fist(sign["thumb"] == "down")
    else:
        layer = _open_hand(sign)
    return _finish(layer, size)


def image_path(sign):
    return IMAGES / f"{sign['slug']}.png"


def load(sign, size=320):
    """Return PNG bytes for the sign, drawing and saving the picture if it doesn't exist."""
    path = image_path(sign)
    if not path.exists():
        IMAGES.mkdir(exist_ok=True)
        cv2.imwrite(str(path), render(sign, size))
    img = cv2.imread(str(path))
    h, w = img.shape[:2]
    scale = size / max(h, w)
    if scale != 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return cv2.imencode(".png", img)[1].tobytes()


if __name__ == "__main__":
    # Redraw every picture (overwrites images/*.png, including any you replaced).
    from signs import SIGNS
    IMAGES.mkdir(exist_ok=True)
    for sign in SIGNS:
        cv2.imwrite(str(image_path(sign)), render(sign))
    print(f"Drew {len(SIGNS)} pictures in {IMAGES}")
