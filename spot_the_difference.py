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
# Main
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("This module is not meant to be run directly. Run main.py instead.")
