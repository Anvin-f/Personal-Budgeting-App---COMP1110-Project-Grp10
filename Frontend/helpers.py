"""Shared Tkinter helpers: cards, buttons, text capture, zebra rows."""

import io
import sys
import tkinter as tk
from tkinter import ttk

import Backend.settings as app_settings
import Backend.tags as tags
import platform

from .constants import ACCENT, BG, BORDER, CARD, FONT_H, TEXT, FONT_FAMILY


def capture_output(fn, *args, **kwargs):
    """Run *fn* and return everything it printed as a string."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        fn(*args, **kwargs)
    finally:
        sys.stdout = old
    return buf.getvalue()


def card(parent, **kwargs):
    """Themed card container."""
    return tk.Frame(
        parent, bg=CARD, relief="flat",
        highlightbackground=BORDER, highlightthickness=1,
        **kwargs,
    )


def button(parent, text, command, color=ACCENT, fg="white", **kwargs):
    """Themed pill button. On macOS, a Label is used to keep the background colour."""
    if platform.system() == "Darwin":
        lbl = tk.Label(
            parent,
            text=text,
            bg=color,
            fg=fg,
            font=(FONT_FAMILY, 10, "bold"),
            cursor="hand2",
            relief="flat",
            bd=2,
            highlightbackground=color,
            padx=14,
            pady=7,
            **kwargs,
        )
        lbl.bind("<Button-1>", lambda e, cmd=command: cmd())
        lbl._is_action_button = True   # mark for _fix_sidebar_bg
        return lbl
    else:
        btn = tk.Button(
            parent, text=text, command=command,
            bg=color, fg=fg,
            font=(FONT_FAMILY, 10, "bold"),
            bd=0, cursor="hand2",
            activebackground=color, activeforeground=fg,
            relief="flat", padx=14, pady=7,
            **kwargs,
        )
        btn._is_action_button = True
        return btn


def page_header(parent, title):
    """Standard page title bar."""
    wrapper = tk.Frame(parent, bg=BG)
    wrapper.pack(fill="x", padx=24, pady=(18, 0))
    tk.Label(wrapper, text=title, bg=BG, fg=TEXT, font=FONT_H).pack(anchor="w")
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 0))


def safe_read_tags():
    """Return tags dict, or empty dict on any error."""
    try:
        return tags.read_tag_csv()
    except Exception:
        return {}


def safe_float(value, default=0.0):
    """Parse *value* to float; return *default* on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def zebra(tree):
    """Configure alternating row colours on a Treeview."""
    dark = app_settings.read_settings().get("dark_mode", False)
    if dark:
        odd_bg, even_bg = "#263247", "#1e293b"
        row_fg = "#e2e8f0"
    else:
        odd_bg, even_bg = "#f9fafb", CARD
        row_fg = TEXT
    tree.tag_configure("odd", background=odd_bg, foreground=row_fg)
    tree.tag_configure("even", background=even_bg, foreground=row_fg)


def repaint_tree(tree):
    """Apply zebra tags to every visible row."""
    for idx, item_id in enumerate(tree.get_children()):
        tree.item(item_id, tags=("odd" if idx % 2 else "even",))


def bind_tree_sort(tree, col_id, _col_idx, parse_fn=None):
    """Make a Treeview column sortable by clicking its header.
    *col_id*   – column name as passed to tree.heading().
    *_col_idx* – reserved for backward-compatible call sites.
    *parse_fn* – optional parser for cell text (e.g. strip HK$, parse %)."""
    if not hasattr(tree, "_sort_states"):
        tree._sort_states = {}  # col_id -> reverse bool

    def _sort():
        reverse = not tree._sort_states.get(col_id, False)
        tree._sort_states[col_id] = reverse
        rows = []
        for item in tree.get_children(""):
            val = tree.set(item, col_id)
            if parse_fn is not None:
                try:
                    val = parse_fn(val)
                except Exception:
                    val = 0
            rows.append((val, item))
        try:
            rows.sort(key=lambda r: r[0], reverse=reverse)
        except TypeError:
            rows.sort(key=lambda r: str(r[0]), reverse=reverse)
        for idx, (_, item) in enumerate(rows):
            tree.move(item, "", idx)
        repaint_tree(tree)

    tree.heading(col_id, command=_sort)
