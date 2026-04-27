import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk

import core.alerts as alerts

from ..base import Page
from ..constants import ACCENT, BG, CARD, DANGER, FONT_SM, MUTED, SUCCESS, TEXT
from ..helpers import capture_output, card, page_header


class DashboardPage(Page):
    def build(self):
        page_header(self, "Dashboard")

        cards_row = tk.Frame(self, bg=BG)
        cards_row.pack(fill="x", padx=24, pady=14)

        self._today_val = self._stat_card(cards_row, "Today", ACCENT)
        self._week_val = self._stat_card(cards_row, "This Week", "#8b5cf6")
        self._month_val = self._stat_card(cards_row, "This Month", "#f59e0b")
        self._safe_val = self._stat_card(cards_row, "Safe / Day", SUCCESS)

        tk.Label(
            self,
            text="Alerts & Notifications",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 12, "bold"),
        ).pack(anchor="w", padx=24, pady=(10, 4))
        alert_card = card(self)
        alert_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        header = tk.Frame(alert_card, bg=CARD)
        header.pack(fill="x", padx=12, pady=(12, 8))

        self._total_chip = self._alert_chip(header, "Total", ACCENT)
        self._alert_chip(header, "", CARD).pack_forget()
        self._warning_chip = self._alert_chip(header, "Warnings", "#f59e0b")
        self._ok_chip = self._alert_chip(header, "OK", SUCCESS)
        self._info_chip = self._alert_chip(header, "Info", MUTED)

        table_wrap = tk.Frame(alert_card, bg=CARD)
        table_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        columns = ("severity", "message")
        self.alert_tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=8)
        self.alert_tree.heading("severity", text="Severity")
        self.alert_tree.heading("message", text="Message")
        self.alert_tree.column("severity", width=120, anchor="center")
        self.alert_tree.column("message", width=840, anchor="w")

        self.alert_tree.tag_configure("warning", background="#fff7ed", foreground="#9a3412")
        self.alert_tree.tag_configure("alert", background="#fef2f2", foreground="#991b1b")
        self.alert_tree.tag_configure("ok", background="#ecfdf5", foreground="#065f46")
        self.alert_tree.tag_configure("info", background="#f8fafc", foreground="#334155")

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=self.alert_tree.yview)
        self.alert_tree.configure(yscrollcommand=scrollbar.set)
        self.alert_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _alert_chip(self, parent, label, color):
        chip = tk.Frame(parent, bg="#f8fafc", highlightbackground="#e5e7eb", highlightthickness=1)
        chip.pack(side="left", padx=(0, 8))
        tk.Label(chip, text=label.upper(), bg="#f8fafc", fg=MUTED, font=("Helvetica Neue", 8, "bold")).pack(
            padx=10,
            pady=(6, 0),
        )
        value = tk.Label(chip, text="0", bg="#f8fafc", fg=color, font=("Helvetica Neue", 14, "bold"))
        value.pack(padx=10, pady=(0, 6))
        return value

    def _parse_alert_lines(self, output):
        parsed = []
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("===") or line.startswith("---"):
                continue
            if line.startswith("[") and "]" in line:
                severity = line[1 : line.index("]")].strip().lower()
                message = line[line.index("]") + 1 :].strip()
                parsed.append((severity or "info", message or line))
            else:
                parsed.append(("info", line))
        return parsed

    def _render_alerts(self, output):
        lines = self._parse_alert_lines(output)
        if not lines:
            lines = [("ok", "No active alerts. You are all set.")]

        self.alert_tree.delete(*self.alert_tree.get_children())

        totals = {"alert": 0, "warning": 0, "ok": 0, "info": 0}
        for severity, message in lines:
            normalized = severity if severity in totals else "info"
            totals[normalized] += 1
            self.alert_tree.insert("", "end", values=(normalized.upper(), message), tags=(normalized,))

        total_count = sum(totals.values())
        self._total_chip.config(text=str(total_count))
        self._warning_chip.config(text=str(totals["warning"] + totals["alert"]))
        self._ok_chip.config(text=str(totals["ok"]))
        self._info_chip.config(text=str(totals["info"]))

    def _stat_card(self, parent, label, accent_color):
        outer = tk.Frame(parent, bg=accent_color)
        outer.pack(side="left", fill="both", expand=True, padx=5)

        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="both", expand=True, padx=0, pady=(3, 0))

        tk.Label(
            inner,
            text=label.upper(),
            bg=CARD,
            fg=MUTED,
            font=("Helvetica Neue", 9, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 2))
        value_label = tk.Label(
            inner,
            text="HK$0.00",
            bg=CARD,
            fg=accent_color,
            font=("Helvetica Neue", 22, "bold"),
        )
        value_label.pack(anchor="w", padx=14, pady=(0, 14))
        return value_label

    def load(self):
        transactions = alerts.read_transactions_csv()
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        week_cutoff = today - timedelta(days=6)

        today_total = 0.0
        week_total = 0.0
        month_total = 0.0
        for row in transactions:
            try:
                date_value = datetime.strptime(row["Date"], "%Y-%m-%d")
                amount = float(row["Amount"])
            except (ValueError, KeyError):
                continue
            if date_value >= today:
                today_total += amount
            if date_value >= week_cutoff:
                week_total += amount
            if date_value.year == today.year and date_value.month == today.month:
                month_total += amount

        self._today_val.config(text=f"HK${today_total:.2f}")
        self._week_val.config(text=f"HK${week_total:.2f}")
        self._month_val.config(text=f"HK${month_total:.2f}")

        budgets = alerts.read_budget_csv()
        total_budget = sum(amount for (_, period), amount in budgets.items() if period == "monthly")
        days_left = max(1, alerts._days_in_month(today) - today.day)
        safe_day = (total_budget - month_total) / days_left if total_budget else 0.0
        self._safe_val.config(text=f"HK${safe_day:.2f}", fg=SUCCESS if safe_day >= 0 else DANGER)

        output = capture_output(alerts.check_all_alerts)
        self._render_alerts(output)