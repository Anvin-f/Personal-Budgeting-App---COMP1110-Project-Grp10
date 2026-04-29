"""Settings page: API key, profile, dark mode, preferences."""

import tkinter as tk

import Backend.settings as app_settings

from ..base import Page
from ..constants import BG, BORDER, CARD, FONT, FONT_H, FONT_FAMILY, TEXT
from ..helpers import button, card, page_header


class SettingsPage(Page):
    def build(self):
        page_header(self, "⚙️  Settings")

        wrapper = card(self)
        wrapper.pack(fill="both", expand=True, padx=24, pady=(12, 18))

        scroll_container = tk.Frame(wrapper, bg=CARD)
        scroll_container.pack(fill="both", expand=True)

        self._settings_canvas = tk.Canvas(
            scroll_container, bg=CARD, highlightthickness=0, bd=0,
        )
        self._settings_canvas.pack(side="left", fill="both", expand=True)

        settings_scrollbar = tk.Scrollbar(
            scroll_container, orient="vertical",
            command=self._settings_canvas.yview,
        )
        settings_scrollbar.pack(side="right", fill="y")
        self._settings_canvas.configure(yscrollcommand=settings_scrollbar.set)

        form = tk.Frame(self._settings_canvas, bg=CARD)
        self._canvas_window = self._settings_canvas.create_window(
            (0, 0), window=form, anchor="nw",
        )
        form.bind(
            "<Configure>",
            lambda _e: self._settings_canvas.configure(
                scrollregion=self._settings_canvas.bbox("all"),
            ),
        )
        self._settings_canvas.bind("<Configure>", self._on_canvas_resize)
        self._settings_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ── AI Assistant ────────────────────────────────────────────────────
        tk.Label(
            form, text="AI Assistant",
            bg=CARD, fg=TEXT, font=(FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))
        tk.Frame(form, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 10))

        api_row = tk.Frame(form, bg=CARD)
        api_row.pack(fill="x", padx=16, pady=(4, 8))
        tk.Label(
            api_row, text="DeepSeek API Key",
            bg=CARD, fg=TEXT, font=(FONT_FAMILY, 10, "bold"), anchor="w",
        ).pack(anchor="w")
        tk.Label(
            api_row,
            text="Required for AI Assistant chat. Stored locally only.",
            bg=CARD, fg="#6b7280", font=(FONT_FAMILY, 9), anchor="w",
        ).pack(anchor="w", padx=(24, 0), pady=(0, 4))

        key_entry_frame = tk.Frame(api_row, bg=CARD)
        key_entry_frame.pack(anchor="w", padx=(24, 0), fill="x")
        self.api_key_var = tk.StringVar()
        self.api_key_entry = tk.Entry(
            key_entry_frame, textvariable=self.api_key_var,
            font=(FONT_FAMILY, 10),
            bg="#f3f4f6", fg=TEXT,
            bd=0, highlightbackground=BORDER, highlightthickness=1,
            relief="flat", show="*", width=48,
        )
        self.api_key_entry.pack(side="left", ipady=6, padx=(0, 8))

        self._show_key = False
        self.toggle_btn = tk.Button(
            key_entry_frame, text="Show",
            bg="#e5e7eb", fg=TEXT, font=(FONT_FAMILY, 9),
            bd=0, cursor="hand2", relief="flat", padx=8, pady=4,
            command=self._toggle_key_visibility,
        )
        self.toggle_btn.pack(side="left")

        tk.Frame(form, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 10))

        # ── Profile ──────────────────────────────────────────────────────────
        tk.Label(
            form, text="👤  Personal Profile",
            bg=CARD, fg=TEXT, font=(FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=16, pady=(4, 6))
        tk.Frame(form, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 10))

        self.profile_name_var = tk.StringVar(value="")
        self._text_field(form, "Your Name", "Optional. Used in AI analysis.", self.profile_name_var)

        self.profile_job_var = tk.StringVar(value="")
        self._text_field(form, "Job/Profession", "E.g., Software Engineer, Teacher.", self.profile_job_var)

        self.profile_monthly_income_var = tk.StringVar(value="")
        self._text_field(form, "Monthly Income (HK$)", "E.g., 30000.", self.profile_monthly_income_var)

        tk.Frame(form, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 10))

        # ── Appearance ──────────────────────────────────────────────────────
        tk.Label(
            form, text="Appearance & Preferences",
            bg=CARD, fg=TEXT, font=(FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=16, pady=(4, 6))
        tk.Frame(form, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 10))

        self.dark_mode_var = tk.BooleanVar(value=False)
        self.compact_tables_var = tk.BooleanVar(value=False)
        self.show_filter_chips_var = tk.BooleanVar(value=True)
        self.confirm_delete_var = tk.BooleanVar(value=True)

        self._check(form, "Dark Mode", "Use a darker application theme.", self.dark_mode_var)
        self._check(form, "Compact Tables", "Reduce table row height.", self.compact_tables_var)
        self._check(form, "Show Filter Chips", "Display active filter chips in Transactions.", self.show_filter_chips_var)
        self._check(form, "Confirm Before Delete", "Ask before deleting records.", self.confirm_delete_var)

        self.status_label = tk.Label(
            form, text="", bg=CARD, fg="#6b7280",
            font=(FONT_FAMILY, 9, "bold"),
        )
        self.status_label.pack(anchor="w", padx=16, pady=(8, 0))

        btn_row = tk.Frame(form, bg=CARD)
        btn_row.pack(anchor="w", padx=16, pady=(12, 16))
        button(btn_row, "✅  Apply", self._apply, "#3b82f6").pack(side="left", padx=(0, 8))
        button(btn_row, "🔄  Reset", self._reset, "#6b7280").pack(side="left", padx=(0, 8))
        button(btn_row, "📂  Open Data Folder", self._open_data_folder, "#374151").pack(side="left")

    def _on_canvas_resize(self, event):
        self._settings_canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self._settings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _check(self, parent, title, description, variable):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", padx=16, pady=(4, 4))
        tk.Checkbutton(
            row, text=title, variable=variable,
            bg=CARD, fg=TEXT, font=(FONT_FAMILY, 10, "bold"),
            activebackground=CARD, activeforeground=TEXT,
            selectcolor=CARD, anchor="w", relief="flat", bd=0,
            highlightthickness=0, padx=2, pady=2,
        ).pack(anchor="w")
        tk.Label(
            row, text=description, bg=CARD, fg="#6b7280",
            font=(FONT_FAMILY, 9), wraplength=680,
            justify="left", anchor="w",
        ).pack(anchor="w", padx=(24, 0))

    def _text_field(self, parent, title, description, variable):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", padx=16, pady=(4, 8))
        tk.Label(
            row, text=title, bg=CARD, fg=TEXT,
            font=(FONT_FAMILY, 10, "bold"), anchor="w",
        ).pack(anchor="w")
        tk.Label(
            row, text=description, bg=CARD, fg="#6b7280",
            font=(FONT_FAMILY, 9), anchor="w",
        ).pack(anchor="w", padx=(24, 0), pady=(0, 4))
        entry = tk.Entry(
            row, textvariable=variable, font=(FONT_FAMILY, 10),
            bg="#f3f4f6", fg=TEXT,
            bd=0, highlightbackground=BORDER, highlightthickness=1,
            relief="flat", width=48,
        )
        entry.pack(anchor="w", padx=(24, 0), ipady=6)

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
        self.profile_name_var.set(settings.get("profile_name", ""))
        self.profile_job_var.set(settings.get("profile_job", ""))
        self.profile_monthly_income_var.set(settings.get("profile_monthly_income", ""))

    def _apply(self):
        app_settings.write_settings({
            "api_key": self.api_key_var.get().strip(),
            "dark_mode": self.dark_mode_var.get(),
            "compact_tables": self.compact_tables_var.get(),
            "show_filter_chips": self.show_filter_chips_var.get(),
            "confirm_delete": self.confirm_delete_var.get(),
            "profile_name": self.profile_name_var.get().strip(),
            "profile_job": self.profile_job_var.get().strip(),
            "profile_monthly_income": self.profile_monthly_income_var.get().strip(),
        })
        top = self.winfo_toplevel()
        if hasattr(top, "apply_runtime_settings"):
            top.apply_runtime_settings(app_settings.read_settings())
            self.status_label.config(text="Settings applied.")
        else:
            self.status_label.config(text="Settings saved. Restart if needed.")

    def _reset(self):
        defaults = app_settings.write_settings(app_settings.DEFAULT_SETTINGS)
        self.api_key_var.set(defaults.get("api_key", ""))
        self.dark_mode_var.set(defaults["dark_mode"])
        self.compact_tables_var.set(defaults["compact_tables"])
        self.show_filter_chips_var.set(defaults["show_filter_chips"])
        self.confirm_delete_var.set(defaults["confirm_delete"])
        self.profile_name_var.set(defaults.get("profile_name", ""))
        self.profile_job_var.set(defaults.get("profile_job", ""))
        self.profile_monthly_income_var.set(defaults.get("profile_monthly_income", ""))
        top = self.winfo_toplevel()
        if hasattr(top, "apply_runtime_settings"):
            top.apply_runtime_settings(defaults)
        self.status_label.config(text="Defaults restored.")

    def _open_data_folder(self):
        """Open the data directory in the system file explorer."""
        import os
        import subprocess
        import sys

        data_dir = os.path.abspath("data")
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(data_dir)
        elif sys.platform == "darwin":
            subprocess.run(["open", data_dir])
        else:
            subprocess.run(["xdg-open", data_dir])
