import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import defaultdict

import Backend.alerts as alerts
import Backend.transaction as transaction

from ..base import Page
from ..helpers import capture_output, card, page_header, safe_read_tags
from ..constants import BG, CARD, DANGER, FONT_H, FONT_SM, MUTED, SUCCESS, TEXT, ACCENT, FONT_FAMILY


class DashboardPage(Page):
    def build(self):
        page_header(self, "🏠  Dashboard")

        # ── KPI CARDS ────────────────────────────────────────────────────
        kpi_container = tk.Frame(self, bg=BG)
        kpi_container.pack(fill="x", padx=24, pady=(14, 20))
        
        self._month_pct_label = None
        self._today_val, self._today_card = self._kpi_card(kpi_container, "Today", ACCENT, "💰")
        self._week_val, self._week_card = self._kpi_card(kpi_container, "This Week", "#8b5cf6", "📊")
        self._month_val, self._month_card = self._kpi_card(kpi_container, "This Month", "#f59e0b", "📈")
        self._safe_val, self._safe_card = self._kpi_card(kpi_container, "Budget Health", SUCCESS, "✓")

        # KPI click navigation
        self._today_card.bind("<Button-1>", lambda e: self._navigate_filtered("today"))
        self._week_card.bind("<Button-1>", lambda e: self._navigate_filtered("week"))
        self._month_card.bind("<Button-1>", lambda e: self._navigate_filtered("month"))
        self._safe_card.bind("<Button-1>", lambda e: self._navigate_tab("💰  Budgets"))

        # ── CHARTS SECTION ───────────────────────────────────────────────
        charts_container = tk.Frame(self, bg=BG)
        charts_container.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        # Left: Spending Trend Chart
        chart_left = card(charts_container)
        chart_left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        tk.Label(
            chart_left, text="7-Day Spending Trend",
            bg=CARD, fg=TEXT,
            font=(FONT_FAMILY, 11, "bold"),
        ).pack(anchor="w", padx=12, pady=(12, 8))

        self.fig_trend = Figure(figsize=(5, 3), dpi=75, facecolor=CARD, edgecolor="none")
        self.ax_trend = self.fig_trend.add_subplot(111, facecolor=CARD)
        self.canvas_trend = FigureCanvasTkAgg(self.fig_trend, chart_left)
        self.canvas_trend.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Right: Category Breakdown
        chart_right = card(charts_container)
        chart_right.pack(side="right", fill="both", expand=True, padx=(12, 0))

        tk.Label(
            chart_right, text="Category Breakdown (This Month)",
            bg=CARD, fg=TEXT,
            font=(FONT_FAMILY, 11, "bold"),
        ).pack(anchor="w", padx=12, pady=(12, 8))

        self.fig_pie = Figure(figsize=(5, 3), dpi=75, facecolor=CARD, edgecolor="none")
        self.ax_pie = self.fig_pie.add_subplot(111, facecolor=CARD)
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, chart_right)
        self.canvas_pie.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ── ALERTS SECTION ───────────────────────────────────────────────
        alert_label = tk.Label(
            self, text="Status & Alerts",
            bg=BG, fg=TEXT,
            font=(FONT_FAMILY, 12, "bold"),
        )
        alert_label.pack(anchor="w", padx=24, pady=(0, 8))

        alert_card = card(self)
        alert_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        header = tk.Frame(alert_card, bg=CARD)
        header.pack(fill="x", padx=12, pady=(12, 8))

        self._total_chip = self._alert_chip(header, "Total", ACCENT)
        self._warning_chip = self._alert_chip(header, "Warnings", "#f59e0b")
        self._ok_chip = self._alert_chip(header, "OK", SUCCESS)
        self._info_chip = self._alert_chip(header, "Info", MUTED)

        table_wrap = tk.Frame(alert_card, bg=CARD)
        table_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        columns = ("severity", "message")
        self.alert_tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=6)
        self.alert_tree.heading("severity", text="Severity")
        self.alert_tree.heading("message", text="Message")
        self.alert_tree.column("severity", width=120, anchor="center")
        self.alert_tree.column("message", width=840, anchor="w")

        self.alert_tree.tag_configure("warning", background="#fff7ed", foreground="#9a3412")
        self.alert_tree.tag_configure("alert", background="#fef2f2", foreground="#991b1b")
        self.alert_tree.tag_configure("ok", background="#ecfdf5", foreground="#065f46")
        self.alert_tree.tag_configure("info", background="#f8fafc", foreground="#334155")

        # Double-click alert → navigate to Budgets
        self.alert_tree.bind("<Double-1>", lambda e: self._navigate_tab("💰  Budgets"))

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=self.alert_tree.yview)
        self.alert_tree.configure(yscrollcommand=scrollbar.set)
        self.alert_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _kpi_card(self, parent, label, accent_color, icon):
        """Modern KPI card with icon and value. Returns (value_label, card_frame)."""
        card_frame = tk.Frame(parent, bg=CARD, relief="flat",
                              highlightbackground=accent_color, highlightthickness=2)
        card_frame.pack(side="left", fill="both", expand=True, padx=6, pady=4)

        top = tk.Frame(card_frame, bg=CARD)
        top.pack(fill="x", padx=16, pady=(16, 8))
        tk.Label(top, text=icon, bg=CARD, fg=accent_color,
                 font=(FONT_FAMILY, 24)).pack(side="left")
        tk.Label(top, text=label.upper(), bg=CARD, fg=MUTED,
                 font=(FONT_FAMILY, 8, "bold")).pack(side="left", padx=(12, 0), anchor="w")

        value_label = tk.Label(card_frame, text="HK$0.00", bg=CARD, fg=accent_color,
                               font=(FONT_FAMILY, 18, "bold"))
        value_label.pack(anchor="w", padx=16, pady=(0, 16))

        def _forward_click(event):
            card_frame.event_generate("<Button-1>", when="tail")

        def _make_clickable(widget):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", _forward_click, add="+")
            for child in widget.winfo_children():
                _make_clickable(child)

        _make_clickable(card_frame)

        return value_label, card_frame

    def _alert_chip(self, parent, label, color):
        chip = tk.Frame(parent, bg="#f8fafc", highlightbackground="#e5e7eb", highlightthickness=1)
        chip.pack(side="left", padx=(0, 8))
        tk.Label(chip, text=label.upper(), bg="#f8fafc", fg=MUTED,
                 font=(FONT_FAMILY, 8, "bold")).pack(padx=10, pady=(6, 0))
        value = tk.Label(chip, text="0", bg="#f8fafc", fg=color,
                         font=(FONT_FAMILY, 14, "bold"))
        value.pack(padx=10, pady=(0, 6))
        return value

    def _navigate_tab(self, tab_name):
        """Switch to the named sidebar tab."""
        top = self.winfo_toplevel()
        pages = getattr(top, "_pages", {})
        for i, btn in enumerate(getattr(top, "_nav_buttons", [])):
            if btn.cget("text").strip() == tab_name:
                top._select_tab(i)
                if tab_name in pages:
                    pages[tab_name].load()
                break

    def _navigate_filtered(self, period):
        """Jump to Transactions page with date filter set."""
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "today":
            from_d = today.strftime("%Y-%m-%d")
            to_d = from_d
        elif period == "week":
            from_d = (today - timedelta(days=6)).strftime("%Y-%m-%d")
            to_d = today.strftime("%Y-%m-%d")
        else:  # month
            from_d = today.replace(day=1).strftime("%Y-%m-%d")
            to_d = today.strftime("%Y-%m-%d")

        self._navigate_tab("💳  Transactions")
        top = self.winfo_toplevel()
        tx_page = getattr(top, "_pages", {}).get("💳  Transactions")
        if tx_page:
            tx_page.date_from_var.set(from_d)
            tx_page.date_to_var.set(to_d)
            tx_page._apply_search()

    def _parse_alert_lines(self, output):
        parsed = []
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("===") or line.startswith("---"):
                continue
            if line.startswith("[") and "]" in line:
                severity = line[1:line.index("]")].strip().lower()
                message = line[line.index("]") + 1:].strip()
                parsed.append((severity or "info", message or line))
            else:
                parsed.append(("info", line))
        return parsed

    def _update_alert_tags(self):
        """Update alert tree tag colours for the current theme."""
        top = self.winfo_toplevel()
        dark = getattr(top, "_dark", False)
        if dark:
            self.alert_tree.tag_configure("warning", background="#78350f", foreground="#fef3c7")
            self.alert_tree.tag_configure("alert", background="#7f1d1d", foreground="#fee2e2")
            self.alert_tree.tag_configure("ok", background="#064e3b", foreground="#d1fae5")
            self.alert_tree.tag_configure("info", background="#1e293b", foreground="#cbd5e1")
        else:
            self.alert_tree.tag_configure("warning", background="#fff7ed", foreground="#9a3412")
            self.alert_tree.tag_configure("alert", background="#fef2f2", foreground="#991b1b")
            self.alert_tree.tag_configure("ok", background="#ecfdf5", foreground="#065f46")
            self.alert_tree.tag_configure("info", background="#f8fafc", foreground="#334155")

    def _render_alerts(self, output):
        self._update_alert_tags()
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

    def _draw_spending_trend(self, days_data):
        """Draw 7-day spending trend as column chart."""
        self.ax_trend.clear()
        self.ax_trend.set_facecolor(CARD)

        if days_data:
            dates = [d[0].strftime("%a").upper() for d in days_data]
            amounts = [d[1] for d in days_data]
            colors = [ACCENT if amt > 0 else MUTED for amt in amounts]

            bars = self.ax_trend.bar(range(len(dates)), amounts, color=colors, width=0.7)
            self.ax_trend.set_xticks(range(len(dates)))
            self.ax_trend.set_xticklabels(dates, fontsize=8, color=TEXT)
            self.ax_trend.set_ylabel("Spending (HK$)", fontsize=9, color=MUTED)
            self.ax_trend.spines["top"].set_visible(False)
            self.ax_trend.spines["right"].set_visible(False)
            self.ax_trend.spines["left"].set_color(MUTED)
            self.ax_trend.spines["bottom"].set_color(MUTED)
            self.ax_trend.tick_params(colors=MUTED, labelsize=8)

            for bar, amt in zip(bars, amounts):
                height = bar.get_height()
                self.ax_trend.text(bar.get_x() + bar.get_width() / 2., height,
                                   f"HK${amt:.0f}", ha="center", va="bottom",
                                   fontsize=7, color=TEXT)
        else:
            self.ax_trend.text(0.5, 0.5, "No data", ha="center", va="center",
                               color=MUTED, transform=self.ax_trend.transAxes)

        self.fig_trend.tight_layout()
        self.canvas_trend.draw()

    def _draw_category_pie(self, by_category):
        """Draw category breakdown as pie chart."""
        self.ax_pie.clear()
        self.ax_pie.set_facecolor(CARD)

        if by_category:
            labels = list(by_category.keys())
            amounts = list(by_category.values())
            colors = ["#3b82f6", "#8b5cf6", "#f59e0b", "#10b981",
                      "#ef4444", "#ec4899", "#06b6d4", "#f97316"]
            colors = colors[:len(labels)]

            _, _, autotexts = self.ax_pie.pie(
                amounts, labels=labels, autopct="%1.1f%%",
                colors=colors, startangle=90,
                textprops={"fontsize": 8, "color": TEXT},
            )
            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_weight("bold")
        else:
            self.ax_pie.text(0.5, 0.5, "No data", ha="center", va="center",
                             color=MUTED, transform=self.ax_pie.transAxes)

        self.fig_pie.tight_layout()
        self.canvas_pie.draw()

    def load(self):
        try:
            transactions = transaction._load_transactions()
            assignments = transaction._load_assignments()
            tag_dict = safe_read_tags()
        except Exception:
            transactions = []
            assignments = []
            tag_dict = {}

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

        try:
            budgets = alerts.read_budget_csv()
            total_budget = sum(amount for (_, period), amount in budgets.items()
                               if period == "monthly")
            pct = (month_total / total_budget * 100) if total_budget > 0 else 0
            if self._month_pct_label is None:
                self._month_pct_label = tk.Label(
                    self._month_card,
                    text="",
                    bg=CARD,
                    fg=MUTED,
                    font=(FONT_FAMILY, 9),
                )
                self._month_pct_label.pack(anchor="w", padx=16, pady=(0, 8))
            self._month_pct_label.config(text=f"{pct:.0f}% of budget")
        except Exception:
            if self._month_pct_label is not None:
                self._month_pct_label.config(text="")

        try:
            budgets = alerts.read_budget_csv()
            total_budget = sum(amount for (_, period), amount in budgets.items()
                               if period == "monthly")
            days_left = max(1, alerts._days_in_month(today) - today.day)
            safe_day = (total_budget - month_total) / days_left if total_budget else 0.0
            self._safe_val.config(text=f"HK${safe_day:.2f}",
                                  fg=SUCCESS if safe_day >= 0 else DANGER)
        except Exception:
            self._safe_val.config(text="HK$0.00", fg=MUTED)

        days_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_total = sum(float(t["Amount"]) for t in transactions
                            if datetime.strptime(t["Date"], "%Y-%m-%d").date() == day.date())
            days_data.append((day, day_total))
        self._draw_spending_trend(days_data)

        by_category = defaultdict(float)
        for trans in transactions:
            try:
                date_value = datetime.strptime(trans["Date"], "%Y-%m-%d")
                if date_value.year == today.year and date_value.month == today.month:
                    trans_id = trans["ID"]
                    amount = float(trans["Amount"])
                    for assign in assignments:
                        if assign["ID"] == trans_id:
                            tag_id = assign["TagID"]
                            tag_info = tag_dict.get(tag_id, {})
                            tag_name = tag_info.get("Tag_name", f"Tag {tag_id}")
                            by_category[tag_name] += amount
                            break
            except (ValueError, KeyError):
                continue

        self._draw_category_pie(by_category)

        output = capture_output(alerts.check_all_alerts)
        self._render_alerts(output)

        # ── Capture new alerts for sidebar badge ─────────────────────────
        new_output = capture_output(alerts.check_new_alerts)
        new_lines = self._parse_alert_lines(new_output)
        top = self.winfo_toplevel()
        if hasattr(top, "update_alert_badge"):
            top.update_alert_badge(new_lines)
