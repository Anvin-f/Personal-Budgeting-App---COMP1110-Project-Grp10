from collections import defaultdict
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import core.alerts as alerts
import core.adjustments as adjustments

from ..base import Page
from ..constants import BG, BORDER, CARD, FONT_SM, MUTED, TEXT, FONT_FAMILY
from ..helpers import card, page_header, bind_tree_sort


class AnalysisPage(Page):
    def build(self):
        page_header(self, "📈  Analysis")

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

        self._month_toggle = tk.Label(
            toggle_frame,
            text="Month",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            bd=2, padx=10, pady=5, cursor="hand2",
        )
        self._month_toggle.bind("<Button-1>", lambda e: self._set_view_mode("month"))
        self._month_toggle.pack(side="left", padx=(0, 2))

        self._year_toggle = tk.Label(
            toggle_frame,
            text="Year",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=2, padx=10, pady=5, cursor="hand2",
        )
        self._year_toggle.bind("<Button-1>", lambda e: self._set_view_mode("year"))
        self._year_toggle.pack(side="left")

        # Divider
        tk.Frame(toggle_frame, bg=BORDER, width=1, height=20).pack(side="left", padx=8)

        self._bar_toggle = tk.Label(
            toggle_frame,
            text="Bar",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            bd=2, padx=10, pady=5, cursor="hand2",
        )
        self._bar_toggle.bind("<Button-1>", lambda e: self._set_chart_type("bar"))
        self._bar_toggle.pack(side="left", padx=(0, 2))

        self._pie_toggle = tk.Label(
            toggle_frame,
            text="Pie",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=2, padx=10, pady=5, cursor="hand2",
        )
        self._pie_toggle.bind("<Button-1>", lambda e: self._set_chart_type("pie"))
        self._pie_toggle.pack(side="left")

        # ── Month navigation ─────────────────────────────────────────────────
        self._month_nav_frame = tk.Frame(nav, bg=BG)
        self._month_nav_frame.pack(side="left")

        self.prev_btn = tk.Label(
            self._month_nav_frame,
            text="< Previous",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=2, padx=10, pady=5, cursor="hand2",
        )
        self.prev_btn.bind("<Button-1>", self._on_prev_month_click)
        self.prev_btn.pack(side="left")

        self.month_label = tk.Label(
            self._month_nav_frame,
            text="",
            bg=BG,
            fg=TEXT,
            font=(FONT_FAMILY, 11, "bold"),
        )
        self.month_label.pack(side="left", padx=12)

        self.next_btn = tk.Label(
            self._month_nav_frame,
            text="Next >",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=2, padx=10, pady=5, cursor="hand2",
        )
        self.next_btn.bind("<Button-1>", self._on_next_month_click)
        self.next_btn.pack(side="left")

        # ── Year navigation ──────────────────────────────────────────────────
        self._year_nav_frame = tk.Frame(nav, bg=BG)
        # starts hidden; shown when year mode is active

        self._prev_year_btn = tk.Label(
            self._year_nav_frame,
            text="< Previous",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=2, padx=10, pady=5, cursor="hand2",
        )
        self._prev_year_btn.bind("<Button-1>", self._on_prev_year_click)
        self._prev_year_btn.pack(side="left")

        self._next_year_btn = tk.Label(
            self._year_nav_frame,
            text="Next >",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#e5e7eb",
            fg=TEXT,
            relief="flat",
            bd=2, padx=10, pady=5, cursor="hand2",
        )
        self._next_year_btn.bind("<Button-1>", self._on_next_year_click)
        self._next_year_btn.pack(side="left")

        self._year_label = tk.Label(
            self._year_nav_frame,
            text="",
            bg=BG,
            fg=TEXT,
            font=(FONT_FAMILY, 11, "bold"),
        )
        self._year_label.pack(side="left", padx=12)

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
            font=(FONT_FAMILY, 12, "bold"),
        ).pack(anchor="w", padx=14, pady=(14, 4))
        tk.Frame(text_card, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(0, 6))

        metrics_row = tk.Frame(text_card, bg=CARD)
        metrics_row.pack(fill="x", padx=10, pady=(2, 8))

        self._metric_values = {}
        metric_specs = [
            ("regular", "Regular Total", "#3b82f6"),
            ("irregular", "Irregular", "#f59e0b"),
            ("net", "Balance Net", "#10b981"),
            ("scope", "Scope", "#8b5cf6"),
        ]
        for key, title, accent in metric_specs:
            metric_card = tk.Frame(metrics_row, bg="#f8fafc", highlightbackground=BORDER, highlightthickness=1)
            metric_card.pack(side="left", fill="both", expand=True, padx=4)
            tk.Label(
                metric_card,
                text=title,
                bg="#f8fafc",
                fg=MUTED,
                font=(FONT_FAMILY, 8, "bold"),
            ).pack(anchor="w", padx=8, pady=(6, 0))
            value_label = tk.Label(
                metric_card,
                text="-",
                bg="#f8fafc",
                fg=accent,
                font=(FONT_FAMILY, 10, "bold"),
            )
            value_label.pack(anchor="w", padx=8, pady=(0, 6))
            self._metric_values[key] = value_label

        self.summary_tabs = ttk.Notebook(text_card)
        self.summary_tabs.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        breakdown_tab = tk.Frame(self.summary_tabs, bg=CARD)
        adjustments_tab = tk.Frame(self.summary_tabs, bg=CARD)
        peers_tab = tk.Frame(self.summary_tabs, bg=CARD)
        self.summary_tabs.add(breakdown_tab, text="Breakdown")
        self.summary_tabs.add(adjustments_tab, text="Adjustments")
        self.summary_tabs.add(peers_tab, text="Peers")

        self.summary_breakdown_tree = ttk.Treeview(
            breakdown_tab,
            columns=("item", "amount", "share", "note"),
            show="headings",
            height=9,
        )
        self.summary_breakdown_tree.heading("item", text="Item")
        self.summary_breakdown_tree.heading("amount", text="Amount")
        self.summary_breakdown_tree.heading("share", text="Share")
        self.summary_breakdown_tree.heading("note", text="Note")
        self.summary_breakdown_tree.column("item", width=130, anchor="w")
        self.summary_breakdown_tree.column("amount", width=90, anchor="e")
        self.summary_breakdown_tree.column("share", width=70, anchor="center")
        self.summary_breakdown_tree.column("note", width=120, anchor="w")
        breakdown_scroll = ttk.Scrollbar(breakdown_tab, orient="vertical", command=self.summary_breakdown_tree.yview)
        self.summary_breakdown_tree.configure(yscrollcommand=breakdown_scroll.set)
        self.summary_breakdown_tree.pack(side="left", fill="both", expand=True)
        breakdown_scroll.pack(side="right", fill="y")

        self.summary_adjust_tree = ttk.Treeview(
            adjustments_tab,
            columns=("metric", "amount", "status"),
            show="headings",
            height=9,
        )
        self.summary_adjust_tree.heading("metric", text="Metric")
        self.summary_adjust_tree.heading("amount", text="Amount")
        self.summary_adjust_tree.heading("status", text="Status")
        self.summary_adjust_tree.column("metric", width=160, anchor="w")
        self.summary_adjust_tree.column("amount", width=110, anchor="e")
        self.summary_adjust_tree.column("status", width=110, anchor="center")
        adjust_scroll = ttk.Scrollbar(adjustments_tab, orient="vertical", command=self.summary_adjust_tree.yview)
        self.summary_adjust_tree.configure(yscrollcommand=adjust_scroll.set)
        self.summary_adjust_tree.pack(side="left", fill="both", expand=True)
        adjust_scroll.pack(side="right", fill="y")

        self.summary_peer_tree = ttk.Treeview(
            peers_tab,
            columns=("peer", "period_net", "all_time_net", "trend"),
            show="headings",
            height=9,
        )
        self.summary_peer_tree.heading("peer", text="Peer")
        self.summary_peer_tree.heading("period_net", text="Selected")
        self.summary_peer_tree.heading("all_time_net", text="All Time")
        self.summary_peer_tree.heading("trend", text="Trend")
        self.summary_peer_tree.column("peer", width=110, anchor="w")
        self.summary_peer_tree.column("period_net", width=90, anchor="e")
        self.summary_peer_tree.column("all_time_net", width=90, anchor="e")
        self.summary_peer_tree.column("trend", width=90, anchor="center")
        peer_scroll = ttk.Scrollbar(peers_tab, orient="vertical", command=self.summary_peer_tree.yview)
        self.summary_peer_tree.configure(yscrollcommand=peer_scroll.set)
        self.summary_peer_tree.pack(side="left", fill="both", expand=True)
        peer_scroll.pack(side="right", fill="y")
        
        def _parse_hkd(v):
            from ..helpers import safe_float
            return safe_float(v.replace("HK$", "").replace(",", ""))
        bind_tree_sort(self.summary_breakdown_tree, "item", 0)
        bind_tree_sort(self.summary_breakdown_tree, "amount", 1, parse_fn=_parse_hkd)
        bind_tree_sort(self.summary_breakdown_tree, "share", 2, parse_fn=lambda v: float(v.replace("%", "")))
        bind_tree_sort(self.summary_breakdown_tree, "note", 3)
        bind_tree_sort(self.summary_adjust_tree, "metric", 0)
        bind_tree_sort(self.summary_adjust_tree, "amount", 1, parse_fn=_parse_hkd)
        bind_tree_sort(self.summary_adjust_tree, "status", 2)
        bind_tree_sort(self.summary_peer_tree, "peer", 0)
        bind_tree_sort(self.summary_peer_tree, "period_net", 1, parse_fn=_parse_hkd)
        bind_tree_sort(self.summary_peer_tree, "all_time_net", 2, parse_fn=_parse_hkd)
        bind_tree_sort(self.summary_peer_tree, "trend", 3)
    
    def _on_prev_month_click(self, event):
        if self._selected_month > self._min_month:
            self._go_prev_month()

    def _on_next_month_click(self, event):
        if self._selected_month < self._max_month:
            self._go_next_month()

    def _on_prev_year_click(self, event):
        if self._selected_year > self._min_year:
            self._go_prev_year()

    def _on_next_year_click(self, event):
        if self._selected_year < self._max_year:
            self._go_next_year()

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
        prev_enabled = self._selected_month > self._min_month
        next_enabled = self._selected_month < self._max_month
        self.prev_btn.config(
            bg="#e5e7eb" if prev_enabled else "#d1d5db",
            fg=TEXT if prev_enabled else MUTED,
            cursor="hand2" if prev_enabled else "arrow",
        )
        self.next_btn.config(
            bg="#e5e7eb" if next_enabled else "#d1d5db",
            fg=TEXT if next_enabled else MUTED,
            cursor="hand2" if next_enabled else "arrow",
        )

    def _refresh_year_nav(self):
        self._year_label.config(text=str(self._selected_year))
        prev_enabled = self._selected_year > self._min_year
        next_enabled = self._selected_year < self._max_year
        self._prev_year_btn.config(
            bg="#e5e7eb" if prev_enabled else "#d1d5db",
            fg=TEXT if prev_enabled else MUTED,
            cursor="hand2" if prev_enabled else "arrow",
        )
        self._next_year_btn.config(
            bg="#e5e7eb" if next_enabled else "#d1d5db",
            fg=TEXT if next_enabled else MUTED,
            cursor="hand2" if next_enabled else "arrow",
        )

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
        peer_year_balances = {}

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
                peer_name = "Unknown"
                for t in tags_list:
                    tag_name = t.get("Tag_name", "")
                    if tag_name.startswith(adjustments.PEER_TAG_PREFIX):
                        peer_name = tag_name[len(adjustments.PEER_TAG_PREFIX) :].strip() or "Unknown"
                        break

                peer_entry = peer_year_balances.setdefault(peer_name, {"out": 0.0, "in": 0.0, "net": 0.0})
                name_text = (row.get("Name") or "").strip().lower()
                if name_text.startswith("balance in"):
                    balance_year_in += amount
                    peer_entry["in"] += amount
                else:
                    balance_year_out += amount
                    peer_entry["out"] += amount
                peer_entry["net"] = peer_entry["out"] - peer_entry["in"]

            if is_balance or is_irregular:
                continue

            m = date_value.month - 1  # 0-based
            cat = category_name(tags_list)
            by_month[m] += amount
            by_category_year[cat] += amount
            monthly_detail[m][cat] += amount

        self._draw_year_charts(by_month, by_category_year, year, MONTH_NAMES)
        peer_balances = adjustments.calculate_peer_balances()
        self._draw_year_summary(
            year, by_month, by_category_year, monthly_detail,
            irregular_year, balance_year_out, balance_year_in,
            peer_year_balances, peer_balances, MONTH_NAMES
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
        irregular_year, balance_year_out, balance_year_in,
        peer_year_balances, peer_balances, month_names
    ):
        year_total = sum(by_month.values())
        net_balance = balance_year_out - balance_year_in
        active_months = sum(1 for i in range(12) if by_month.get(i, 0.0) > 0)

        self._set_summary_metrics(
            regular=year_total,
            irregular=irregular_year,
            net=net_balance,
            scope=f"{active_months} active months",
        )
        self._clear_summary_tables()

        for i, mname in enumerate(month_names):
            m_total = by_month.get(i, 0.0)
            if m_total <= 0:
                continue
            pct = (m_total / year_total * 100) if year_total > 0 else 0
            top_cat = "-"
            if monthly_detail[i]:
                top_cat = max(monthly_detail[i].items(), key=lambda item: item[1])[0]
            self.summary_breakdown_tree.insert(
                "",
                "end",
                values=(mname, f"HK${m_total:.2f}", f"{pct:.1f}%", top_cat),
            )

        if not self.summary_breakdown_tree.get_children():
            self.summary_breakdown_tree.insert("", "end", values=("No data", "-", "-", "-"))

        adjustments_rows = [
            ("Irregular Expenses", irregular_year, "Warning" if irregular_year > 0 else "OK"),
            ("Balance Out", balance_year_out, "Outgoing"),
            ("Balance In", balance_year_in, "Incoming"),
            ("Net Balance", net_balance, "High" if net_balance > 500 else "Normal"),
        ]
        for metric, amount, status in adjustments_rows:
            self.summary_adjust_tree.insert("", "end", values=(metric, f"HK${amount:.2f}", status))

        merged_peers = set(peer_year_balances.keys()) | set(peer_balances.keys())
        for peer in sorted(merged_peers, key=str.lower):
            year_net = peer_year_balances.get(peer, {}).get("net", 0.0)
            all_time_net = peer_balances.get(peer, {}).get("net", 0.0)
            trend = "Owed" if all_time_net > 0 else ("Credit" if all_time_net < 0 else "Balanced")
            self.summary_peer_tree.insert(
                "",
                "end",
                values=(peer, f"HK${year_net:.2f}", f"HK${all_time_net:.2f}", trend),
            )

        if not self.summary_peer_tree.get_children():
            self.summary_peer_tree.insert("", "end", values=("No peers", "-", "-", "-"))

        self.summary_tabs.tab(0, text="Monthly Totals")
        self.summary_tabs.tab(1, text="Adjustments")
        self.summary_tabs.tab(2, text="Peer Balances")

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
        month_label = selected_month.strftime("%b %Y")
        net_balance = balance_month_out - balance_month_in

        self._set_summary_metrics(
            regular=total_month,
            irregular=irregular_month_total,
            net=net_balance,
            scope=month_label,
        )
        self._clear_summary_tables()

        sorted_categories = sorted(by_category_month.items(), key=lambda x: x[1], reverse=True)
        for name, amount in sorted_categories:
            pct = (amount / total_month * 100) if total_month > 0 else 0
            note = "Top" if pct >= 25 else "Tracked"
            self.summary_breakdown_tree.insert(
                "",
                "end",
                values=(name, f"HK${amount:.2f}", f"{pct:.1f}%", note),
            )

        if not self.summary_breakdown_tree.get_children():
            self.summary_breakdown_tree.insert("", "end", values=("No categories", "-", "-", "-"))

        adjustments_rows = [
            ("Irregular Expenses", irregular_month_total, "Warning" if irregular_month_total > 0 else "OK"),
            ("Balance Out", balance_month_out, "Outgoing"),
            ("Balance In", balance_month_in, "Incoming"),
            ("Net Balance", net_balance, "High" if net_balance > 500 else "Normal"),
        ]
        for metric, amount, status in adjustments_rows:
            self.summary_adjust_tree.insert("", "end", values=(metric, f"HK${amount:.2f}", status))

        merged_peers = set(peer_month_balances.keys()) | set(peer_balances.keys())
        for peer in sorted(merged_peers, key=str.lower):
            period_net = peer_month_balances.get(peer, {}).get("net", 0.0)
            all_time_net = peer_balances.get(peer, {}).get("net", 0.0)
            trend = "Owed" if all_time_net > 0 else ("Credit" if all_time_net < 0 else "Balanced")
            self.summary_peer_tree.insert(
                "",
                "end",
                values=(peer, f"HK${period_net:.2f}", f"HK${all_time_net:.2f}", trend),
            )

        if not self.summary_peer_tree.get_children():
            self.summary_peer_tree.insert("", "end", values=("No peers", "-", "-", "-"))

        self.summary_tabs.tab(0, text="Categories")
        self.summary_tabs.tab(1, text="Adjustments")
        self.summary_tabs.tab(2, text="Peer Balances")

    def _clear_summary_tables(self):
        self.summary_breakdown_tree.delete(*self.summary_breakdown_tree.get_children())
        self.summary_adjust_tree.delete(*self.summary_adjust_tree.get_children())
        self.summary_peer_tree.delete(*self.summary_peer_tree.get_children())

    def _set_summary_metrics(self, regular, irregular, net, scope):
        self._metric_values["regular"].config(text=f"HK${regular:.2f}", fg="#3b82f6")
        self._metric_values["irregular"].config(
            text=f"HK${irregular:.2f}",
            fg="#f59e0b" if irregular > 0 else "#10b981",
        )
        self._metric_values["net"].config(
            text=f"HK${net:.2f}",
            fg="#ef4444" if net > 500 else ("#f59e0b" if net > 0 else "#10b981"),
        )
        self._metric_values["scope"].config(text=scope, fg="#8b5cf6")