import tkinter as tk
from datetime import datetime, timedelta
from tkinter import scrolledtext

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

        self.alert_box = scrolledtext.ScrolledText(
            alert_card,
            font=FONT_SM,
            bg=CARD,
            fg=TEXT,
            relief="flat",
            wrap="word",
            state="disabled",
            padx=8,
            pady=8,
        )
        self.alert_box.pack(fill="both", expand=True)

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
        self.alert_box.config(state="normal")
        self.alert_box.delete("1.0", "end")
        self.alert_box.insert("end", output or "No alerts.")
        self.alert_box.config(state="disabled")