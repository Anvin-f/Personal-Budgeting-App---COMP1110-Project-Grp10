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

    def load(self):
        transactions = alerts.read_transactions_csv()
        tag_dict = alerts.read_tags_csv()
        assignments = alerts.read_assignments_csv()

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

        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        week_cutoff = today - timedelta(days=6)
        thirty_day_cutoff = today - timedelta(days=29)

        by_category_today = defaultdict(float)
        by_category_week = defaultdict(float)
        by_category_month = defaultdict(float)
        per_day = defaultdict(float)
        total_today = 0.0
        total_week = 0.0
        total_month = 0.0
        irregular_month_total = 0.0
        balance_month_out = 0.0
        balance_month_in = 0.0

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
            transaction_id = row.get("ID")
            tags_for_transaction = tag_map.get(transaction_id, [])
            is_balance = has_tag_type(tags_for_transaction, adjustments.BALANCE_TAG_TYPE)
            is_irregular = has_tag_type(tags_for_transaction, adjustments.IRREGULAR_TAG_TYPE)

            if date_value.year == today.year and date_value.month == today.month:
                if is_irregular:
                    irregular_month_total += amount
                if is_balance:
                    name_text = (row.get("Name") or "").strip().lower()
                    if name_text.startswith("balance in"):
                        balance_month_in += amount
                    else:
                        balance_month_out += amount

            if is_balance or is_irregular:
                continue

            tag_name = category_name(tags_for_transaction)

            if date_value >= today:
                by_category_today[tag_name] += amount
                total_today += amount
            if date_value >= week_cutoff:
                by_category_week[tag_name] += amount
                total_week += amount
            if date_value.year == today.year and date_value.month == today.month:
                by_category_month[tag_name] += amount
                total_month += amount
            if date_value >= thirty_day_cutoff:
                per_day[date_value.strftime("%m/%d")] += amount

        peer_balances = adjustments.calculate_peer_balances()

        self._draw_charts(by_category_month, per_day)
        self._draw_summary(
            total_today,
            total_week,
            total_month,
            by_category_today,
            by_category_week,
            by_category_month,
            irregular_month_total,
            balance_month_out,
            balance_month_in,
            peer_balances,
        )

    def _draw_charts(self, by_category_month, per_day):
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
                "No transactions this month",
                ha="center",
                va="center",
                transform=self.ax1.transAxes,
                color=MUTED,
                fontsize=10,
            )

        self.ax1.set_title("Monthly Spending by Category", fontsize=10, pad=8, color=TEXT, fontweight="bold")
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
                "No transactions in last 30 days",
                ha="center",
                va="center",
                transform=self.ax2.transAxes,
                color=MUTED,
                fontsize=10,
            )

        self.ax2.set_title("Daily Spending (Last 30 Days)", fontsize=10, pad=8, color=TEXT, fontweight="bold")
        self.ax2.set_ylabel("HK$", fontsize=9, color=MUTED)
        self.ax2.tick_params(axis="x", rotation=45, labelsize=7, colors=TEXT)
        self.ax2.tick_params(axis="y", labelsize=8, colors=MUTED)

        self.fig.tight_layout(pad=2.5)
        self.canvas.draw()

    def _draw_summary(
        self,
        total_today,
        total_week,
        total_month,
        by_category_today,
        by_category_week,
        by_category_month,
        irregular_month_total,
        balance_month_out,
        balance_month_in,
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

        body = []
        body += section("TODAY", total_today, by_category_today)
        body.append("")
        body += section("THIS WEEK", total_week, by_category_week)
        body.append("")
        body += section("THIS MONTH", total_month, by_category_month)

        if by_category_month:
            body.append("")
            body.append("TOP 3 CATEGORIES")
            for name, amount in sorted(by_category_month.items(), key=lambda item: item[1], reverse=True)[:3]:
                body.append(f"  {name}: HK${amount:.2f}")

        body.append("")
        body.append("ADJUSTMENTS (THIS MONTH)")
        body.append(f"Irregular Expenses: HK${irregular_month_total:.2f}")
        body.append(f"Balance Out: HK${balance_month_out:.2f}")
        body.append(f"Balance In: HK${balance_month_in:.2f}")
        body.append(f"Net Peer Balance: HK${(balance_month_out - balance_month_in):.2f}")

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