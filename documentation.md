# Spot the Difference — HIT137 Group Assignment 3

### Desktop Application Documentation

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Requirements & Installation](#2-system-requirements--installation)
3. [How to Run the Application](#3-how-to-run-the-application)
4. [Application Features & How to Play](#4-application-features--how-to-play)
5. [Software Architecture & OOP Design](#5-software-architecture--oop-design)
6. [Class Reference](#6-class-reference)
7. [Image Processing with OpenCV](#7-image-processing-with-opencv)
8. [GUI Design with Tkinter](#8-gui-design-with-tkinter)
9. [Game Logic & State Management](#9-game-logic--state-management)
10. [OOP Concepts Demonstrated](#10-oop-concepts-demonstrated)
11. [Configuration & Constants](#11-configuration--constants)
12. [Known Limitations](#12-known-limitations)

---

## 1. Project Overview

**Application Name:** Spot the Difference  
**Course:** HIT137 — Software Now  
**Assignment:** Group Assignment 3 (30%)  
**Language:** Python 3.10+  
**Frameworks:** Tkinter (GUI), OpenCV (image processing), Pillow (image rendering)

### Summary

Spot the Difference is a desktop game in which the player is presented with two images side by side. The left image is the original. The right image is a programmatically altered clone containing exactly **five hidden differences**. The player clicks on the modified image to identify each difference. The application validates every click against the known difference regions and provides immediate visual feedback.

Each time an image is loaded, the positions and types of alterations are randomised, ensuring a unique experience on every round. The application tracks mistakes, enforces a maximum of three mistakes per image, and provides a reveal function to expose any unfound differences.

### Key Capabilities

- Loads any JPG, PNG, BMP, TIFF, or WEBP image from disk
- Generates exactly 5 non-overlapping differences using OpenCV, randomised on every load
- Supports 5 distinct alteration types: Colour Shift, Noise Patch, Gaussian Blur, Brightness Invert, Hue Rotate
- Validates player clicks with spatial proximity detection
- Draws red circles around found differences on both images simultaneously
- Draws blue circles around revealed differences on both images simultaneously
- Enforces a 3-mistake limit per round with clear on-screen feedback
- Tracks a cumulative score across multiple images in one session
- Correctly letterboxes images of any aspect ratio

---

## 2. System Requirements & Installation

### Prerequisites

| Component                | Version             | Purpose                             |
| ------------------------ | ------------------- | ----------------------------------- |
| Python                   | 3.10 or higher      | Runtime                             |
| OpenCV (`opencv-python`) | 4.x                 | Image processing and alteration     |
| Pillow (`Pillow`)        | 9.x or higher       | Displaying OpenCV images in Tkinter |
| Tkinter                  | Bundled with Python | GUI framework                       |

### Installation

Tkinter is included with most standard Python distributions. If it is missing (some Linux systems), install it with your package manager:

```bash
# Ubuntu / Debian
sudo apt install python3-tk

# macOS (if using Homebrew Python)
brew install python-tk
```

Install the two Python library dependencies with pip:

```bash
pip install opencv-python pillow
```

Verify all dependencies are available:

```bash
python3 -c "import cv2, tkinter, PIL; print('All dependencies OK')"
```

---

## 3. How to Run the Application

Navigate to the directory containing `spot_the_difference.py` and run:

```bash
python3 spot_the_difference.py
```

On Windows:

```cmd
python spot_the_difference.py
```

No additional configuration or setup is required.

---

## 4. Application Features & How to Play

### Starting a Round

1. Launch the application. The window opens with two empty panels and the status message _"Load an image to begin."_
2. Click the **📁 Load Image** button. A file dialog opens.
3. Select any JPG, PNG, BMP, TIFF, or WEBP image from your disk.
4. The application immediately:
   - Loads the image and scales it proportionally (preserving aspect ratio)
   - Generates 5 random non-overlapping difference regions
   - Applies a randomly chosen alteration type to each region
   - Displays the original on the left and the modified version on the right
   - Enables the Reveal All button
   - Resets the mistake counter to 0

### Finding Differences

- **Only the right panel (Modified) responds to clicks.** The left panel is a visual reference only.
- Click anywhere on the modified image where you think a difference exists.
- If your click falls within **45 pixels** of the centre of an undetected difference region (measured in source image coordinates), the difference is marked as **found**:
  - A **red circle** is drawn around the region on **both** the original and modified images.
  - An expanding ring animation plays on the modified panel.
  - The **Remaining** counter decreases by 1.
  - The **Score** counter increases by 1.

### Mistakes

- If your click does not fall near any unfound difference, it counts as a **mistake**.
- A red × appears briefly at the click location.
- The **Mistakes** counter increments (e.g., "Mistakes: 1 / 3").
- After **3 mistakes**, all further clicks are disabled and a warning dialog appears, displaying how many differences were found. The Reveal All button remains active so the player can see the missed differences.

### Winning a Round

When all 5 differences are found:

- A congratulatory pop-up dialog appears showing the number of mistakes made and the cumulative score.
- Clicks on the modified panel are disabled.
- The player can then load a new image to continue playing.

### Reveal All

Clicking the **💡 Reveal All** button at any point during an active round:

- Draws a **blue circle** around every unfound difference on both panels.
- Updates the engine's found-flags so the Remaining counter correctly reaches 0.
- Disables further clicks.
- The player can then load a new image.

### Cumulative Score

The score counter in the top-right corner accumulates across multiple images. Each correctly found difference adds 1 point. Loading a new image does not reset the total score — only the per-round mistakes counter resets.

---

## 5. Software Architecture & OOP Design

The application is structured into **four classes**, each with a clearly defined responsibility. No class handles concerns that belong to another.

```
┌─────────────────────────────────────────────────────────────────┐
│                          GameApp                                │
│   Owns: engine, orig_panel, mod_panel, score, mistakes, state   │
│   Responsibility: orchestration, game rules, HUD updates        │
└───────┬────────────────┬───────────────────┬────────────────────┘
        │ creates        │ owns              │ owns
        ▼                ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌────────────────────┐
│Difference-   │  │  ImagePanel  │  │  ModifiedPanel     │
│Engine        │  │  (base)      │  │  (subclass)        │
│              │  │              │  │                    │
│ Pure OpenCV  │  │ Canvas, scale│  │ + click handling   │
│ logic only.  │  │ letterbox,   │  │ + draw_marker()    │
│ No UI refs.  │  │ draw_marker()│  │   override with    │
│              │  │ polymorphic  │  │   ring animation   │
└──────────────┘  └──────────────┘  └────────────────────┘
        ▲                                    │
        │         inherits ──────────────────┘
        │
  check_click(), regions, found_flags
  (queried by GameApp only)
```

### Design Principles Applied

**Separation of Concerns.** `DifferenceEngine` contains every pixel-level decision. It has no knowledge of Tkinter, canvases, or screen coordinates. `GameApp` contains every game-rule decision but performs no image manipulation. The two communicate only through a clean public interface (`check_click`, `regions`, `found_flags`).

**Single Responsibility.** Each class does one thing well. `ImagePanel` knows how to display an image and draw circles. `ModifiedPanel` knows how to handle clicks. `DifferenceEngine` knows how to create and validate differences. `GameApp` knows how to run a game.

**Encapsulation.** All internal state uses Python's convention of `_private` attributes. External code accesses `DifferenceEngine` state only through read-only properties (`regions`, `found_flags`, `num_remaining`, etc.), preventing accidental mutation.

---

## 6. Class Reference

### `DifferenceEngine`

The image-processing core. Accepts a BGR NumPy array (an OpenCV image), creates an internal clone, applies 5 non-overlapping randomised alterations to the clone, and validates player click coordinates against the known regions.

**Constructor**

```python
DifferenceEngine(original_bgr: np.ndarray)
```

Accepts a BGR image array. Immediately generates all 5 difference regions and applies alterations. After construction, both `original` and `modified` images are ready.

**Properties (read-only)**

| Property        | Type          | Description                                                                 |
| --------------- | ------------- | --------------------------------------------------------------------------- |
| `original`      | `np.ndarray`  | The unmodified source image (BGR)                                           |
| `modified`      | `np.ndarray`  | The altered clone (BGR)                                                     |
| `regions`       | `list[tuple]` | Copy of the list of `(x, y, w, h)` tuples in source-image pixel coordinates |
| `found_flags`   | `list[bool]`  | Copy of the per-region found status                                         |
| `num_found`     | `int`         | Number of differences found so far                                          |
| `num_remaining` | `int`         | `NUM_DIFFS − num_found`                                                     |
| `all_found`     | `bool`        | `True` when all 5 differences have been found                               |

**Methods**

```python
check_click(src_x: int, src_y: int) -> int
```

Tests whether the point `(src_x, src_y)` — given in **source image pixel coordinates** — falls within `CLICK_RADIUS` pixels of the centre of any unfound difference region. If a match is found, marks that region as found and returns its index (0–4). Returns `-1` if the click is a miss or all regions are already found.

**Private Methods**

| Method                            | Description                                                                              |
| --------------------------------- | ---------------------------------------------------------------------------------------- |
| `_generate_differences()`         | Randomly places 5 non-overlapping bounding boxes and assigns one alteration type to each |
| `_boxes_overlap(a, b)`            | Returns `True` if two `(x, y, w, h)` boxes overlap (including the minimum gap margin)    |
| `_apply_alteration(kind, region)` | Applies the named alteration to the given region on `_modified`                          |

---

### `ImagePanel`

A Tkinter widget wrapper that owns a `tk.Canvas` and can display a BGR OpenCV image with correct aspect-ratio letterboxing. Serves as the **base class** for `ModifiedPanel`.

**Constructor**

```python
ImagePanel(parent: tk.Widget, label_text: str)
```

Creates a labelled frame containing a `tk.Canvas` of size `DISPLAY_SIZE`. Initialises scale and offset attributes to neutral values.

**Key Attributes (private)**

| Attribute                | Description                                                                 |
| ------------------------ | --------------------------------------------------------------------------- |
| `_canvas`                | The underlying `tk.Canvas` widget                                           |
| `_photo_ref`             | Holds a reference to the `ImageTk.PhotoImage` to prevent garbage collection |
| `_scale_x`, `_scale_y`   | Ratio of source pixels to display pixels on each axis                       |
| `_offset_x`, `_offset_y` | Pixel offset for letterbox centering within the canvas                      |

**Methods**

```python
show_image(bgr: np.ndarray)
```

Converts a BGR array to RGB, scales it to fit within `DISPLAY_SIZE` while **preserving the aspect ratio** (letterboxing with a dark background for unused space), and renders it on the canvas. Stores scale and offset values used by coordinate conversion methods.

```python
draw_marker(src_x, src_y, src_r, color_hex, tag="marker")
```

Draws a circle outline on the canvas. Coordinates and radius are given in **source image pixels** and automatically converted to display coordinates using the stored scale and offset. This method is **polymorphic** — it is overridden by `ModifiedPanel`.

```python
src_to_display(sx, sy) -> (dx, dy)
display_to_src(dx, dy) -> (sx, sy)
```

Bi-directional coordinate conversion between source-image pixel space and canvas display space, accounting for the letterbox offset.

```python
clear()
```

Deletes all canvas items and resets internal state.

---

### `ModifiedPanel` _(inherits `ImagePanel`)_

The interactive right-hand panel. Extends `ImagePanel` by adding click event binding and overriding `draw_marker` with an expanding ring animation. This class **demonstrates inheritance and polymorphism**.

**Constructor**

```python
ModifiedPanel(parent: tk.Widget)
```

Calls `super().__init__()` to set up the canvas, then binds the `<Button-1>` click event and initialises `_active = False`.

**Additional Methods**

```python
activate(callback: callable)
```

Enables click handling for the current round. The provided `callback` is called with `(src_x, src_y, disp_x, disp_y)` whenever the player clicks.

```python
deactivate()
```

Disables click handling. Called at round end (success, 3 mistakes, or reveal).

**Overridden Method**

```python
draw_marker(src_x, src_y, src_r, color_hex, tag="marker")  # override
```

First calls `super().draw_marker(...)` to draw the permanent circle, then launches `_animate_ring()` which creates a sequence of expanding, thinning ghost rings over 7 frames at 60 ms intervals, producing a ripple effect.

---

### `GameApp`

The root application class. Owns the `tk.Tk` root window, the two image panels, the `DifferenceEngine` instance, and all game-state variables. Contains no image-processing logic — it delegates entirely to `DifferenceEngine`.

**Constructor**

```python
GameApp()
```

Creates the Tkinter root window, initialises game-state variables (`_engine`, `_mistakes`, `_score`, `_game_over`), and calls `_build_ui()`.

**Game State Variables**

| Variable     | Type                       | Description                                                   |
| ------------ | -------------------------- | ------------------------------------------------------------- |
| `_engine`    | `DifferenceEngine \| None` | The current round's engine instance; `None` before first load |
| `_mistakes`  | `int`                      | Per-round mistake count (resets on each new image)            |
| `_score`     | `int`                      | Cumulative correct finds across the session                   |
| `_game_over` | `bool`                     | Guards against clicks after a round ends                      |

**Key Methods**

| Method                                           | Description                                                                                                  |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `_load_image()`                                  | Opens file dialog, reads with `cv2.imread`, scales large sources to ≤960×720, calls `_start_round()`         |
| `_start_round(bgr)`                              | Resets per-round state, creates a new `DifferenceEngine`, displays both images, activates the modified panel |
| `_on_player_click(src_x, src_y, disp_x, disp_y)` | Calls `engine.check_click()`, routes to correct/incorrect handling, fires round-end logic                    |
| `_mark_found(idx, found, reveal)`                | Draws a red (found) or blue (revealed) circle on **both** panels for region `idx`                            |
| `_reveal_all()`                                  | Marks all unfound regions in the engine, draws blue circles on both panels, refreshes HUD                    |
| `_end_round_success()`                           | Disables clicks, shows success dialog with score                                                             |
| `_end_round_fail()`                              | Disables clicks, shows warning dialog, keeps Reveal button active                                            |
| `_refresh_hud()`                                 | Updates the Remaining and Mistakes labels from live state                                                    |
| `_animate_mistake(cx, cy)`                       | Draws a temporary red × at the click position, auto-removed after 600 ms                                     |
| `run()`                                          | Starts the Tkinter event loop                                                                                |

---

## 7. Image Processing with OpenCV

All image manipulation is performed exclusively with OpenCV (`cv2`). Pillow is used only for rendering OpenCV arrays inside Tkinter canvases.

### Image Loading and Preprocessing

```python
bgr = cv2.imread(path)
```

OpenCV reads images as BGR (Blue-Green-Red) NumPy arrays. If the loaded image exceeds 960×720 pixels, it is downscaled while preserving its aspect ratio using `cv2.INTER_AREA` (best quality for downscaling):

```python
scale = min(960 / w, 720 / h)
bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
```

This step ensures that difference regions of a consistent size (60–110 px) are visually proportionate regardless of the original image resolution.

### Difference Region Generation

`DifferenceEngine._generate_differences()` uses a rejection-sampling loop (up to 2000 attempts) to place 5 non-overlapping bounding boxes. Each box has:

- **Width:** random integer in `[DIFF_MIN_SIZE, DIFF_MAX_SIZE]` = `[60, 110]` px
- **Height:** random integer in `[DIFF_MIN_SIZE, DIFF_MAX_SIZE]` = `[60, 110]` px
- **Position:** randomly placed with a margin from image edges to prevent partial regions

Two boxes are considered overlapping if they are closer than `DIFF_MIN_GAP` (20 px) on any side, checked via:

```python
def _boxes_overlap(self, a, b) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    gap = DIFF_MIN_GAP
    return not (ax + aw + gap <= bx or bx + bw + gap <= ax or
                ay + ah + gap <= by or by + bh + gap <= ay)
```

Once 5 valid positions are found, the 5 alteration types are drawn from the catalogue, shuffled randomly, and assigned one per region. This guarantees that each round uses a different combination.

### The Five Alteration Types

All alterations work on a `patch` — a NumPy slice of the modified image at the region's bounding box.

#### 1. Colour Shift (`colour_shift`)

Converts the patch from BGR to HSV colour space, shifts the **Hue channel** by a randomly chosen amount (±40, ±60, or +80 degrees), then converts back to BGR. This changes the perceived colour of objects in the region while preserving their shape and texture.

```python
hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).astype(np.int16)
shift = random.choice([40, -40, 60, -60, 80])
hsv[:, :, 0] = (hsv[:, :, 0] + shift) % 180
self._modified[y:y+h, x:x+w] = cv2.cvtColor(
    np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
```

#### 2. Noise Patch (`noise_patch`)

Adds a uniform random noise array (values 0–80 per channel) to the patch using `cv2.add()`, which clamps the result at 255 automatically. This produces a grainy, brightened appearance in the affected region.

```python
noise = np.random.randint(0, 80, patch.shape, dtype=np.uint8)
self._modified[y:y+h, x:x+w] = cv2.add(patch, noise)
```

#### 3. Gaussian Blur (`blur_patch`)

Applies a large Gaussian blur kernel (21×21 for regions ≥40 px, 15×15 for smaller) to the patch using `cv2.GaussianBlur()`. This makes the region appear smeared or out of focus while the rest of the image remains sharp.

```python
k = 21 if min(w, h) >= 40 else 15
self._modified[y:y+h, x:x+w] = cv2.GaussianBlur(patch, (k, k), 0)
```

#### 4. Brightness Invert (`brightness_invert`)

Converts the patch to HSV, inverts the **Value (brightness) channel** (`V = 255 − V`), and converts back. Dark areas become bright and vice versa, creating a distinctive local contrast reversal.

```python
hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).astype(np.int16)
hsv[:, :, 2] = 255 - hsv[:, :, 2]
self._modified[y:y+h, x:x+w] = cv2.cvtColor(
    np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
```

#### 5. Hue Rotate (`hue_rotate`)

A stronger variant of colour shift: rotates the Hue channel by +90 degrees **and** boosts the Saturation channel by +80, making colours in the region both shifted and more vivid/saturated than the original.

```python
hsv[:, :, 0] = (hsv[:, :, 0] + 90) % 180
hsv[:, :, 1] = np.clip(hsv[:, :, 1] + 80, 0, 255)
```

### Aspect-Ratio-Correct Display

Before displaying an image in the canvas, `ImagePanel.show_image()` computes a uniform scale factor that fits the image inside `DISPLAY_SIZE = (480, 360)` without distortion:

```python
scale = min(DISPLAY_SIZE[0] / src_w, DISPLAY_SIZE[1] / src_h)
fit_w, fit_h = int(src_w * scale), int(src_h * scale)
```

The scaled image is centered within the canvas, and unused areas are filled with a dark background. The scale factors and pixel offsets are stored for use in coordinate conversion.

---

## 8. GUI Design with Tkinter

### Window Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  SPOT THE DIFFERENCE                             Score: 0       │ ← Title bar
├──────────────────────────┬──────────────────────────────────────┤
│  📷 Original             │  🔍 Modified                        │
│  ─ Reference only ─      │  ─ Click here to find differences ─ │
│                          │                                      │
│   [480 × 360 canvas]     │        [480 × 360 canvas]           │ ← Image panels
│                          │                                      │
│                          │                                      │
├─────────────────────────────────────────────────────────────────┤
│  Remaining: 5   Mistakes: 0 / 3          Find 5 differences!   │ ← Status bar
├─────────────────────────────────────────────────────────────────┤
│    [ 📁 Load Image ]   [ 💡 Reveal All ]                        │ ← Buttons
│   Alterations: Colour Shift · Noise · Blur · ...               │ ← Legend
└─────────────────────────────────────────────────────────────────┘
```

### UI Components

| Widget            | Type                             | Role                                                        |
| ----------------- | -------------------------------- | ----------------------------------------------------------- |
| Title label       | `tk.Label`                       | Displays application name                                   |
| Score label       | `tk.Label` (StringVar)           | Live cumulative score                                       |
| Original canvas   | `tk.Canvas` (in `ImagePanel`)    | Left panel, reference only                                  |
| Modified canvas   | `tk.Canvas` (in `ModifiedPanel`) | Right panel, click-interactive                              |
| Remaining label   | `tk.Label` (StringVar)           | Count of unfound differences                                |
| Mistakes label    | `tk.Label` (StringVar)           | Current / max mistakes                                      |
| Status label      | `tk.Label` (StringVar)           | Contextual messages (colour-coded)                          |
| Load Image button | `tk.Button`                      | Triggers file dialog                                        |
| Reveal All button | `tk.Button`                      | Reveals unfound differences; disabled before a round starts |

### Click Detection Pipeline

When the player clicks the right canvas, the following chain executes:

```
Player clicks (disp_x, disp_y) on canvas
        │
        ▼
ModifiedPanel._handle_click(event)
        │ convert coords
        ▼
display_to_src(disp_x, disp_y) → (src_x, src_y)
        │ apply scale and letterbox offset
        ▼
GameApp._on_player_click(src_x, src_y, disp_x, disp_y)
        │
        ▼
DifferenceEngine.check_click(src_x, src_y)
        │ Euclidean distance check against all unfound region centres
        ▼
     idx ≥ 0?
    ┌────┴────┐
   YES        NO
    │          │
mark found  count mistake
draw circles  animate ×
refresh HUD  refresh HUD
```

The conversion from display coordinates to source coordinates accounts for the letterbox offset:

```python
src_x = (disp_x − offset_x) × scale_x
src_y = (disp_y − offset_y) × scale_y
```

### Visual Feedback System

| Event          | Feedback                                                     |
| -------------- | ------------------------------------------------------------ |
| Correct click  | Red circle on both images + ring animation on modified panel |
| Wrong click    | Red × at click point (fades after 600 ms)                    |
| All 5 found    | Green status message + success dialog                        |
| 3 mistakes     | Red status message + warning dialog                          |
| Reveal pressed | Blue circles on both images + counter reaches 0              |

---

## 9. Game Logic & State Management

### Per-Round State (reset on each new image load)

| Variable     | Initial Value          | Changes on                          |
| ------------ | ---------------------- | ----------------------------------- |
| `_mistakes`  | `0`                    | Each wrong click                    |
| `_game_over` | `False`                | Round end (success / fail / reveal) |
| `_engine`    | New `DifferenceEngine` | Each `_load_image()` call           |

### Session State (never reset)

| Variable | Description                                                            |
| -------- | ---------------------------------------------------------------------- |
| `_score` | Cumulative sum of correctly found differences across all loaded images |

### Round End Conditions

| Condition  | Trigger                    | Effect                                                           |
| ---------- | -------------------------- | ---------------------------------------------------------------- |
| **Win**    | `engine.all_found == True` | Deactivates panel, shows dialog, disables Reveal                 |
| **Fail**   | `_mistakes >= 3`           | Deactivates panel, shows warning, keeps Reveal active            |
| **Reveal** | Player presses Reveal All  | Marks remaining in engine, draws blue circles, deactivates panel |

### The 3-Mistake Rule

After 3 mistakes, `_mod_panel.deactivate()` sets `_active = False` on the `ModifiedPanel`, causing `_handle_click()` to return immediately without calling the game callback. Clicks are effectively ignored at the Tkinter level — no state checks needed in the callback. The Reveal All button intentionally remains enabled after a failure so the player can see what they missed before loading a new image.

---

## 10. OOP Concepts Demonstrated

### Encapsulation

All internal state of every class uses the `_private` naming convention. `DifferenceEngine` exposes its data only through read-only `@property` decorators, preventing `GameApp` or any other class from accidentally modifying the list of found flags or regions directly. The only intentional internal access (`self._engine._found[i] = True` in `_reveal_all`) is a deliberate, documented exception.

### Constructors

Every class defines an `__init__` method that fully initialises the object's state. No object is left in a partially constructed state. `DifferenceEngine.__init__` immediately calls `_generate_differences()` so the engine is fully operational the moment it is constructed.

### Methods

Each class exposes a cohesive set of methods that operate on its own state. Methods are named to communicate intent (`check_click`, `show_image`, `draw_marker`, `activate`, `deactivate`) rather than exposing implementation details.

### Class Interaction

`GameApp` creates a `DifferenceEngine` and stores it as `_engine`. It passes itself (via a lambda callback) to `ModifiedPanel.activate()`. When the player clicks, the modified panel calls back into `GameApp`, which queries the engine, then instructs both panels to draw markers. Three classes collaborate without any circular dependencies.

### Inheritance

`ModifiedPanel` inherits from `ImagePanel` using `class ModifiedPanel(ImagePanel)`. The constructor calls `super().__init__(parent, label_text)` to reuse all canvas construction logic. `ModifiedPanel` gains all `ImagePanel` methods for free and adds click-handling behaviour on top.

### Polymorphism

`ImagePanel.draw_marker()` defines the base drawing behaviour: convert coordinates, draw an oval on the canvas. `ModifiedPanel` overrides this method:

```python
# ModifiedPanel.draw_marker — polymorphic override
def draw_marker(self, src_x, src_y, src_r, color_hex, tag="marker"):
    super().draw_marker(src_x, src_y, src_r, color_hex, tag)  # base behaviour
    # Extended behaviour: ring animation unique to the interactive panel
    self._animate_ring(dx, dy, dr, color_hex, step=0)
```

`GameApp._mark_found()` calls `draw_marker()` on both panels without knowing or caring which concrete type each panel is. The original panel draws a static circle; the modified panel draws the same circle plus an animation. This is classic runtime polymorphism.

---

## 11. Configuration & Constants

The following constants at the top of the file control game behaviour and can be adjusted without modifying any class:

| Constant        | Default      | Description                                                 |
| --------------- | ------------ | ----------------------------------------------------------- |
| `MAX_MISTAKES`  | `3`          | Maximum wrong clicks allowed per image                      |
| `NUM_DIFFS`     | `5`          | Number of differences generated per image                   |
| `DISPLAY_SIZE`  | `(480, 360)` | Canvas size in pixels (width, height)                       |
| `CLICK_RADIUS`  | `45`         | Proximity threshold for a valid click (source image pixels) |
| `DIFF_MIN_SIZE` | `60`         | Minimum difference region side length (px)                  |
| `DIFF_MAX_SIZE` | `110`        | Maximum difference region side length (px)                  |
| `DIFF_MIN_GAP`  | `20`         | Minimum gap between any two difference regions (px)         |

---

## 12. Known Limitations

- **Small images:** Images smaller than approximately 200×200 pixels may not reliably produce 5 non-overlapping regions. The placement loop runs up to 2000 attempts; on a very small image it may place fewer than 5 differences. For typical photographs (≥640×480), this is not an issue.

- **Greyscale / single-channel images:** OpenCV reads greyscale JPEG files as 3-channel arrays in most cases, but some BMP/PNG greyscale files may be read as 1-channel arrays. The HSV-based alteration types require 3 channels. If a single-channel image is loaded, alterations will fall back gracefully for noise and blur types, but colour-based types may produce unexpected results.

- **Blur on very flat regions:** The Gaussian Blur alteration produces no visible change on a region that contains a single uniform colour (zero variance). On photographic images this is rare; on solid-colour test images it may result in a difference that is invisible.

---

_Documentation prepared for HIT137 Group Assignment 3._
