"""Sign definitions and hand-shape recognition.

Each sign is described once by a pose, and that pose is used twice: to recognise the
hand in front of the camera (detect) and to draw the picture shown in the app (art.py).

  curl    how curled [index, middle, ring, pinky] are: 0 straight, 0.5 hooked, 1 fist
  thumb   what the thumb does: "in" (tucked), "out", "up", "down", or "touch:N" where
          N is the fingertip it touches (0 index, 1 middle, 2 ring, 3 pinky)
  spread  optional: "apart" or "together" for the index and middle fingertips
  tilt    drawing only: sideways angle of each finger, in degrees
"""
import math
import re

ASPECT = 4 / 3   # camera frames are resized to 4:3, landmark x/z are relative to width

SIGNS = [
    dict(name="Hello",      curl=[0, 0, 0, 0],       thumb="out",     tilt=[-8, -3, 3, 8],
         how="Open hand, all five fingers spread, palm facing forward."),
    dict(name="Yes",        curl=[1, 1, 1, 1],       thumb="in",
         how="Closed fist with the thumb across the fingers. Nod it like a head nodding."),
    dict(name="Good",       curl=[1, 1, 1, 1],       thumb="up",
         how="Fist with the thumb pointing up."),
    dict(name="Bad",        curl=[1, 1, 1, 1],       thumb="down",
         how="Fist with the thumb pointing down."),
    dict(name="Four",       curl=[0, 0, 0, 0],       thumb="in",
         how="Four fingers straight up and together, thumb folded across the palm."),
    dict(name="Letter C",   curl=[.5, .5, .5, .5],   thumb="out",
         how="Curve all fingers and the thumb into the shape of a C."),
    dict(name="Letter D",   curl=[0, 1, 1, 1],       thumb="in",
         how="Index finger straight up; the other fingers curl to meet the thumb."),
    dict(name="Letter I",   curl=[1, 1, 1, 0],       thumb="in",
         how="Fist with only the pinky finger pointing up."),
    dict(name="Letter L",   curl=[0, 1, 1, 1],       thumb="out",
         how="Index finger up and thumb out to the side, forming an L."),
    dict(name="Letter O",   curl=[.6, .6, .6, .6],   thumb="touch:0",
         how="Curve all fingers so the tips meet the thumb, making an O."),
    dict(name="OK",         curl=[.5, 0, 0, 0],      thumb="touch:0",
         how="Touch thumb and index fingertip in a circle; other three fingers up."),
    dict(name="Letter U",   curl=[0, 0, 1, 1],       thumb="in", spread="together",
         how="Index and middle fingers up and pressed together."),
    dict(name="Letter V",   curl=[0, 0, 1, 1],       thumb="in", spread="apart", tilt=[-10, 10, 0, 0],
         how="Index and middle fingers up and spread apart, also the number two."),
    dict(name="Letter W",   curl=[0, 0, 0, 1],       thumb="in", spread="apart", tilt=[-12, 0, 12, 0],
         how="Index, middle and ring fingers up and spread; thumb holds down the pinky."),
    dict(name="Six",        curl=[0, 0, 0, .5],      thumb="touch:3",
         how="Thumb touches the pinky fingertip; the other three fingers point up."),
    dict(name="Seven",      curl=[0, 0, .5, 0],      thumb="touch:2",
         how="Thumb touches the ring fingertip; the other three fingers point up."),
    dict(name="Eight",      curl=[0, .5, 0, 0],      thumb="touch:1",
         how="Thumb touches the middle fingertip; the other three fingers point up."),
    dict(name="Letter X",   curl=[.5, 1, 1, 1],      thumb="in",
         how="Fist with the index finger hooked like a bent hook."),
    dict(name="Letter Y",   curl=[1, 1, 1, 0],       thumb="out",
         how="Thumb and pinky out, the other fingers folded. Also means call me."),
    dict(name="I love you", curl=[0, 1, 1, 0],       thumb="out",
         how="Thumb, index finger and pinky out; middle and ring fingers folded."),
    dict(name="Rock on",    curl=[0, 1, 1, 0],       thumb="in",
         how="Index finger and pinky up; thumb, middle and ring fingers folded."),
    dict(name="Three",      curl=[0, 0, 1, 1],       thumb="out",
         how="Thumb, index and middle fingers out; ring and pinky folded."),
]

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
