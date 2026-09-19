"""Sign definitions and hand-shape recognition.

Each sign is described once, in signs.json (shared with the web app), by a pose. That pose
is used twice: to recognise the hand in front of the camera (detect) and to draw the
picture shown in the app (art.py).

  curl    how curled [index, middle, ring, pinky] are: 0 straight, 0.5 hooked, 1 fist
  thumb   what the thumb does: "in" (tucked), "out", "up", "down", or "touch:N" where
          N is the fingertip it touches (0 index, 1 middle, 2 ring, 3 pinky)
  spread  optional: "apart" or "together" for the index and middle fingertips
  tilt    drawing only: sideways angle of each finger, in degrees
"""
import json
import math
import re
from pathlib import Path

ASPECT = 4 / 3   # camera frames are resized to 4:3, landmark x/z are relative to width

SIGNS = json.loads((Path(__file__).resolve().parent.parent / "signs.json").read_text(encoding="utf-8"))

for _s in SIGNS:
    _s["slug"] = re.sub(r"[^a-z0-9]+", "_", _s["name"].lower()).strip("_")


def _d(a, b):
    return math.sqrt(((a.x - b.x) * ASPECT) ** 2 + (a.y - b.y) ** 2 + ((a.z - b.z) * ASPECT) ** 2)


def _curl(lm, f):
    """0 for a straight finger up to 1 for one folded into the palm."""
    mcp, pip, dip, tip = (5 + 4 * f, 6 + 4 * f, 7 + 4 * f, 8 + 4 * f)
    length = _d(lm[0], lm[mcp]) + _d(lm[mcp], lm[pip]) + _d(lm[pip], lm[dip]) + _d(lm[dip], lm[tip])
    ratio = _d(lm[0], lm[tip]) / length
    return min(1.0, max(0.0, (0.95 - ratio) / 0.6))


def features(lm):
    scale = _d(lm[0], lm[9])
    curls = [_curl(lm, f) for f in range(4)]
    tags = set()
    if _d(lm[4], lm[5]) / scale > 0.75:
        tags.add("out")
        if lm[4].y < lm[0].y - 0.3 * scale:
            tags.add("up")
        elif lm[4].y > lm[0].y + 0.3 * scale:
            tags.add("down")
    else:
        tags.add("in")
    for k in range(4):
        if _d(lm[4], lm[8 + 4 * k]) / scale < 0.35:
            tags.add(f"touch:{k}")
    spread = "apart" if _d(lm[8], lm[12]) / scale > 0.3 else "together"
    return curls, tags, spread


def detect(lm, threshold=1.0):
    """Return the index into SIGNS that best matches the hand in `lm`, or None."""
    curls, tags, spread = features(lm)
    best, best_score = None, threshold
    for i, s in enumerate(SIGNS):
        if s["thumb"] not in tags:
            continue
        if s.get("spread") and s["spread"] != spread:
            continue
        score = sum(abs(a - b) for a, b in zip(curls, s["curl"]))
        if score < best_score:
            best, best_score = i, score
    return best
