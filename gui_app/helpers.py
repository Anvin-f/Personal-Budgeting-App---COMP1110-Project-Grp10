import io
import sys
import tkinter as tk

import core.settings as app_settings
import core.tags as tags

from .constants import ACCENT, BG, BORDER, CARD, FONT_H, TEXT


def capture_output(fn, *args, **kwargs):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        fn(*args, **kwargs)
    finally:
        sys.stdout = old
    return buf.getvalue()


def card(parent, **kwargs):
    return tk.Frame(
        parent,
        bg=CARD,
        relief="flat",
        highlightbackground=BORDER,
        highlightthickness=1,
        **kwargs,
    )


def button(parent, text, command, color=ACCENT, fg="white", **kwargs):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg=fg,
        font=("Helvetica Neue", 10, "bold"),
        bd=0,
        cursor="hand2",
        activebackground=color,
        activeforeground=fg,
        relief="flat",
        padx=14,
        pady=7,
        **kwargs,
    )


def page_header(parent, title):
    wrapper = tk.Frame(parent, bg=BG)
    wrapper.pack(fill="x", padx=24, pady=(18, 0))
    tk.Label(wrapper, text=title, bg=BG, fg=TEXT, font=FONT_H).pack(anchor="w")
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 0))


def safe_read_tags():
    try:
        return tags.read_tag_csv()
    except Exception:
        return {}


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def zebra(tree):
    dark_mode = app_settings.read_settings().get("dark_mode", False)
    if dark_mode:
        odd_bg = "#263247"
        even_bg = "#1e293b"
        row_fg = "#e2e8f0"
    else:
        odd_bg = "#f9fafb"
        even_bg = CARD
        row_fg = TEXT

    tree.tag_configure("odd", background=odd_bg, foreground=row_fg)
    tree.tag_configure("even", background=even_bg, foreground=row_fg)


def repaint_tree(tree):
    for index, item_id in enumerate(tree.get_children()):
        tree.item(item_id, tags=("odd" if index % 2 else "even",))