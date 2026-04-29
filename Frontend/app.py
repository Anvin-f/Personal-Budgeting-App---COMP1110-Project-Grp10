"""Main Tkinter application window and navigation."""
import tkinter as tk
from tkinter import ttk

import Backend.settings as app_settings
from .constants import (
    ACCENT, BG, BORDER, CARD, DARK_BG, DARK_BORDER, DARK_CARD,
    DARK_MUTED, DARK_SIDEBAR, DARK_TEXT, FONT, SIDEBAR,
    SIDEBAR_FONT, TEXT, MUTED, FONT_FAMILY,
)
from .helpers import button
from .pages import (
    AnalysisPage, BudgetPage, ChatbotPage, DashboardPage,
    SettingsPage, SummaryPage, TagsPage, TransactionsPage,
)


class BudgetApp(tk.Tk):
    """Root window that owns the sidebar, notebook, and theme switching."""

    def __init__(self):
        super().__init__()
        self.settings = app_settings.read_settings()
        self._dark = bool(self.settings.get("dark_mode", False))
        self._pal = self._palette(self._dark)
        self.title("Personal Budget Tracker")
        self.geometry("1280x800")
        self.configure(bg=self._pal["bg"])
        self.resizable(True, True)
        self.state("zoomed")
        self._apply_styles()

        # Sidebar alert badge state
        self._pending_alerts = []      # new alert lines for badge
        self._alert_cleared = False
        self._last_alert_count = 0
        self._popup = None

        self._build_layout()
        self._retheme_widgets()

        # Global click listener for popup dismissal (only active when popup exists)
        self.bind("<Button-1>", self._on_global_click, add="+")

    # ── palette ────────────────────────────────────────────────────────────
    def _palette(self, dark):
        """Return dict of runtime colour tokens for light or dark mode."""
        if dark:
            return {
                "bg": DARK_BG, "card": DARK_CARD, "text": DARK_TEXT,
                "muted": DARK_MUTED, "border": DARK_BORDER,
                "sidebar": DARK_SIDEBAR, "sidebar_active": "#1e293b",
                "sidebar_text": "#cbd5e1",
            }
        return {
            "bg": BG, "card": CARD, "text": TEXT,
            "muted": MUTED, "border": BORDER,
            "sidebar": SIDEBAR, "sidebar_active": "#1f2937",
            "sidebar_text": "#d1d5db",
        }

    # ── ttk styles ─────────────────────────────────────────────────────────
    def _apply_styles(self):
        """Configure ttk styles for the whole app."""
        style = ttk.Style()
        style.theme_use("clam")
        row_height = 28 if self.settings.get("compact_tables", False) else 36

        style.layout("TNotebook.Tab", [])
        style.configure("TNotebook", background=self._pal["bg"], borderwidth=0, tabmargins=0)
        style.configure("TNotebook.Tab", font=(FONT_FAMILY, 10, "bold"),
                        padding=[16, 8], background=self._pal["border"],
                        foreground=self._pal["text"])
        style.map("TNotebook.Tab",
                  background=[("selected", self._pal["card"])],
                  foreground=[("selected", ACCENT)])

        style.configure("Treeview", font=FONT, rowheight=row_height,
                        background=self._pal["card"], fieldbackground=self._pal["card"],
                        foreground=self._pal["text"], borderwidth=0)
        style.configure("Treeview.Heading", font=(FONT_FAMILY, 10, "bold"),
                        background=self._pal["border"], foreground=self._pal["text"],
                        relief="flat", padding=(8, 6))
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        style.configure("TScrollbar", background=self._pal["border"],
                        troughcolor=self._pal["bg"], borderwidth=0, arrowsize=12)
        style.configure("TCombobox", font=FONT, foreground=self._pal["text"])
        style.map("TCombobox", fieldbackground=[("readonly", self._pal["card"])])

    # ── layout ─────────────────────────────────────────────────────────────
    def _build_layout(self):
        """Build the sidebar, notebook, and alert badge."""
        sidebar = tk.Frame(self, bg=self._pal["sidebar"], width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.sidebar = sidebar

        # logo
        logo_frame = tk.Frame(sidebar, bg=self._pal["sidebar"])
        logo_frame.pack(fill="x", pady=(24, 8))
        tk.Label(logo_frame, text="Budget", bg=self._pal["sidebar"],
                 fg=self._pal["sidebar_text"], font=(FONT_FAMILY, 18, "bold")).pack(anchor="w", padx=18)
        tk.Label(logo_frame, text="Tracker", bg=self._pal["sidebar"],
                 fg=ACCENT, font=(FONT_FAMILY, 18, "bold")).pack(anchor="w", padx=18)

        tk.Frame(sidebar, bg=self._pal["border"], height=1).pack(fill="x", padx=14, pady=(4, 12))

        # Alert badge area
        alert_frame = tk.Frame(sidebar, bg=self._pal["sidebar"])
        alert_frame.pack(fill="x", padx=14, pady=(4, 4))
        self.alert_icon = tk.Label(
            alert_frame,
            text="🔔 0",
            bg=self._pal["sidebar"],
            fg=self._pal["sidebar_text"],
            font=(FONT_FAMILY, 10, "bold"),
            cursor="hand2",
            anchor="w",
        )
        self.alert_icon.pack(side="left", padx=(2, 0))
        self.alert_icon.bind("<Button-1>", lambda e: self.show_alert_popup())

        # notebook
        self.notebook = ttk.Notebook(self, style="TNotebook")
        self.notebook.pack(side="left", fill="both", expand=True)

        page_defs = [
            ("🏠  Dashboard", DashboardPage),
            ("💳  Transactions", TransactionsPage),
            ("🏷️  Tags", TagsPage),
            ("💰  Budgets", BudgetPage),
            ("📈  Analysis", AnalysisPage),
            ("📊  Summary", SummaryPage),
            ("💬  AI Assistant", ChatbotPage),
            ("⚙️  Settings", SettingsPage),
        ]
        self._pages = {}
        for name, page_class in page_defs:
            page = page_class(self.notebook)
            self.notebook.add(page, text=f"  {name}  ")
            self._pages[name] = page

        # nav buttons
        self._nav_buttons = []
        import platform
        is_mac = platform.system() == "Darwin"
        for index, (name, _) in enumerate(page_defs):
            if is_mac:
                btn = tk.Label(sidebar, text=f"    {name}",
                               bg=self._pal["sidebar"], fg=self._pal["sidebar_text"],
                               font=SIDEBAR_FONT, cursor="hand2", anchor="w",
                               relief="flat", padx=0, pady=8)
                btn.bind("<Button-1>", lambda e, idx=index: self._select_tab(idx))
            else:
                btn = tk.Button(sidebar, text=f"    {name}",
                                bg=self._pal["sidebar"], fg=self._pal["sidebar_text"],
                                font=SIDEBAR_FONT, bd=0,
                                activebackground=self._pal["sidebar_active"],
                                activeforeground="white", cursor="hand2",
                                anchor="w", relief="flat",
                                highlightbackground=self._pal["sidebar"],
                                highlightthickness=0,
                                command=lambda idx=index: self._select_tab(idx))
            btn._nav_btn = True
            btn.pack(fill="x", padx=0, pady=1)
            self._nav_buttons.append(btn)

        self._select_tab(0)

        tk.Frame(sidebar, bg=self._pal["sidebar"]).pack(fill="both", expand=True)
        tk.Frame(sidebar, bg=self._pal["border"], height=1).pack(fill="x", padx=14, pady=(0, 10))
        button(sidebar, "🔄  Refresh", self._refresh_all,
               color=self._pal["sidebar_active"],
               fg=self._pal["sidebar_text"]).pack(fill="x", padx=14, pady=(0, 20), ipady=4)

    def _select_tab(self, index):
        """Switch the notebook to the given tab index."""
        self.notebook.select(index)
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.config(bg=self._pal["sidebar_active"], fg="white",
                           font=(FONT_FAMILY, 11, "bold"),
                           highlightbackground=self._pal["sidebar_active"])
            else:
                btn.config(bg=self._pal["sidebar"], fg=self._pal["sidebar_text"],
                           font=SIDEBAR_FONT,
                           highlightbackground=self._pal["sidebar"])
        page_names = list(self._pages.keys())
        if 0 <= index < len(page_names):
            self._pages[page_names[index]].load()
        self.update_idletasks()

    def _refresh_all(self):
        """Refresh all pages."""
        for page in self._pages.values():
            page.load()

    # ── alert badge methods ────────────────────────────────────────────────
    def update_alert_badge(self, new_lines):
        """
        Update sidebar alert icon.
        new_lines is list of (severity, message).
        Cleared state is kept until new alert count exceeds last seen count.
        """
        self._pending_alerts = new_lines
        count = len(new_lines)

        if self._alert_cleared:
            if count > self._last_alert_count:
                self._alert_cleared = False
                self._last_alert_count = count
            else:
                # stay cleared
                self.alert_icon.config(text="🔔 0", fg=self._pal["sidebar_text"])
                return
        else:
            self._last_alert_count = count

        # update badge colour
        color = self._pal["sidebar_text"]
        if count >= 3:
            color = "#ef4444"
        elif count >= 1:
            color = "#f59e0b"
        self.alert_icon.config(text=f"🔔 {count}", fg=color)

    def show_alert_popup(self):
        """Display a floating popup with current new alerts."""
        # Destroy existing popup
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()

        # Mark as cleared (badge will show 0)
        self._alert_cleared = True
        self.alert_icon.config(text="🔔 0", fg=self._pal["sidebar_text"])

        popup = tk.Toplevel(self)
        popup.title("Alerts")
        popup.configure(bg=self._pal["card"])
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        x = self.winfo_rootx() + 190 + 10
        y = self.winfo_rooty() + 100
        popup.geometry(f"400x200+{x}+{y}")

        # header
        tk.Label(popup, text="New Alerts", bg=self._pal["card"],
                 fg=self._pal["text"], font=(FONT_FAMILY, 11, "bold")).pack(padx=12, pady=(8, 4))

        frame = tk.Frame(popup, bg=self._pal["card"])
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        if not self._pending_alerts:
            tk.Label(frame, text="No new alerts", bg=self._pal["card"],
                     fg=self._pal["muted"], font=(FONT_FAMILY, 9)).pack(pady=20)
        else:
            visible = self._pending_alerts[:5]
            for sev, msg in visible:
                line_frame = tk.Frame(frame, bg=self._pal["card"], cursor="hand2")
                line_frame.pack(fill="x", pady=2)
                color = "#ef4444" if sev == "alert" else "#f59e0b" if sev == "warning" else self._pal["text"]
                tk.Label(line_frame, text=f"• {msg}", bg=self._pal["card"],
                         fg=color, font=(FONT_FAMILY, 9), anchor="w",
                         wraplength=380, justify="left").pack(side="left")
                line_frame.bind("<Button-1>", lambda e: self._jump_to_dashboard())
                for child in line_frame.winfo_children():
                    child.bind("<Button-1>", lambda e: self._jump_to_dashboard())

        # close button
        tk.Button(popup, text="Close", command=popup.destroy,
                  bg=self._pal["border"], fg=self._pal["text"],
                  font=(FONT_FAMILY, 8), relief="flat",
                  cursor="hand2").pack(pady=(0, 6))

        self._popup = popup

    def _on_global_click(self, event):
        """Dismiss popup if user clicks outside it."""
        # Ignore clicks on the alert icon itself
        if event.widget is self.alert_icon:
            return

        if self._popup and self._popup.winfo_exists():
            try:
                widget = self._popup.winfo_containing(event.x_root, event.y_root)
                # If the click is outside the popup (not on popup or its children), close
                if not (widget is self._popup or widget in self._popup.winfo_children()):
                    self._popup.destroy()
            except:
                pass

    def _jump_to_dashboard(self):
        """Navigate to Dashboard tab."""
        for i, btn in enumerate(self._nav_buttons):
            if btn.cget("text").strip() == "🏠  Dashboard":
                self._select_tab(i)
                break
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()

    # ── runtime recolour ───────────────────────────────────────────────────
    def _retheme_widgets(self):
        """Walk all descendants and swap known colour tokens."""
        dark_palette = self._palette(True)
        color_groups = {
            "bg": {BG, dark_palette["bg"], "#f3f4f6", "#e5e7eb"},
            "card": {CARD, dark_palette["card"], "#f9fafb", "#f8fafc", "#ffffff"},
            "text": {TEXT, dark_palette["text"]},
            "muted": {"#6b7280", "#9ca3af", dark_palette["muted"]},
            "border": {BORDER, dark_palette["border"], "#374151", "#d1d5db", "#e5e7eb", "#f3f4f6"},
            "sidebar": {SIDEBAR, dark_palette["sidebar"]},
            "sidebar_text": {"#d1d5db", "#cbd5e1", "#9ca3af"},
            "sidebar_active": {"#1f2937", dark_palette["sidebar_active"]},
        }
        target = {
            "bg": self._pal["bg"], "card": self._pal["card"], "text": self._pal["text"],
            "muted": self._pal["muted"], "border": self._pal["border"],
            "sidebar": self._pal["sidebar"], "sidebar_text": self._pal["sidebar_text"],
            "sidebar_active": self._pal["sidebar_active"],
        }
        def _map_color(value):
            if value is None: return None
            s = str(value)
            for group, values in color_groups.items():
                if s in values:
                    return target[group]
            return None
        def _apply(widget):
            for opt in ("bg", "activebackground", "highlightbackground", "selectcolor"):
                try:
                    c = _map_color(widget.cget(opt))
                    if c is not None:
                        widget.configure(**{opt: c})
                except tk.TclError: pass
            for opt in ("fg", "activeforeground", "insertbackground"):
                try:
                    c = _map_color(widget.cget(opt))
                    if c is not None:
                        widget.configure(**{opt: c})
                except tk.TclError: pass
            for child in widget.winfo_children():
                _apply(child)
        _apply(self)

    def apply_runtime_settings(self, settings):
        """Apply settings from the Settings page."""
        self.settings = app_settings.write_settings(settings)
        self._dark = bool(self.settings.get("dark_mode", False))
        self._pal = self._palette(self._dark)
        self.configure(bg=self._pal["bg"])
        self._apply_styles()
        if hasattr(self, "sidebar"):
            self.sidebar.configure(bg=self._pal["sidebar"])
        self._refresh_all()
        self._retheme_widgets()
        self._fix_sidebar_bg()
        self._select_tab(self.notebook.index("current"))

    def _fix_sidebar_bg(self):
        """Force sidebar and its non-button descendants to use the sidebar background."""
        if not hasattr(self, "sidebar"): return
        color = self._pal["sidebar"]
        def set_bg(widget):
            if getattr(widget, "_is_action_button", False) or getattr(widget, "_nav_btn", False):
                return
            try:
                widget.configure(bg=color)
            except tk.TclError: pass
            for child in widget.winfo_children():
                set_bg(child)
        set_bg(self.sidebar)
