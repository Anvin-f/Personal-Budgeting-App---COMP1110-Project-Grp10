"""Theme constants: colours, fonts, and cross-platform font detection."""

import platform
import tkinter as tk


_system = platform.system()
if _system == "Windows":
    FONT_FAMILY = "Segoe UI"
elif _system == "Darwin":
    FONT_FAMILY = "Helvetica Neue"
else:
    FONT_FAMILY = "Ubuntu"


# ── font tuples ──────────────────────────────────────────────────────────
FONT    = (FONT_FAMILY, 12)
FONT_H  = (FONT_FAMILY, 17, "bold")
FONT_SM = (FONT_FAMILY, 10)
SIDEBAR_FONT = (FONT_FAMILY, 11)

# ── light-theme palette ──────────────────────────────────────────────────
BG       = "#f5f7fa"
SIDEBAR  = "#111827"
CARD     = "#ffffff"
ACCENT   = "#3b82f6"
TEXT     = "#111827"
MUTED    = "#6b7280"
SUCCESS  = "#10b981"
DANGER   = "#ef4444"
BORDER   = "#d1d5db"

# ── dark-theme palette ───────────────────────────────────────────────────
DARK_BG       = "#0f172a"
DARK_SIDEBAR  = "#020617"
DARK_CARD     = "#1e293b"
DARK_TEXT     = "#f1f5f9"
DARK_MUTED    = "#94a3b8"
DARK_BORDER   = "#334155"