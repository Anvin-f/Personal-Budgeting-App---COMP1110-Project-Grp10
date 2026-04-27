import tkinter as tk
from tkinter import messagebox, ttk

import core.alerts as alerts

from ..base import Page
from ..constants import BG, BORDER, DANGER, FONT, FONT_H, SUCCESS, TEXT
from ..helpers import button, card, repaint_tree, zebra


class BudgetPage(Page):
    def build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(top, text="Budgets", bg=BG, fg=TEXT, font=FONT_H).pack(side="left")

        buttons = tk.Frame(top, bg=BG)
        buttons.pack(side="right", anchor="s")
        button(buttons, "+ Add Budget", self._add_dialog, SUCCESS).pack(side="left", padx=4)
        button(buttons, "Delete Selected", self._delete_selected, DANGER).pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 10))

        budget_card = card(self)
        budget_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        columns = ("Tag ID", "Tag Name", "Period", "Budget (HK$)")
        self.tree = ttk.Treeview(budget_card, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("Tag ID", text="ID")
        self.tree.heading("Tag Name", text="Tag Name")
        self.tree.heading("Period", text="Period")
        self.tree.heading("Budget (HK$)", text="Budget (HK$)")
        self.tree.column("Tag ID", width=65, anchor="center")
        self.tree.column("Tag Name", width=230)
        self.tree.column("Period", width=110, anchor="center")
        self.tree.column("Budget (HK$)", width=150, anchor="e")

        zebra(self.tree)
        scrollbar = ttk.Scrollbar(budget_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    def load(self):
        self.tree.delete(*self.tree.get_children())
        budgets = alerts.read_budget_csv()
        tag_dict = alerts.read_tags_csv()
        for (tag_id, period), amount in sorted(budgets.items(), key=lambda item: int(item[0][0])):
            tag_name = tag_dict.get(tag_id, {}).get("Tag_name", f"Tag {tag_id}")
            self.tree.insert("", "end", values=(tag_id, tag_name, period.title(), f"HK${amount:.2f}"))
        repaint_tree(self.tree)

    def _delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No selection", "Select a budget to delete.")
            return
        row = self.tree.item(selection[0], "values")
        tag_id = str(row[0])
        period = row[2].lower()
        if not messagebox.askyesno("Confirm Delete", f"Delete budget for '{row[1]}' ({period})?"):
            return
        budgets = alerts.read_budget_csv()
        key = (tag_id, period)
        if key in budgets:
            del budgets[key]
            alerts.write_budget_csv(budgets)
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
        options = [
            f"{value['Tag_id']}: {value['Tag_type']} – {value['Tag_name']}"
            for value in sorted(self._tag_dict.values(), key=lambda item: int(item["Tag_id"]))
        ]
        if not options:
            messagebox.showwarning("No Tags", "Create a tag before adding a budget.", parent=parent)
            self.destroy()
            return

        tk.Label(
            form,
            text="Tag",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 10, "bold"),
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
            font=("Helvetica Neue", 10, "bold"),
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
            font=("Helvetica Neue", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 3))
        self.amount_var = tk.StringVar()
        tk.Entry(form, textvariable=self.amount_var, font=FONT, relief="solid", bd=1).pack(fill="x", ipady=5)

        button_row = tk.Frame(self, bg=BG)
        button_row.pack(pady=22)
        button(button_row, "Save Budget", self._save, SUCCESS).pack(side="left", padx=6)
        button(button_row, "Cancel", self.destroy, DANGER).pack(side="left", padx=6)

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