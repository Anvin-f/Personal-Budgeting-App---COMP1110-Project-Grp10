import tkinter as tk
from tkinter import ttk

from .constants import ACCENT, BG, BORDER, CARD, FONT, SIDEBAR, SIDEBAR_FONT, TEXT
from .helpers import button
from .pages import AnalysisPage, BudgetPage, DashboardPage, TagsPage, TransactionsPage


class BudgetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Budget Tracker")
        self.geometry("1180x750")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._apply_styles()
        self._build_layout()

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=0)
        style.configure(
            "TNotebook.Tab",
            font=("Helvetica Neue", 10, "bold"),
            padding=[16, 8],
            background="#e5e7eb",
            foreground=TEXT,
        )
        style.map("TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", ACCENT)])

        style.configure(
            "Treeview",
            font=FONT,
            rowheight=32,
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            font=("Helvetica Neue", 10, "bold"),
            background="#f3f4f6",
            foreground=TEXT,
            relief="flat",
            padding=(8, 6),
        )
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])

        style.configure("TScrollbar", background=BORDER, troughcolor=BG, borderwidth=0, arrowsize=12)
        style.configure("TCombobox", font=FONT, foreground=TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", CARD)])

    def _build_layout(self):
        sidebar = tk.Frame(self, bg=SIDEBAR, width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo_frame = tk.Frame(sidebar, bg=SIDEBAR)
        logo_frame.pack(fill="x", pady=(24, 8))
        tk.Label(
            logo_frame,
            text="Budget",
            bg=SIDEBAR,
            fg="white",
            font=("Helvetica Neue", 17, "bold"),
        ).pack(anchor="w", padx=18)
        tk.Label(
            logo_frame,
            text="Tracker",
            bg=SIDEBAR,
            fg=ACCENT,
            font=("Helvetica Neue", 17, "bold"),
        ).pack(anchor="w", padx=18)

        tk.Frame(sidebar, bg="#374151", height=1).pack(fill="x", padx=14, pady=(4, 12))

        self.notebook = ttk.Notebook(self, style="TNotebook")
        self.notebook.pack(side="left", fill="both", expand=True)

        page_definitions = [
            ("Dashboard", DashboardPage),
            ("Transactions", TransactionsPage),
            ("Tags", TagsPage),
            ("Budgets", BudgetPage),
            ("Analysis", AnalysisPage),
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
                bg=SIDEBAR,
                fg="#d1d5db",
                font=SIDEBAR_FONT,
                bd=0,
                activebackground="#1f2937",
                activeforeground="white",
                cursor="hand2",
                anchor="w",
                relief="flat",
                command=lambda index=index: self._select_tab(index),
            )
            button_widget.pack(fill="x", padx=0, pady=1, ipady=8)
            self._nav_buttons.append(button_widget)

        self._select_tab(0)

        tk.Frame(sidebar, bg=SIDEBAR).pack(fill="both", expand=True)
        tk.Frame(sidebar, bg="#374151", height=1).pack(fill="x", padx=14, pady=(0, 10))
        button(sidebar, "↻  Refresh All", self._refresh_all, color="#1f2937", fg="#d1d5db").pack(
            fill="x",
            padx=14,
            pady=(0, 20),
            ipady=4,
        )

    def _select_tab(self, index):
        self.notebook.select(index)
        for button_index, button_widget in enumerate(self._nav_buttons):
            if button_index == index:
                button_widget.config(bg="#1f2937", fg="white", font=("Helvetica Neue", 11, "bold"))
            else:
                button_widget.config(bg=SIDEBAR, fg="#9ca3af", font=SIDEBAR_FONT)

    def _refresh_all(self):
        for page in self._pages.values():
            page.load()