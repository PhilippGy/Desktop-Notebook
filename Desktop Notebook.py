#!/usr/bin/env python3
"""
Personal Digital Notebook Desktop Application
=============================================
A warm, analog-inspired desktop notebook application built with Python & Tkinter.
Zero third-party dependencies required—runs natively on Windows, macOS, and Linux.

Features:
- Starts in fullscreen mode (F11 toggles fullscreen, Esc exits fullscreen).
- Three selectable themes (Warm Paper, Light Blue, Dark Blue) in top-left Settings.
- Export and Import notebooks as standalone .json files so work is never lost.
- Left sidebar notebook library (Create, Rename, Delete, Switch).
- Three paper backgrounds (Plain, Lined, Square Grid) that never reflow text or ink.
- Full-page click-anywhere text editor with wrap-safe pasting and selection highlight.
- Word-style floating mini-toolbar over highlighted text (Size, Bold, Underline,
  and 4-color Text & Underline selectors: Red, Green, Yellow, Blue).
- Keyboard shortcuts: Ctrl+Z (Undo), Ctrl+Y / Ctrl+Shift+Z (Redo),
  Ctrl+Backspace / Ctrl+Delete (word delete), Ctrl+Left / Ctrl+Right (word jump),
  Ctrl+B (Bold), Ctrl+U (Underline), Ctrl+A/C/X/V.
- Page creation, deletion (- Page), and smooth 500ms curling page-turn animation.
- Automatic local JSON persistence in ~/.personal_digital_notebook/notebooks.json.
"""

import copy
import json
import math
import os
import time
import uuid
import tkinter as tk
from tkinter import filedialog
from tkinter import font as tkfont
from tkinter import messagebox, simpledialog


# =============================================================================
# COLOR PALETTES & THEME DEFINITIONS
# =============================================================================
THEMES = {
    "warm": {
        "name": "Warm Paper (Default)",
        "desk_bg": "#E8E1D5",
        "sidebar_bg": "#EFE9DD",
        "sidebar_hover": "#E4DCCD",
        "sidebar_active": "#DCD1BE",
        "sidebar_border": "#D5CBB8",
        "toolbar_bg": "#F4EFE6",
        "toolbar_border": "#D8CFC0",
        "paper_bg": "#FCF9F2",
        "paper_stack": "#EAE2D3",
        "paper_edge": "#D4C9B6",
        "paper_shadow": "#D8CFC0",
        "spine_shadow": "#EAE2D3",
        "spine_line": "#DFD5C3",
        "grain_dot": "#ECE4D5",
        "line_blue": "#C7D8E8",
        "margin_red": "#E4B8B8",
        "ink_text": "#232220",
        "muted_text": "#6E685F",
        "accent": "#5C4D3C",
        "accent_light": "#8C7760",
        "btn_bg": "#EAE2D3",
        "btn_active": "#5C4D3C",
        "btn_active_fg": "#FCF9F2",
        "selection_bg": "#D9E4EC",
        "curl_shadow": "#DDD3C2",
        "curl_back": "#F4EEE1",
        "curl_edge": "#C9BEA9",
        "curl_highlight": "#FFFDF8",
    },
    "light_blue": {
        "name": "Light Blue",
        "desk_bg": "#D9E6F2",
        "sidebar_bg": "#E4EEF7",
        "sidebar_hover": "#D4E3F0",
        "sidebar_active": "#C3D8EC",
        "sidebar_border": "#B8CFE4",
        "toolbar_bg": "#ECF3FA",
        "toolbar_border": "#C3D5E6",
        "paper_bg": "#F8FBFF",
        "paper_stack": "#E3EDF7",
        "paper_edge": "#B9CDE0",
        "paper_shadow": "#C5D7E8",
        "spine_shadow": "#E1ECF6",
        "spine_line": "#C8D9EA",
        "grain_dot": "#E5EFF8",
        "line_blue": "#BDD5EC",
        "margin_red": "#E2B4BE",
        "ink_text": "#182838",
        "muted_text": "#566D84",
        "accent": "#2B5B84",
        "accent_light": "#487BA8",
        "btn_bg": "#DCE8F4",
        "btn_active": "#2B5B84",
        "btn_active_fg": "#F8FBFF",
        "selection_bg": "#C7DFF5",
        "curl_shadow": "#C8D9EA",
        "curl_back": "#E8F1FA",
        "curl_edge": "#AEC5DC",
        "curl_highlight": "#FFFFFF",
    },
    "dark_blue": {
        "name": "Dark Blue",
        "desk_bg": "#0F1926",
        "sidebar_bg": "#152334",
        "sidebar_hover": "#1D3047",
        "sidebar_active": "#253D59",
        "sidebar_border": "#263B54",
        "toolbar_bg": "#18283B",
        "toolbar_border": "#2A415C",
        "paper_bg": "#1B2B3E",
        "paper_stack": "#142131",
        "paper_edge": "#2F4866",
        "paper_shadow": "#0B131D",
        "spine_shadow": "#142130",
        "spine_line": "#283E59",
        "grain_dot": "#21344B",
        "line_blue": "#2A4463",
        "margin_red": "#6E3B49",
        "ink_text": "#E6EEF8",
        "muted_text": "#8FA6C0",
        "accent": "#4A89C7",
        "accent_light": "#68A3DC",
        "btn_bg": "#233852",
        "btn_active": "#4A89C7",
        "btn_active_fg": "#F5F9FF",
        "selection_bg": "#2E527A",
        "curl_shadow": "#101B29",
        "curl_back": "#22364E",
        "curl_edge": "#385577",
        "curl_highlight": "#5D9AD4",
    },
}

THEME = dict(THEMES["warm"])

INK_COLORS = [
    ("Charcoal Ink", "#232220"),
    ("Fountain Blue", "#1E4D7B"),
    ("Crimson Nib", "#9E2A2B"),
    ("Forest Green", "#2D5A3C"),
    ("Sepia Brown", "#6B4423"),
]

# Fixed 4-color set for rich-text color and underline color
RICH_TEXT_COLORS = [
    ("Red", "#C92A2A"),
    ("Green", "#2B8A3E"),
    ("Yellow", "#D99B00"),
    ("Blue", "#1864AB"),
]

UNDERLINE_COLORS = [
    ("Black", "#232220"),
    ("Red", "#C92A2A"),
    ("Green", "#2B8A3E"),
    ("Yellow", "#D99B00"),
    ("Blue", "#1864AB"),
]

PEN_SIZES = [
    ("Fine", 2),
    ("Medium", 4),
    ("Bold", 7),
]

PAPER_STYLES = [
    ("lined", "Lined Paper"),
    ("grid", "Square Grid"),
    ("plain", "Plain Paper"),
]


# =============================================================================
# LOCAL STORAGE MANAGER
# =============================================================================
class NotebookStorage:
    """Handles reliable local JSON persistence in the user's home directory."""

    def __init__(self):
        base_dir = os.path.join(os.path.expanduser("~"), ".personal_digital_notebook")
        os.makedirs(base_dir, exist_ok=True)
        self.filepath = os.path.join(base_dir, "notebooks.json")

    def create_default_page(self, style="lined"):
        return {
            "id": str(uuid.uuid4()),
            "style": style,
            "orientation": "portrait",
            "text": "",
            "formats": [],  # Parallel 2D list of per-character dicts or None
            "strokes": [],  # List of {"color": str, "width": int, "points": [[x, y], ...]}
        }

    def create_default_data(self):
        return {
            "active_notebook_id": None,
            "theme": "warm",
            "notebooks": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Personal",
                    "active_page_index": 0,
                    "pages": [self.create_default_page("lined")],
                }
            ],
        }

    def load(self):
        if not os.path.exists(self.filepath):
            data = self.create_default_data()
            data["active_notebook_id"] = data["notebooks"][0]["id"]
            self.save(data)
            return data

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data.get("notebooks"):
                data = self.create_default_data()
            if not data.get("active_notebook_id"):
                data["active_notebook_id"] = data["notebooks"][0]["id"]
            if data.get("theme") not in THEMES:
                data["theme"] = "warm"
            return data
        except Exception:
            data = self.create_default_data()
            data["active_notebook_id"] = data["notebooks"][0]["id"]
            return data

    def save(self, data):
        tmp_path = self.filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.filepath)
        except Exception as e:
            print(f"Warning: Could not save notebook data: {e}")


# =============================================================================
# VIRTUAL CLICK-ANYWHERE PAPER CANVAS (TEXT + RICH FORMAT + DRAWING + FLIP)
# =============================================================================
class NotebookPageCanvas(tk.Canvas):
    """
    Custom canvas rendering:
    1. Realistic paper sheet with subtle grain, binding spine, and stacked edge shadow.
    2. Visual background style (Plain, Lined, Square Grid) independent of content.
    3. Full-page click-anywhere character grid editor with wrap-safe pasting.
    4. Per-character formatting (font size, bold, 4-color text, 4-color underline).
    5. Smooth freehand drawing & erasing layer coexisting with text.
    6. Curling 3D-style page-turning animation.
    """

    def __init__(self, master, app, **kwargs):
        super().__init__(
            master,
            bg=THEME["desk_bg"],
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.app = app

        # Typography metrics for deterministic virtual character grid
        self.font_family = self._choose_handwriting_mono_font()
        self.base_font_size = 13
        self.text_font = tkfont.Font(family=self.font_family, size=self.base_font_size)
        self._font_cache = {}
        self.char_w = max(8, self.text_font.measure("M"))
        self.line_h = 28

        # Paper geometry (updated dynamically on resize)
        self.paper_rect = (40, 20, 840, 1020)
        self.margin_left = 48
        self.margin_right = 36
        self.margin_top = 44
        self.margin_bottom = 36

        # Text editor state
        self.lines = [""]
        self.line_formats = [[]]  # Parallel 2D list of per-char format dicts or None
        self.cursor_row = 0
        self.cursor_col = 0
        self.preferred_col = None  # Remembers target column across short lines (IDE-style)
        self.sel_anchor = None  # (row, col) or None
        self.cursor_visible = True
        self._blink_job = None

        # Per-page Undo / Redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Drawing state
        self.strokes = []
        self.current_stroke = None
        self.is_erasing = False

        # Page turn animation state
        self.is_animating = False
        self.anim_progress = 0.0
        self.anim_direction = 1

        # Current page orientation ("portrait" or "landscape")
        self.orientation = "portrait"

        # Subtle static paper grain offsets
        self.grain_dots = [
            ((i * 73) % 997 / 997.0, (i * 137) % 991 / 991.0) for i in range(180)
        ]

        # Event bindings
        self.bind("<Configure>", self._on_resize)
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.bind("<KeyPress>", self._on_key_press)
        self.bind("<FocusIn>", lambda e: self._reset_blink())

        self._schedule_blink()

    def _choose_handwriting_mono_font(self):
        available = set(tkfont.families())
        preferred = [
            "Courier Prime",
            "American Typewriter",
            "Bradley Hand",
            "Consolas",
            "Menlo",
            "DejaVu Sans Mono",
            "Courier New",
            "Courier",
        ]
        for f in preferred:
            if f in available:
                return f
        return "Courier"

    def _get_styled_font(self, size, bold):
        key = (size, bool(bold))
        if key not in self._font_cache:
            self._font_cache[key] = tkfont.Font(
                family=self.font_family,
                size=size,
                weight="bold" if bold else "normal",
            )
        return self._font_cache[key]

    # -------------------------------------------------------------------------
    # UNDO / REDO SNAPSHOTS
    # -------------------------------------------------------------------------
    def _push_undo_state(self):
        snapshot = {
            "lines": list(self.lines),
            "line_formats": copy.deepcopy(self.line_formats),
            "strokes": copy.deepcopy(self.strokes),
            "cursor_row": self.cursor_row,
            "cursor_col": self.cursor_col,
        }
        if self.undo_stack:
            top = self.undo_stack[-1]
            if (
                top["lines"] == snapshot["lines"]
                and top["line_formats"] == snapshot["line_formats"]
                and top["strokes"] == snapshot["strokes"]
            ):
                return
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 80:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack or self.is_animating:
            return
        current = {
            "lines": list(self.lines),
            "line_formats": copy.deepcopy(self.line_formats),
            "strokes": copy.deepcopy(self.strokes),
            "cursor_row": self.cursor_row,
            "cursor_col": self.cursor_col,
        }
        self.redo_stack.append(current)
        prev = self.undo_stack.pop()
        self.lines = list(prev["lines"])
        self.line_formats = copy.deepcopy(prev["line_formats"])
        self._sync_formats_shape()
        self.strokes = copy.deepcopy(prev["strokes"])
        self.cursor_row = min(prev["cursor_row"], len(self.lines) - 1)
        self.cursor_col = min(prev["cursor_col"], len(self.lines[self.cursor_row]))
        self.sel_anchor = None
        self.redraw()
        self.app.trigger_autosave()

    def redo(self):
        if not self.redo_stack or self.is_animating:
            return
        current = {
            "lines": list(self.lines),
            "line_formats": copy.deepcopy(self.line_formats),
            "strokes": copy.deepcopy(self.strokes),
            "cursor_row": self.cursor_row,
            "cursor_col": self.cursor_col,
        }
        self.undo_stack.append(current)
        nxt = self.redo_stack.pop()
        self.lines = list(nxt["lines"])
        self.line_formats = copy.deepcopy(nxt["line_formats"])
        self._sync_formats_shape()
        self.strokes = copy.deepcopy(nxt["strokes"])
        self.cursor_row = min(nxt["cursor_row"], len(self.lines) - 1)
        self.cursor_col = min(nxt["cursor_col"], len(self.lines[self.cursor_row]))
        self.sel_anchor = None
        self.redraw()
        self.app.trigger_autosave()

    # -------------------------------------------------------------------------
    # PAGE DATA LOADING & SERIALIZATION
    # -------------------------------------------------------------------------
    def _sync_formats_shape(self):
        """Ensure line_formats strictly matches the row and column counts of self.lines."""
        while len(self.line_formats) < len(self.lines):
            self.line_formats.append([])
        if len(self.line_formats) > len(self.lines):
            del self.line_formats[len(self.lines) :]

        for r, line_str in enumerate(self.lines):
            row_fmt = self.line_formats[r]
            if len(row_fmt) < len(line_str):
                row_fmt.extend([None] * (len(line_str) - len(row_fmt)))
            elif len(row_fmt) > len(line_str):
                del row_fmt[len(line_str) :]

    def load_page(self, page_data):
        """Load text, character formatting, orientation, and strokes from page dict."""
        self.orientation = page_data.get("orientation", "portrait")
        raw_text = page_data.get("text", "")
        self.lines = raw_text.split("\n") if raw_text else [""]

        saved_formats = page_data.get("formats", [])
        self.line_formats = copy.deepcopy(saved_formats) if saved_formats else []
        self._sync_formats_shape()

        self.strokes = [
            {
                "color": s["color"],
                "width": s["width"],
                "points": [list(p) for p in s["points"]],
            }
            for s in page_data.get("strokes", [])
        ]
        self.cursor_row = min(self.cursor_row, len(self.lines) - 1)
        self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_row]))
        self.sel_anchor = None
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._on_resize()

    def export_page_state(self):
        """Return current text, character formatting, orientation, and strokes for saving."""
        self._sync_formats_shape()
        return {
            "orientation": self.orientation,
            "text": "\n".join(self.lines),
            "formats": copy.deepcopy(self.line_formats),
            "strokes": self.strokes,
        }

    # -------------------------------------------------------------------------
    # GEOMETRY & COORDINATE MAPPING
    # -------------------------------------------------------------------------
    def _get_symmetric_half_dims(self):
        """
        Compute unified (half_cols, half_rows) so that:
        - Portrait  = half_cols wide  x (2 * half_rows) tall
        - Landscape = (2 * half_cols) wide x half_rows tall
        Every half-page has the exact same character and pixel capacity in both modes,
        so switching orientations never truncates right-side text or bleeds strokes.
        """
        w = max(420, self.winfo_width())
        h = max(480, self.winfo_height())

        pad_x = max(20, int(w * 0.03))
        pad_y = max(18, int(h * 0.03))
        avail_w = w - pad_x * 2
        avail_h = h - pad_y * 2

        chrome_w = self.margin_left + self.margin_right
        chrome_h = self.margin_top + self.margin_bottom

        max_portrait_cols = max(20, int((min(880, avail_w) - chrome_w) // self.char_w))
        max_landscape_half_cols = max(20, int((avail_w - chrome_w) // (2 * self.char_w)))
        half_cols = min(max_portrait_cols, max_landscape_half_cols)

        max_portrait_half_rows = max(6, int((avail_h - chrome_h) // (2 * self.line_h)))
        half_rows = max_portrait_half_rows
        return half_cols, half_rows

    def _compute_paper_rect_for(self, orientation):
        w = max(420, self.winfo_width())
        h = max(480, self.winfo_height())
        half_cols, half_rows = self._get_symmetric_half_dims()

        chrome_w = self.margin_left + self.margin_right
        chrome_h = self.margin_top + self.margin_bottom

        if orientation == "landscape":
            page_w = chrome_w + (2 * half_cols) * self.char_w
            page_h = chrome_h + half_rows * self.line_h
        else:
            page_w = chrome_w + half_cols * self.char_w
            page_h = chrome_h + (2 * half_rows) * self.line_h

        x0 = max(12, (w - page_w) // 2)
        y0 = max(12, (h - page_h) // 2)
        return (x0, y0, x0 + page_w, y0 + page_h)

    def _on_resize(self, event=None):
        self.paper_rect = self._compute_paper_rect_for(self.orientation)
        self.redraw()

    def convert_orientation(self, new_orientation):
        """
        Convert page between portrait and landscape with exact 1:1 half-page geometry:
        - Portrait -> Landscape: cuts the page in half vertically and places the
          bottom half on the right side of the top half.
        - Landscape -> Portrait: cuts the page in half horizontally and places the
          right half beneath the left half.
        """
        if new_orientation == self.orientation:
            return

        self._push_undo_state()
        self._sync_formats_shape()

        half_cols, half_rows = self._get_symmetric_half_dims()
        new_rect = self._compute_paper_rect_for(new_orientation)

        if new_orientation == "landscape":
            # Cut vertically in half: top half stays left, bottom half moves to right half
            split_row = half_rows
            right_col_offset = half_cols
            total_land_cols = 2 * half_cols

            top_lines = self.lines[:split_row]
            top_fmts = self.line_formats[:split_row]
            bot_lines = self.lines[split_row:]
            bot_fmts = self.line_formats[split_row:]

            merged_rows = max(len(top_lines), len(bot_lines))
            new_lines = []
            new_fmts = []
            for r in range(merged_rows):
                l_txt = top_lines[r][:right_col_offset] if r < len(top_lines) else ""
                l_fmt = top_fmts[r][:right_col_offset] if r < len(top_fmts) else []
                r_txt = bot_lines[r] if r < len(bot_lines) else ""
                r_fmt = bot_fmts[r] if r < len(bot_fmts) else []

                if r_txt or any(r_fmt):
                    pad = right_col_offset - len(l_txt)
                    combined_txt = l_txt + (" " * pad) + r_txt
                    combined_fmt = list(l_fmt) + ([None] * pad) + list(r_fmt)
                else:
                    combined_txt = l_txt
                    combined_fmt = list(l_fmt)

                new_lines.append(combined_txt[:total_land_cols])
                new_fmts.append(combined_fmt[:total_land_cols])

            while len(new_lines) > 1 and not new_lines[-1] and not any(new_fmts[-1]):
                new_lines.pop()
                new_fmts.pop()

            self.lines = new_lines if new_lines else [""]
            self.line_formats = new_fmts if new_fmts else [[]]

            # Transform ink strokes: bottom half shifts up & right beside top half
            split_y_paper = self.margin_top + split_row * self.line_h
            right_x_shift = right_col_offset * self.char_w
            self.strokes = self._split_and_transform_strokes(
                self.strokes,
                axis="y",
                split_val=split_y_paper,
                transform_second=lambda x, y: [
                    round(x + right_x_shift, 1),
                    round(max(self.margin_top, y - split_y_paper + self.margin_top), 1),
                ],
            )
        else:
            # Landscape -> Portrait: cut horizontally in half; right half goes below left half
            split_col = half_cols
            split_row = half_rows
            top_lines = []
            top_fmts = []
            bot_lines = []
            bot_fmts = []

            for r, line_str in enumerate(self.lines):
                row_fmt = self.line_formats[r]
                raw_left = line_str[:split_col]
                trim_len = len(raw_left.rstrip(" "))
                # Keep trailing spaces only if they carry custom formatting (e.g. underline)
                while trim_len < len(raw_left) and row_fmt[trim_len] is not None:
                    trim_len += 1
                left_part = raw_left[:trim_len]
                left_fmt = row_fmt[:trim_len]

                right_part = line_str[split_col : split_col + half_cols]
                right_fmt = row_fmt[split_col : split_col + half_cols]

                top_lines.append(left_part)
                top_fmts.append(left_fmt)
                bot_lines.append(right_part)
                bot_fmts.append(right_fmt)

            while len(top_lines) > 1 and not top_lines[-1] and not any(top_fmts[-1]):
                top_lines.pop()
                top_fmts.pop()

            while bot_lines and not bot_lines[-1] and not any(bot_fmts[-1]):
                bot_lines.pop()
                bot_fmts.pop()

            if bot_lines:
                while len(top_lines) < split_row:
                    top_lines.append("")
                    top_fmts.append([])
                top_lines.extend(bot_lines)
                top_fmts.extend(bot_fmts)

            self.lines = top_lines if top_lines else [""]
            self.line_formats = top_fmts if top_fmts else [[]]

            # Transform ink strokes: right half shifts left & down beneath top half
            split_x_paper = self.margin_left + split_col * self.char_w
            bot_y_shift = split_row * self.line_h
            self.strokes = self._split_and_transform_strokes(
                self.strokes,
                axis="x",
                split_val=split_x_paper,
                transform_second=lambda x, y: [
                    round(max(self.margin_left, x - split_x_paper + self.margin_left), 1),
                    round(y + bot_y_shift, 1),
                ],
            )

        self.orientation = new_orientation
        self.paper_rect = new_rect
        self._sync_formats_shape()
        self.cursor_row = min(self.cursor_row, len(self.lines) - 1)
        self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_row]))
        self.sel_anchor = None
        self.redraw()

    def _split_and_transform_strokes(self, strokes, axis, split_val, transform_second):
        """
        Split strokes cleanly whenever they cross the half-page cutoff boundary so
        segments on opposite halves never connect across the page, then transform
        the second-half segments into their new region.
        """
        idx = 1 if axis == "y" else 0
        result = []

        for stroke in strokes:
            pts = stroke.get("points", [])
            if len(pts) < 2:
                continue

            segments = []  # List of (is_second_half, point_list)
            cur_side = pts[0][idx] >= split_val
            cur_pts = [list(pts[0])]

            for i in range(1, len(pts)):
                p0 = pts[i - 1]
                p1 = pts[i]
                v0 = p0[idx]
                v1 = p1[idx]
                s1 = v1 >= split_val

                if s1 == cur_side:
                    cur_pts.append(list(p1))
                else:
                    # Interpolate exact intersection point on the split line
                    dv = v1 - v0
                    t = (split_val - v0) / dv if abs(dv) > 1e-6 else 0.5
                    ix = round(p0[0] + t * (p1[0] - p0[0]), 1)
                    iy = round(p0[1] + t * (p1[1] - p0[1]), 1)
                    if axis == "y":
                        iy = round(split_val, 1)
                    else:
                        ix = round(split_val, 1)

                    cur_pts.append([ix, iy])
                    if len(cur_pts) >= 2:
                        segments.append((cur_side, cur_pts))

                    cur_side = s1
                    cur_pts = [[ix, iy], list(p1)]

            if len(cur_pts) >= 2:
                segments.append((cur_side, cur_pts))

            for is_second, seg_pts in segments:
                if is_second:
                    mapped = [transform_second(px, py) for px, py in seg_pts]
                else:
                    mapped = [[round(px, 1), round(py, 1)] for px, py in seg_pts]
                if len(mapped) >= 2:
                    result.append(
                        {
                            "color": stroke["color"],
                            "width": stroke["width"],
                            "points": mapped,
                        }
                    )

        return result

    def _get_text_bounds(self):
        x0, y0, x1, y1 = self.paper_rect
        tx0 = x0 + self.margin_left
        ty0 = y0 + self.margin_top
        tx1 = x1 - self.margin_right
        ty1 = y1 - self.margin_bottom
        max_cols = max(10, int((tx1 - tx0) // self.char_w))
        max_rows = max(5, int((ty1 - ty0) // self.line_h))
        return tx0, ty0, tx1, ty1, max_cols, max_rows

    def _canvas_to_grid(self, cx, cy):
        tx0, ty0, _, _, max_cols, max_rows = self._get_text_bounds()
        rel_x = max(0, cx - tx0)
        rel_y = max(0, cy - ty0)
        col = min(max_cols - 1, int(round(rel_x / self.char_w)))
        row = min(max_rows - 1, int(rel_y // self.line_h))
        return row, col

    def _grid_to_canvas(self, row, col):
        tx0, ty0, _, _, _, _ = self._get_text_bounds()
        return tx0 + col * self.char_w, ty0 + row * self.line_h

    def _canvas_to_norm_paper(self, cx, cy):
        x0, y0, _, _ = self.paper_rect
        return [round(cx - x0, 1), round(cy - y0, 1)]

    def _norm_paper_to_canvas(self, px, py):
        x0, y0, _, _ = self.paper_rect
        return x0 + px, y0 + py

    # -------------------------------------------------------------------------
    # MOUSE & PEN INTERACTION (WRITE vs DRAW vs ERASER)
    # -------------------------------------------------------------------------
    def _on_mouse_down(self, event):
        if self.is_animating:
            return
        self.focus_set()

        x0, y0, x1, y1 = self.paper_rect
        if not (x0 <= event.x <= x1 and y0 <= event.y <= y1):
            return

        mode = self.app.current_mode.get()

        if mode == "write":
            row, col = self._canvas_to_grid(event.x, event.y)
            self._place_cursor_at_virtual_position(row, col)
            self.sel_anchor = (self.cursor_row, self.cursor_col)
            self._reset_blink()
            self.redraw()

        elif mode == "draw":
            self._push_undo_state()
            pt = self._canvas_to_norm_paper(event.x, event.y)
            self.current_stroke = {
                "color": self.app.pen_color.get(),
                "width": self.app.pen_width.get(),
                "points": [pt, [pt[0] + 0.1, pt[1] + 0.1]],
            }
            self.strokes.append(self.current_stroke)
            self.redraw()

        elif mode == "eraser":
            self._push_undo_state()
            self.is_erasing = True
            self._erase_near(event.x, event.y)

    def _on_mouse_drag(self, event):
        if self.is_animating:
            return
        mode = self.app.current_mode.get()

        if mode == "write" and self.sel_anchor is not None:
            row, col = self._canvas_to_grid(event.x, event.y)
            self._ensure_grid_exists(row, col)
            self.cursor_row = row
            self.cursor_col = col
            self.redraw()

        elif mode == "draw" and self.current_stroke is not None:
            x0, y0, x1, y1 = self.paper_rect
            cx = min(max(event.x, x0 + 4), x1 - 4)
            cy = min(max(event.y, y0 + 4), y1 - 4)
            pt = self._canvas_to_norm_paper(cx, cy)
            last = self.current_stroke["points"][-1]
            if math.hypot(pt[0] - last[0], pt[1] - last[1]) >= 1.5:
                self.current_stroke["points"].append(pt)
                self.redraw()

        elif mode == "eraser" and self.is_erasing:
            self._erase_near(event.x, event.y)

    def _on_mouse_up(self, event):
        mode = self.app.current_mode.get()
        if mode == "write":
            if self.sel_anchor == (self.cursor_row, self.cursor_col):
                self.sel_anchor = None
            self.redraw()
            self.app.trigger_autosave()
        elif mode == "draw" and self.current_stroke is not None:
            self.current_stroke = None
            self.app.trigger_autosave()
        elif mode == "eraser" and self.is_erasing:
            self.is_erasing = False
            self.app.trigger_autosave()

    def _erase_near(self, cx, cy, radius=14):
        x0, y0, _, _ = self.paper_rect
        px, py = cx - x0, cy - y0
        kept = []
        changed = False
        for stroke in self.strokes:
            hit = False
            pts = stroke["points"]
            for i in range(len(pts)):
                if math.hypot(pts[i][0] - px, pts[i][1] - py) <= radius:
                    hit = True
                    break
            if hit:
                changed = True
            else:
                kept.append(stroke)
        if changed:
            self.strokes = kept
            self.redraw()

    # -------------------------------------------------------------------------
    # FULL-PAGE CLICK-TO-POSITION TEXT EDITOR & RICH FORMATTING LOGIC
    # -------------------------------------------------------------------------
    def _ensure_grid_exists(self, target_row, target_col):
        while len(self.lines) <= target_row:
            self.lines.append("")
            self.line_formats.append([])
        line = self.lines[target_row]
        if len(line) < target_col:
            pad = target_col - len(line)
            self.lines[target_row] = line + (" " * pad)
            self.line_formats[target_row].extend([None] * pad)
        self._sync_formats_shape()

    def _place_cursor_at_virtual_position(self, row, col):
        self._ensure_grid_exists(row, col)
        self.cursor_row = row
        self.cursor_col = col
        self.preferred_col = None

    def _get_ordered_selection(self):
        if not self.sel_anchor:
            return None
        r1, c1 = self.sel_anchor
        r2, c2 = self.cursor_row, self.cursor_col
        if (r1, c1) == (r2, c2):
            return None
        if (r1, c1) > (r2, c2):
            return (r2, c2), (r1, c1)
        return (r1, c1), (r2, c2)

    def _get_selected_text(self):
        sel = self._get_ordered_selection()
        if not sel:
            return ""
        (r1, c1), (r2, c2) = sel
        if r1 == r2:
            return self.lines[r1][c1:c2]
        parts = [self.lines[r1][c1:]]
        for r in range(r1 + 1, r2):
            parts.append(self.lines[r])
        parts.append(self.lines[r2][:c2])
        return "\n".join(parts)

    def apply_format_to_selection(self, modifier_fn):
        """Apply a formatting mutation function to every character in the current selection."""
        sel = self._get_ordered_selection()
        if not sel:
            return False
        self._push_undo_state()
        self._sync_formats_shape()
        (r1, c1), (r2, c2) = sel
        for r in range(r1, r2 + 1):
            line_len = len(self.lines[r])
            start_c = c1 if r == r1 else 0
            end_c = c2 if r == r2 else line_len
            for c in range(start_c, min(end_c, line_len)):
                cur = dict(self.line_formats[r][c] or {})
                updated = modifier_fn(cur)
                self.line_formats[r][c] = updated if updated else None
        self.redraw()
        self.app.trigger_autosave()
        return True

    def _delete_selection(self):
        sel = self._get_ordered_selection()
        if not sel:
            return False
        self._sync_formats_shape()
        (r1, c1), (r2, c2) = sel
        if r1 == r2:
            line = self.lines[r1]
            fmt = self.line_formats[r1]
            self.lines[r1] = line[:c1] + line[c2:]
            self.line_formats[r1] = fmt[:c1] + fmt[c2:]
        else:
            first_part = self.lines[r1][:c1]
            last_part = self.lines[r2][c2:]
            first_fmt = self.line_formats[r1][:c1]
            last_fmt = self.line_formats[r2][c2:]
            self.lines[r1] = first_part + last_part
            self.line_formats[r1] = first_fmt + last_fmt
            del self.lines[r1 + 1 : r2 + 1]
            del self.line_formats[r1 + 1 : r2 + 1]
        self.cursor_row, self.cursor_col = r1, c1
        self.sel_anchor = None
        return True

    def _delete_word_backward(self, max_cols, max_rows):
        if self._delete_selection():
            return
        if self.cursor_col == 0:
            if self.cursor_row > 0:
                prev_len = len(self.lines[self.cursor_row - 1])
                self.lines[self.cursor_row - 1] += self.lines[self.cursor_row]
                self.line_formats[self.cursor_row - 1].extend(
                    self.line_formats[self.cursor_row]
                )
                del self.lines[self.cursor_row]
                del self.line_formats[self.cursor_row]
                self.cursor_row -= 1
                self.cursor_col = prev_len
            return

        line = self.lines[self.cursor_row]
        idx = self.cursor_col
        while idx > 0 and line[idx - 1] == " ":
            idx -= 1
        while idx > 0 and line[idx - 1] != " ":
            idx -= 1
        self.lines[self.cursor_row] = line[:idx] + line[self.cursor_col :]
        fmt = self.line_formats[self.cursor_row]
        self.line_formats[self.cursor_row] = fmt[:idx] + fmt[self.cursor_col :]
        self.cursor_col = idx

    def _delete_word_forward(self):
        if self._delete_selection():
            return
        line = self.lines[self.cursor_row]
        if self.cursor_col >= len(line):
            if self.cursor_row + 1 < len(self.lines):
                self.lines[self.cursor_row] += self.lines[self.cursor_row + 1]
                self.line_formats[self.cursor_row].extend(
                    self.line_formats[self.cursor_row + 1]
                )
                del self.lines[self.cursor_row + 1]
                del self.line_formats[self.cursor_row + 1]
            return

        idx = self.cursor_col
        while idx < len(line) and line[idx] != " ":
            idx += 1
        while idx < len(line) and line[idx] == " ":
            idx += 1
        self.lines[self.cursor_row] = line[: self.cursor_col] + line[idx:]
        fmt = self.line_formats[self.cursor_row]
        self.line_formats[self.cursor_row] = fmt[: self.cursor_col] + fmt[idx:]

    def _move_word_left(self):
        if self.cursor_col == 0:
            if self.cursor_row > 0:
                self.cursor_row -= 1
                self.cursor_col = len(self.lines[self.cursor_row])
            return
        line = self.lines[self.cursor_row]
        idx = self.cursor_col
        while idx > 0 and line[idx - 1] == " ":
            idx -= 1
        while idx > 0 and line[idx - 1] != " ":
            idx -= 1
        self.cursor_col = idx

    def _move_word_right(self):
        line = self.lines[self.cursor_row]
        if self.cursor_col >= len(line):
            if self.cursor_row + 1 < len(self.lines):
                self.cursor_row += 1
                self.cursor_col = 0
            return
        idx = self.cursor_col
        while idx < len(line) and line[idx] != " ":
            idx += 1
        while idx < len(line) and line[idx] == " ":
            idx += 1
        self.cursor_col = idx

    def _on_key_press(self, event):
        if self.is_animating:
            return

        shift = (event.state & 0x0001) != 0
        ctrl = (event.state & 0x0004) != 0 or (event.state & 0x0008) != 0
        ks = event.keysym.lower()

        # Global Undo / Redo (works in both Write and Draw modes)
        if ctrl and ks == "z" and not shift:
            self.undo()
            return "break"
        if ctrl and (ks == "y" or (ks == "z" and shift)):
            self.redo()
            return "break"

        # Automatically switch to Write mode if user types printable text (without Ctrl)
        if (
            self.app.current_mode.get() != "write"
            and not ctrl
            and event.char
            and event.char.isprintable()
        ):
            self.app.set_mode("write")

        if self.app.current_mode.get() != "write":
            return

        _, _, _, _, max_cols, max_rows = self._get_text_bounds()

        # Rich-Text Shortcuts on Selection (Ctrl+B, Ctrl+U)
        if ctrl and ks == "b":
            self.app._toggle_selected_bold()
            return "break"
        if ctrl and ks == "u":
            self.app._toggle_selected_underline()
            return "break"

        # Select All (Ctrl+A)
        if ctrl and ks == "a":
            self.sel_anchor = (0, 0)
            self.cursor_row = len(self.lines) - 1
            self.cursor_col = len(self.lines[-1])
            self.redraw()
            return "break"

        # Copy / Cut / Paste (Ctrl+C, Ctrl+X, Ctrl+V)
        if ctrl and ks == "c":
            txt = self._get_selected_text()
            if txt:
                self.clipboard_clear()
                self.clipboard_append(txt)
            return "break"

        if ctrl and ks == "x":
            txt = self._get_selected_text()
            if txt:
                self._push_undo_state()
                self.clipboard_clear()
                self.clipboard_append(txt)
                self._delete_selection()
                self.redraw()
                self.app.trigger_autosave()
            return "break"

        if ctrl and ks == "v":
            try:
                clip = self.clipboard_get()
            except tk.TclError:
                clip = ""
            if clip:
                self._push_undo_state()
                self._delete_selection()
                self._insert_text_raw(clip, max_cols, max_rows)
                self._reset_blink()
                self.redraw()
                self.app.trigger_autosave()
            return "break"

        # Word-level Backspace / Delete (Ctrl+Backspace, Ctrl+Delete)
        if ctrl and event.keysym == "BackSpace":
            self._push_undo_state()
            self._delete_word_backward(max_cols, max_rows)
            self._reset_blink()
        # Navigation Keys (supports Shift selection, Ctrl word jumping & IDE-style Up/Down)
        if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End"):
            if shift and not self.sel_anchor:
                self.sel_anchor = (self.cursor_row, self.cursor_col)
            elif not shift:
                self.sel_anchor = None

            if event.keysym not in ("Up", "Down"):
                self.preferred_col = None

            if event.keysym == "Left":
                if ctrl:
                    self._move_word_left()
                elif self.cursor_col > 0:
                    self.cursor_col -= 1
                elif self.cursor_row > 0:
                    self.cursor_row -= 1
                    self.cursor_col = len(self.lines[self.cursor_row])
            elif event.keysym == "Right":
                if ctrl:
                    self._move_word_right()
                elif self.cursor_col < len(self.lines[self.cursor_row]):
                    self.cursor_col += 1
                elif self.cursor_row + 1 < len(self.lines):
                    self.cursor_row += 1
                    self.cursor_col = 0
            elif event.keysym == "Up":
                if self.preferred_col is None:
                    self.preferred_col = self.cursor_col
                if self.cursor_row > 0:
                    self.cursor_row -= 1
                    self.cursor_col = min(
                        self.preferred_col, len(self.lines[self.cursor_row])
                    )
            elif event.keysym == "Down":
                if self.preferred_col is None:
                    self.preferred_col = self.cursor_col
                if self.cursor_row + 1 < max_rows:
                    self.cursor_row += 1
                    if self.cursor_row >= len(self.lines):
                        self.lines.append("")
                        self.line_formats.append([])
                    self.cursor_col = min(
                        self.preferred_col, len(self.lines[self.cursor_row])
                    )
            elif event.keysym == "Home":
                if ctrl:
                    self.cursor_row = 0
                self.cursor_col = 0
            elif event.keysym == "End":
                if ctrl:
                    self.cursor_row = len(self.lines) - 1
                self.cursor_col = len(self.lines[self.cursor_row].rstrip(" "))

            self._reset_blink()
            self.redraw()
            return "break"

        # Any editing action resets IDE vertical column memory
        self.preferred_col = None

        # Enter / Return
        if event.keysym in ("Return", "KP_Enter"):
            self._push_undo_state()
            self._delete_selection()
            self._insert_newline(max_rows)
            self._reset_blink()
            self.redraw()
            self.app.trigger_autosave()
            return "break"

        # Backspace
        if event.keysym == "BackSpace":
            self._push_undo_state()
            if not self._delete_selection():
                if self.cursor_col > 0:
                    line = self.lines[self.cursor_row]
                    fmt = self.line_formats[self.cursor_row]
                    self.lines[self.cursor_row] = (
                        line[: self.cursor_col - 1] + line[self.cursor_col :]
                    )
                    self.line_formats[self.cursor_row] = (
                        fmt[: self.cursor_col - 1] + fmt[self.cursor_col :]
                    )
                    self.cursor_col -= 1
                elif self.cursor_row > 0:
                    prev_len = len(self.lines[self.cursor_row - 1])
                    self.lines[self.cursor_row - 1] += self.lines[self.cursor_row]
                    self.line_formats[self.cursor_row - 1].extend(
                        self.line_formats[self.cursor_row]
                    )
                    del self.lines[self.cursor_row]
                    del self.line_formats[self.cursor_row]
                    self.cursor_row -= 1
                    self.cursor_col = prev_len
            self._reset_blink()
            self.redraw()
            self.app.trigger_autosave()
            return "break"

        # Delete
        if event.keysym == "Delete":
            self._push_undo_state()
            if not self._delete_selection():
                line = self.lines[self.cursor_row]
                fmt = self.line_formats[self.cursor_row]
                if self.cursor_col < len(line):
                    self.lines[self.cursor_row] = (
                        line[: self.cursor_col] + line[self.cursor_col + 1 :]
                    )
                    self.line_formats[self.cursor_row] = (
                        fmt[: self.cursor_col] + fmt[self.cursor_col + 1 :]
                    )
                elif self.cursor_row + 1 < len(self.lines):
                    self.lines[self.cursor_row] += self.lines[self.cursor_row + 1]
                    self.line_formats[self.cursor_row].extend(
                        self.line_formats[self.cursor_row + 1]
                    )
                    del self.lines[self.cursor_row + 1]
                    del self.line_formats[self.cursor_row + 1]
            self._reset_blink()
            self.redraw()
            self.app.trigger_autosave()
            return "break"

        # Tab
        if event.keysym == "Tab":
            self._push_undo_state()
            self._delete_selection()
            self._insert_text_raw("    ", max_cols, max_rows)
            self._reset_blink()
            self.redraw()
            self.app.trigger_autosave()
            return "break"

        # Printable character input
        if not ctrl and event.char and event.char.isprintable():
            self._push_undo_state()
            self._delete_selection()
            self._insert_text_raw(event.char, max_cols, max_rows)
            self._reset_blink()
            self.redraw()
            self.app.trigger_autosave()
            return "break"

    def _insert_newline(self, max_rows):
        if len(self.lines) < max_rows:
            self._sync_formats_shape()
            line = self.lines[self.cursor_row]
            fmt = self.line_formats[self.cursor_row]
            self.lines[self.cursor_row] = line[: self.cursor_col]
            self.line_formats[self.cursor_row] = fmt[: self.cursor_col]
            self.lines.insert(self.cursor_row + 1, line[self.cursor_col :])
            self.line_formats.insert(self.cursor_row + 1, fmt[self.cursor_col :])
            self.cursor_row += 1
            self.cursor_col = 0

    def _insert_text_raw(self, text_str, max_cols, max_rows):
        """
        Insert single or multi-line text character-by-character so pasted paragraphs
        wrap cleanly inside the right margin without bleeding off the paper edge.
        """
        text_str = text_str.replace("\r\n", "\n").replace("\r", "\n")
        for ch in text_str:
            if ch == "\n":
                self._insert_newline(max_rows)
                continue

            if ch == "\t":
                self._insert_text_raw("    ", max_cols, max_rows)
                continue

            if not ch.isprintable():
                continue

            self._ensure_grid_exists(self.cursor_row, self.cursor_col)
            line = self.lines[self.cursor_row]
            fmt = self.line_formats[self.cursor_row]

            # Inherit adjacent character formatting if typing inside formatted span
            inherited_fmt = None
            if self.cursor_col > 0 and fmt[self.cursor_col - 1]:
                inherited_fmt = dict(fmt[self.cursor_col - 1])

            self.lines[self.cursor_row] = (
                line[: self.cursor_col] + ch + line[self.cursor_col :]
            )
            self.line_formats[self.cursor_row] = (
                fmt[: self.cursor_col] + [inherited_fmt] + fmt[self.cursor_col :]
            )
            self.cursor_col += 1

            # Wrap line cleanly whenever it reaches or exceeds max_cols
            while len(self.lines[self.cursor_row]) > max_cols:
                cur_line = self.lines[self.cursor_row]
                cur_fmt = self.line_formats[self.cursor_row]

                # Prefer breaking at the last space before max_cols for clean word wrap
                break_idx = cur_line.rfind(" ", 1, max_cols + 1)
                if break_idx > 0:
                    keep_line = cur_line[:break_idx]
                    keep_fmt = cur_fmt[:break_idx]
                    overflow_line = cur_line[break_idx + 1 :]
                    overflow_fmt = cur_fmt[break_idx + 1 :]
                    had_space_break = True
                else:
                    keep_line = cur_line[:max_cols]
                    keep_fmt = cur_fmt[:max_cols]
                    overflow_line = cur_line[max_cols:]
                    overflow_fmt = cur_fmt[max_cols:]
                    had_space_break = False

                self.lines[self.cursor_row] = keep_line
                self.line_formats[self.cursor_row] = keep_fmt

                if self.cursor_row + 1 < max_rows:
                    next_r = self.cursor_row + 1
                    if next_r >= len(self.lines):
                        self.lines.append(overflow_line)
                        self.line_formats.append(overflow_fmt)
                    else:
                        sep = " " if (overflow_line and self.lines[next_r]) else ""
                        sep_fmt = [None] if sep else []
                        self.lines[next_r] = overflow_line + sep + self.lines[next_r]
                        self.line_formats[next_r] = (
                            overflow_fmt + sep_fmt + self.line_formats[next_r]
                        )

                    if self.cursor_col > len(keep_line):
                        shift_amt = len(keep_line) + (1 if had_space_break else 0)
                        self.cursor_row = next_r
                        self.cursor_col = max(0, self.cursor_col - shift_amt)
                    else:
                        break
                else:
                    self.cursor_col = min(self.cursor_col, max_cols)
                    break

    def _schedule_blink(self):
        self.cursor_visible = not self.cursor_visible
        if not self.is_animating and self.app.current_mode.get() == "write":
            self.redraw()
        self._blink_job = self.after(530, self._schedule_blink)

    def _reset_blink(self):
        self.cursor_visible = True

    # -------------------------------------------------------------------------
    # RENDERING PIPELINE (PAPER, BACKGROUND STYLE, RICH TEXT, STROKES, FLIP)
    # -------------------------------------------------------------------------
    def redraw(self):
        self.delete("all")
        page = self.app.get_current_page()
        if not page:
            return

        x0, y0, x1, y1 = self.paper_rect

        # 1. Stacked underlying notebook pages edge effect
        for offset in (6, 4, 2):
            self.create_rectangle(
                x0 + offset,
                y0 + offset,
                x1 + offset,
                y1 + offset,
                fill=THEME["paper_stack"] if offset == 2 else THEME["paper_shadow"],
                outline=THEME["paper_edge"],
                width=1,
            )

        # 2. Main paper sheet
        self._draw_paper_sheet(
            x0,
            y0,
            x1,
            y1,
            style=page.get("style", "lined"),
            lines=self.lines,
            strokes=self.strokes,
            show_cursor=(
                self.app.current_mode.get() == "write" and not self.is_animating
            ),
        )

        # 3. Curling page-turn overlay when flipping between pages
        if self.is_animating:
            self._draw_page_turn_overlay()

        # 4. Sync floating selection mini-toolbar (Word-style)
        if hasattr(self.app, "_sync_floating_format_bar"):
            self.app._sync_floating_format_bar()

    def _draw_paper_sheet(self, x0, y0, x1, y1, style, lines, strokes, show_cursor=False):
        w = x1 - x0
        h = y1 - y0

        # Base paper rectangle
        self.create_rectangle(
            x0,
            y0,
            x1,
            y1,
            fill=THEME["paper_bg"],
            outline=THEME["paper_edge"],
            width=1.5,
        )

        # Subtle binding spine shadow on left edge
        self.create_rectangle(
            x0 + 1, y0 + 1, x0 + 18, y1 - 1, fill=THEME["spine_shadow"], outline=""
        )
        self.create_line(
            x0 + 18, y0 + 1, x0 + 18, y1 - 1, fill=THEME["spine_line"], width=1
        )

        # Subtle paper fiber grain speckles
        for gx, gy in self.grain_dots:
            px = x0 + 22 + gx * (w - 30)
            py = y0 + 10 + gy * (h - 20)
            self.create_rectangle(
                px, py, px + 1, py + 1, fill=THEME["grain_dot"], outline=""
            )

        tx0, ty0, _, _, max_cols, max_rows = self._get_text_bounds()

        # Background Pattern Layer (Purely visual—never affects text or stroke metrics)
        if style == "lined":
            self.create_line(
                tx0 - 10, y0 + 6, tx0 - 10, y1 - 6, fill=THEME["margin_red"], width=1
            )
            for r in range(max_rows + 1):
                ly = ty0 + r * self.line_h + self.line_h - 4
                if ly < y1 - 14:
                    self.create_line(
                        x0 + 20, ly, x1 - 14, ly, fill=THEME["line_blue"], width=1
                    )
        elif style == "grid":
            grid_step = self.line_h
            for r in range(max_rows + 1):
                ly = ty0 + r * grid_step + grid_step - 4
                if ly < y1 - 14:
                    self.create_line(
                        x0 + 20, ly, x1 - 14, ly, fill=THEME["line_blue"], width=1
                    )
            gx = tx0
            while gx <= x1 - 16:
                self.create_line(
                    gx, y0 + 12, gx, y1 - 12, fill=THEME["line_blue"], width=1
                )
                gx += grid_step

        # Half-Page Cutoff Margin Ticks (outside the paper edge, short & subtle)
        tick_color = {
            "warm": "#C2B8A8",
            "light_blue": "#A6BDD4",
            "dark_blue": "#2D435E",
        }.get(self.app.active_theme_key, "#C2B8A8")
        if self.orientation == "portrait":
            split_row = max(1, max_rows // 2)
            mid_y = ty0 + split_row * self.line_h
            if y0 + 16 < mid_y < y1 - 16:
                self.create_line(
                    x0 - 11, mid_y, x0 - 3, mid_y, fill=tick_color, width=1, dash=(2, 2)
                )
                self.create_line(
                    x1 + 9, mid_y, x1 + 17, mid_y, fill=tick_color, width=1, dash=(2, 2)
                )
        else:
            split_col = max(1, max_cols // 2)
            mid_x = tx0 + split_col * self.char_w
            if x0 + 24 < mid_x < x1 - 24:
                self.create_line(
                    mid_x, y0 - 11, mid_x, y0 - 3, fill=tick_color, width=1, dash=(2, 2)
                )
                self.create_line(
                    mid_x, y1 + 9, mid_x, y1 + 17, fill=tick_color, width=1, dash=(2, 2)
                )

        # Selection Highlight Layer (drawn behind text so highlighted characters stand out)
        sel = self._get_ordered_selection()
        if sel:
            (sr1, sc1), (sr2, sc2) = sel
            for r in range(sr1, min(sr2 + 1, max_rows)):
                line_len = len(self.lines[r]) if r < len(self.lines) else 0
                c_start = sc1 if r == sr1 else 0
                c_end = sc2 if r == sr2 else max(line_len, 1)
                c_start = min(c_start, max_cols)
                c_end = min(c_end, max_cols)
                if c_end > c_start:
                    sx0, sy0 = self._grid_to_canvas(r, c_start)
                    sx1, _ = self._grid_to_canvas(r, c_end)
                    self.create_rectangle(
                        sx0,
                        sy0 + 2,
                        sx1,
                        sy0 + self.line_h - 4,
                        fill=THEME["selection_bg"],
                        outline="",
                    )

        # Text Content Layer (per-character size, bold, color, and colored underline)
        self._sync_formats_shape()
        for r, line_str in enumerate(lines):
            if r >= max_rows:
                break
            if not line_str:
                continue

            visible_str = line_str[:max_cols]
            row_fmt = self.line_formats[r][:max_cols]

            # Fast path when the entire line uses default unformatted styling
            if not any(row_fmt):
                lx, ly = self._grid_to_canvas(r, 0)
                self.create_text(
                    lx,
                    ly + (self.line_h // 2) - 2,
                    text=visible_str,
                    anchor="w",
                    font=self.text_font,
                    fill=THEME["ink_text"],
                )
                continue

            # Rich-formatted path: draw character cells and custom colored underlines
            for c, ch in enumerate(visible_str):
                fmt = row_fmt[c] or {}
                cx, cy = self._grid_to_canvas(r, c)
                mid_y = cy + (self.line_h // 2) - 2

                if ch != " ":
                    sz = fmt.get("size", self.base_font_size)
                    is_bold = fmt.get("bold", False)
                    fg_col = fmt.get("color") or THEME["ink_text"]
                    font_obj = self._get_styled_font(sz, is_bold)
                    self.create_text(
                        cx + (self.char_w // 2),
                        mid_y,
                        text=ch,
                        anchor="center",
                        font=font_obj,
                        fill=fg_col,
                    )

                if fmt.get("underline"):
                    ul_col = (
                        fmt.get("underline_color")
                        or fmt.get("color")
                        or THEME["ink_text"]
                    )
                    ul_y = cy + self.line_h - 6
                    self.create_line(
                        cx,
                        ul_y,
                        cx + self.char_w,
                        ul_y,
                        fill=ul_col,
                        width=1.6,
                    )

        # Blinking Fountain-Pen Text Cursor
        if show_cursor and self.cursor_visible:
            draw_col = min(self.cursor_col, max_cols)
            cx, cy = self._grid_to_canvas(self.cursor_row, draw_col)
            self.create_line(
                cx,
                cy + 3,
                cx,
                cy + self.line_h - 5,
                fill=THEME["accent"],
                width=2,
            )
        # 5. Freehand Ink Drawing Layer (coexists seamlessly on top of text)
        if self.app.show_drawings.get():
            for stroke in strokes:
                pts = stroke.get("points", [])
                if len(pts) < 2:
                    continue
                flat = []
                for px, py in pts:
                    abs_x, abs_y = self._norm_paper_to_canvas(px, py)
                    flat.extend([abs_x, abs_y])
                self.create_line(
                    *flat,
                    fill=stroke.get("color", THEME["ink_text"]),
                    width=stroke.get("width", 2),
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND,
                    smooth=True,
                )

    # -------------------------------------------------------------------------
    # SMOOTH PAGE-TURNING ANIMATION (~500ms)
    # -------------------------------------------------------------------------
    def start_page_turn(self, direction, on_midpoint_switch):
        if self.is_animating:
            on_midpoint_switch()
            return

        self.is_animating = True
        self.anim_direction = direction
        self.anim_progress = 0.0
        self._midpoint_callback = on_midpoint_switch
        self._switched = False
        self._anim_start_time = time.perf_counter()
        self._anim_duration = 0.50
        self._step_page_turn()

    def _step_page_turn(self):
        elapsed = time.perf_counter() - self._anim_start_time
        t = min(1.0, elapsed / self._anim_duration)
        eased = 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2
        self.anim_progress = eased

        if t >= 0.45 and not self._switched:
            self._switched = True
            self._midpoint_callback()

        self.redraw()

        if t < 1.0:
            self.after(16, self._step_page_turn)
        else:
            self.is_animating = False
            self.redraw()

    def _draw_page_turn_overlay(self):
        x0, y0, x1, y1 = self.paper_rect
        w = x1 - x0
        p = self.anim_progress

        if self.anim_direction == 1:
            fold_x = x1 - p * w
        else:
            fold_x = x0 + p * w

        curl_width = math.sin(p * math.pi) * min(110, w * 0.22)
        lift_y = math.sin(p * math.pi) * 18

        shadow_x0 = max(x0, fold_x - curl_width * 0.6)
        shadow_x1 = min(x1, fold_x + curl_width * 1.4)
        self.create_polygon(
            shadow_x0,
            y0,
            shadow_x1,
            y0,
            shadow_x1,
            y1,
            shadow_x0,
            y1,
            fill=THEME["curl_shadow"],
            outline="",
        )

        leaf_right = min(x1, fold_x + curl_width)
        self.create_polygon(
            fold_x,
            y0,
            leaf_right,
            y0 - lift_y,
            leaf_right,
            y1 - lift_y,
            fold_x,
            y1,
            fill=THEME["curl_back"],
            outline=THEME["curl_edge"],
            width=1.5,
        )

        self.create_line(
            fold_x, y0, fold_x, y1, fill=THEME["curl_highlight"], width=2
        )


# =============================================================================
# MAIN DESKTOP APPLICATION WINDOW
# =============================================================================
class DigitalNotebookApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Notebook")
        self.geometry("1180x820")
        self.minsize(860, 620)

        # Initialize storage & load notebooks + saved theme
        self.storage = NotebookStorage()
        self.data = self.storage.load()
        self.active_theme_key = self.data.get("theme", "warm")
        THEME.clear()
        THEME.update(THEMES.get(self.active_theme_key, THEMES["warm"]))
        self.configure(bg=THEME["desk_bg"])

        # Always start in Fullscreen mode (F11 toggles, Escape exits)
        self.is_fullscreen = True
        self.attributes("-fullscreen", True)
        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)

        # Reactive UI state
        self.current_mode = tk.StringVar(value="write")
        self.pen_color = tk.StringVar(value=INK_COLORS[0][1])
        self.pen_width = tk.IntVar(value=2)
        self.show_drawings = tk.BooleanVar(value=True)
        self.paper_style = tk.StringVar(value="lined")
        self.page_orientation = tk.StringVar(value="portrait")
        self.underline_color = tk.StringVar(value=UNDERLINE_COLORS[0][1])
        self.save_status = tk.StringVar(value="Saved locally")
        self._autosave_job = None

        self._build_ui()
        self._refresh_sidebar()
        self._load_active_notebook_and_page()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -------------------------------------------------------------------------
    # FULLSCREEN & THEME HELPERS
    # -------------------------------------------------------------------------
    def _toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    def _exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)

    def _set_theme(self, theme_key):
        if theme_key not in THEMES:
            return
        self.active_theme_key = theme_key
        self.data["theme"] = theme_key
        THEME.clear()
        THEME.update(THEMES[theme_key])
        self._apply_theme_to_widgets()
        self.trigger_autosave()

    def _apply_theme_to_widgets(self):
        self.configure(bg=THEME["desk_bg"])
        self.root_pane.configure(bg=THEME["desk_bg"])
        self.sidebar.configure(
            bg=THEME["sidebar_bg"], highlightbackground=THEME["sidebar_border"]
        )
        self.sb_header.configure(bg=THEME["sidebar_bg"])
        self.settings_btn.configure(
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            activebackground=THEME["sidebar_active"],
        )
        self.sb_title_lbl.configure(fg=THEME["accent"], bg=THEME["sidebar_bg"])
        self.new_nb_btn.configure(
            bg=THEME["accent"],
            fg=THEME["btn_active_fg"],
            activebackground=THEME["accent_light"],
            activeforeground=THEME["btn_active_fg"],
        )
        self.nb_list_frame.configure(bg=THEME["sidebar_bg"])
        self.sb_footer.configure(bg=THEME["sidebar_bg"])
        self.save_status_lbl.configure(
            fg=THEME["muted_text"], bg=THEME["sidebar_bg"]
        )

        self.workspace.configure(bg=THEME["desk_bg"])
        self.toolbar.configure(
            bg=THEME["toolbar_bg"], highlightbackground=THEME["toolbar_border"]
        )
        for sep in self.toolbar_seps:
            sep.configure(bg=THEME["toolbar_border"])

        self.nav_frame.configure(bg=THEME["toolbar_bg"])
        self.prev_page_btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])
        self.page_indicator_label.configure(
            fg=THEME["ink_text"], bg=THEME["toolbar_bg"]
        )
        self.next_page_btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])
        self.new_page_btn.configure(
            bg=THEME["accent"],
            fg=THEME["btn_active_fg"],
            activebackground=THEME["accent_light"],
            activeforeground=THEME["btn_active_fg"],
        )
        self.del_page_btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])

        if hasattr(self, "draw_tools_frame"):
            self.draw_tools_frame.configure(bg=THEME["toolbar_bg"])
            self.draw_tools_sep.configure(bg=THEME["toolbar_border"])
        if hasattr(self, "eraser_tools_frame"):
            self.eraser_tools_frame.configure(bg=THEME["toolbar_bg"])
            self.eraser_tools_sep.configure(bg=THEME["toolbar_border"])
            self.show_drawings_chk.configure(
                bg=THEME["toolbar_bg"],
                fg=THEME["ink_text"],
                activebackground=THEME["toolbar_bg"],
                activeforeground=THEME["ink_text"],
                selectcolor=THEME["paper_bg"],
            )
            self.clear_all_btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])

        if hasattr(self, "page_style_btn"):
            self.page_style_btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])
        if hasattr(self, "orientation_btn"):
            self.orientation_btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])

        self.page_canvas.configure(bg=THEME["desk_bg"])
        self._refresh_sidebar()
        self._update_toolbar_highlights()
        self.page_canvas.redraw()

    # -------------------------------------------------------------------------
    # DATA ACCESSORS
    # -------------------------------------------------------------------------
    def get_active_notebook(self):
        active_id = self.data.get("active_notebook_id")
        for nb in self.data["notebooks"]:
            if nb["id"] == active_id:
                return nb
        return self.data["notebooks"][0]

    def get_current_page(self):
        nb = self.get_active_notebook()
        idx = max(0, min(nb.get("active_page_index", 0), len(nb["pages"]) - 1))
        nb["active_page_index"] = idx
        return nb["pages"][idx]

    # -------------------------------------------------------------------------
    # UI CONSTRUCTION
    # -------------------------------------------------------------------------
    def _build_ui(self):
        self.root_pane = tk.Frame(self, bg=THEME["desk_bg"])
        self.root_pane.pack(fill=tk.BOTH, expand=True)

        # === A. LEFT SIDEBAR (NOTEBOOK LIBRARY + TOP-LEFT SETTINGS) ===
        self.sidebar = tk.Frame(
            self.root_pane,
            width=245,
            bg=THEME["sidebar_bg"],
            highlightbackground=THEME["sidebar_border"],
            highlightthickness=1,
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Sidebar Header with Top-Left Settings Button
        self.sb_header = tk.Frame(
            self.sidebar, bg=THEME["sidebar_bg"], pady=14, padx=14
        )
        self.sb_header.pack(fill=tk.X)

        self.settings_btn = tk.Button(
            self.sb_header,
            text="⚙",
            font=("Arial", 12),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            activebackground=THEME["sidebar_active"],
            relief=tk.FLAT,
            padx=7,
            pady=1,
            cursor="hand2",
            command=self._open_settings_menu,
        )
        self.settings_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.sb_title_lbl = tk.Label(
            self.sb_header,
            text="NOTEBOOKS",
            font=("Georgia", 11, "bold"),
            fg=THEME["accent"],
            bg=THEME["sidebar_bg"],
        )
        self.sb_title_lbl.pack(side=tk.LEFT)

        # + New Notebook Button
        self.new_nb_btn = tk.Button(
            self.sidebar,
            text="+  New Notebook",
            font=("Georgia", 10, "bold"),
            bg=THEME["accent"],
            fg=THEME["btn_active_fg"],
            activebackground=THEME["accent_light"],
            activeforeground=THEME["btn_active_fg"],
            relief=tk.FLAT,
            cursor="hand2",
            pady=8,
            command=self._create_notebook,
        )
        self.new_nb_btn.pack(fill=tk.X, padx=14, pady=(0, 12))

        # Notebook List Container
        self.nb_list_frame = tk.Frame(self.sidebar, bg=THEME["sidebar_bg"])
        self.nb_list_frame.pack(fill=tk.BOTH, expand=True, padx=8)

        # Local Storage Status Footer
        self.sb_footer = tk.Frame(
            self.sidebar, bg=THEME["sidebar_bg"], pady=10, padx=14
        )
        self.sb_footer.pack(side=tk.BOTTOM, fill=tk.X)
        self.save_status_lbl = tk.Label(
            self.sb_footer,
            textvariable=self.save_status,
            font=("Georgia", 9, "italic"),
            fg=THEME["muted_text"],
            bg=THEME["sidebar_bg"],
        )
        self.save_status_lbl.pack(side=tk.LEFT)

        # === RIGHT WORKSPACE (COMPACT TOP TOOLBAR + OPEN NOTEBOOK CANVAS) ===
        self.workspace = tk.Frame(self.root_pane, bg=THEME["desk_bg"])
        self.workspace.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # === C. COMPACT TOP TOOLBAR ===
        self.toolbar = tk.Frame(
            self.workspace,
            height=52,
            bg=THEME["toolbar_bg"],
            highlightbackground=THEME["toolbar_border"],
            highlightthickness=1,
            padx=14,
            pady=7,
        )
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.toolbar_seps = []

        # 1. Mode Selection (Write / Draw / Eraser)
        self.mode_buttons = {}
        mode_specs = [
            ("write", "✎ Write"),
            ("draw", "✒ Draw"),
            ("eraser", "⌫ Eraser"),
        ]
        for mode_key, label in mode_specs:
            btn = tk.Button(
                self.toolbar,
                text=label,
                font=("Georgia", 10),
                relief=tk.FLAT,
                padx=11,
                pady=4,
                cursor="hand2",
                command=lambda m=mode_key: self.set_mode(m),
            )
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.mode_buttons[mode_key] = btn

        # 2. Contextual Draw-Mode Controls (visible ONLY when Draw is selected)
        self.draw_tools_frame = tk.Frame(self.toolbar, bg=THEME["toolbar_bg"])
        self.draw_tools_sep = tk.Frame(
            self.draw_tools_frame, width=1, height=24, bg=THEME["toolbar_border"]
        )
        self.draw_tools_sep.pack(side=tk.LEFT, padx=8, pady=2)

        self.color_buttons = {}
        for _, hex_code in INK_COLORS:
            swatch = tk.Button(
                self.draw_tools_frame,
                text="●",
                font=("Arial", 13),
                fg=hex_code,
                bg=THEME["toolbar_bg"],
                activebackground=THEME["btn_bg"],
                relief=tk.FLAT,
                padx=4,
                pady=1,
                cursor="hand2",
                command=lambda c=hex_code: self._set_pen_color(c),
            )
            swatch.pack(side=tk.LEFT, padx=1)
            self.color_buttons[hex_code] = swatch

        self._add_toolbar_separator(parent=self.draw_tools_frame)

        self.width_buttons = {}
        for label, width_val in PEN_SIZES:
            wbtn = tk.Button(
                self.draw_tools_frame,
                text=label,
                font=("Georgia", 9),
                relief=tk.FLAT,
                padx=7,
                pady=4,
                cursor="hand2",
                command=lambda w=width_val: self._set_pen_width(w),
            )
            wbtn.pack(side=tk.LEFT, padx=2)
            self.width_buttons[width_val] = wbtn

        # 3. Contextual Eraser-Mode Controls (visible ONLY when Eraser is selected)
        self.eraser_tools_frame = tk.Frame(self.toolbar, bg=THEME["toolbar_bg"])
        self.eraser_tools_sep = tk.Frame(
            self.eraser_tools_frame, width=1, height=24, bg=THEME["toolbar_border"]
        )
        self.eraser_tools_sep.pack(side=tk.LEFT, padx=8, pady=2)

        self.show_drawings_chk = tk.Checkbutton(
            self.eraser_tools_frame,
            text="Show drawings",
            variable=self.show_drawings,
            font=("Georgia", 9),
            bg=THEME["toolbar_bg"],
            fg=THEME["ink_text"],
            activebackground=THEME["toolbar_bg"],
            activeforeground=THEME["ink_text"],
            selectcolor=THEME["paper_bg"],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._toggle_show_drawings,
        )
        self.show_drawings_chk.pack(side=tk.LEFT, padx=(2, 6))

        self.clear_all_btn = tk.Button(
            self.eraser_tools_frame,
            text="Clear all",
            font=("Georgia", 9),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._clear_all_drawings,
        )
        self.clear_all_btn.pack(side=tk.LEFT, padx=2)

        self.paper_style_sep = tk.Frame(
            self.toolbar, width=1, height=24, bg=THEME["toolbar_border"]
        )
        self.paper_style_sep.pack(side=tk.LEFT, padx=8, pady=2)
        self.toolbar_seps.append(self.paper_style_sep)

        # 4. Page Background Selector ("Page style" dropdown) & Orientation Toggle
        self.page_style_btn = tk.Button(
            self.toolbar,
            text="Page style ▾",
            font=("Georgia", 9),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self._open_page_style_menu,
        )
        self.page_style_btn.pack(side=tk.LEFT, padx=2)

        self.orientation_btn = tk.Button(
            self.toolbar,
            text="▯ Portrait",
            font=("Georgia", 9),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self._toggle_page_orientation,
        )
        self.orientation_btn.pack(side=tk.LEFT, padx=(4, 2))

        # 5. Right-Aligned Page Navigation, "+ Page", and "- Page"
        self.nav_frame = tk.Frame(self.toolbar, bg=THEME["toolbar_bg"])
        self.nav_frame.pack(side=tk.RIGHT)

        self.prev_page_btn = tk.Button(
            self.nav_frame,
            text="◀ Prev",
            font=("Georgia", 9),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._prev_page,
        )
        self.prev_page_btn.pack(side=tk.LEFT, padx=2)

        self.page_indicator_label = tk.Label(
            self.nav_frame,
            text="Page 1 of 1",
            font=("Georgia", 10),
            fg=THEME["ink_text"],
            bg=THEME["toolbar_bg"],
            padx=8,
        )
        self.page_indicator_label.pack(side=tk.LEFT)

        self.next_page_btn = tk.Button(
            self.nav_frame,
            text="Next ▶",
            font=("Georgia", 9),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._next_page,
        )
        self.next_page_btn.pack(side=tk.LEFT, padx=2)

        self.new_page_btn = tk.Button(
            self.nav_frame,
            text="+ Page",
            font=("Georgia", 9, "bold"),
            bg=THEME["accent"],
            fg=THEME["btn_active_fg"],
            activebackground=THEME["accent_light"],
            activeforeground=THEME["btn_active_fg"],
            relief=tk.FLAT,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self._add_new_page,
        )
        self.new_page_btn.pack(side=tk.LEFT, padx=(6, 2))

        self.del_page_btn = tk.Button(
            self.nav_frame,
            text="- Page",
            font=("Georgia", 9),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._delete_current_page,
        )
        self.del_page_btn.pack(side=tk.LEFT, padx=(2, 0))

        # === B. MAIN AREA (OPEN NOTEBOOK PAGE CANVAS) ===
        self.page_canvas = NotebookPageCanvas(self.workspace, self)
        self.page_canvas.pack(fill=tk.BOTH, expand=True)

        # === FLOATING WORD-STYLE MINI-TOOLBAR OVER HIGHLIGHTED TEXT ===
        self.float_bar = tk.Frame(
            self.page_canvas,
            bg=THEME["toolbar_bg"],
            highlightbackground=THEME["accent"],
            highlightthickness=1,
            padx=6,
            pady=4,
        )
        self.float_visible = False

        self.txt_dec_btn = tk.Button(
            self.float_bar,
            text="A-",
            font=("Georgia", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=6,
            pady=2,
            cursor="hand2",
            command=lambda: self._format_selected_text_size(-2),
        )
        self.txt_dec_btn.pack(side=tk.LEFT, padx=1)

        self.txt_inc_btn = tk.Button(
            self.float_bar,
            text="A+",
            font=("Georgia", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=6,
            pady=2,
            cursor="hand2",
            command=lambda: self._format_selected_text_size(2),
        )
        self.txt_inc_btn.pack(side=tk.LEFT, padx=1)

        self.txt_bold_btn = tk.Button(
            self.float_bar,
            text="B",
            font=("Georgia", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=7,
            pady=2,
            cursor="hand2",
            command=self._toggle_selected_bold,
        )
        self.txt_bold_btn.pack(side=tk.LEFT, padx=(4, 1))

        self.txt_ul_btn = tk.Button(
            self.float_bar,
            text="U",
            font=("Georgia", 9, "underline"),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=7,
            pady=2,
            cursor="hand2",
            command=self._toggle_selected_underline,
        )
        self.txt_ul_btn.pack(side=tk.LEFT, padx=1)

        self.txt_color_btn = tk.Button(
            self.float_bar,
            text="A▾",
            font=("Georgia", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["ink_text"],
            relief=tk.FLAT,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self._open_text_color_menu,
        )
        self.txt_color_btn.pack(side=tk.LEFT, padx=(4, 1))

        self.ul_color_btn = tk.Button(
            self.float_bar,
            text="U̲▾",
            font=("Georgia", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=self.underline_color.get(),
            relief=tk.FLAT,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self._open_underline_color_menu,
        )
        self.ul_color_btn.pack(side=tk.LEFT, padx=1)

        self._update_toolbar_highlights()

    def _add_toolbar_separator(self, parent=None):
        target = parent if parent is not None else self.toolbar
        sep = tk.Frame(target, width=1, height=24, bg=THEME["toolbar_border"])
        sep.pack(side=tk.LEFT, padx=8, pady=2)
        self.toolbar_seps.append(sep)

    # -------------------------------------------------------------------------
    # SETTINGS MENU (FULLSCREEN, THEMES, BACKUP EXPORT / IMPORT)
    # -------------------------------------------------------------------------
    def _open_settings_menu(self):
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=THEME["toolbar_bg"],
            fg=THEME["ink_text"],
            activebackground=THEME["accent"],
            activeforeground=THEME["btn_active_fg"],
            font=("Georgia", 10),
        )

        fs_label = (
            "✓ Fullscreen Mode (F11)"
            if self.is_fullscreen
            else "   Fullscreen Mode (F11)"
        )
        menu.add_command(label=fs_label, command=self._toggle_fullscreen)
        menu.add_separator()

        theme_menu = tk.Menu(
            menu,
            tearoff=0,
            bg=THEME["toolbar_bg"],
            fg=THEME["ink_text"],
            activebackground=THEME["accent"],
            activeforeground=THEME["btn_active_fg"],
            font=("Georgia", 10),
        )
        for key, spec in THEMES.items():
            prefix = "✓ " if self.active_theme_key == key else "   "
            theme_menu.add_command(
                label=f"{prefix}{spec['name']}",
                command=lambda k=key: self._set_theme(k),
            )
        menu.add_cascade(label="Theme", menu=theme_menu)
        menu.add_separator()

        menu.add_command(
            label="Download Active Notebook (.json)...",
            command=self._export_active_notebook,
        )
        menu.add_command(
            label="Import Notebook (.json)...",
            command=self._import_notebook_file,
        )

        bx = self.settings_btn.winfo_rootx()
        by = self.settings_btn.winfo_rooty() + self.settings_btn.winfo_height() + 2
        menu.tk_popup(bx, by)

    def _export_active_notebook(self):
        self._commit_current_page_to_memory()
        nb = self.get_active_notebook()
        safe_name = (
            "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_" for c in nb["name"]
            ).strip()
            or "notebook"
        )
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Download Notebook Backup",
            defaultextension=".json",
            initialfile=f"{safe_name}.json",
            filetypes=[("Notebook JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        payload = {
            "format": "personal_digital_notebook_v1",
            "notebook": copy.deepcopy(nb),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            self.save_status.set("Notebook exported")
        except Exception as e:
            messagebox.showerror(
                "Export Error", f"Could not save file:\n{e}", parent=self
            )

    def _import_notebook_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Open / Import Notebook",
            filetypes=[("Notebook JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            if isinstance(raw, dict) and "notebook" in raw:
                imported_nbs = [raw["notebook"]]
            elif isinstance(raw, dict) and "notebooks" in raw:
                imported_nbs = raw["notebooks"]
            elif isinstance(raw, dict) and "pages" in raw:
                imported_nbs = [raw]
            else:
                raise ValueError("Unrecognized notebook file format.")

            self._commit_current_page_to_memory()
            last_id = None
            for nb in imported_nbs:
                if not isinstance(nb.get("pages"), list) or not nb["pages"]:
                    nb["pages"] = [self.storage.create_default_page("lined")]
                nb["id"] = str(uuid.uuid4())
                nb["name"] = nb.get("name", "Imported Notebook")
                nb["active_page_index"] = min(
                    nb.get("active_page_index", 0), len(nb["pages"]) - 1
                )
                self.data["notebooks"].append(nb)
                last_id = nb["id"]

            if last_id:
                self.data["active_notebook_id"] = last_id
            self._refresh_sidebar()
            self._load_active_notebook_and_page()
            self.trigger_autosave()
            self.save_status.set("Notebook imported")
        except Exception as e:
            messagebox.showerror(
                "Import Error", f"Could not import notebook:\n{e}", parent=self
            )

    # -------------------------------------------------------------------------
    # TOOLBAR & FLOATING SELECTION MINI-TOOLBAR ACTIONS
    # -------------------------------------------------------------------------
    def set_mode(self, mode):
        self.current_mode.set(mode)
        if mode == "write":
            self.page_canvas.config(cursor="xterm")
        elif mode == "draw":
            self.page_canvas.config(cursor="pencil")
        else:
            self.page_canvas.config(cursor="circle")
        self._update_toolbar_highlights()
        self.page_canvas.redraw()

    def _set_pen_color(self, hex_code):
        self.pen_color.set(hex_code)
        if self.current_mode.get() == "eraser":
            self.set_mode("draw")
        else:
            self._update_toolbar_highlights()

    def _set_pen_width(self, width_val):
        self.pen_width.set(width_val)
        if self.current_mode.get() == "eraser":
            self.set_mode("draw")
        else:
            self._update_toolbar_highlights()

    def _toggle_show_drawings(self):
        self.page_canvas.redraw()

    def _clear_all_drawings(self):
        if not self.page_canvas.strokes:
            messagebox.showinfo(
                "Nothing to Clear",
                "There are no drawings on this page.",
                parent=self,
            )
            return
        confirm = messagebox.askyesno(
            "Clear All Drawings",
            "Are you sure you want to clear all drawings on this page?",
            parent=self,
        )
        if not confirm:
            return
        self.page_canvas._push_undo_state()
        self.page_canvas.strokes.clear()
        self.page_canvas.redraw()
        self.trigger_autosave()

    def _set_paper_style(self, style_key):
        page = self.get_current_page()
        page["style"] = style_key
        self.paper_style.set(style_key)
        self._update_toolbar_highlights()
        self.page_canvas.redraw()
        self.trigger_autosave()

    def _open_page_style_menu(self):
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=THEME["toolbar_bg"],
            fg=THEME["ink_text"],
            activebackground=THEME["accent"],
            activeforeground=THEME["btn_active_fg"],
            font=("Georgia", 9),
        )
        cur_style = self.paper_style.get()
        for style_key, style_label in PAPER_STYLES:
            prefix = "✓ " if cur_style == style_key else "   "
            menu.add_command(
                label=f"{prefix}{style_label}",
                command=lambda s=style_key: self._set_paper_style(s),
            )
        bx = self.page_style_btn.winfo_rootx()
        by = (
            self.page_style_btn.winfo_rooty()
            + self.page_style_btn.winfo_height()
            + 2
        )
        menu.tk_popup(bx, by)

    def _toggle_page_orientation(self):
        page = self.get_current_page()
        cur = page.get("orientation", "portrait")
        nxt = "landscape" if cur == "portrait" else "portrait"
        self.page_canvas.convert_orientation(nxt)
        page["orientation"] = nxt
        self.page_orientation.set(nxt)
        self._update_toolbar_highlights()
        self.trigger_autosave()

    def _sync_floating_format_bar(self):
        """Position the Word-style mini-toolbar above the highlighted text, or hide when unselected."""
        if not hasattr(self, "float_bar"):
            return
        sel = self.page_canvas._get_ordered_selection()
        if (
            not sel
            or self.current_mode.get() != "write"
            or self.page_canvas.is_animating
        ):
            if self.float_visible:
                self.float_bar.place_forget()
                self.float_visible = False
            return

        (sr1, sc1), (sr2, sc2) = sel
        sx0, sy0 = self.page_canvas._grid_to_canvas(sr1, sc1)
        end_col = sc2 if sr1 == sr2 else max(sc1 + 6, len(self.page_canvas.lines[sr1]))
        sx1, _ = self.page_canvas._grid_to_canvas(sr1, end_col)

        self.float_bar.update_idletasks()
        bar_w = max(220, self.float_bar.winfo_reqwidth())
        bar_h = max(34, self.float_bar.winfo_reqheight())
        canvas_w = max(300, self.page_canvas.winfo_width())

        center_x = (sx0 + sx1) / 2
        px = int(max(12, min(canvas_w - bar_w - 12, center_x - bar_w / 2)))
        py = int(sy0 - bar_h - 8)
        if py < 8:
            py = int(sy0 + self.page_canvas.line_h + 6)

        self.float_bar.place(x=px, y=py)
        self.float_bar.lift()
        self.float_visible = True

    def _format_selected_text_size(self, delta):
        def mod(fmt):
            cur_sz = fmt.get("size", self.page_canvas.base_font_size)
            new_sz = max(10, min(22, cur_sz + delta))
            if new_sz == self.page_canvas.base_font_size:
                fmt.pop("size", None)
            else:
                fmt["size"] = new_sz
            return fmt

        self.page_canvas.apply_format_to_selection(mod)

    def _toggle_selected_bold(self):
        sel = self.page_canvas._get_ordered_selection()
        if not sel:
            return
        (r1, c1), _ = sel
        first_fmt = (
            self.page_canvas.line_formats[r1][c1]
            if r1 < len(self.page_canvas.line_formats)
            and c1 < len(self.page_canvas.line_formats[r1])
            else None
        ) or {}
        target = not first_fmt.get("bold", False)

        def mod(fmt):
            if target:
                fmt["bold"] = True
            else:
                fmt.pop("bold", None)
            return fmt

        self.page_canvas.apply_format_to_selection(mod)

    def _toggle_selected_underline(self):
        sel = self.page_canvas._get_ordered_selection()
        if not sel:
            return
        (r1, c1), _ = sel
        first_fmt = (
            self.page_canvas.line_formats[r1][c1]
            if r1 < len(self.page_canvas.line_formats)
            and c1 < len(self.page_canvas.line_formats[r1])
            else None
        ) or {}
        target = not first_fmt.get("underline", False)
        ul_col = self.underline_color.get()

        def mod(fmt):
            if target:
                fmt["underline"] = True
                fmt["underline_color"] = ul_col
            else:
                fmt.pop("underline", None)
                fmt.pop("underline_color", None)
            return fmt

        self.page_canvas.apply_format_to_selection(mod)

    def _open_text_color_menu(self):
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=THEME["toolbar_bg"],
            fg=THEME["ink_text"],
            activebackground=THEME["accent"],
            activeforeground=THEME["btn_active_fg"],
            font=("Georgia", 9),
        )
        menu.add_command(
            label="● Default Ink",
            command=lambda: self._apply_selected_text_color(None),
        )
        menu.add_separator()
        for name, hex_code in RICH_TEXT_COLORS:
            menu.add_command(
                label=f"● {name}",
                foreground=hex_code,
                command=lambda c=hex_code: self._apply_selected_text_color(c),
            )
        bx = self.txt_color_btn.winfo_rootx()
        by = (
            self.txt_color_btn.winfo_rooty()
            + self.txt_color_btn.winfo_height()
            + 2
        )
        menu.tk_popup(bx, by)

    def _apply_selected_text_color(self, hex_code):
        def mod(fmt):
            if hex_code is None:
                fmt.pop("color", None)
            else:
                fmt["color"] = hex_code
            return fmt

        self.page_canvas.apply_format_to_selection(mod)

    def _open_underline_color_menu(self):
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=THEME["toolbar_bg"],
            fg=THEME["ink_text"],
            activebackground=THEME["accent"],
            activeforeground=THEME["btn_active_fg"],
            font=("Georgia", 9),
        )
        for name, hex_code in UNDERLINE_COLORS:
            menu.add_command(
                label=f"▬ {name} Underline",
                foreground=hex_code,
                command=lambda c=hex_code: self._apply_selected_underline_color(c),
            )
        bx = self.ul_color_btn.winfo_rootx()
        by = (
            self.ul_color_btn.winfo_rooty()
            + self.ul_color_btn.winfo_height()
            + 2
        )
        menu.tk_popup(bx, by)

    def _apply_selected_underline_color(self, hex_code):
        self.underline_color.set(hex_code)
        self.ul_color_btn.configure(fg=hex_code)

        def mod(fmt):
            fmt["underline"] = True
            fmt["underline_color"] = hex_code
            return fmt

        self.page_canvas.apply_format_to_selection(mod)

    def _update_toolbar_highlights(self):
        active_mode = self.current_mode.get()
        for key, btn in self.mode_buttons.items():
            if key == active_mode:
                btn.configure(bg=THEME["btn_active"], fg=THEME["btn_active_fg"])
            else:
                btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])

        # Show Draw controls only in Draw mode; Eraser controls only in Eraser mode
        if hasattr(self, "draw_tools_frame") and hasattr(self, "eraser_tools_frame"):
            self.draw_tools_frame.pack_forget()
            self.eraser_tools_frame.pack_forget()
            if active_mode == "draw":
                self.draw_tools_frame.pack(
                    side=tk.LEFT, before=self.paper_style_sep
                )
            elif active_mode == "eraser":
                self.eraser_tools_frame.pack(
                    side=tk.LEFT, before=self.paper_style_sep
                )

        active_color = self.pen_color.get()
        for hex_code, btn in self.color_buttons.items():
            btn.configure(
                bg=(
                    THEME["sidebar_active"]
                    if hex_code == active_color
                    else THEME["toolbar_bg"]
                )
            )

        active_width = self.pen_width.get()
        for w_val, btn in self.width_buttons.items():
            if w_val == active_width:
                btn.configure(bg=THEME["btn_active"], fg=THEME["btn_active_fg"])
            else:
                btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])

        if hasattr(self, "page_style_btn"):
            self.page_style_btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])

        if hasattr(self, "orientation_btn"):
            is_land = self.page_orientation.get() == "landscape"
            self.orientation_btn.configure(
                text="▭ Landscape" if is_land else "▯ Portrait",
                bg=THEME["btn_bg"],
                fg=THEME["ink_text"],
            )

        if hasattr(self, "float_bar"):
            self.float_bar.configure(
                bg=THEME["toolbar_bg"], highlightbackground=THEME["accent"]
            )
            for btn in (
                self.txt_dec_btn,
                self.txt_inc_btn,
                self.txt_bold_btn,
                self.txt_ul_btn,
                self.txt_color_btn,
            ):
                btn.configure(bg=THEME["btn_bg"], fg=THEME["ink_text"])
            self.ul_color_btn.configure(
                bg=THEME["btn_bg"], fg=self.underline_color.get()
            )

    # -------------------------------------------------------------------------
    # SIDEBAR NOTEBOOK MANAGEMENT
    # -------------------------------------------------------------------------
    def _refresh_sidebar(self):
        for child in self.nb_list_frame.winfo_children():
            child.destroy()

        active_id = self.data.get("active_notebook_id")

        for nb in self.data["notebooks"]:
            is_active = nb["id"] == active_id
            row_bg = THEME["sidebar_active"] if is_active else THEME["sidebar_bg"]

            item = tk.Frame(
                self.nb_list_frame,
                bg=row_bg,
                pady=7,
                padx=10,
                cursor="hand2",
            )
            item.pack(fill=tk.X, pady=2)

            title_lbl = tk.Label(
                item,
                text=f"📓  {nb['name']}",
                font=("Georgia", 10, "bold" if is_active else "normal"),
                fg=THEME["ink_text"],
                bg=row_bg,
                anchor="w",
            )
            title_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            del_btn = tk.Button(
                item,
                text="✕",
                font=("Arial", 8),
                fg=THEME["muted_text"],
                bg=row_bg,
                activebackground=THEME["sidebar_hover"],
                relief=tk.FLAT,
                bd=0,
                padx=4,
                cursor="hand2",
                command=lambda n=nb: self._delete_notebook(n),
            )
            del_btn.pack(side=tk.RIGHT)

            ren_btn = tk.Button(
                item,
                text="✎",
                font=("Arial", 9),
                fg=THEME["muted_text"],
                bg=row_bg,
                activebackground=THEME["sidebar_hover"],
                relief=tk.FLAT,
                bd=0,
                padx=4,
                cursor="hand2",
                command=lambda n=nb: self._rename_notebook(n),
            )
            ren_btn.pack(side=tk.RIGHT)

            item.bind(
                "<Button-1>", lambda e, n_id=nb["id"]: self._select_notebook(n_id)
            )
            title_lbl.bind(
                "<Button-1>", lambda e, n_id=nb["id"]: self._select_notebook(n_id)
            )

    def _select_notebook(self, notebook_id):
        if notebook_id == self.data.get("active_notebook_id"):
            return
        self._commit_current_page_to_memory()
        self.data["active_notebook_id"] = notebook_id
        self._refresh_sidebar()
        self._load_active_notebook_and_page()
        self.trigger_autosave()

    def _create_notebook(self):
        name = simpledialog.askstring(
            "New Notebook", "Enter a name for your new notebook:", parent=self
        )
        if not name or not name.strip():
            return
        self._commit_current_page_to_memory()
        new_nb = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "active_page_index": 0,
            "pages": [self.storage.create_default_page("lined")],
        }
        self.data["notebooks"].append(new_nb)
        self.data["active_notebook_id"] = new_nb["id"]
        self._refresh_sidebar()
        self._load_active_notebook_and_page()
        self.trigger_autosave()

    def _rename_notebook(self, notebook):
        new_name = simpledialog.askstring(
            "Rename Notebook",
            "Enter a new name:",
            initialvalue=notebook["name"],
            parent=self,
        )
        if new_name and new_name.strip():
            notebook["name"] = new_name.strip()
            self._refresh_sidebar()
            self.trigger_autosave()

    def _delete_notebook(self, notebook):
        if len(self.data["notebooks"]) <= 1:
            messagebox.showinfo(
                "Cannot Delete",
                "You must keep at least one notebook in your library.",
                parent=self,
            )
            return

        confirm = messagebox.askyesno(
            "Delete Notebook",
            f"Delete '{notebook['name']}' and all of its pages?",
            parent=self,
        )
        if not confirm:
            return

        self.data["notebooks"] = [
            nb for nb in self.data["notebooks"] if nb["id"] != notebook["id"]
        ]
        if self.data["active_notebook_id"] == notebook["id"]:
            self.data["active_notebook_id"] = self.data["notebooks"][0]["id"]

        self._refresh_sidebar()
        self._load_active_notebook_and_page()
        self.trigger_autosave()

    # -------------------------------------------------------------------------
    # PAGE NAVIGATION, CREATION, DELETION & ANIMATION
    # -------------------------------------------------------------------------
    def _load_active_notebook_and_page(self):
        page = self.get_current_page()
        self.paper_style.set(page.get("style", "lined"))
        self.page_orientation.set(page.get("orientation", "portrait"))
        self.page_canvas.load_page(page)
        self._update_page_indicator()
        self._update_toolbar_highlights()

    def _update_page_indicator(self):
        nb = self.get_active_notebook()
        idx = nb["active_page_index"]
        total = len(nb["pages"])
        self.page_indicator_label.configure(text=f"Page {idx + 1} of {total}")

        self.prev_page_btn.configure(state=tk.NORMAL if idx > 0 else tk.DISABLED)
        self.next_page_btn.configure(
            state=tk.NORMAL if idx + 1 < total else tk.DISABLED
        )

    def _prev_page(self):
        nb = self.get_active_notebook()
        idx = nb["active_page_index"]
        if idx <= 0:
            return
        self._commit_current_page_to_memory()

        def switch():
            nb["active_page_index"] = idx - 1
            self._load_active_notebook_and_page()
            self.trigger_autosave()

        self.page_canvas.start_page_turn(direction=-1, on_midpoint_switch=switch)

    def _next_page(self):
        nb = self.get_active_notebook()
        idx = nb["active_page_index"]
        if idx + 1 >= len(nb["pages"]):
            return
        self._commit_current_page_to_memory()

        def switch():
            nb["active_page_index"] = idx + 1
            self._load_active_notebook_and_page()
            self.trigger_autosave()

        self.page_canvas.start_page_turn(direction=1, on_midpoint_switch=switch)

    def _add_new_page(self):
        self._commit_current_page_to_memory()
        nb = self.get_active_notebook()
        current_style = self.get_current_page().get("style", "lined")
        new_page = self.storage.create_default_page(style=current_style)
        insert_idx = nb["active_page_index"] + 1
        nb["pages"].insert(insert_idx, new_page)

        def switch():
            nb["active_page_index"] = insert_idx
            self._load_active_notebook_and_page()
            self.trigger_autosave()

        self.page_canvas.start_page_turn(direction=1, on_midpoint_switch=switch)

    def _delete_current_page(self):
        nb = self.get_active_notebook()
        idx = nb["active_page_index"]
        total = len(nb["pages"])

        if total <= 1:
            confirm = messagebox.askyesno(
                "Clear Page",
                "This is the only page in this notebook. Clear its contents?",
                parent=self,
            )
            if not confirm:
                return
            current_style = nb["pages"][0].get("style", "lined")
            nb["pages"][0] = self.storage.create_default_page(style=current_style)
            self._load_active_notebook_and_page()
            self.trigger_autosave()
            return

        confirm = messagebox.askyesno(
            "Delete Page",
            f"Delete Page {idx + 1} of {total}?",
            parent=self,
        )
        if not confirm:
            return

        del nb["pages"][idx]
        new_idx = min(idx, len(nb["pages"]) - 1)

        def switch():
            nb["active_page_index"] = new_idx
            self._load_active_notebook_and_page()
            self.trigger_autosave()

        self.page_canvas.start_page_turn(direction=-1, on_midpoint_switch=switch)

    # -------------------------------------------------------------------------
    # PERSISTENCE & AUTOSAVE
    # -------------------------------------------------------------------------
    def _commit_current_page_to_memory(self):
        page = self.get_current_page()
        exported = self.page_canvas.export_page_state()
        page["orientation"] = exported["orientation"]
        page["text"] = exported["text"]
        page["formats"] = exported["formats"]
        page["strokes"] = exported["strokes"]

    def trigger_autosave(self):
        self.save_status.set("Saving...")
        if self._autosave_job is not None:
            self.after_cancel(self._autosave_job)
        self._autosave_job = self.after(300, self._perform_save)

    def _perform_save(self):
        self._autosave_job = None
        self._commit_current_page_to_memory()
        self.storage.save(self.data)
        self.save_status.set("Saved locally")

    def _on_close(self):
        self._perform_save()
        self.destroy()


if __name__ == "__main__":
    app = DigitalNotebookApp()
    app.mainloop()