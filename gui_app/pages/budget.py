import tkinter as tk
from collections import defaultdict
from datetime import datetime
from tkinter import messagebox, ttk

import core.alerts as alerts
import core.adjustments as adjustments
import core.settings as app_settings

from ..base import Page
from ..constants import ACCENT, BG, BORDER, CARD, DANGER, FONT, FONT_H, FONT_SM, MUTED, SUCCESS, TEXT, FONT_FAMILY
from ..helpers import button, card, repaint_tree, zebra, bind_tree_sort, safe_float


class BudgetPage(Page):
    def build(self):
        self._selected_ids = set()  # budget tag_ids selected via checkbox

        today = datetime.today()
        self._selected_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self._min_month = self._selected_month
        self._max_month = self._selected_month

        # ── header row ───────────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(top, text="💰  Budgets", bg=BG, fg=TEXT, font=FONT_H).pack(side="left")

        buttons = tk.Frame(top, bg=BG)
        buttons.pack(side="right", anchor="s")
        button(buttons, "➕  Add", self._add_dialog, SUCCESS).pack(side="left", padx=4)
        button(buttons, "☑  Select All", self._select_all_toggle, "#374151").pack(side="left", padx=4)
        button(buttons, "🗑️  Delete", self._delete_selected, DANGER).pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 6))

        # ── month navigation ─────────────────────────────────────────────────
        nav = tk.Frame(self, bg=BG)
        nav.pack(fill="x", padx=24, pady=(0, 8))

        self._prev_btn = tk.Label(
            nav, text="< Previous",
            font=(FONT_FAMILY, 9, "bold"), bg="#e5e7eb", fg=TEXT,
            relief="flat", bd=2, padx=10, pady=5, cursor="hand2",
        )
        self._prev_btn.bind("<Button-1>", self._on_prev_click)
        self._prev_btn.pack(side="left")
        self._next_btn = tk.Label(
            nav, text="Next >",
            font=(FONT_FAMILY, 9, "bold"), bg="#e5e7eb", fg=TEXT,
            relief="flat", bd=2, padx=10, pady=5, cursor="hand2",
        )
        self._next_btn.bind("<Button-1>", self._on_next_click)
        self._next_btn.pack(side="left")
        self._month_label = tk.Label(nav, text="", bg=BG, fg=TEXT,
                             font=(FONT_FAMILY, 11, "bold"))
        self._month_label.pack(side="left", padx=12)

        # ── totals bar ───────────────────────────────────────────────────────
        totals_frame = tk.Frame(self, bg=CARD, bd=0, relief="flat")
        totals_frame.pack(fill="x", padx=24, pady=(0, 6))
        tk.Frame(totals_frame, bg=BORDER, height=1).pack(fill="x")
        inner = tk.Frame(totals_frame, bg=CARD)
        inner.pack(fill="x", padx=14, pady=8)

        self._lbl_total_budget = tk.Label(inner, text="Total Budget: –", bg=CARD, fg=TEXT, font=FONT_SM)
        self._lbl_total_budget.pack(side="left", padx=(0, 20))
        self._lbl_total_spent = tk.Label(inner, text="Total Spent: –", bg=CARD, fg=TEXT, font=FONT_SM)
        self._lbl_total_spent.pack(side="left", padx=(0, 20))
        self._lbl_remaining = tk.Label(inner, text="Remaining: –", bg=CARD, fg=TEXT, font=FONT_SM)
        self._lbl_remaining.pack(side="left")
        tk.Frame(totals_frame, bg=BORDER, height=1).pack(fill="x")

        # ── table ────────────────────────────────────────────────────────────
        budget_card = card(self)
        budget_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        columns = ("☐", "Tag ID", "Tag Name", "Budget (HK$)", "Spent (HK$)", "Remaining (HK$)", "Used %")
        self.tree = ttk.Treeview(budget_card, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("☐", text="☐")
        self.tree.heading("Tag ID", text="ID")
        self.tree.heading("Tag Name", text="Tag Name")
        self.tree.heading("Budget (HK$)", text="Budget (HK$)")
        self.tree.heading("Spent (HK$)", text="Spent (HK$)")
        self.tree.heading("Remaining (HK$)", text="Remaining (HK$)")
        self.tree.heading("Used %", text="Used %")
        self.tree.column("☐", width=30, anchor="center")
        self.tree.column("Tag ID", width=55, anchor="center")
        self.tree.column("Tag Name", width=180)
        self.tree.column("Budget (HK$)", width=130, anchor="e")
        self.tree.column("Spent (HK$)", width=130, anchor="e")
        self.tree.column("Remaining (HK$)", width=140, anchor="e")
        self.tree.column("Used %", width=80, anchor="center")

        # colour tags: over budget = red tint
        self.tree.tag_configure("over", background="#fee2e2")
        self.tree.tag_configure("warn", background="#fef9c3")

        zebra(self.tree)
        scrollbar = ttk.Scrollbar(budget_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # column sorting (note: checkbox column will also be sortable)
        def _parse_hkd(v):
            return safe_float(v.replace("HK$", "").replace(",", ""))
        def _parse_pct(v):
            return safe_float(v.replace("%", ""))
        bind_tree_sort(self.tree, "☐", 0)
        bind_tree_sort(self.tree, "Tag ID", 1, parse_fn=lambda v: safe_float(v))
        bind_tree_sort(self.tree, "Tag Name", 2)
        bind_tree_sort(self.tree, "Budget (HK$)", 3, parse_fn=_parse_hkd)
        bind_tree_sort(self.tree, "Spent (HK$)", 4, parse_fn=_parse_hkd)
        bind_tree_sort(self.tree, "Remaining (HK$)", 5, parse_fn=_parse_hkd)
        bind_tree_sort(self.tree, "Used %", 6, parse_fn=_parse_pct)

        self.tree.bind("<Button-1>", self._on_click_check_column)
    
    def _on_prev_click(self, event):
        if self._selected_month > self._min_month:
            self._go_prev()
    def _on_next_click(self, event):
        if self._selected_month < self._max_month:
            self._go_next()

    # ── navigation ───────────────────────────────────────────────────────────
    def _shift_month(self, value, delta):
        idx = (value.year * 12 + value.month - 1) + delta
        return datetime(idx // 12, idx % 12 + 1, 1)

    def _go_prev(self):
        self._selected_month = self._shift_month(self._selected_month, -1)
        self.load()

    def _go_next(self):
        self._selected_month = self._shift_month(self._selected_month, 1)
        self.load()

    def _refresh_nav(self):
        self._month_label.config(text=self._selected_month.strftime("%B %Y"))
        prev_enabled = self._selected_month > self._min_month
        next_enabled = self._selected_month < self._max_month
        self._prev_btn.config(
            bg="#e5e7eb" if prev_enabled else "#d1d5db",
            fg=TEXT if prev_enabled else MUTED,
            cursor="hand2" if prev_enabled else "arrow",
        )
        self._next_btn.config(
            bg="#e5e7eb" if next_enabled else "#d1d5db",
            fg=TEXT if next_enabled else MUTED,
            cursor="hand2" if next_enabled else "arrow",
        )

    # ── data loading ─────────────────────────────────────────────────────────
    def _compute_spending_by_tag(self, month_start, month_end):
        """Return dict {tag_id_str: total_spent} for regular (non-balance, non-irregular) txns."""
        transactions = alerts.read_transactions_csv()
        tag_dict = alerts.read_tags_csv()
        assignments = alerts.read_assignments_csv()

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

        by_tag = defaultdict(float)
        for row in transactions:
            try:
                date_value = datetime.strptime(row["Date"], "%Y-%m-%d")
                amount = float(row["Amount"])
            except (ValueError, KeyError):
                continue
            if date_value < month_start or date_value >= month_end:
                continue
            tid = row.get("ID")
            tags_list = tag_map.get(tid, [])
            # skip balance / irregular
            skip = False
            for t in tags_list:
                ttype = t.get("Tag_type", "").strip().lower()
                if ttype in (adjustments.BALANCE_TAG_TYPE.lower(), adjustments.IRREGULAR_TAG_TYPE.lower()):
                    skip = True
                    break
            if skip:
                continue
            for t in tags_list:
                by_tag[t.get("Tag_id", "")] += amount
        return by_tag

    def load(self):
        zebra(self.tree)
        transactions = alerts.read_transactions_csv()
        # update min/max from data
        today = datetime.today()
        current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        months_in_data = set()
        for row in transactions:
            try:
                d = datetime.strptime(row["Date"], "%Y-%m-%d")
            except (ValueError, KeyError):
                continue
            months_in_data.add(d.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
        if months_in_data:
            self._min_month = min(months_in_data)
            self._max_month = max(max(months_in_data), current_month)
        else:
            self._min_month = current_month
            self._max_month = current_month
        self._selected_month = max(self._min_month, min(self._selected_month, self._max_month))
        self._refresh_nav()

        month_start = self._selected_month
        month_end = self._shift_month(month_start, 1)
        spending = self._compute_spending_by_tag(month_start, month_end)

        budgets = alerts.read_budget_csv()
        tag_dict = alerts.read_tags_csv()

        self.tree.delete(*self.tree.get_children())
        total_budget = 0.0
        total_spent = 0.0

        budgeted_tag_ids = set()
        OTHERS_TAG_ID = "0"
        others_budget = budgets.get((OTHERS_TAG_ID, "monthly"), None)
        checked_ids = self._selected_ids.copy()

        for (tag_id, period), budget_amount in sorted(
            budgets.items(),
            key=lambda item: (int(item[0][0]) if item[0][0].isdigit() else -1),
        ):
            if tag_id == OTHERS_TAG_ID:
                continue  # handled separately after the loop
            tag_name = tag_dict.get(tag_id, {}).get("Tag_name", f"Tag {tag_id}")
            spent = spending.get(tag_id, 0.0)
            remaining = budget_amount - spent
            pct = (spent / budget_amount * 100) if budget_amount > 0 else 0.0

            total_budget += budget_amount
            total_spent += spent
            budgeted_tag_ids.add(tag_id)

            row_tag = "over" if spent > budget_amount else ("warn" if pct >= 80 else "")
            mark = "✓" if tag_id in checked_ids else ""
            self.tree.insert(
                "", "end",
                values=(mark, tag_id, tag_name,
                        f"HK${budget_amount:.2f}",
                        f"HK${spent:.2f}",
                        f"HK${remaining:.2f}",
                        f"{pct:.0f}%"),
                tags=(row_tag,) if row_tag else (),
            )
            if mark == "✓":
                self._selected_ids.add(tag_id)

        # ── Others row ───────────────────────────────────────────────────────
        others_spent = sum(amt for tid, amt in spending.items() if tid not in budgeted_tag_ids)
        total_spent += others_spent
        if others_budget is not None:
            total_budget += others_budget
            remaining = others_budget - others_spent
            pct = (others_spent / others_budget * 100) if others_budget > 0 else 0.0
            row_tag = "over" if others_spent > others_budget else ("warn" if pct >= 80 else "")
            self.tree.insert(
                "", "end",
                values=("", OTHERS_TAG_ID, "Others",
                        f"HK${others_budget:.2f}",
                        f"HK${others_spent:.2f}",
                        f"HK${remaining:.2f}",
                        f"{pct:.0f}%"),
                tags=(row_tag,) if row_tag else (),
            )
        elif others_spent > 0:
            self.tree.insert(
                "", "end",
                values=("", "–", "Others", "–", f"HK${others_spent:.2f}", "–", "–"),
            )

        repaint_tree(self.tree)

        total_remaining = total_budget - total_spent
        self._lbl_total_budget.config(text=f"Total Budget: HK${total_budget:.2f}")
        self._lbl_total_spent.config(
            text=f"Total Spent: HK${total_spent:.2f}",
            fg=DANGER if total_spent > total_budget else TEXT,
        )
        self._lbl_remaining.config(
            text=f"Remaining: HK${total_remaining:.2f}",
            fg=DANGER if total_remaining < 0 else SUCCESS,
        )

    # ── checkbox & selection ────────────────────────────────────────────────
    def _on_click_check_column(self, event):
        """Toggle checkbox on first column click."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify("column", event.x, event.y)
        if column != "#1":
            return
        item = self.tree.identify("item", event.x, event.y)
        if not item:
            return
        values = list(self.tree.item(item, "values"))
        tag_id = str(values[1])  # second column (Tag ID)
        if values[0] == "✓":
            values[0] = ""
            self._selected_ids.discard(tag_id)
        else:
            values[0] = "✓"
            self._selected_ids.add(tag_id)
        self.tree.item(item, values=values)

    def _select_all_toggle(self):
        """Toggle select all / deselect all for visible budget rows."""
        children = self.tree.get_children("")
        if not children:
            return
        all_checked = all(self.tree.item(ch, "values")[0] == "✓" for ch in children)
        for ch in children:
            vals = list(self.tree.item(ch, "values"))
            tag_id = str(vals[1])
            if all_checked:
                vals[0] = ""
                self._selected_ids.discard(tag_id)
            else:
                # only select rows that have a valid budget (not "–")
                if tag_id != "–":
                    vals[0] = "✓"
                    self._selected_ids.add(tag_id)
            self.tree.item(ch, values=vals)

    # ── delete logic ─────────────────────────────────────────────────────────
    def _delete_selected(self):
        """Delete checked budget rows, or fallback to single selection."""
        if self._selected_ids:
            ids_to_delete = self._selected_ids.copy()
        else:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("No selection", "Select a budget to delete.")
                return
            row = self.tree.item(selection[0], "values")
            tag_id = str(row[1])
            if tag_id == "–":
                messagebox.showinfo("Info", "The Others row has no budget to delete.")
                return
            ids_to_delete = {tag_id}

        count = len(ids_to_delete)
        period = "monthly"
        if app_settings.read_settings().get("confirm_delete", True):
            if not messagebox.askyesno("Confirm Delete", f"Delete {count} selected budget(s)?"):
                return

        budgets = alerts.read_budget_csv()
        for tid in ids_to_delete:
            key = (tid, period)
            if key in budgets:
                del budgets[key]
        alerts.write_budget_csv(budgets)
        self._selected_ids.clear()
        self.load()

    def _add_dialog(self):
        AddBudgetDialog(self, on_save=self.load)


class AddBudgetDialog(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Add / Update Budget")
        self.geometry("400x310")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        tk.Label(self, text="Add / Update Budget", bg=BG, fg=TEXT, font=FONT_H).pack(
            anchor="w",
            padx=28,
            pady=(20, 4),
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(0, 12))

        form = tk.Frame(self, bg=BG)
        form.pack(padx=28, fill="x")

        self._tag_dict = alerts.read_tags_csv()
        options = ["0: Others (untagged spending)"]
        options += [
            f"{value['Tag_id']}: {value['Tag_type']} – {value['Tag_name']}"
            for value in sorted(self._tag_dict.values(), key=lambda item: int(item["Tag_id"]))
        ]

        tk.Label(
            form,
            text="Tag",
            bg=BG,
            fg=TEXT,
            font=(FONT_FAMILY, 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 3))
        self.tag_combo = ttk.Combobox(form, values=options, state="readonly", font=FONT)
        self.tag_combo.current(0)
        self.tag_combo.pack(fill="x", ipady=4)

        tk.Label(
            form,
            text="Period",
            bg=BG,
            fg=TEXT,
            font=(FONT_FAMILY, 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 3))
        self.period_combo = ttk.Combobox(form, values=["Monthly"], state="readonly", font=FONT)
        self.period_combo.current(0)
        self.period_combo.pack(fill="x", ipady=4)

        tk.Label(
            form,
            text="Budget Amount (HK$)",
            bg=BG,
            fg=TEXT,
            font=(FONT_FAMILY, 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 3))
        self.amount_var = tk.StringVar()
        tk.Entry(form, textvariable=self.amount_var, font=FONT, relief="solid", bd=1).pack(fill="x", ipady=5)

        button_row = tk.Frame(self, bg=BG)
        button_row.pack(pady=22)
        button(button_row, "Save Budget", self._save, SUCCESS, pady=10).pack(side="left", padx=6)
        button(button_row, "Cancel", self.destroy, DANGER, pady=10).pack(side="left", padx=6)

    def _save(self):
        selection = self.tag_combo.get()
        tag_id = selection.split(":")[0].strip()
        period = self.period_combo.get().lower()
        try:
            amount = float(self.amount_var.get().strip())
            if amount < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter a valid positive amount.", parent=self)
            return
        budgets = alerts.read_budget_csv()
        budgets[(tag_id, period)] = amount
        alerts.write_budget_csv(budgets)
        self.on_save()
        self.destroy()