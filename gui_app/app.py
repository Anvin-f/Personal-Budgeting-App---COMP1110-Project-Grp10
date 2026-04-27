import tkinter as tk
from tkinter import ttk

import core.settings as app_settings

from .constants import ACCENT, BG, BORDER, CARD, FONT, SIDEBAR, SIDEBAR_FONT, TEXT
from .helpers import button
from .pages import AnalysisPage, BudgetPage, ChatbotPage, DashboardPage, SettingsPage, TagsPage, TransactionsPage


class BudgetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = app_settings.read_settings()
        self._current_palette = self._palette(self.settings.get("dark_mode", False))
        self.title("Personal Budget Tracker")
        self.geometry("1180x750")
        self.configure(bg=self._current_palette["bg"])
        self.resizable(True, True)
        self._apply_styles()
        self._build_layout()
        self._retheme_widgets()

    def _palette(self, dark_mode):
        if dark_mode:
            return {
                "bg": "#0f172a",
                "card": "#1e293b",
                "text": "#e2e8f0",
                "muted": "#94a3b8",
                "border": "#334155",
                "sidebar": "#0b1220",
                "sidebar_active": "#1e293b",
                "sidebar_text": "#cbd5e1",
            }
        return {
            "bg": BG,
            "card": CARD,
            "text": TEXT,
            "muted": "#6b7280",
            "border": BORDER,
            "sidebar": SIDEBAR,
            "sidebar_active": "#1f2937",
            "sidebar_text": "#d1d5db",
        }

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        row_height = 28 if self.settings.get("compact_tables", False) else 32

        style.layout("TNotebook.Tab", [])
        style.configure("TNotebook", background=self._current_palette["bg"], borderwidth=0, tabmargins=0)
        style.configure(
            "TNotebook.Tab",
            font=("Helvetica Neue", 10, "bold"),
            padding=[16, 8],
            background=self._current_palette["border"],
            foreground=self._current_palette["text"],
        )
        style.map("TNotebook.Tab", background=[("selected", self._current_palette["card"])], foreground=[("selected", ACCENT)])

        style.configure(
            "Treeview",
            font=FONT,
            rowheight=row_height,
            background=self._current_palette["card"],
            fieldbackground=self._current_palette["card"],
            foreground=self._current_palette["text"],
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            font=("Helvetica Neue", 10, "bold"),
            background=self._current_palette["border"],
            foreground=self._current_palette["text"],
            relief="flat",
            padding=(8, 6),
        )
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])

        style.configure("TScrollbar", background=self._current_palette["border"], troughcolor=self._current_palette["bg"], borderwidth=0, arrowsize=12)
        style.configure("TCombobox", font=FONT, foreground=self._current_palette["text"])
        style.map("TCombobox", fieldbackground=[("readonly", self._current_palette["card"])])

    def _build_layout(self):
        sidebar = tk.Frame(self, bg=self._current_palette["sidebar"], width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.sidebar = sidebar

        logo_frame = tk.Frame(sidebar, bg=self._current_palette["sidebar"])
        logo_frame.pack(fill="x", pady=(24, 8))
        tk.Label(
            logo_frame,
            text="Budget",
            bg=self._current_palette["sidebar"],
            fg="white",
            font=("Helvetica Neue", 17, "bold"),
        ).pack(anchor="w", padx=18)
        tk.Label(
            logo_frame,
            text="Tracker",
            bg=self._current_palette["sidebar"],
            fg=ACCENT,
            font=("Helvetica Neue", 17, "bold"),
        ).pack(anchor="w", padx=18)

        tk.Frame(sidebar, bg=self._current_palette["border"], height=1).pack(fill="x", padx=14, pady=(4, 12))

        self.notebook = ttk.Notebook(self, style="TNotebook")
        self.notebook.pack(side="left", fill="both", expand=True)

        page_definitions = [
            ("🏠  Dashboard", DashboardPage),
            ("💳  Transactions", TransactionsPage),
            ("🏷️  Tags", TagsPage),
            ("💰  Budgets", BudgetPage),
            ("📈  Analysis", AnalysisPage),
            ("💬  AI Assistant", ChatbotPage),
            ("⚙️  Settings", SettingsPage),
        ]
        self._pages = {}
        for name, page_class in page_definitions:
            page = page_class(self.notebook)
            self.notebook.add(page, text=f"  {name}  ")
            self._pages[name] = page

        self._nav_buttons = []
        for index, (name, _) in enumerate(page_definitions):
            button_widget = tk.Button(
                sidebar,
                text=f"    {name}",
                bg=self._current_palette["sidebar"],
                fg=self._current_palette["sidebar_text"],
                font=SIDEBAR_FONT,
                bd=0,
                activebackground=self._current_palette["sidebar_active"],
                activeforeground="white",
                cursor="hand2",
                anchor="w",
                relief="flat",
                command=lambda index=index: self._select_tab(index),
            )
            button_widget.pack(fill="x", padx=0, pady=1, ipady=8)
            self._nav_buttons.append(button_widget)

        self._select_tab(0)

        tk.Frame(sidebar, bg=self._current_palette["sidebar"]).pack(fill="both", expand=True)
        tk.Frame(sidebar, bg=self._current_palette["border"], height=1).pack(fill="x", padx=14, pady=(0, 10))
        button(sidebar, "🔄  Refresh", self._refresh_all, color=self._current_palette["sidebar_active"], fg=self._current_palette["sidebar_text"]).pack(
            fill="x",
            padx=14,
            pady=(0, 20),
            ipady=4,
        )

    def _select_tab(self, index):
        self.notebook.select(index)
        for button_index, button_widget in enumerate(self._nav_buttons):
            if button_index == index:
                button_widget.config(bg=self._current_palette["sidebar_active"], fg="white", font=("Helvetica Neue", 11, "bold"))
            else:
                button_widget.config(bg=self._current_palette["sidebar"], fg="#9ca3af", font=SIDEBAR_FONT)

    def _refresh_all(self):
        for page in self._pages.values():
            page.load()

    def _retheme_widgets(self):
        dark_palette = self._palette(True)
        color_groups = {
            "bg": {BG, dark_palette["bg"]},
            "card": {CARD, dark_palette["card"], "#f9fafb"},
            "text": {TEXT, dark_palette["text"]},
            "muted": {"#6b7280", "#9ca3af", dark_palette["muted"]},
            "border": {BORDER, dark_palette["border"], "#374151", "#f3f4f6"},
            "sidebar": {SIDEBAR, dark_palette["sidebar"]},
            "sidebar_text": {"#d1d5db", "#cbd5e1"},
            "sidebar_active": {"#1f2937", dark_palette["sidebar_active"]},
        }
        target = {
            "bg": self._current_palette["bg"],
            "card": self._current_palette["card"],
            "text": self._current_palette["text"],
            "muted": self._current_palette["muted"],
            "border": self._current_palette["border"],
            "sidebar": self._current_palette["sidebar"],
            "sidebar_text": self._current_palette["sidebar_text"],
            "sidebar_active": self._current_palette["sidebar_active"],
        }

        option_map = {
            "bg": ["bg", "activebackground", "highlightbackground", "selectcolor"],
            "fg": ["fg", "activeforeground", "insertbackground"],
        }

        def map_color(value):
            if value is None:
                return None
            value_text = str(value)
            for group, values in color_groups.items():
                if value_text in values:
                    return target[group]
            return None

        def apply_recursive(widget):
            for option in option_map["bg"]:
                try:
                    mapped = map_color(widget.cget(option))
                    if mapped is not None:
                        widget.configure(**{option: mapped})
                except tk.TclError:
                    pass
            for option in option_map["fg"]:
                try:
                    mapped = map_color(widget.cget(option))
                    if mapped is not None:
                        widget.configure(**{option: mapped})
                except tk.TclError:
                    pass
            for child in widget.winfo_children():
                apply_recursive(child)

        apply_recursive(self)

    def apply_runtime_settings(self, settings):
        self.settings = app_settings.write_settings(settings)
        self._current_palette = self._palette(self.settings.get("dark_mode", False))
        self.configure(bg=self._current_palette["bg"])
        self._apply_styles()
        if hasattr(self, "sidebar"):
            self.sidebar.configure(bg=self._current_palette["sidebar"])
        self._refresh_all()
        self._retheme_widgets()
        self._select_tab(self.notebook.index("current"))