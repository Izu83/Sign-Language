<p align="center">
  <img src="assets/banner.svg" alt="Sign Language" width="100%">
</p>

A small desktop app that teaches sign language through your webcam. One big sign is shown
on the right, you make it in front of the camera, and the app checks it for you and moves
on to the next one.

## Features

- **Two modes.** *Sign + meaning* shows the picture and how to make it. *Meaning only* shows
  just the word so you have to remember the sign (there is a hint button if you get stuck).
- **Live hand tracking** with an optional hand outline on the camera (press `H` to toggle).
- **22 signs:** letters (C, D, I, L, O, U, V, W, X, Y), numbers (Four, Six, Seven, Eight),
  and words (Hello, Yes, Good, Bad, OK, Three, Rock on, I love you).
- **Progress is saved**, and you can skip a sign or reset everything at any time.
- **Your own pictures.** Every sign picture lives in `images/`; drop in a PNG with the same
  name to replace one.

## Getting started

Requires Python 3.10 or newer and a webcam.

```bash
pip install -r requirements.txt
python src/main.py
```

The first run downloads Google's hand-tracking model (about 8 MB) into `models/`.

## How it works

Each sign is described once in `src/signs.py` by how curled each finger is and what the
thumb is doing. That description is used twice:

1. **Recognition:** MediaPipe finds 21 landmarks on your hand, the app measures finger
   curl and thumb position from them, and picks the closest matching sign. Hold it for
   about half a second to count.
2. **Pictures:** `src/art.py` draws the illustration for each sign from the same
   description, so what you see is what the camera looks for.

Recognition looks at the shape of the hand, not movement, so signs that need motion are not
included.

## Project layout

| Path | What it is |
| --- | --- |
| `src/main.py` | The window, camera loop and progress |
| `src/signs.py` | The signs and the code that recognises them |
| `src/art.py` | Draws the pictures (`python src/art.py` redraws all of them) |
| `images/` | One PNG per sign |
| `assets/` | The README banner |
| `models/`, `data/` | Downloaded model and saved progress (not committed) |

## Customising

- **Font:** change `FONT_NAME` at the top of `src/main.py`.
- **Colours:** Cyprus `#004643` and Sand `#F0EDE5`, defined at the top of `src/main.py` and
  `src/art.py`.
- **Sensitivity:** `HOLD_FRAMES` in `src/main.py` controls how long a sign must be held, and
  the thresholds in `src/signs.py` control how strict matching is.

---

Made by Izu83
