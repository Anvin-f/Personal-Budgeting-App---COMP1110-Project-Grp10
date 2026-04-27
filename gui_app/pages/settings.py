import tkinter as tk

import core.settings as app_settings

from ..base import Page
from ..constants import BG, BORDER, CARD, FONT_H, TEXT
from ..helpers import button, card, page_header


class SettingsPage(Page):
    def build(self):
        page_header(self, "⚙️  Settings")

        wrapper = card(self)
        wrapper.pack(fill="both", expand=True, padx=24, pady=(12, 18))

        # AI Assistant section
        tk.Label(
            wrapper,
            text="AI Assistant",
            bg=CARD,
            fg=TEXT,
            font=("Helvetica Neue", 13, "bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))
        tk.Frame(wrapper, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 10))

        api_row = tk.Frame(wrapper, bg=CARD)
        api_row.pack(fill="x", padx=16, pady=(4, 8))
        tk.Label(
            api_row,
            text="DeepSeek API Key",
            bg=CARD,
            fg=TEXT,
            font=("Helvetica Neue", 10, "bold"),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            api_row,
            text="Required to use the AI Assistant chat. Your key is stored locally.",
            bg=CARD,
            fg="#6b7280",
            font=("Helvetica Neue", 9),
            anchor="w",
        ).pack(anchor="w", padx=(24, 0), pady=(0, 4))

        key_entry_frame = tk.Frame(api_row, bg=CARD)
        key_entry_frame.pack(anchor="w", padx=(24, 0), fill="x")
        self.api_key_var = tk.StringVar()
        self.api_key_entry = tk.Entry(
            key_entry_frame,
            textvariable=self.api_key_var,
            font=("Helvetica Neue", 10),
            bg="#f3f4f6",
            fg=TEXT,
            bd=0,
            highlightbackground=BORDER,
            highlightthickness=1,
            relief="flat",
            show="*",
            width=48,
        )
        self.api_key_entry.pack(side="left", ipady=6, padx=(0, 8))

        self._show_key = False
        self.toggle_btn = tk.Button(
            key_entry_frame,
            text="Show",
            bg="#e5e7eb",
            fg=TEXT,
            font=("Helvetica Neue", 9),
            bd=0,
            cursor="hand2",
            relief="flat",
            padx=8,
            pady=4,
            command=self._toggle_key_visibility,
        )
        self.toggle_btn.pack(side="left")

        tk.Frame(wrapper, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 10))

        # Appearance section
        tk.Label(
            wrapper,
            text="Appearance & Preferences",
            bg=CARD,
            fg=TEXT,
            font=("Helvetica Neue", 13, "bold"),
        ).pack(anchor="w", padx=16, pady=(4, 6))
        tk.Frame(wrapper, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 10))

        self.dark_mode_var = tk.BooleanVar(value=False)
        self.compact_tables_var = tk.BooleanVar(value=False)
        self.show_filter_chips_var = tk.BooleanVar(value=True)
        self.confirm_delete_var = tk.BooleanVar(value=True)

        self._check(
            wrapper,
            "Dark Mode",
            "Use a darker application theme.",
            self.dark_mode_var,
        )
        self._check(
            wrapper,
            "Compact Tables",
            "Reduce table row height to display more rows.",
            self.compact_tables_var,
        )
        self._check(
            wrapper,
            "Show Filter Chips",
            "Display active filter chips in Transactions.",
            self.show_filter_chips_var,
        )
        self._check(
            wrapper,
            "Confirm Before Delete",
            "Ask for confirmation before deleting records.",
            self.confirm_delete_var,
        )

        self.status_label = tk.Label(
            wrapper,
            text="",
            bg=CARD,
            fg="#6b7280",
            font=("Helvetica Neue", 9, "bold"),
        )
        self.status_label.pack(anchor="w", padx=16, pady=(8, 0))

        btn_row = tk.Frame(wrapper, bg=CARD)
        btn_row.pack(anchor="w", padx=16, pady=(12, 16))
        button(btn_row, "✅  Apply", self._apply, "#3b82f6").pack(side="left", padx=(0, 8))
        button(btn_row, "🔄  Reset", self._reset, "#6b7280").pack(side="left")

    def _check(self, parent, title, description, variable):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", padx=16, pady=(4, 4))

        tk.Checkbutton(
            row,
            text=title,
            variable=variable,
            bg=CARD,
            fg=TEXT,
            font=("Helvetica Neue", 10, "bold"),
            activebackground=CARD,
            activeforeground=TEXT,
            selectcolor=CARD,
            anchor="w",
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=2,
            pady=2,
        ).pack(anchor="w")
        tk.Label(
            row,
            text=description,
            bg=CARD,
            fg="#6b7280",
            font=("Helvetica Neue", 9),
            wraplength=680,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=(24, 0))

    def _toggle_key_visibility(self):
        self._show_key = not self._show_key
        self.api_key_entry.configure(show="" if self._show_key else "*")
        self.toggle_btn.configure(text="Hide" if self._show_key else "Show")

    def load(self):
        settings = app_settings.read_settings()
        self.api_key_var.set(settings.get("api_key", ""))
        self.dark_mode_var.set(settings.get("dark_mode", False))
        self.compact_tables_var.set(settings.get("compact_tables", False))
        self.show_filter_chips_var.set(settings.get("show_filter_chips", True))
        self.confirm_delete_var.set(settings.get("confirm_delete", True))
        self.status_label.config(text="")

    def _apply(self):
        updated = app_settings.write_settings(
            {
                "api_key": self.api_key_var.get().strip(),
                "dark_mode": self.dark_mode_var.get(),
                "compact_tables": self.compact_tables_var.get(),
                "show_filter_chips": self.show_filter_chips_var.get(),
                "confirm_delete": self.confirm_delete_var.get(),
            }
        )
        top = self.winfo_toplevel()
        if hasattr(top, "apply_runtime_settings"):
            top.apply_runtime_settings(updated)
            self.status_label.config(text="Settings applied.")
        else:
            self.status_label.config(text="Settings saved. Restart app if needed.")

    def _reset(self):
        defaults = app_settings.write_settings(app_settings.DEFAULT_SETTINGS)
        self.api_key_var.set(defaults.get("api_key", ""))
        self.dark_mode_var.set(defaults["dark_mode"])
        self.compact_tables_var.set(defaults["compact_tables"])
        self.show_filter_chips_var.set(defaults["show_filter_chips"])
        self.confirm_delete_var.set(defaults["confirm_delete"])
        top = self.winfo_toplevel()
        if hasattr(top, "apply_runtime_settings"):
            top.apply_runtime_settings(defaults)
        self.status_label.config(text="Defaults restored.")
