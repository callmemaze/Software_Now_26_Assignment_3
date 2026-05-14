"""
Spot the Difference — HIT137 Group Assignment 3
================================================
A desktop game where players find 5 programmatic differences between two images.

Architecture (OOP):
  DifferenceEngine   — Pure image-processing logic (OpenCV). Knows nothing about UI.
  ImagePanel         — Tkinter canvas that displays one image and handles drawing.
  ModifiedPanel      — Subclass of ImagePanel; adds click-detection behaviour.
  GameApp            — Root application. Owns all state, orchestrates the game.

Demonstrates: encapsulation, constructors, methods, class interaction,
              inheritance (ModifiedPanel → ImagePanel), polymorphism (draw_marker).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import random
import math
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Palette & Constants
# ──────────────────────────────────────────────────────────────────────────────
MAX_MISTAKES   = 3
NUM_DIFFS      = 5
DISPLAY_SIZE   = (480, 360)   # (width, height) each panel is shown at
CLICK_RADIUS   = 45           # pixels — proximity threshold for a valid click
DIFF_MIN_SIZE  = 60           # minimum side length of a difference region (px on source image)
DIFF_MAX_SIZE  = 110          # maximum side length
DIFF_MIN_GAP   = 20           # minimum gap between difference bounding boxes (px on source image)

# Visual markers
FOUND_COLOR   = (0, 0, 255)   # BGR red  — drawn around found differences
REVEAL_COLOR  = (255, 120, 0) # BGR blue — drawn around revealed differences
MARKER_THICK  = 3             # circle stroke width

# UI colours (hex)
BG_DARK   = "#1a1a2e"
BG_MID    = "#16213e"
BG_PANEL  = "#0f3460"
ACCENT    = "#e94560"
ACCENT2   = "#f5a623"
TEXT_MAIN = "#eaeaea"
TEXT_SUB  = "#9090a0"
SUCCESS   = "#4caf50"
DANGER    = "#e94560"


# ──────────────────────────────────────────────────────────────────────────────
# DifferenceEngine — pure image-processing logic, zero UI
# ──────────────────────────────────────────────────────────────────────────────
class DifferenceEngine:
    """
    Creates a modified clone of an image with exactly NUM_DIFFS non-overlapping
    programmatic alterations, and validates player clicks against those regions.

    Encapsulation: all difference data (regions, found-flags) lives here.
    """

    # The alteration catalogue — each callable takes (image, x, y, w, h) → image
    ALTERATION_TYPES = ("colour_shift", "noise_patch", "blur_patch",
                        "brightness_invert", "hue_rotate")

    def __init__(self, original_bgr: np.ndarray):
        self._original  = original_bgr          # source image, never mutated
        self._modified  = original_bgr.copy()   # clone that receives alterations
        self._regions   = []                    # list of (x, y, w, h) in source px
        self._types     = []                    # alteration type per region
        self._found     = []                    # bool per region

        self._generate_differences()

    # ── Public interface ───────────────────────────────────────────────────────

    @property
    def original(self) -> np.ndarray:
        return self._original

    @property
    def modified(self) -> np.ndarray:
        return self._modified

    @property
    def regions(self):
        return list(self._regions)

    @property
    def found_flags(self):
        return list(self._found)

    @property
    def num_found(self) -> int:
        return sum(self._found)

    @property
    def num_remaining(self) -> int:
        return NUM_DIFFS - self.num_found

    @property
    def all_found(self) -> bool:
        return all(self._found)

    def check_click(self, src_x: int, src_y: int) -> int:
        """
        Test whether (src_x, src_y) in source-image coordinates is near an
        unfound difference centre.  Returns the index of the matched region,
        or -1 if no match.
        """
        for i, (rx, ry, rw, rh) in enumerate(self._regions):
            if self._found[i]:
                continue
            cx, cy = rx + rw // 2, ry + rh // 2
            dist   = math.hypot(src_x - cx, src_y - cy)
            if dist <= CLICK_RADIUS:
                self._found[i] = True
                return i
        return -1

    # ── Private: difference generation ────────────────────────────────────────

    def _generate_differences(self):
        h, w = self._original.shape[:2]
        margin = DIFF_MAX_SIZE // 2 + 5

        placed = []
        attempts = 0
        while len(placed) < NUM_DIFFS and attempts < 2000:
            attempts += 1
            bw = random.randint(DIFF_MIN_SIZE, DIFF_MAX_SIZE)
            bh = random.randint(DIFF_MIN_SIZE, DIFF_MAX_SIZE)
            bx = random.randint(margin, w - bw - margin)
            by = random.randint(margin, h - bh - margin)
            box = (bx, by, bw, bh)

            if not any(self._boxes_overlap(box, p) for p in placed):
                placed.append(box)

        self._regions = placed
        self._found   = [False] * len(placed)

        # Choose distinct alteration types (cycling if needed)
        type_pool = list(self.ALTERATION_TYPES)
        random.shuffle(type_pool)
        for i, region in enumerate(self._regions):
            alt = type_pool[i % len(type_pool)]
            self._types.append(alt)
            self._apply_alteration(alt, region)

    def _boxes_overlap(self, a, b) -> bool:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        gap = DIFF_MIN_GAP
        return not (ax + aw + gap <= bx or bx + bw + gap <= ax or
                    ay + ah + gap <= by or by + bh + gap <= ay)

    def _apply_alteration(self, kind: str, region):
        x, y, w, h = region
        patch = self._modified[y:y+h, x:x+w]

        if kind == "colour_shift":
            # Shift hue in HSV space — visually distinct but subtle
            hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).astype(np.int16)
            shift = random.choice([40, -40, 60, -60, 80])
            hsv[:, :, 0] = (hsv[:, :, 0] + shift) % 180
            hsv = np.clip(hsv, 0, 255).astype(np.uint8)
            self._modified[y:y+h, x:x+w] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        elif kind == "noise_patch":
            # Add structured salt-and-pepper noise
            noise = np.random.randint(0, 80, patch.shape, dtype=np.uint8)
            self._modified[y:y+h, x:x+w] = cv2.add(patch, noise)

        elif kind == "blur_patch":
            # Heavy Gaussian blur — makes region look smeared
            k = 21 if min(w, h) >= 40 else 15
            k = k if k % 2 == 1 else k + 1
            self._modified[y:y+h, x:x+w] = cv2.GaussianBlur(patch, (k, k), 0)

        elif kind == "brightness_invert":
            # Partially invert brightness in HSV
            hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).astype(np.int16)
            hsv[:, :, 2] = 255 - hsv[:, :, 2]
            self._modified[y:y+h, x:x+w] = cv2.cvtColor(
                np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)

        elif kind == "hue_rotate":
            # Saturate and shift — makes colours punchier
            hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).astype(np.int16)
            hsv[:, :, 0] = (hsv[:, :, 0] + 90) % 180
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] + 80, 0, 255)
            self._modified[y:y+h, x:x+w] = cv2.cvtColor(
                np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)


# ──────────────────────────────────────────────────────────────────────────────
# ImagePanel — a Tkinter canvas that displays one image
# ──────────────────────────────────────────────────────────────────────────────
class ImagePanel:
    """
    Base class: owns a tk.Canvas, shows a PIL/OpenCV image scaled to
    DISPLAY_SIZE, and can draw marker circles onto it.

    Polymorphism: draw_marker can be overridden by subclasses.
    """

    def __init__(self, parent: tk.Widget, label_text: str):
        self._frame = tk.Frame(parent, bg=BG_PANEL, bd=2, relief="flat")

        # Header label above the canvas
        header = tk.Label(
            self._frame, text=label_text,
            bg=BG_PANEL, fg=TEXT_SUB,
            font=("Helvetica", 11, "bold"), pady=6
        )
        header.pack()

        # The canvas itself
        self._canvas = tk.Canvas(
            self._frame,
            width=DISPLAY_SIZE[0], height=DISPLAY_SIZE[1],
            bg="#111122", highlightthickness=0, cursor="crosshair"
        )
        self._canvas.pack(padx=8, pady=(0, 8))

        # Internal state
        self._photo_ref  = None  # keep a reference so GC doesn't collect it
        self._scale_x    = 1.0   # source px / display px  (set when image loaded)
        self._scale_y    = 1.0
        self._src_w      = 1
        self._src_h      = 1
        self._markers    = []    # list of (cx, cy, r, colour) in display coords

    # ── Layout ────────────────────────────────────────────────────────────────

    def pack(self, **kwargs):
        self._frame.pack(**kwargs)

    # ── Image management ──────────────────────────────────────────────────────

    def show_image(self, bgr: np.ndarray):
        """Display a BGR OpenCV image, scaling to fit DISPLAY_SIZE."""
        self._src_h, self._src_w = bgr.shape[:2]
        self._scale_x = self._src_w / DISPLAY_SIZE[0]
        self._scale_y = self._src_h / DISPLAY_SIZE[1]

        rgb   = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        pil   = Image.fromarray(rgb).resize(DISPLAY_SIZE, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(pil)

        self._photo_ref = photo
        self._canvas.delete("all")
        self._markers.clear()
        self._canvas.create_image(0, 0, anchor="nw", image=photo)

    def clear(self):
        self._canvas.delete("all")
        self._markers.clear()
        self._photo_ref = None

    # ── Coordinate helpers ─────────────────────────────────────────────────────

    def src_to_display(self, sx: int, sy: int) -> tuple[int, int]:
        return int(sx / self._scale_x), int(sy / self._scale_y)

    def display_to_src(self, dx: int, dy: int) -> tuple[int, int]:
        return int(dx * self._scale_x), int(dy * self._scale_y)

    # ── Marker drawing (polymorphic) ──────────────────────────────────────────

    def draw_marker(self, src_x: int, src_y: int, src_r: int, color_hex: str,
                    tag: str = "marker"):
        """Draw a circle around (src_x, src_y) using source-image coordinates."""
        dx, dy = self.src_to_display(src_x, src_y)
        # Scale radius too (average of both axes)
        dr = int(src_r / ((self._scale_x + self._scale_y) / 2))
        self._canvas.create_oval(
            dx - dr, dy - dr, dx + dr, dy + dr,
            outline=color_hex, width=3, tags=tag
        )
        self._markers.append((dx, dy, dr, color_hex))

    def _region_centre_radius(self, region) -> tuple[int, int, int]:
        x, y, w, h = region
        cx, cy = x + w // 2, y + h // 2
        r      = int(max(w, h) / 2 + 12)
        return cx, cy, r


# ──────────────────────────────────────────────────────────────────────────────
# ModifiedPanel — subclass with click-handling; the interactive right panel
# ──────────────────────────────────────────────────────────────────────────────
class ModifiedPanel(ImagePanel):
    """
    Inherits ImagePanel; overrides draw_marker to also flash an animation,
    and adds a click-callback hook for the game to respond to player input.
    """

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, "🔍  Modified  —  Click here to find differences")
        self._on_click_cb = None
        self._canvas.bind("<Button-1>", self._handle_click)
        self._active = False  # only respond to clicks when a game is running

    def activate(self, callback):
        self._active     = True
        self._on_click_cb = callback

    def deactivate(self):
        self._active = False

    def _handle_click(self, event: tk.Event):
        if not self._active or self._on_click_cb is None:
            return
        src_x, src_y = self.display_to_src(event.x, event.y)
        self._on_click_cb(src_x, src_y, event.x, event.y)

    # Polymorphism: override to add a brief ring animation
    def draw_marker(self, src_x: int, src_y: int, src_r: int, color_hex: str,
                    tag: str = "marker"):
        super().draw_marker(src_x, src_y, src_r, color_hex, tag)
        # Animate an expanding ghost ring
        dx, dy = self.src_to_display(src_x, src_y)
        dr = int(src_r / ((self._scale_x + self._scale_y) / 2))
        self._animate_ring(dx, dy, dr, color_hex, step=0)

    def _animate_ring(self, cx, cy, base_r, color_hex, step):
        if step > 6:
            return
        r       = base_r + step * 5
        alpha_s = max(0, 1.0 - step / 7)
        # Approximate alpha by brightening — hex manipulation
        ring_id = self._canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=color_hex, width=max(1, 3 - step), tags="ring"
        )
        self._canvas.after(60, lambda: (
            self._canvas.delete(ring_id),
            self._animate_ring(cx, cy, base_r, color_hex, step + 1)
        ))

# ──────────────────────────────────────────────────────────────────────────────
# GameApp — the conductor
# ──────────────────────────────────────────────────────────────────────────────
class GameApp:
    """
    Root application class.  Owns all game state and ties the UI together.
    No image-processing logic lives here — that's DifferenceEngine's job.
    """

    def __init__(self):
        # ── Window setup ──────────────────────────────────────────────────────
        self._root = tk.Tk()
        self._root.title("Spot the Difference")
        self._root.configure(bg=BG_DARK)
        self._root.resizable(False, False)

        # ── Game state ────────────────────────────────────────────────────────
        self._engine   : Optional[DifferenceEngine] = None
        self._mistakes : int = 0
        self._score    : int = 0   # cumulative found differences across all images
        self._game_over: bool = False

        # ── Build UI ──────────────────────────────────────────────────────────
        self._build_ui()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ─ Title bar ──────────────────────────────────────────────────────────
        title_frame = tk.Frame(self._root, bg=BG_DARK)
        title_frame.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            title_frame,
            text="SPOT  THE  DIFFERENCE",
            bg=BG_DARK, fg=ACCENT,
            font=("Helvetica", 22, "bold")
        ).pack(side="left")

        # Score badge on the right
        self._score_var = tk.StringVar(value="Score: 0")
        tk.Label(
            title_frame, textvariable=self._score_var,
            bg=BG_DARK, fg=ACCENT2,
            font=("Helvetica", 14, "bold")
        ).pack(side="right", padx=8)

# ──────────────────────────────────────────────────────────────────────────────
# GameApp — the conductor
# ──────────────────────────────────────────────────────────────────────────────
class GameApp:
    """
    Root application class.  Owns all game state and ties the UI together.
    No image-processing logic lives here — that's DifferenceEngine's job.
    """

    def __init__(self):
        # ── Window setup ──────────────────────────────────────────────────────
        self._root = tk.Tk()
        self._root.title("Spot the Difference")
        self._root.configure(bg=BG_DARK)
        self._root.resizable(False, False)

        # ── Game state ────────────────────────────────────────────────────────
        self._engine   : Optional[DifferenceEngine] = None
        self._mistakes : int = 0
        self._score    : int = 0   # cumulative found differences across all images
        self._game_over: bool = False

        # ── Build UI ──────────────────────────────────────────────────────────
        self._build_ui()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ─ Title bar ──────────────────────────────────────────────────────────
        title_frame = tk.Frame(self._root, bg=BG_DARK)
        title_frame.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            title_frame,
            text="SPOT  THE  DIFFERENCE",
            bg=BG_DARK, fg=ACCENT,
            font=("Helvetica", 22, "bold")
        ).pack(side="left")

        # Score badge on the right
        self._score_var = tk.StringVar(value="Score: 0")
        tk.Label(
            title_frame, textvariable=self._score_var,
            bg=BG_DARK, fg=ACCENT2,
            font=("Helvetica", 14, "bold")
        ).pack(side="right", padx=8)

        # ─ Image panels ───────────────────────────────────────────────────────
        panels_frame = tk.Frame(self._root, bg=BG_DARK)
        panels_frame.pack(padx=16, pady=4)

        # Left: original (reference only)
        self._orig_panel = ImagePanel(panels_frame, "📷  Original  —  Reference only")
        self._orig_panel.pack(side="left", padx=(0, 8))

        # Right: modified (interactive)
        self._mod_panel = ModifiedPanel(panels_frame)
        self._mod_panel.pack(side="left")

        # ─ Status bar ─────────────────────────────────────────────────────────
        status_frame = tk.Frame(self._root, bg=BG_MID, pady=10)
        status_frame.pack(fill="x", padx=16, pady=4)

        self._remaining_var = tk.StringVar(value="Remaining: —")
        tk.Label(
            status_frame, textvariable=self._remaining_var,
            bg=BG_MID, fg=TEXT_MAIN,
            font=("Helvetica", 13, "bold")
        ).pack(side="left", padx=16)

        self._mistakes_var = tk.StringVar(value="Mistakes: 0 / 3")
        tk.Label(
            status_frame, textvariable=self._mistakes_var,
            bg=BG_MID, fg=DANGER,
            font=("Helvetica", 13)
        ).pack(side="left", padx=16)

        self._status_var = tk.StringVar(value="Load an image to begin.")
        self._status_lbl = tk.Label(
            status_frame, textvariable=self._status_var,
            bg=BG_MID, fg=TEXT_SUB,
            font=("Helvetica", 11, "italic")
        )
        self._status_lbl.pack(side="right", padx=16)

        # ─ Button row ─────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self._root, bg=BG_DARK)
        btn_frame.pack(pady=12)

        btn_style = dict(
            font=("Helvetica", 12, "bold"),
            relief="flat", cursor="hand2",
            padx=20, pady=8, bd=0
        )

        self._load_btn = tk.Button(
            btn_frame, text="📁  Load Image",
            bg=ACCENT, fg="white",
            activebackground="#c73050", activeforeground="white",
            command=self._load_image, **btn_style # type: ignore
        )
        self._load_btn.pack(side="left", padx=8)

        self._reveal_btn = tk.Button(
            btn_frame, text="💡  Reveal All",
            bg="#2a4a6a", fg=TEXT_SUB,
            activebackground="#1d3a54", activeforeground=TEXT_MAIN,
            command=self._reveal_all, state="disabled", **btn_style # type: ignore
        )
        self._reveal_btn.pack(side="left", padx=8)

        # ─ Difference type legend (bottom) ────────────────────────────────────
        legend = tk.Frame(self._root, bg=BG_DARK)
        legend.pack(pady=(0, 14))
        tk.Label(
            legend,
            text="Alterations: Colour Shift · Noise · Blur · Brightness Invert · Hue Rotate",
            bg=BG_DARK, fg=TEXT_SUB, font=("Helvetica", 9)
        ).pack()


    # ── Game flow ─────────────────────────────────────────────────────────────

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                       ("All files", "*.*")]
        )
        if not path:
            return

        bgr = cv2.imread(path)
        if bgr is None:
            messagebox.showerror("Error", "Could not read image. Try a different file.")
            return

        # Resize source to a sane maximum so differences are proportionate
        MAX_SRC = (960, 720)
        h, w = bgr.shape[:2]
        if w > MAX_SRC[0] or h > MAX_SRC[1]:
            scale = min(MAX_SRC[0] / w, MAX_SRC[1] / h)
            bgr   = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        self._start_round(bgr)

    def _start_round(self, bgr: np.ndarray):
        # Reset per-round state
        self._mistakes  = 0
        self._game_over = False
        self._engine    = DifferenceEngine(bgr)

        # Display both images
        self._orig_panel.show_image(self._engine.original)
        self._mod_panel.show_image(self._engine.modified)

        # Activate click-handling on the modified panel
        self._mod_panel.activate(self._on_player_click)
        self._reveal_btn.config(state="normal", bg="#2a4a6a", fg=TEXT_SUB)

        self._refresh_hud()
        self._set_status("Find 5 differences! Click the right image.", TEXT_SUB)

    def _on_player_click(self, src_x: int, src_y: int, disp_x: int, disp_y: int):
        if self._game_over or self._engine is None:
            return

        idx = self._engine.check_click(src_x, src_y)

        if idx >= 0:
            # ✅ Correct!
            self._score += 1
            self._score_var.set(f"Score: {self._score}")
            self._mark_found(idx, found=True)
            self._refresh_hud()

            if self._engine.all_found:
                self._end_round_success()
            else:
                self._set_status(
                    f"✓  Found one! {self._engine.num_remaining} remaining.", SUCCESS
                )
        else:
            # ✗ Mistake
            self._mistakes += 1
            self._refresh_hud()
            # Flash the mistake indicator
            self._animate_mistake(disp_x, disp_y)

            if self._mistakes >= MAX_MISTAKES:
                self._end_round_fail()
            else:
                self._set_status(
                    f"✗  Not quite.  {MAX_MISTAKES - self._mistakes} mistake(s) left.", DANGER
                )

    def _mark_found(self, idx: int, found: bool, reveal: bool = False):
        """Draw a circle on BOTH panels for a difference region."""
        region = self._engine.regions[idx] # type: ignore
        cx, cy, r = self._orig_panel._region_centre_radius(region)
        color_hex  = "#ff4444" if found else "#3399ff"

        self._orig_panel.draw_marker(cx, cy, r, color_hex, tag=f"diff_{idx}")
        self._mod_panel.draw_marker(cx, cy, r, color_hex, tag=f"diff_{idx}")

    def _reveal_all(self):
        if self._engine is None:
            return
        for i, flag in enumerate(self._engine.found_flags):
            if not flag:
                self._mark_found(i, found=False, reveal=True)

        self._game_over = True
        self._mod_panel.deactivate()
        self._reveal_btn.config(state="disabled")
        self._set_status(
            f"Differences revealed. Found {self._engine.num_found}/{NUM_DIFFS}. Load a new image!",
            ACCENT2
        )

    def _end_round_success(self):
        self._game_over = True
        self._mod_panel.deactivate()
        self._reveal_btn.config(state="disabled")
        self._set_status("🎉  All 5 found! Load another image to keep playing.", SUCCESS)
        messagebox.showinfo(
            "Well Done!",
            f"You found all 5 differences with only {self._mistakes} mistake(s)!\n\n"
            f"Cumulative score: {self._score}"
        )

    def _end_round_fail(self):
        self._game_over = True
        self._mod_panel.deactivate()
        self._reveal_btn.config(state="disabled")

        found = self._engine.num_found # type: ignore
        self._set_status(
            f"❌  3 mistakes reached. Found {found}/{NUM_DIFFS}. Load a new image.", DANGER
        )
        messagebox.showwarning(
            "Too Many Mistakes",
            f"You reached the maximum of {MAX_MISTAKES} mistakes.\n"
            f"You found {found} out of {NUM_DIFFS} differences.\n\n"
            "Load a new image to try again!"
        )

    # ── HUD helpers ───────────────────────────────────────────────────────────

    def _refresh_hud(self):
        if self._engine:
            self._remaining_var.set(f"Remaining: {self._engine.num_remaining}")
        self._mistakes_var.set(f"Mistakes: {self._mistakes} / {MAX_MISTAKES}")

    def _set_status(self, msg: str, color: str = TEXT_SUB):
        self._status_var.set(msg)
        self._status_lbl.config(fg=color)

    def _animate_mistake(self, cx: int, cy: int):
        """Draw a fading X on the modified panel at the click point."""
        size = 16
        item1 = self._mod_panel._canvas.create_line(
            cx - size, cy - size, cx + size, cy + size,
            fill=DANGER, width=3, tags="mistake"
        )
        item2 = self._mod_panel._canvas.create_line(
            cx + size, cy - size, cx - size, cy + size,
            fill=DANGER, width=3, tags="mistake"
        )
        self._root.after(600, lambda: (
            self._mod_panel._canvas.delete(item1),
            self._mod_panel._canvas.delete(item2)
        ))

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self):
        self._root.mainloop()


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = GameApp()
    app.run()
