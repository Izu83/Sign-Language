"""Sign language trainer: camera on the left, one big sign on the right."""
import base64
import json
import time
import tkinter as tk
import tkinter.font as tkfont
import urllib.request
from pathlib import Path

from signs import SIGNS, detect

# Heavy libraries are imported after the window is on screen (see App.boot).
cv2 = mp = art = None

CYPRUS = "#004643"
SAND = "#F0EDE5"
FONT_NAME = "Gastilo"          # falls back to FALLBACK_FONT if not installed
FALLBACK_FONT = "Georgia"

HOLD_FRAMES = 12               # frames a sign must be held to count
CAM_W, CAM_H = 800, 600
PANEL_W = 380
PICTURE_SIZE = 280
WINDOW_W, WINDOW_H = 1280, 720

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "hand_landmarker.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
             "hand_landmarker/float16/latest/hand_landmarker.task")
PROGRESS_FILE = ROOT / "data" / "progress.json"
SETTINGS_FILE = ROOT / "data" / "settings.json"

CV_SAND = (229, 237, 240)      # OpenCV colours are BGR
CV_CYPRUS = (67, 70, 0)

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
]


def ensure_model():
    if not MODEL_PATH.exists():
        print("Downloading hand model (~8 MB, first run only)...")
        MODEL_PATH.parent.mkdir(exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Sign Language Trainer")
        root.configure(bg=CYPRUS)
        x = max((root.winfo_screenwidth() - WINDOW_W) // 2, 0)
        y = max((root.winfo_screenheight() - WINDOW_H) // 2 - 20, 0)
        root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")
        root.resizable(False, False)

        self.family = FONT_NAME if FONT_NAME in set(tkfont.families()) else FALLBACK_FONT
        self.mode = "learn"              # "learn" or "guess"
        self.current = 0
        self.revealed = False
        self.hold = 0
        self.done = self.load_progress()
        self.pictures = {}               # sign name -> PhotoImage
        self.show_outline = self.load_settings().get("outline", True)
        self.banner_text, self.banner_until = "", 0.0
        self.frame_ts = 0

        self.cap = self.landmarker = None

        self.build_ui()
        self.style_modes()
        self.name.configure(text="Sign Language")
        self.how.configure(text="Loading...")
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(50, self.boot)        # let the window appear first

    def boot(self):
        """Load the heavy libraries, the hand model and the camera."""
        global cv2, mp, art
        import cv2, mediapipe as mp, art
        self.status.set("Loading hand model...")
        self.root.update_idletasks()
        ensure_model()
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
        self.status.set("Show your hand" if self.cap.isOpened() else "Camera not found")
        self.render()
        self.tick()

    # ---------- persistence ----------
    def load_progress(self):
        try:
            names = set(json.loads(PROGRESS_FILE.read_text()))
            return {i for i, s in enumerate(SIGNS) if s["name"] in names}
        except (OSError, ValueError, TypeError):
            return set()

    def load_settings(self):
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except (OSError, ValueError):
            return {}

    def save_progress(self):
        PROGRESS_FILE.parent.mkdir(exist_ok=True)
        PROGRESS_FILE.write_text(json.dumps(sorted(SIGNS[i]["name"] for i in self.done)))

    # ---------- UI ----------
    def font(self, size, bold=False):
        return (self.family, size, "bold" if bold else "normal")

    def build_ui(self):
        stage = tk.Frame(self.root, bg=CYPRUS)
        stage.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        self.video_label = tk.Label(stage, bg="#00312F")
        self.video_label.pack(expand=True)
        self.status = tk.StringVar(value="Starting...")
        tk.Label(stage, textvariable=self.status, bg=CYPRUS, fg=SAND,
                 font=self.font(13)).pack(pady=(10, 0))

        panel = tk.Frame(self.root, bg=SAND, width=PANEL_W)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        # mode switch
        modes = tk.Frame(panel, bg=CYPRUS, padx=2, pady=2)
        modes.pack(fill="x", padx=28, pady=(28, 0))
        self.mode_btns = {}
        for key, text in (("learn", "Sign + meaning"), ("guess", "Meaning only")):
            b = tk.Button(modes, text=text, font=self.font(12), bd=0, relief="flat",
                          cursor="hand2", command=lambda k=key: self.set_mode(k))
            b.pack(side="left", fill="x", expand=True)
            self.mode_btns[key] = b

        # progress
        self.counter = tk.Label(panel, bg=SAND, fg=CYPRUS, font=self.font(12))
        self.counter.pack(pady=(24, 6))
        self.bar = tk.Canvas(panel, width=PANEL_W - 56, height=6, bg="#D9D5CB",
                             highlightthickness=0)
        self.bar.pack()

        # the big sign
        card = tk.Frame(panel, bg=SAND)
        card.pack(expand=True, fill="both", padx=28)
        self.picture = tk.Label(card, bg=SAND, fg=CYPRUS, font=self.font(110))
        self.picture.pack(pady=(24, 0))
        self.name = tk.Label(card, bg=SAND, fg=CYPRUS, font=self.font(34),
                             wraplength=PANEL_W - 56)
        self.name.pack(pady=(6, 0))
        self.how = tk.Label(card, bg=SAND, fg=CYPRUS, font=self.font(13),
                            wraplength=PANEL_W - 70, justify="center")
        self.how.pack(pady=(12, 0))
        self.hint_btn = tk.Button(card, text="Show me the sign", bg=SAND, fg=CYPRUS,
                                  activebackground=SAND, font=self.font(12), bd=0,
                                  cursor="hand2", command=self.reveal)

        # bottom buttons
        bottom = tk.Frame(panel, bg=SAND)
        bottom.pack(fill="x", padx=28, pady=(0, 24))
        self.skip_btn = tk.Button(bottom, text="Skip  →", bg=CYPRUS, fg=SAND, bd=0,
                                  activebackground=CYPRUS, activeforeground=SAND,
                                  font=self.font(14), cursor="hand2", pady=8,
                                  command=lambda: self.advance(self.current))
        self.skip_btn.pack(fill="x")
        links = tk.Frame(bottom, bg=SAND)
        links.pack(fill="x", pady=(10, 0))
        self.outline_btn = tk.Button(links, bg=SAND, fg=CYPRUS, bd=0, activebackground=SAND,
                                     font=self.font(11), cursor="hand2",
                                     command=self.toggle_outline)
        self.outline_btn.pack(side="left")
        tk.Button(links, text="Reset progress", bg=SAND, fg=CYPRUS, bd=0,
                  activebackground=SAND, font=self.font(11), cursor="hand2",
                  command=self.reset).pack(side="right")
        self.root.bind("<h>", lambda e: self.toggle_outline())
        self.update_outline_btn()

    def style_modes(self):
        for key, b in self.mode_btns.items():
            on = key == self.mode
            b.configure(bg=CYPRUS if on else SAND, fg=SAND if on else CYPRUS,
                        activebackground=CYPRUS if on else SAND,
                        activeforeground=SAND if on else CYPRUS)

    def render(self):
        self.style_modes()

        total, n = len(SIGNS), len(self.done)
        self.bar.delete("all")
        self.bar.create_rectangle(0, 0, (PANEL_W - 56) * n / total, 6, fill=CYPRUS, width=0)

        self.hint_btn.pack_forget()
        if n == total:
            self.counter.configure(text="All done!")
            self.show_picture(None, "✓")
            self.name.configure(text="You know them all")
            self.how.configure(text="Reset your progress to practise again.")
            self.skip_btn.configure(state="disabled")
            return

        self.skip_btn.configure(state="normal")
        self.counter.configure(text=f"{n} of {total} learned")
        sign = SIGNS[self.current]
        self.name.configure(text=sign["name"])
        if self.mode == "learn" or self.revealed:
            self.show_picture(sign)
            self.how.configure(text=sign["how"])
        else:
            self.show_picture(None, "?")
            self.how.configure(text="Make this sign in front of the camera.")
            self.hint_btn.pack(pady=(10, 0))

    def show_picture(self, sign, text=""):
        if sign is None:
            self.picture.configure(image="", text=text, height=1, width=0)
            return
        if sign["name"] not in self.pictures:
            data = base64.b64encode(art.load(sign, PICTURE_SIZE))
            self.pictures[sign["name"]] = tk.PhotoImage(data=data)
        self.picture.configure(image=self.pictures[sign["name"]], text="", height=0, width=0)

    def update_outline_btn(self):
        self.outline_btn.configure(text=f"Hand outline: {'on' if self.show_outline else 'off'}")

    def toggle_outline(self):
        self.show_outline = not self.show_outline
        self.update_outline_btn()
        try:
            SETTINGS_FILE.parent.mkdir(exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps({"outline": self.show_outline}))
        except OSError:
            pass

    # ---------- actions ----------
    def set_mode(self, mode):
        self.mode, self.revealed = mode, False
        self.render()

    def reveal(self):
        self.revealed = True
        self.render()

    def reset(self):
        self.done.clear()
        self.save_progress()
        self.current, self.revealed, self.hold = 0, False, 0
        self.render()

    def advance(self, after):
        """Move to the next sign that isn't done yet, wrapping around."""
        for step in range(1, len(SIGNS) + 1):
            nxt = (after + step) % len(SIGNS)
            if nxt not in self.done:
                self.current = nxt
                break
        self.revealed, self.hold = False, 0
        self.render()

    def complete(self, i):
        self.done.add(i)
        self.save_progress()
        self.banner_text = f"{SIGNS[i]['name']}  OK"
        self.banner_until = time.time() + 1.5
        self.advance(i)

    # ---------- main loop ----------
    def tick(self):
        ok, frame = self.cap.read() if self.cap.isOpened() else (False, None)
        if ok:
            frame = cv2.flip(cv2.resize(frame, (CAM_W, CAM_H)), 1)
            self.process(frame)
            self.video_label.configure(image=self.to_photo(frame))
        self.root.after(15, self.tick)

    def to_photo(self, frame):
        _, buf = cv2.imencode(".ppm", frame)
        self.photo = tk.PhotoImage(data=buf.tobytes(), format="PPM")  # keep a reference
        return self.photo

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.frame_ts += 33
        result = self.landmarker.detect_for_video(
            mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), self.frame_ts)

        if not result.hand_landmarks:
            self.status.set("Show your hand")
            self.hold = 0
        else:
            lm = result.hand_landmarks[0]
            if self.show_outline:
                pts = [(int(p.x * CAM_W), int(p.y * CAM_H)) for p in lm]
                for a, b in HAND_CONNECTIONS:
                    cv2.line(frame, pts[a], pts[b], CV_SAND, 3, cv2.LINE_AA)
                for p in pts:
                    cv2.circle(frame, p, 6, CV_SAND, -1, cv2.LINE_AA)
                    cv2.circle(frame, p, 6, CV_CYPRUS, 1, cv2.LINE_AA)

            seen = detect(lm)
            self.status.set(SIGNS[seen]["name"] if seen is not None else "Hand detected")
            if seen is not None and seen == self.current and len(self.done) < len(SIGNS):
                self.hold += 1
                if self.hold >= HOLD_FRAMES:
                    self.complete(seen)
            else:
                self.hold = 0

        if time.time() < self.banner_until:
            text = self.banner_text
            (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)
            x = (CAM_W - w) // 2
            cv2.rectangle(frame, (x - 16, 20), (x + w + 16, 30 + h + 16), CV_SAND, -1)
            cv2.putText(frame, text, (x, 30 + h), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        CV_CYPRUS, 2, cv2.LINE_AA)

    def close(self):
        if self.cap:
            self.cap.release()
        if self.landmarker:
            self.landmarker.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
