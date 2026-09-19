<p align="center">
  <img src="assets/banner.svg" alt="Sign Language" width="100%">
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-004643?style=for-the-badge&logo=python&logoColor=F0EDE5&labelColor=004643&color=0b6560">
  <img alt="MediaPipe" src="https://img.shields.io/badge/MediaPipe-hand%20tracking-004643?style=for-the-badge&labelColor=004643&color=0b6560">
  <img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-camera-004643?style=for-the-badge&logo=opencv&logoColor=F0EDE5&labelColor=004643&color=0b6560">
  <img alt="Runs offline" src="https://img.shields.io/badge/runs-offline-004643?style=for-the-badge&labelColor=004643&color=0b6560">
</p>

<p align="center">
  Learn sign language with your webcam. One big sign on screen, you make it in front of the camera,
  and the app checks it and moves on to the next.
</p>

<h2><img src="assets/headers/what-it-does.svg" alt="What it does" width="100%"></h2>

- **Tracks your hand** with your webcam and recognises 22 signs: letters, numbers and everyday words.
- **One sign at a time.** A big picture, the meaning and a one-line description of how to make it sit next to the camera.
- **Two ways to practise.** *Sign + meaning* shows the picture and the word. *Meaning only* shows just the word, so you have to remember the sign, with a hint button if you get stuck.
- **Checks you automatically.** Hold the sign for about half a second and it is ticked off and the next one appears. Skip any sign you want to leave for later.
- **Hand outline on or off.** Show the tracked hand skeleton on the camera, or hide it. Press `H` to switch.
- **Saves your progress** between sessions, with a reset whenever you want a fresh start.
- **Runs offline.** Hand tracking happens on your PC. Nothing from your camera is uploaded.
- **Bring your own pictures.** Every sign picture is a PNG in `images/`; drop in a file with the same name to replace it.

<h2><img src="assets/headers/the-signs.svg" alt="The signs" width="100%"></h2>

<table>
  <tr>
    <td align="center" width="25%"><img src="images/hello.png" width="150" alt="Hello"><br><b>Hello</b></td>
    <td align="center" width="25%"><img src="images/yes.png" width="150" alt="Yes"><br><b>Yes</b></td>
    <td align="center" width="25%"><img src="images/good.png" width="150" alt="Good"><br><b>Good</b></td>
    <td align="center" width="25%"><img src="images/bad.png" width="150" alt="Bad"><br><b>Bad</b></td>
  </tr>
  <tr>
    <td align="center" width="25%"><img src="images/four.png" width="150" alt="Four"><br><b>Four</b></td>
    <td align="center" width="25%"><img src="images/letter_c.png" width="150" alt="Letter C"><br><b>Letter C</b></td>
    <td align="center" width="25%"><img src="images/letter_d.png" width="150" alt="Letter D"><br><b>Letter D</b></td>
    <td align="center" width="25%"><img src="images/letter_i.png" width="150" alt="Letter I"><br><b>Letter I</b></td>
  </tr>
  <tr>
    <td align="center" width="25%"><img src="images/letter_l.png" width="150" alt="Letter L"><br><b>Letter L</b></td>
    <td align="center" width="25%"><img src="images/letter_o.png" width="150" alt="Letter O"><br><b>Letter O</b></td>
    <td align="center" width="25%"><img src="images/ok.png" width="150" alt="OK"><br><b>OK</b></td>
    <td align="center" width="25%"><img src="images/letter_u.png" width="150" alt="Letter U"><br><b>Letter U</b></td>
  </tr>
  <tr>
    <td align="center" width="25%"><img src="images/letter_v.png" width="150" alt="Letter V"><br><b>Letter V</b></td>
    <td align="center" width="25%"><img src="images/letter_w.png" width="150" alt="Letter W"><br><b>Letter W</b></td>
    <td align="center" width="25%"><img src="images/six.png" width="150" alt="Six"><br><b>Six</b></td>
    <td align="center" width="25%"><img src="images/seven.png" width="150" alt="Seven"><br><b>Seven</b></td>
  </tr>
  <tr>
    <td align="center" width="25%"><img src="images/eight.png" width="150" alt="Eight"><br><b>Eight</b></td>
    <td align="center" width="25%"><img src="images/letter_x.png" width="150" alt="Letter X"><br><b>Letter X</b></td>
    <td align="center" width="25%"><img src="images/letter_y.png" width="150" alt="Letter Y"><br><b>Letter Y</b></td>
    <td align="center" width="25%"><img src="images/i_love_you.png" width="150" alt="I love you"><br><b>I love you</b></td>
  </tr>
  <tr>
    <td align="center" width="25%"><img src="images/rock_on.png" width="150" alt="Rock on"><br><b>Rock on</b></td>
    <td align="center" width="25%"><img src="images/three.png" width="150" alt="Three"><br><b>Three</b></td>
    <td></td>
    <td></td>
  </tr>
</table>

Recognition looks at the shape of the hand, not its movement, so signs that need motion (like J or Z) are not included.

<h2><img src="assets/headers/getting-started.svg" alt="Getting started" width="100%"></h2>

You need Python 3.10 or newer and a webcam.

```bash
git clone https://github.com/Izu83/Sign-Language.git
cd Sign-Language
pip install -r requirements.txt
python src/main.py
```

The first launch downloads Google's hand-tracking model (about 8 MB) into `models/`, so it needs an internet connection once.

<h2><img src="assets/headers/how-to-use-it.svg" alt="How to use it" width="100%"></h2>

1. Pick a mode at the top of the right-hand panel.
2. Look at the sign shown, then make it with one hand in front of the camera.
3. Hold it steady until the banner appears. The app moves on by itself.
4. Not feeling one? Press **Skip**. Want to start over? Press **Reset progress**.

| Key or button | What it does |
| --- | --- |
| `Sign + meaning` / `Meaning only` | Switch between learning and guessing |
| `Show me the sign` | Reveal the picture in guessing mode |
| `Skip →` | Move to the next sign without ticking this one off |
| `H` or `Hand outline` | Show or hide the hand skeleton on the camera |
| `Reset progress` | Clear everything you have learned |

<h2><img src="assets/headers/how-it-works.svg" alt="How it works" width="100%"></h2>

Each sign is described once in `src/signs.py`: how curled each finger is, and what the thumb is doing. That single description is used twice.

- **Recognition.** MediaPipe finds 21 landmarks on your hand. The app measures how curled each finger is and where the thumb is, then picks the closest matching sign. The sign has to be held for a few frames so a passing hand shape does not count.
- **Pictures.** `src/art.py` draws the illustration for each sign from the same description, so the picture you see is the shape the camera looks for.

<h2><img src="assets/headers/project-layout.svg" alt="Project layout" width="100%"></h2>

| Path | What it is |
| --- | --- |
| `src/main.py` | The window, camera loop and progress |
| `src/signs.py` | The signs and the code that recognises them |
| `src/art.py` | Draws the pictures (`python src/art.py` redraws all of them) |
| `images/` | One PNG per sign |
| `assets/` | The banner and section headers used in this README |
| `models/` | The downloaded hand model (not committed) |
| `data/` | Your saved progress and settings (not committed) |

<h2><img src="assets/headers/customising.svg" alt="Customising" width="100%"></h2>

- **Font.** Change `FONT_NAME` at the top of `src/main.py`. It falls back to Georgia if the font is not installed.
- **Colours.** Cyprus `#004643` and Sand `#F0EDE5`, defined at the top of `src/main.py` and `src/art.py`.
- **How long to hold a sign.** `HOLD_FRAMES` in `src/main.py`.
- **How strict matching is.** The thresholds in `src/signs.py` (`detect` and `_curl`).
- **Add a sign.** Add an entry to `SIGNS` in `src/signs.py` with its finger curls and thumb, then run `python src/art.py` to draw its picture.

<h2><img src="assets/headers/troubleshooting.svg" alt="Troubleshooting" width="100%"></h2>

- **"Camera not found".** Close other apps that use the webcam, and check your camera permissions in Windows settings.
- **The model will not download.** Download `hand_landmarker.task` from Google's MediaPipe models page and put it in `models/`.
- **A sign will not register.** Keep your whole hand in view, well lit, with the palm facing the camera, and hold it still for a moment. Similar shapes such as D and L, or O and OK, need the thumb clearly placed.
- **Wrong font.** The app uses Georgia unless the font in `FONT_NAME` is installed.

<p align="center">
  <img src="assets/avatar.png" width="56" alt="Izu83"><br>
  Made by <b>Izu83</b>
</p>
