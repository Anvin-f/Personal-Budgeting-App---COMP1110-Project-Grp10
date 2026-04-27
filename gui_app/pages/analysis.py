from collections import defaultdict
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import scrolledtext

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import core.alerts as alerts
import core.adjustments as adjustments

from ..base import Page
from ..constants import BG, BORDER, CARD, FONT_SM, MUTED, TEXT
from ..helpers import card, page_header


class AnalysisPage(Page):
    def build(self):
        page_header(self, "Analysis")

        today = datetime.today()
        self._view_mode = "month"  # "month" or "year"
        self._chart_type = "bar"   # "bar" or "pie"
        self._selected_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self._selected_year = today.year
        self._min_month = self._selected_month
        self._max_month = self._selected_month
        self._min_year = today.year
        self._max_year = today.year

        # ── top nav bar ──────────────────────────────────────────────────────
        nav = tk.Frame(self, bg=BG)
        nav.pack(fill="x", padx=24, pady=(10, 0))

        # Toggle buttons: Month | Year  +  Bar | Pie
        toggle_frame = tk.Frame(nav, bg=BG)
        toggle_frame.pack(side="right", padx=(8, 0))

        self._month_toggle = tk.Button(
            toggle_frame,
            text="Month",
            font=("Helvetica Neue", 9, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=lambda: self._set_view_mode("month"),
        )
        self._month_toggle.pack(side="left", padx=(0, 2))

        self._year_toggle = tk.Button(
            toggle_frame,
            text="Year",
            font=("Helvetica Neue", 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=lambda: self._set_view_mode("year"),
        )
        self._year_toggle.pack(side="left")

        # Divider
        tk.Frame(toggle_frame, bg=BORDER, width=1, height=20).pack(side="left", padx=8)

        self._bar_toggle = tk.Button(
            toggle_frame,
            text="Bar",
            font=("Helvetica Neue", 9, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=lambda: self._set_chart_type("bar"),
        )
        self._bar_toggle.pack(side="left", padx=(0, 2))

        self._pie_toggle = tk.Button(
            toggle_frame,
            text="Pie",
            font=("Helvetica Neue", 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=lambda: self._set_chart_type("pie"),
        )
        self._pie_toggle.pack(side="left")

        # ── Month navigation ─────────────────────────────────────────────────
        self._month_nav_frame = tk.Frame(nav, bg=BG)
        self._month_nav_frame.pack(side="left")

        self.prev_btn = tk.Button(
            self._month_nav_frame,
            text="< Previous",
            font=("Helvetica Neue", 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._go_prev_month,
        )
        self.prev_btn.pack(side="left")

        self.month_label = tk.Label(
            self._month_nav_frame,
            text="",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 11, "bold"),
        )
        self.month_label.pack(side="left", padx=12)

        self.next_btn = tk.Button(
            self._month_nav_frame,
            text="Next >",
            font=("Helvetica Neue", 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._go_next_month,
        )
        self.next_btn.pack(side="left")

        # ── Year navigation ──────────────────────────────────────────────────
        self._year_nav_frame = tk.Frame(nav, bg=BG)
        # starts hidden; shown when year mode is active

        self._prev_year_btn = tk.Button(
            self._year_nav_frame,
            text="< Previous",
            font=("Helvetica Neue", 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._go_prev_year,
        )
        self._prev_year_btn.pack(side="left")

        self._year_label = tk.Label(
            self._year_nav_frame,
            text="",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 11, "bold"),
        )
        self._year_label.pack(side="left", padx=12)

        self._next_year_btn = tk.Button(
            self._year_nav_frame,
            text="Next >",
            font=("Helvetica Neue", 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._go_next_year,
        )
        self._next_year_btn.pack(side="left")

        paned = tk.PanedWindow(self, orient="horizontal", bg=BG, sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=24, pady=(10, 18))

        chart_card = card(paned)
        paned.add(chart_card, minsize=430)

        self.fig = Figure(figsize=(6, 6), dpi=90, facecolor=CARD)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.fig.tight_layout(pad=2.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        text_card = card(paned)
        paned.add(text_card, minsize=250)

        tk.Label(
            text_card,
            text="Spending Summary",
            bg=CARD,
            fg=TEXT,
            font=("Helvetica Neue", 12, "bold"),
        ).pack(anchor="w", padx=14, pady=(14, 4))
        tk.Frame(text_card, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(0, 6))

        self.summary_box = scrolledtext.ScrolledText(
            text_card,
            font=FONT_SM,
            bg=CARD,
            fg=TEXT,
            relief="flat",
            wrap="word",
            state="disabled",
            padx=8,
        )
        self.summary_box.pack(fill="both", expand=True, padx=6, pady=(0, 14))

    def _set_view_mode(self, mode):
        self._view_mode = mode
        if mode == "month":
            self._month_toggle.config(bg="#3b82f6", fg="white")
            self._year_toggle.config(bg="#e5e7eb", fg=TEXT)
            self._year_nav_frame.pack_forget()
            self._month_nav_frame.pack(side="left")
        else:
            self._year_toggle.config(bg="#3b82f6", fg="white")
            self._month_toggle.config(bg="#e5e7eb", fg=TEXT)
            self._month_nav_frame.pack_forget()
            self._year_nav_frame.pack(side="left")
        self.load()

    def _set_chart_type(self, chart_type):
        self._chart_type = chart_type
        if chart_type == "bar":
            self._bar_toggle.config(bg="#3b82f6", fg="white")
            self._pie_toggle.config(bg="#e5e7eb", fg=TEXT)
        else:
            self._pie_toggle.config(bg="#3b82f6", fg="white")
            self._bar_toggle.config(bg="#e5e7eb", fg=TEXT)
        self.load()

    def _shift_month(self, value, delta):
        month_index = (value.year * 12 + value.month - 1) + delta
        year = month_index // 12
        month = month_index % 12 + 1
        return datetime(year, month, 1)

    def _refresh_month_nav(self):
        self.month_label.config(text=self._selected_month.strftime("%B %Y"))
        prev_state = "disabled" if self._selected_month <= self._min_month else "normal"
        next_state = "disabled" if self._selected_month >= self._max_month else "normal"
        self.prev_btn.config(state=prev_state)
        self.next_btn.config(state=next_state)

    def _refresh_year_nav(self):
        self._year_label.config(text=str(self._selected_year))
        prev_state = "disabled" if self._selected_year <= self._min_year else "normal"
        next_state = "disabled" if self._selected_year >= self._max_year else "normal"
        self._prev_year_btn.config(state=prev_state)
        self._next_year_btn.config(state=next_state)

    def _go_prev_month(self):
        self._selected_month = self._shift_month(self._selected_month, -1)
        self.load()

    def _go_next_month(self):
        self._selected_month = self._shift_month(self._selected_month, 1)
        self.load()

    def _go_prev_year(self):
        self._selected_year -= 1
        self.load()

    def _go_next_year(self):
        self._selected_year += 1
        self.load()

    def load(self):
        transactions = alerts.read_transactions_csv()
        tag_dict = alerts.read_tags_csv()
        assignments = alerts.read_assignments_csv()

        today = datetime.today()
        current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        months_in_data = set()
        years_in_data = set()
        for row in transactions:
            try:
                date_value = datetime.strptime(row["Date"], "%Y-%m-%d")
            except (ValueError, KeyError):
                continue
            months_in_data.add(date_value.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
            years_in_data.add(date_value.year)

        if months_in_data:
            self._min_month = min(months_in_data)
            self._max_month = max(max(months_in_data), current_month)
        else:
            self._min_month = current_month
            self._max_month = current_month

        if years_in_data:
            self._min_year = min(years_in_data)
            self._max_year = max(max(years_in_data), today.year)
        else:
            self._min_year = today.year
            self._max_year = today.year

        if self._selected_month < self._min_month:
            self._selected_month = self._min_month
        if self._selected_month > self._max_month:
            self._selected_month = self._max_month

        self._selected_year = max(self._min_year, min(self._selected_year, self._max_year))

        if self._view_mode == "year":
            self._refresh_year_nav()
            self._load_for_year(transactions, assignments, tag_dict)
            return

        self._refresh_month_nav()

        selected_start = self._selected_month
        selected_end = self._shift_month(selected_start, 1)

        tag_map = {}
        for assignment in assignments:
            transaction_id = assignment.get("ID")
            tag_id = assignment.get("TagID")
            if not transaction_id or not tag_id:
                continue
            tag = tag_dict.get(tag_id)
            if tag is None:
                continue
            tag_map.setdefault(transaction_id, []).append(tag)

        by_category_month = defaultdict(float)
        per_day = defaultdict(float)
        total_month = 0.0
        irregular_month_total = 0.0
        balance_month_out = 0.0
        balance_month_in = 0.0
        peer_month_balances = {}

        def has_tag_type(tags_for_transaction, tag_type):
            wanted = tag_type.strip().lower()
            return any(tag.get("Tag_type", "").strip().lower() == wanted for tag in tags_for_transaction)

        def category_name(tags_for_transaction):
            for tag in tags_for_transaction:
                if tag.get("Tag_type", "").strip().lower() not in (
                    adjustments.BALANCE_TAG_TYPE.lower(),
                    adjustments.IRREGULAR_TAG_TYPE.lower(),
                ):
                    return tag.get("Tag_name", "Untagged")
            if tags_for_transaction:
                return tags_for_transaction[0].get("Tag_name", "Untagged")
            return "Untagged"

        for row in transactions:
            try:
                date_value = datetime.strptime(row["Date"], "%Y-%m-%d")
                amount = float(row["Amount"])
            except (ValueError, KeyError):
                continue
            if date_value < selected_start or date_value >= selected_end:
                continue

            transaction_id = row.get("ID")
            tags_for_transaction = tag_map.get(transaction_id, [])
            is_balance = has_tag_type(tags_for_transaction, adjustments.BALANCE_TAG_TYPE)
            is_irregular = has_tag_type(tags_for_transaction, adjustments.IRREGULAR_TAG_TYPE)

            peer_name = "Unknown"
            for tag in tags_for_transaction:
                tag_name = tag.get("Tag_name", "")
                if tag_name.startswith(adjustments.PEER_TAG_PREFIX):
                    peer_name = tag_name[len(adjustments.PEER_TAG_PREFIX) :].strip() or "Unknown"
                    break

            if is_balance:
                peer_entry = peer_month_balances.setdefault(peer_name, {"out": 0.0, "in": 0.0, "net": 0.0})

            if is_irregular:
                irregular_month_total += amount
            if is_balance:
                name_text = (row.get("Name") or "").strip().lower()
                if name_text.startswith("balance in"):
                    balance_month_in += amount
                    peer_entry["in"] += amount
                else:
                    balance_month_out += amount
                    peer_entry["out"] += amount
                peer_entry["net"] = peer_entry["out"] - peer_entry["in"]

            if is_balance or is_irregular:
                continue

            tag_name = category_name(tags_for_transaction)

            by_category_month[tag_name] += amount
            total_month += amount
            per_day[date_value.strftime("%m/%d")] += amount

        peer_balances = adjustments.calculate_peer_balances()

        self._draw_charts(by_category_month, per_day, selected_start)
        self._draw_summary(
            selected_start,
            total_month,
            by_category_month,
            irregular_month_total,
            balance_month_out,
            balance_month_in,
            peer_month_balances,
            peer_balances,
        )

    # ── Year view ────────────────────────────────────────────────────────────

    def _load_for_year(self, transactions, assignments, tag_dict):
        year = self._selected_year
        year_start = datetime(year, 1, 1)
        year_end = datetime(year + 1, 1, 1)

        tag_map = {}
        for assignment in assignments:
            tid = assignment.get("ID")
            tag_id = assignment.get("TagID")
            if not tid or not tag_id:
                continue
            tag = tag_dict.get(tag_id)
            if tag is None:
                continue
            tag_map.setdefault(tid, []).append(tag)

        def has_tag_type(tags_list, tag_type):
            wanted = tag_type.strip().lower()
            return any(t.get("Tag_type", "").strip().lower() == wanted for t in tags_list)

        def category_name(tags_list):
            for t in tags_list:
                if t.get("Tag_type", "").strip().lower() not in (
                    adjustments.BALANCE_TAG_TYPE.lower(),
                    adjustments.IRREGULAR_TAG_TYPE.lower(),
                ):
                    return t.get("Tag_name", "Untagged")
            return tags_list[0].get("Tag_name", "Untagged") if tags_list else "Untagged"

        MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        by_month = defaultdict(float)           # month_index (0-11) -> regular total
        by_category_year = defaultdict(float)   # category -> total for year
        monthly_detail = {i: defaultdict(float) for i in range(12)}  # month -> categories
        irregular_year = 0.0
        balance_year_out = 0.0
        balance_year_in = 0.0

        for row in transactions:
            try:
                date_value = datetime.strptime(row["Date"], "%Y-%m-%d")
                amount = float(row["Amount"])
            except (ValueError, KeyError):
                continue
            if date_value < year_start or date_value >= year_end:
                continue

            tid = row.get("ID")
            tags_list = tag_map.get(tid, [])
            is_balance = has_tag_type(tags_list, adjustments.BALANCE_TAG_TYPE)
            is_irregular = has_tag_type(tags_list, adjustments.IRREGULAR_TAG_TYPE)

            if is_irregular:
                irregular_year += amount
            if is_balance:
                name_text = (row.get("Name") or "").strip().lower()
                if name_text.startswith("balance in"):
                    balance_year_in += amount
                else:
                    balance_year_out += amount

            if is_balance or is_irregular:
                continue

            m = date_value.month - 1  # 0-based
            cat = category_name(tags_list)
            by_month[m] += amount
            by_category_year[cat] += amount
            monthly_detail[m][cat] += amount

        self._draw_year_charts(by_month, by_category_year, year, MONTH_NAMES)
        self._draw_year_summary(
            year, by_month, by_category_year, monthly_detail,
            irregular_year, balance_year_out, balance_year_in, MONTH_NAMES
        )

    _PIE_COLORS = [
        "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
        "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16",
        "#f97316", "#14b8a6", "#a855f7", "#64748b",
    ]

    def _draw_year_charts(self, by_month, by_category_year, year, month_names):
        self.fig.clear()
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.fig.patch.set_facecolor(CARD)

        amounts = [by_month.get(i, 0.0) for i in range(12)]
        has_data = any(a > 0 for a in amounts)

        if self._chart_type == "pie":
            # ── Pie charts ──────────────────────────────────────────────────
            for axis in (self.ax1, self.ax2):
                axis.set_facecolor(CARD)

            # ax1: monthly spending pie
            nonzero = [(month_names[i], amounts[i]) for i in range(12) if amounts[i] > 0]
            if nonzero:
                labels, vals = zip(*nonzero)
                self.ax1.pie(
                    vals, labels=labels, autopct="%1.0f%%",
                    colors=self._PIE_COLORS[:len(vals)],
                    startangle=90, textprops={"fontsize": 8, "color": TEXT},
                )
            else:
                self.ax1.text(0.5, 0.5, "No spending this year",
                              ha="center", va="center", transform=self.ax1.transAxes, color=MUTED, fontsize=10)
            self.ax1.set_title(f"Monthly Spending - {year}", fontsize=10, pad=8, color=TEXT, fontweight="bold")

            # ax2: top categories pie
            if by_category_year:
                sorted_cats = sorted(by_category_year.items(), key=lambda x: x[1], reverse=True)[:8]
                cat_labels, cat_amounts = zip(*sorted_cats)
                self.ax2.pie(
                    cat_amounts, labels=cat_labels, autopct="%1.0f%%",
                    colors=self._PIE_COLORS[:len(cat_amounts)],
                    startangle=90, textprops={"fontsize": 8, "color": TEXT},
                )
            else:
                self.ax2.text(0.5, 0.5, "No regular spending this year",
                              ha="center", va="center", transform=self.ax2.transAxes, color=MUTED, fontsize=10)
            self.ax2.set_title(f"Top Categories - {year}", fontsize=10, pad=8, color=TEXT, fontweight="bold")

        else:
            # ── Bar charts ──────────────────────────────────────────────────
            for axis in (self.ax1, self.ax2):
                axis.set_facecolor("#f9fafb")
                axis.spines["top"].set_visible(False)
                axis.spines["right"].set_visible(False)
                axis.spines["left"].set_color(BORDER)
                axis.spines["bottom"].set_color(BORDER)

            bars = self.ax1.bar(month_names, amounts, color="#3b82f6", edgecolor="none", zorder=2, width=0.6)
            self.ax1.grid(axis="y", linestyle="--", alpha=0.35, zorder=1)
            if has_data:
                max_a = max(amounts)
                for bar, amount in zip(bars, amounts):
                    if amount > 0:
                        self.ax1.text(
                            bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + max_a * 0.015,
                            f"${amount:.0f}",
                            ha="center", va="bottom", fontsize=7, color=TEXT, fontweight="bold",
                        )
            self.ax1.set_title(f"Monthly Spending - {year}", fontsize=10, pad=8, color=TEXT, fontweight="bold")
            self.ax1.set_ylabel("HK$", fontsize=9, color=MUTED)
            self.ax1.tick_params(axis="x", rotation=0, labelsize=8, colors=TEXT)
            self.ax1.tick_params(axis="y", labelsize=8, colors=MUTED)

            if by_category_year:
                sorted_cats = sorted(by_category_year.items(), key=lambda x: x[1], reverse=True)[:6]
                cat_labels = [c for c, _ in sorted_cats]
                cat_amounts = [a for _, a in sorted_cats]
                self.ax2.bar(cat_labels, cat_amounts, color="#10b981", edgecolor="none", zorder=2, width=0.55)
                self.ax2.grid(axis="y", linestyle="--", alpha=0.35, zorder=1)
            else:
                self.ax2.text(0.5, 0.5, "No regular spending this year",
                              ha="center", va="center", transform=self.ax2.transAxes, color=MUTED, fontsize=10)
            self.ax2.set_title(f"Top Categories - {year}", fontsize=10, pad=8, color=TEXT, fontweight="bold")
            self.ax2.set_ylabel("HK$", fontsize=9, color=MUTED)
            self.ax2.tick_params(axis="x", rotation=30, labelsize=8, colors=TEXT)
            self.ax2.tick_params(axis="y", labelsize=8, colors=MUTED)

        self.fig.tight_layout(pad=2.5)
        self.canvas.draw()

    def _draw_year_summary(
        self, year, by_month, by_category_year, monthly_detail,
        irregular_year, balance_year_out, balance_year_in, month_names
    ):
        body = [f"YEARLY SPENDING - {year}"]
        year_total = sum(by_month.values())
        body.append(f"Total Regular Spending: HK${year_total:.2f}")
        body.append("")
        body.append("MONTHLY BREAKDOWN")
        for i, mname in enumerate(month_names):
            m_total = by_month.get(i, 0.0)
            body.append(f"  {mname}: HK${m_total:.2f}")
            for cat, amt in sorted(monthly_detail[i].items(), key=lambda x: x[1], reverse=True):
                body.append(f"    {cat}: HK${amt:.2f}")
        body.append("")
        body.append(f"TOP CATEGORIES - {year}")
        if by_category_year:
            for cat, amt in sorted(by_category_year.items(), key=lambda x: x[1], reverse=True):
                body.append(f"  {cat}: HK${amt:.2f}")
        else:
            body.append("  No transactions")
        body.append("")
        body.append(f"ADJUSTMENTS - {year}")
        body.append(f"Irregular Expenses: HK${irregular_year:.2f}")
        body.append(f"Balance Out: HK${balance_year_out:.2f}")
        body.append(f"Balance In: HK${balance_year_in:.2f}")
        body.append(f"Net Peer Balance: HK${(balance_year_out - balance_year_in):.2f}")

        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("end", "\n".join(body))
        self.summary_box.config(state="disabled")

    def _draw_charts(self, by_category_month, per_day, selected_month):
        self.fig.clear()
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.fig.patch.set_facecolor(CARD)
        month_title = selected_month.strftime("%B %Y")

        if self._chart_type == "pie":
            # ── Pie charts ──────────────────────────────────────────────────
            for axis in (self.ax1, self.ax2):
                axis.set_facecolor(CARD)

            # ax1: categories pie
            if by_category_month:
                sorted_categories = sorted(by_category_month.items(), key=lambda item: item[1], reverse=True)
                labels = [l for l, _ in sorted_categories]
                amounts = [a for _, a in sorted_categories]
                self.ax1.pie(
                    amounts, labels=labels, autopct="%1.0f%%",
                    colors=self._PIE_COLORS[:len(amounts)],
                    startangle=90, textprops={"fontsize": 8, "color": TEXT},
                )
            else:
                self.ax1.text(0.5, 0.5, "No regular spending in this month",
                              ha="center", va="center", transform=self.ax1.transAxes, color=MUTED, fontsize=10)
            self.ax1.set_title(f"Spending by Category - {month_title}", fontsize=10, pad=8, color=TEXT, fontweight="bold")

            # ax2: daily spending pie
            if per_day:
                sorted_days = sorted(per_day.items())
                labels = [l for l, _ in sorted_days]
                amounts = [a for _, a in sorted_days]
                self.ax2.pie(
                    amounts, labels=labels, autopct="%1.0f%%",
                    colors=self._PIE_COLORS[:len(amounts)],
                    startangle=90, textprops={"fontsize": 8, "color": TEXT},
                )
            else:
                self.ax2.text(0.5, 0.5, "No regular spending days in this month",
                              ha="center", va="center", transform=self.ax2.transAxes, color=MUTED, fontsize=10)
            self.ax2.set_title(f"Daily Spending - {month_title}", fontsize=10, pad=8, color=TEXT, fontweight="bold")

        else:
            # ── Bar charts ──────────────────────────────────────────────────
            for axis in (self.ax1, self.ax2):
                axis.set_facecolor("#f9fafb")
                axis.spines["top"].set_visible(False)
                axis.spines["right"].set_visible(False)
                axis.spines["left"].set_color(BORDER)
                axis.spines["bottom"].set_color(BORDER)

            if by_category_month:
                sorted_categories = sorted(by_category_month.items(), key=lambda item: item[1], reverse=True)
                labels = [label for label, _ in sorted_categories]
                amounts = [amount for _, amount in sorted_categories]
                bars = self.ax1.bar(labels, amounts, color="#3b82f6", edgecolor="none", zorder=2, width=0.55)
                self.ax1.grid(axis="y", linestyle="--", alpha=0.35, zorder=1)
                max_amount = max(amounts)
                for bar, amount in zip(bars, amounts):
                    self.ax1.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max_amount * 0.015,
                        f"${amount:.0f}",
                        ha="center", va="bottom", fontsize=7.5, color=TEXT, fontweight="bold",
                    )
            else:
                self.ax1.text(0.5, 0.5, "No regular spending in this month",
                              ha="center", va="center", transform=self.ax1.transAxes, color=MUTED, fontsize=10)
            self.ax1.set_title(f"Spending by Category - {month_title}", fontsize=10, pad=8, color=TEXT, fontweight="bold")
            self.ax1.set_ylabel("HK$", fontsize=9, color=MUTED)
            self.ax1.tick_params(axis="x", rotation=30, labelsize=8, colors=TEXT)
            self.ax1.tick_params(axis="y", labelsize=8, colors=MUTED)

            if per_day:
                sorted_days = sorted(per_day.items())
                labels = [label for label, _ in sorted_days]
                amounts = [amount for _, amount in sorted_days]
                self.ax2.bar(labels, amounts, color="#10b981", edgecolor="none", zorder=2, width=0.6)
                self.ax2.grid(axis="y", linestyle="--", alpha=0.35, zorder=1)
            else:
                self.ax2.text(0.5, 0.5, "No regular spending days in this month",
                              ha="center", va="center", transform=self.ax2.transAxes, color=MUTED, fontsize=10)
            self.ax2.set_title(f"Daily Spending - {month_title}", fontsize=10, pad=8, color=TEXT, fontweight="bold")
            self.ax2.set_ylabel("HK$", fontsize=9, color=MUTED)
            self.ax2.tick_params(axis="x", rotation=45, labelsize=7, colors=TEXT)
            self.ax2.tick_params(axis="y", labelsize=8, colors=MUTED)

        self.fig.tight_layout(pad=2.5)
        self.canvas.draw()

    def _draw_summary(
        self,
        selected_month,
        total_month,
        by_category_month,
        irregular_month_total,
        balance_month_out,
        balance_month_in,
        peer_month_balances,
        peer_balances,
    ):
        def section(title, total, categories):
            lines = [title, f"Total: HK${total:.2f}"]
            if categories:
                for name, amount in sorted(categories.items(), key=lambda item: item[1], reverse=True):
                    lines.append(f"  {name}: HK${amount:.2f}")
            else:
                lines.append("  No transactions")
            return lines

        month_label = selected_month.strftime("%B %Y").upper()
        body = section(f"REGULAR SPENDING - {month_label}", total_month, by_category_month)

        if by_category_month:
            body.append("")
            body.append(f"TOP 3 CATEGORIES ({month_label})")
            for name, amount in sorted(by_category_month.items(), key=lambda item: item[1], reverse=True)[:3]:
                body.append(f"  {name}: HK${amount:.2f}")

        body.append("")
        body.append(f"ADJUSTMENTS ({month_label})")
        body.append(f"Irregular Expenses: HK${irregular_month_total:.2f}")
        body.append(f"Balance Out: HK${balance_month_out:.2f}")
        body.append(f"Balance In: HK${balance_month_in:.2f}")
        body.append(f"Net Peer Balance: HK${(balance_month_out - balance_month_in):.2f}")

        body.append("")
        body.append(f"PEER BALANCES ({month_label})")
        if peer_month_balances:
            for peer, values in sorted(peer_month_balances.items(), key=lambda item: item[0].lower()):
                body.append(
                    f"  {peer}: Out HK${values['out']:.2f}, "
                    f"In HK${values['in']:.2f}, Net HK${values['net']:.2f}"
                )
        else:
            body.append("  No peer balance adjustments in this month")

        body.append("")
        body.append("PEER BALANCES (ALL TIME)")
        if peer_balances:
            for peer, values in sorted(peer_balances.items(), key=lambda item: item[0].lower()):
                body.append(
                    f"  {peer}: Out HK${values['out']:.2f}, "
                    f"In HK${values['in']:.2f}, Net HK${values['net']:.2f}"
                )
        else:
            body.append("  No peer balance adjustments")

        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("end", "\n".join(body))
        self.summary_box.config(state="disabled")