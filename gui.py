"""
gui.py – Tkinter GUI for the Personal Budget Tracker
Run directly: python gui.py
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from collections import defaultdict
import csv
import io
import sys

import core.transaction as transaction
import core.tags as tags
import core.alerts as alerts

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#f5f7fa"
SIDEBAR = "#111827"
CARD    = "#ffffff"
ACCENT  = "#3b82f6"
TEXT    = "#000000"
MUTED   = "#4b5563"
SUCCESS = "#10b981"
DANGER  = "#ef4444"
BORDER  = "#e5e7eb"

FONT    = ("Helvetica Neue", 11)
FONT_H  = ("Helvetica Neue", 16, "bold")
FONT_SM = ("Helvetica Neue", 10)
FONT_XS = ("Helvetica Neue", 9)
SIDEBAR_FONT = ("Helvetica Neue", 11)


# ── Shared helpers ────────────────────────────────────────────────────────────
def _capture(fn, *args, **kwargs):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        fn(*args, **kwargs)
    finally:
        sys.stdout = old
    return buf.getvalue()


def _card(parent, **kw):
    return tk.Frame(parent, bg=CARD, relief="flat",
                    highlightbackground=BORDER, highlightthickness=1, **kw)


def _btn(parent, text, command, color=ACCENT, fg="white", **kw):
    b = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=fg, font=("Helvetica Neue", 10, "bold"),
        bd=0, cursor="hand2",
        activebackground=color, activeforeground=fg,
        relief="flat", padx=14, pady=7, **kw
    )
    return b


def _page_header(parent, title):
    """Renders a bold page title with a bottom divider line."""
    wrapper = tk.Frame(parent, bg=BG)
    wrapper.pack(fill="x", padx=24, pady=(18, 0))
    tk.Label(wrapper, text=title, bg=BG, fg=TEXT, font=FONT_H).pack(anchor="w")
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 0))


def _safe_read_tags():
    try:
        return tags.read_tag_csv()
    except Exception:
        return {}


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _zebra(tree):
    """Apply alternating row colours to a Treeview."""
    tree.tag_configure("odd",  background="#f9fafb")
    tree.tag_configure("even", background=CARD)


def _repaint_tree(tree):
    for i, iid in enumerate(tree.get_children()):
        tree.item(iid, tags=("odd" if i % 2 else "even",))


# ── Page base ─────────────────────────────────────────────────────────────────
class Page(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.build()
        self.load()

    def build(self):
        pass

    def load(self):
        pass


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardPage(Page):
    def build(self):
        _page_header(self, "Dashboard")

        # Stat cards
        cards_row = tk.Frame(self, bg=BG)
        cards_row.pack(fill="x", padx=24, pady=14)

        self._today_val  = self._stat_card(cards_row, "Today",        ACCENT)
        self._week_val   = self._stat_card(cards_row, "This Week",    "#8b5cf6")
        self._month_val  = self._stat_card(cards_row, "This Month",   "#f59e0b")
        self._safe_val   = self._stat_card(cards_row, "Safe / Day",   SUCCESS)

        # Alerts section
        tk.Label(self, text="Alerts & Notifications", bg=BG, fg=TEXT,
                 font=("Helvetica Neue", 12, "bold")).pack(
            anchor="w", padx=24, pady=(10, 4)
        )
        alert_card = _card(self)
        alert_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        self.alert_box = scrolledtext.ScrolledText(
            alert_card, font=FONT_SM, bg=CARD, fg=TEXT,
            relief="flat", wrap="word", state="disabled", padx=8, pady=8
        )
        self.alert_box.pack(fill="both", expand=True)

    def _stat_card(self, parent, label, accent_color):
        outer = tk.Frame(parent, bg=accent_color)
        outer.pack(side="left", fill="both", expand=True, padx=5)

        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="both", expand=True, padx=0, pady=(3, 0))

        tk.Label(inner, text=label.upper(), bg=CARD, fg=MUTED,
                 font=("Helvetica Neue", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
        val = tk.Label(inner, text="HK$0.00", bg=CARD, fg=accent_color,
                       font=("Helvetica Neue", 22, "bold"))
        val.pack(anchor="w", padx=14, pady=(0, 14))
        return val

    def load(self):
        txns     = alerts.read_transactions_csv()
        today    = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        week_cut = today - timedelta(days=6)

        t_today = t_week = t_month = 0.0
        for t in txns:
            try:
                d   = datetime.strptime(t["Date"], "%Y-%m-%d")
                amt = float(t["Amount"])
            except (ValueError, KeyError):
                continue
            if d >= today:
                t_today += amt
            if d >= week_cut:
                t_week += amt
            if d.year == today.year and d.month == today.month:
                t_month += amt

        self._today_val.config(text=f"HK${t_today:.2f}")
        self._week_val.config(text=f"HK${t_week:.2f}")
        self._month_val.config(text=f"HK${t_month:.2f}")

        budgets      = alerts.read_budget_csv()
        total_budget = sum(a for (_, p), a in budgets.items() if p == "monthly")
        days_left    = max(1, alerts._days_in_month(today) - today.day)
        safe_day     = (total_budget - t_month) / days_left if total_budget else 0.0
        self._safe_val.config(
            text=f"HK${safe_day:.2f}",
            fg=SUCCESS if safe_day >= 0 else DANGER
        )

        output = _capture(alerts.check_all_alerts)
        self.alert_box.config(state="normal")
        self.alert_box.delete("1.0", "end")
        self.alert_box.insert("end", output or "No alerts.")
        self.alert_box.config(state="disabled")


# ── Transactions ──────────────────────────────────────────────────────────────
class TransactionsPage(Page):
    def build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(top, text="Transactions", bg=BG, fg=TEXT, font=FONT_H).pack(side="left")

        btns = tk.Frame(top, bg=BG)
        btns.pack(side="right", anchor="s")
        _btn(btns, "+ Add Transaction", self._add_dialog, SUCCESS).pack(side="left", padx=4)
        _btn(btns, "↑ Import CSV",      self._import_csv, ACCENT ).pack(side="left", padx=4)
        _btn(btns, "Delete Selected",   self._delete_selected, DANGER).pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 10))

        card = _card(self)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        cols = ("ID", "Date", "Name", "Description", "Amount", "Tags")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                 selectmode="browse", style="Modern.Treeview")
        widths = {"ID": 45, "Date": 100, "Name": 170, "Description": 230,
                  "Amount": 100, "Tags": 190}
        anchors = {"ID": "center", "Date": "center", "Amount": "e"}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths[c], anchor=anchors.get(c, "w"))

        _zebra(self.tree)
        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    def load(self):
        self.tree.delete(*self.tree.get_children())
        try:
            txns     = transaction._load_transactions()
            asgns    = transaction._load_assignments()
            tag_dict = _safe_read_tags()
        except Exception:
            return

        tag_map = defaultdict(list)
        for a in asgns:
            tid   = a.get("ID")
            tagid = a.get("TagID")
            tag   = tag_dict.get(tagid)
            if tag:
                tag_map[tid].append(tag.get("Tag_name", ""))

        for t in txns:
            tid     = t.get("ID", "")
            tag_str = ", ".join(tag_map.get(tid, [])) or "—"
            self.tree.insert("", "end", values=(
                tid,
                t.get("Date", ""),
                t.get("Name", ""),
                t.get("Transaction Description", ""),
                f"HK${_safe_float(t.get('Amount')):.2f}",
                tag_str,
            ))
        _repaint_tree(self.tree)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a transaction to delete.")
            return
        row = self.tree.item(sel[0], "values")
        tid, name = str(row[0]), row[2]
        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete transaction #{tid} '{name}'?"):
            return
        txns  = transaction._load_transactions()
        asgns = transaction._load_assignments()
        transaction._save_transactions([t for t in txns  if t["ID"] != tid])
        transaction._save_assignments( [a for a in asgns if a["ID"] != tid])
        self.load()

    def _add_dialog(self):
        AddTransactionDialog(self, on_save=self.load)

    def _import_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        msg = self._run_csv_import(path)
        messagebox.showinfo("Import Result", msg)
        self.load()

    def _run_csv_import(self, file_path):
        imported = []
        try:
            with open(file_path, mode="r", newline="") as f:
                reader   = csv.DictReader(f)
                cols     = set(reader.fieldnames or [])
                required = {"Date", "Name", "Amount"}
                if not required.issubset(cols):
                    return f"[Error] Missing columns: {required - cols}"
                has_tag = "Tag_type" in cols and "Tag_name" in cols
                for _, row in enumerate(reader, start=2):
                    date   = row.get("Date",   "").strip()
                    name   = row.get("Name",   "").strip()
                    desc   = row.get("Transaction Description", "").strip()
                    amount = row.get("Amount", "").strip()
                    ttype  = row.get("Tag_type", "").strip() if has_tag else ""
                    tname  = row.get("Tag_name", "").strip() if has_tag else ""
                    if not transaction._validate_date(date): continue
                    if not name:                              continue
                    if transaction._validate_amount(amount) is None: continue
                    imported.append({"Date": date, "Name": name,
                                     "Transaction Description": desc,
                                     "Amount": amount,
                                     "Tag_type": ttype, "Tag_name": tname})
        except Exception as e:
            return f"[Error] {e}"

        if not imported:
            return "[Info] No valid transactions found in file."

        txns   = transaction._load_transactions()
        nxt_id = transaction._get_next_transaction_id(txns)
        for row in imported:
            ttype = row.pop("Tag_type")
            tname = row.pop("Tag_name")
            row["ID"] = nxt_id
            txns.append(row)
            if ttype:
                transaction._link_tag_to_transaction(nxt_id, ttype, tname)
            nxt_id = str(int(nxt_id) + 1)
        transaction._save_transactions(txns)
        return f"[Success] Imported {len(imported)} transaction(s)."


class AddTransactionDialog(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Add Transaction")
        self.geometry("440x520")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        tk.Label(self, text="New Transaction", bg=BG, fg=TEXT, font=FONT_H).pack(
            anchor="w", padx=28, pady=(20, 4)
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(0, 12))

        form = tk.Frame(self, bg=BG)
        form.pack(padx=28, fill="x")

        self.date_var   = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.name_var   = tk.StringVar()
        self.desc_var   = tk.StringVar()
        self.amount_var = tk.StringVar()

        for label, var in [
            ("Date (YYYY-MM-DD)",      self.date_var),
            ("Name",                   self.name_var),
            ("Description (optional)", self.desc_var),
            ("Amount (HK$)",           self.amount_var),
        ]:
            tk.Label(form, text=label, bg=BG, fg=TEXT,
                     font=("Helvetica Neue", 10, "bold"), anchor="w").pack(
                fill="x", pady=(10, 3)
            )
            tk.Entry(form, textvariable=var, font=FONT, relief="solid", bd=1,
                     highlightthickness=0).pack(fill="x", ipady=5)

        tk.Label(form, text="Assign Tag (optional)", bg=BG, fg=TEXT,
                 font=("Helvetica Neue", 10, "bold"), anchor="w").pack(
            fill="x", pady=(10, 3)
        )
        self._tag_dict = _safe_read_tags()
        options = ["— None —"] + [
            f"{v['Tag_id']}: {v['Tag_type']} – {v['Tag_name']}"
            for v in sorted(self._tag_dict.values(), key=lambda x: int(x["Tag_id"]))
        ]
        self.tag_combo = ttk.Combobox(form, values=options, state="readonly", font=FONT)
        self.tag_combo.current(0)
        self.tag_combo.pack(fill="x", ipady=4)

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=22)
        _btn(btn_row, "Save Transaction", self._save,   SUCCESS).pack(side="left", padx=6)
        _btn(btn_row, "Cancel",           self.destroy, DANGER ).pack(side="left", padx=6)

    def _save(self):
        date   = self.date_var.get().strip()
        name   = self.name_var.get().strip()
        desc   = self.desc_var.get().strip()
        amount = self.amount_var.get().strip()

        if not transaction._validate_date(date):
            messagebox.showerror("Error", "Invalid date. Use YYYY-MM-DD.", parent=self)
            return
        if not name:
            messagebox.showerror("Error", "Name cannot be empty.", parent=self)
            return
        if transaction._validate_amount(amount) is None:
            messagebox.showerror("Error", "Amount must be a positive number.", parent=self)
            return

        txns   = transaction._load_transactions()
        new_id = transaction._get_next_transaction_id(txns)
        txns.append({"ID": new_id, "Date": date, "Name": name,
                     "Transaction Description": desc, "Amount": amount})
        transaction._save_transactions(txns)

        sel = self.tag_combo.get()
        if sel and not sel.startswith("—"):
            tag_id = sel.split(":")[0].strip()
            asgns  = transaction._load_assignments()
            asgns.append({"ID": new_id, "TagID": tag_id})
            transaction._save_assignments(asgns)

        self.on_save()
        self.destroy()


# ── Tags ──────────────────────────────────────────────────────────────────────
class TagsPage(Page):
    def build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(top, text="Tags", bg=BG, fg=TEXT, font=FONT_H).pack(side="left")

        btns = tk.Frame(top, bg=BG)
        btns.pack(side="right", anchor="s")
        _btn(btns, "+ Add Tag",      self._add_dialog,      SUCCESS).pack(side="left", padx=4)
        _btn(btns, "Delete Selected", self._delete_selected, DANGER ).pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 10))

        card = _card(self)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        cols = ("ID", "Type", "Name")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("ID",   text="ID")
        self.tree.heading("Type", text="Tag Type")
        self.tree.heading("Name", text="Tag Name")
        self.tree.column("ID",   width=55,  anchor="center")
        self.tree.column("Type", width=240)
        self.tree.column("Name", width=340)

        _zebra(self.tree)
        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    def load(self):
        self.tree.delete(*self.tree.get_children())
        tag_dict = _safe_read_tags()
        for v in sorted(tag_dict.values(), key=lambda x: int(x["Tag_id"])):
            self.tree.insert("", "end", values=(
                v["Tag_id"], v["Tag_type"], v["Tag_name"]
            ))
        _repaint_tree(self.tree)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a tag to delete.")
            return
        row    = self.tree.item(sel[0], "values")
        tag_id = str(row[0])
        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete tag '{row[1]} – {row[2]}'?"):
            return
        try:
            tags.id_delete_tag(tag_id)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.load()

    def _add_dialog(self):
        AddTagDialog(self, on_save=self.load)


class AddTagDialog(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Add Tag")
        self.geometry("380x280")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        tk.Label(self, text="New Tag", bg=BG, fg=TEXT, font=FONT_H).pack(
            anchor="w", padx=28, pady=(20, 4)
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(0, 12))

        form = tk.Frame(self, bg=BG)
        form.pack(padx=28, fill="x")

        self.type_var = tk.StringVar()
        self.name_var = tk.StringVar()
        for label, var in [("Tag Type", self.type_var), ("Tag Name", self.name_var)]:
            tk.Label(form, text=label, bg=BG, fg=TEXT,
                     font=("Helvetica Neue", 10, "bold"), anchor="w").pack(
                fill="x", pady=(10, 3)
            )
            tk.Entry(form, textvariable=var, font=FONT, relief="solid", bd=1).pack(
                fill="x", ipady=5
            )

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=22)
        _btn(btn_row, "Save Tag", self._save,   SUCCESS).pack(side="left", padx=6)
        _btn(btn_row, "Cancel",   self.destroy, DANGER ).pack(side="left", padx=6)

    def _save(self):
        ttype = self.type_var.get().strip()
        tname = self.name_var.get().strip()
        if not ttype or not tname:
            messagebox.showerror("Error", "Both fields are required.", parent=self)
            return
        tag_dict = _safe_read_tags()
        new_id   = tags.get_next_tag_id(tag_dict) if tag_dict else "1"
        tag_dict[new_id] = {"Tag_id": new_id, "Tag_type": ttype, "Tag_name": tname}
        tags.write_tag_csv(tag_dict)
        self.on_save()
        self.destroy()


# ── Budget ────────────────────────────────────────────────────────────────────
class BudgetPage(Page):
    def build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(top, text="Budgets", bg=BG, fg=TEXT, font=FONT_H).pack(side="left")

        btns = tk.Frame(top, bg=BG)
        btns.pack(side="right", anchor="s")
        _btn(btns, "+ Add Budget",    self._add_dialog,      SUCCESS).pack(side="left", padx=4)
        _btn(btns, "Delete Selected", self._delete_selected, DANGER ).pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 10))

        card = _card(self)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        cols = ("Tag ID", "Tag Name", "Period", "Budget (HK$)")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("Tag ID",       text="ID")
        self.tree.heading("Tag Name",     text="Tag Name")
        self.tree.heading("Period",       text="Period")
        self.tree.heading("Budget (HK$)", text="Budget (HK$)")
        self.tree.column("Tag ID",       width=65,  anchor="center")
        self.tree.column("Tag Name",     width=230)
        self.tree.column("Period",       width=110, anchor="center")
        self.tree.column("Budget (HK$)", width=150, anchor="e")

        _zebra(self.tree)
        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    def load(self):
        self.tree.delete(*self.tree.get_children())
        budgets  = alerts.read_budget_csv()
        tag_dict = alerts.read_tags_csv()
        for (tag_id, period), amount in sorted(
            budgets.items(), key=lambda x: int(x[0][0])
        ):
            tag_name = tag_dict.get(tag_id, {}).get("Tag_name", f"Tag {tag_id}")
            self.tree.insert("", "end", values=(
                tag_id, tag_name, period.title(), f"HK${amount:.2f}"
            ))
        _repaint_tree(self.tree)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a budget to delete.")
            return
        row    = self.tree.item(sel[0], "values")
        tag_id = str(row[0])
        period = row[2].lower()
        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete budget for '{row[1]}' ({period})?"):
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
            anchor="w", padx=28, pady=(20, 4)
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(0, 12))

        form = tk.Frame(self, bg=BG)
        form.pack(padx=28, fill="x")

        self._tag_dict = alerts.read_tags_csv()
        options = [
            f"{v['Tag_id']}: {v['Tag_type']} – {v['Tag_name']}"
            for v in sorted(self._tag_dict.values(), key=lambda x: int(x["Tag_id"]))
        ]
        if not options:
            messagebox.showwarning("No Tags", "Create a tag before adding a budget.",
                                   parent=parent)
            self.destroy()
            return

        tk.Label(form, text="Tag", bg=BG, fg=TEXT,
                 font=("Helvetica Neue", 10, "bold"), anchor="w").pack(
            fill="x", pady=(10, 3)
        )
        self.tag_combo = ttk.Combobox(form, values=options, state="readonly", font=FONT)
        self.tag_combo.current(0)
        self.tag_combo.pack(fill="x", ipady=4)

        tk.Label(form, text="Period", bg=BG, fg=TEXT,
                 font=("Helvetica Neue", 10, "bold"), anchor="w").pack(
            fill="x", pady=(10, 3)
        )
        self.period_combo = ttk.Combobox(form, values=["Monthly"],
                                         state="readonly", font=FONT)
        self.period_combo.current(0)
        self.period_combo.pack(fill="x", ipady=4)

        tk.Label(form, text="Budget Amount (HK$)", bg=BG, fg=TEXT,
                 font=("Helvetica Neue", 10, "bold"), anchor="w").pack(
            fill="x", pady=(10, 3)
        )
        self.amount_var = tk.StringVar()
        tk.Entry(form, textvariable=self.amount_var, font=FONT,
                 relief="solid", bd=1).pack(fill="x", ipady=5)

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=22)
        _btn(btn_row, "Save Budget", self._save,   SUCCESS).pack(side="left", padx=6)
        _btn(btn_row, "Cancel",      self.destroy, DANGER ).pack(side="left", padx=6)

    def _save(self):
        sel    = self.tag_combo.get()
        tag_id = sel.split(":")[0].strip()
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


# ── Analysis ──────────────────────────────────────────────────────────────────
class AnalysisPage(Page):
    def build(self):
        _page_header(self, "Analysis")

        paned = tk.PanedWindow(self, orient="horizontal", bg=BG,
                               sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=24, pady=(10, 18))

        chart_card = _card(paned)
        paned.add(chart_card, minsize=430)

        self.fig = Figure(figsize=(6, 6), dpi=90, facecolor=CARD)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.fig.tight_layout(pad=2.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        text_card = _card(paned)
        paned.add(text_card, minsize=250)

        tk.Label(text_card, text="Spending Summary", bg=CARD, fg=TEXT,
                 font=("Helvetica Neue", 12, "bold")).pack(
            anchor="w", padx=14, pady=(14, 4)
        )
        tk.Frame(text_card, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(0, 6))

        self.summary_box = scrolledtext.ScrolledText(
            text_card, font=FONT_SM, bg=CARD, fg=TEXT,
            relief="flat", wrap="word", state="disabled", padx=8
        )
        self.summary_box.pack(fill="both", expand=True, padx=6, pady=(0, 14))

    def load(self):
        txns     = alerts.read_transactions_csv()
        tag_dict = alerts.read_tags_csv()
        asgns    = alerts.read_assignments_csv()

        tag_map = {}
        for a in asgns:
            tid = a.get("ID")
            if tid and tid not in tag_map:
                tag_map[tid] = a.get("TagID")

        today      = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        week_cut   = today - timedelta(days=6)
        thirty_cut = today - timedelta(days=29)

        cat_today = defaultdict(float)
        cat_week  = defaultdict(float)
        cat_month = defaultdict(float)
        per_day   = defaultdict(float)
        t_today = t_week = t_month = 0.0

        for t in txns:
            try:
                d   = datetime.strptime(t["Date"], "%Y-%m-%d")
                amt = float(t["Amount"])
            except (ValueError, KeyError):
                continue
            tid      = t.get("ID")
            tag_id   = tag_map.get(tid)
            tag_name = (tag_dict.get(tag_id, {}).get("Tag_name", "Untagged")
                        if tag_id else "Untagged")

            if d >= today:
                cat_today[tag_name] += amt
                t_today += amt
            if d >= week_cut:
                cat_week[tag_name] += amt
                t_week += amt
            if d.year == today.year and d.month == today.month:
                cat_month[tag_name] += amt
                t_month += amt
            if d >= thirty_cut:
                per_day[d.strftime("%m/%d")] += amt

        self._draw_charts(cat_month, per_day)
        self._draw_summary(t_today, t_week, t_month, cat_today, cat_week, cat_month)

    def _draw_charts(self, cat_month, per_day):
        self.ax1.cla()
        self.ax2.cla()
        self.fig.patch.set_facecolor(CARD)
        for ax in (self.ax1, self.ax2):
            ax.set_facecolor("#f9fafb")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(BORDER)
            ax.spines["bottom"].set_color(BORDER)

        if cat_month:
            sorted_c = sorted(cat_month.items(), key=lambda x: x[1], reverse=True)
            labels   = [c for c, _ in sorted_c]
            amounts  = [a for _, a in sorted_c]
            bars = self.ax1.bar(labels, amounts, color=ACCENT, edgecolor="none",
                                zorder=2, width=0.55)
            self.ax1.grid(axis="y", linestyle="--", alpha=0.35, zorder=1)
            for bar, amt in zip(bars, amounts):
                self.ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(amounts) * 0.015,
                    f"${amt:.0f}", ha="center", va="bottom",
                    fontsize=7.5, color=TEXT, fontweight="bold"
                )
        else:
            self.ax1.text(0.5, 0.5, "No transactions this month",
                          ha="center", va="center", transform=self.ax1.transAxes,
                          color=MUTED, fontsize=10)

        self.ax1.set_title("Monthly Spending by Category", fontsize=10,
                           pad=8, color=TEXT, fontweight="bold")
        self.ax1.set_ylabel("HK$", fontsize=9, color=MUTED)
        self.ax1.tick_params(axis="x", rotation=30, labelsize=8, colors=TEXT)
        self.ax1.tick_params(axis="y", labelsize=8, colors=MUTED)

        if per_day:
            sorted_d = sorted(per_day.items())
            days     = [d for d, _ in sorted_d]
            amounts  = [a for _, a in sorted_d]
            self.ax2.bar(days, amounts, color=SUCCESS, edgecolor="none",
                         zorder=2, width=0.6)
            self.ax2.grid(axis="y", linestyle="--", alpha=0.35, zorder=1)
        else:
            self.ax2.text(0.5, 0.5, "No transactions in last 30 days",
                          ha="center", va="center", transform=self.ax2.transAxes,
                          color=MUTED, fontsize=10)

        self.ax2.set_title("Daily Spending (Last 30 Days)", fontsize=10,
                           pad=8, color=TEXT, fontweight="bold")
        self.ax2.set_ylabel("HK$", fontsize=9, color=MUTED)
        self.ax2.tick_params(axis="x", rotation=45, labelsize=7, colors=TEXT)
        self.ax2.tick_params(axis="y", labelsize=8, colors=MUTED)

        self.fig.tight_layout(pad=2.5)
        self.canvas.draw()

    def _draw_summary(self, t_today, t_week, t_month,
                      cat_today, cat_week, cat_month):
        def section(title, total, cats):
            lines = [f"{title}", f"Total: HK${total:.2f}"]
            if cats:
                for name, amt in sorted(cats.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"  {name}: HK${amt:.2f}")
            else:
                lines.append("  No transactions")
            return lines

        body = []
        body += section("TODAY",      t_today, cat_today)
        body.append("")
        body += section("THIS WEEK",  t_week,  cat_week)
        body.append("")
        body += section("THIS MONTH", t_month, cat_month)

        if cat_month:
            body.append("")
            body.append("TOP 3 CATEGORIES")
            for name, amt in sorted(cat_month.items(),
                                    key=lambda x: x[1], reverse=True)[:3]:
                body.append(f"  {name}: HK${amt:.2f}")

        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("end", "\n".join(body))
        self.summary_box.config(state="disabled")


# ── Main window ───────────────────────────────────────────────────────────────
class BudgetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Budget Tracker")
        self.geometry("1180x750")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._apply_styles()
        self._build_layout()

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=0)
        s.configure("TNotebook.Tab",
                    font=("Helvetica Neue", 10, "bold"),
                    padding=[16, 8],
                    background="#e5e7eb",
                    foreground=TEXT)
        s.map("TNotebook.Tab",
              background=[("selected", CARD)],
              foreground=[("selected", ACCENT)])

        s.configure("Treeview",
                    font=FONT,
                    rowheight=32,
                    background=CARD,
                    fieldbackground=CARD,
                    foreground=TEXT,
                    borderwidth=0)
        s.configure("Treeview.Heading",
                    font=("Helvetica Neue", 10, "bold"),
                    background="#f3f4f6",
                    foreground=TEXT,
                    relief="flat",
                    padding=(8, 6))
        s.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "white")])

        s.configure("TScrollbar",
                    background=BORDER, troughcolor=BG,
                    borderwidth=0, arrowsize=12)
        s.configure("TCombobox", font=FONT, foreground=TEXT)
        s.map("TCombobox", fieldbackground=[("readonly", CARD)])

    def _build_layout(self):
        # Sidebar
        sidebar = tk.Frame(self, bg=SIDEBAR, width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo area
        logo_frame = tk.Frame(sidebar, bg=SIDEBAR)
        logo_frame.pack(fill="x", pady=(24, 8))
        tk.Label(logo_frame, text="Budget", bg=SIDEBAR, fg="white",
                 font=("Helvetica Neue", 17, "bold")).pack(anchor="w", padx=18)
        tk.Label(logo_frame, text="Tracker", bg=SIDEBAR, fg=ACCENT,
                 font=("Helvetica Neue", 17, "bold")).pack(anchor="w", padx=18)

        tk.Frame(sidebar, bg="#374151", height=1).pack(fill="x", padx=14, pady=(4, 12))

        # Notebook (hidden tab bar — sidebar drives navigation)
        self.notebook = ttk.Notebook(self, style="TNotebook")
        self.notebook.pack(side="left", fill="both", expand=True)

        page_defs = [
            ("Dashboard",    DashboardPage),
            ("Transactions", TransactionsPage),
            ("Tags",         TagsPage),
            ("Budgets",      BudgetPage),
            ("Analysis",     AnalysisPage),
        ]
        self._pages = {}
        for name, cls in page_defs:
            page = cls(self.notebook)
            self.notebook.add(page, text=f"  {name}  ")
            self._pages[name] = page

        # Sidebar nav buttons
        self._nav_btns = []
        for i, (name, _) in enumerate(page_defs):
            btn = tk.Button(
                sidebar, text=f"    {name}",
                bg=SIDEBAR, fg="#d1d5db",
                font=SIDEBAR_FONT,
                bd=0, activebackground="#1f2937",
                activeforeground="white",
                cursor="hand2", anchor="w",
                relief="flat",
                command=lambda i=i: self._select_tab(i)
            )
            btn.pack(fill="x", padx=0, pady=1, ipady=8)
            self._nav_btns.append(btn)

        self._select_tab(0)

        tk.Frame(sidebar, bg=SIDEBAR).pack(fill="both", expand=True)

        tk.Frame(sidebar, bg="#374151", height=1).pack(fill="x", padx=14, pady=(0, 10))
        _btn(sidebar, "↻  Refresh All", self._refresh_all,
             color="#1f2937", fg="#d1d5db").pack(
            fill="x", padx=14, pady=(0, 20), ipady=4
        )

    def _select_tab(self, index):
        self.notebook.select(index)
        for i, btn in enumerate(self._nav_btns):
            if i == index:
                btn.config(bg="#1f2937", fg="white",
                           font=("Helvetica Neue", 11, "bold"))
            else:
                btn.config(bg=SIDEBAR, fg="#9ca3af",
                           font=SIDEBAR_FONT)

    def _refresh_all(self):
        for page in self._pages.values():
            page.load()


def main():
    app = BudgetApp()
    app.mainloop()


if __name__ == "__main__":
    main()
