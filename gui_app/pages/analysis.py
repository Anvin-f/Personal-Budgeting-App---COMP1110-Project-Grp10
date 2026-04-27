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

        self._selected_month = datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self._min_month = self._selected_month
        self._max_month = self._selected_month

        nav = tk.Frame(self, bg=BG)
        nav.pack(fill="x", padx=24, pady=(10, 0))

        self.prev_btn = tk.Button(
            nav,
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
            nav,
            text="",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 11, "bold"),
        )
        self.month_label.pack(side="left", padx=12)

        self.next_btn = tk.Button(
            nav,
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

    def _go_prev_month(self):
        self._selected_month = self._shift_month(self._selected_month, -1)
        self.load()

    def _go_next_month(self):
        self._selected_month = self._shift_month(self._selected_month, 1)
        self.load()

    def load(self):
        transactions = alerts.read_transactions_csv()
        tag_dict = alerts.read_tags_csv()
        assignments = alerts.read_assignments_csv()

        current_month = datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        months_in_data = set()
        for row in transactions:
            try:
                date_value = datetime.strptime(row["Date"], "%Y-%m-%d")
            except (ValueError, KeyError):
                continue
            months_in_data.add(date_value.replace(day=1, hour=0, minute=0, second=0, microsecond=0))

        if months_in_data:
            self._min_month = min(months_in_data)
            self._max_month = max(max(months_in_data), current_month)
        else:
            self._min_month = current_month
            self._max_month = current_month

        if self._selected_month < self._min_month:
            self._selected_month = self._min_month
        if self._selected_month > self._max_month:
            self._selected_month = self._max_month
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

    def _draw_charts(self, by_category_month, per_day, selected_month):
        self.ax1.cla()
        self.ax2.cla()
        self.fig.patch.set_facecolor(CARD)
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
                    ha="center",
                    va="bottom",
                    fontsize=7.5,
                    color=TEXT,
                    fontweight="bold",
                )
        else:
            self.ax1.text(
                0.5,
                0.5,
                "No regular spending in this month",
                ha="center",
                va="center",
                transform=self.ax1.transAxes,
                color=MUTED,
                fontsize=10,
            )

        month_title = selected_month.strftime("%B %Y")
        self.ax1.set_title(
            f"Spending by Category - {month_title}",
            fontsize=10,
            pad=8,
            color=TEXT,
            fontweight="bold",
        )
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
            self.ax2.text(
                0.5,
                0.5,
                "No regular spending days in this month",
                ha="center",
                va="center",
                transform=self.ax2.transAxes,
                color=MUTED,
                fontsize=10,
            )

        self.ax2.set_title(
            f"Daily Spending - {month_title}",
            fontsize=10,
            pad=8,
            color=TEXT,
            fontweight="bold",
        )
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