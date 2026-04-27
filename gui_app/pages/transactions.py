import csv
from collections import defaultdict
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import core.adjustments as adjustments
import core.transaction as transaction

from ..base import Page
from ..constants import ACCENT, BG, BORDER, DANGER, FONT, FONT_H, SUCCESS, TEXT
from ..helpers import button, card, repaint_tree, safe_float, safe_read_tags, zebra


class TransactionsPage(Page):
    def build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(top, text="Transactions", bg=BG, fg=TEXT, font=FONT_H).pack(side="left")

        buttons = tk.Frame(top, bg=BG)
        buttons.pack(side="right", anchor="s")
        button(buttons, "Peer Balance Entry", self._peer_dialog, "#8b5cf6").pack(side="left", padx=4)
        button(buttons, "+ Add Transaction", self._add_dialog, SUCCESS).pack(side="left", padx=4)
        button(buttons, "↑ Import CSV", self._import_csv, ACCENT).pack(side="left", padx=4)
        button(buttons, "Delete Selected", self._delete_selected, DANGER).pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 10))

        transactions_card = card(self)
        transactions_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        columns = ("ID", "Date", "Name", "Description", "Amount", "Tags")
        self.tree = ttk.Treeview(
            transactions_card,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Modern.Treeview",
        )
        widths = {
            "ID": 45,
            "Date": 100,
            "Name": 170,
            "Description": 230,
            "Amount": 100,
            "Tags": 190,
        }
        anchors = {"ID": "center", "Date": "center", "Amount": "e"}
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=widths[column], anchor=anchors.get(column, "w"))

        zebra(self.tree)
        scrollbar = ttk.Scrollbar(transactions_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    def load(self):
        self.tree.delete(*self.tree.get_children())
        try:
            transactions = transaction._load_transactions()
            assignments = transaction._load_assignments()
            tag_dict = safe_read_tags()
        except Exception:
            return

        tag_map = defaultdict(list)
        for assignment in assignments:
            transaction_id = assignment.get("ID")
            tag_id = assignment.get("TagID")
            tag = tag_dict.get(tag_id)
            if tag:
                tag_map[transaction_id].append(tag.get("Tag_name", ""))

        for row in transactions:
            transaction_id = row.get("ID", "")
            tag_string = ", ".join(tag_map.get(transaction_id, [])) or "—"
            self.tree.insert(
                "",
                "end",
                values=(
                    transaction_id,
                    row.get("Date", ""),
                    row.get("Name", ""),
                    row.get("Transaction Description", ""),
                    f"HK${safe_float(row.get('Amount')):.2f}",
                    tag_string,
                ),
            )
        repaint_tree(self.tree)

    def _delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No selection", "Select a transaction to delete.")
            return
        row = self.tree.item(selection[0], "values")
        transaction_id, name = str(row[0]), row[2]
        if not messagebox.askyesno("Confirm Delete", f"Delete transaction #{transaction_id} '{name}'?"):
            return
        transactions = transaction._load_transactions()
        assignments = transaction._load_assignments()
        transaction._save_transactions([item for item in transactions if item["ID"] != transaction_id])
        transaction._save_assignments([item for item in assignments if item["ID"] != transaction_id])
        self.load()

    def _add_dialog(self):
        AddTransactionDialog(self, on_save=self.load)

    def _peer_dialog(self):
        AddPeerBalanceDialog(self, on_save=self.load)

    def _import_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        message = self._run_csv_import(path)
        messagebox.showinfo("Import Result", message)
        self.load()

    def _run_csv_import(self, file_path):
        imported_rows = []
        try:
            with open(file_path, mode="r", newline="") as file_handle:
                reader = csv.DictReader(file_handle)
                columns = set(reader.fieldnames or [])
                required = {"Date", "Name", "Amount"}
                if not required.issubset(columns):
                    return f"[Error] Missing columns: {required - columns}"
                has_tag_columns = "Tag_type" in columns and "Tag_name" in columns
                for row in reader:
                    date_value = row.get("Date", "").strip()
                    name = row.get("Name", "").strip()
                    description = row.get("Transaction Description", "").strip()
                    amount = row.get("Amount", "").strip()
                    tag_type = row.get("Tag_type", "").strip() if has_tag_columns else ""
                    tag_name = row.get("Tag_name", "").strip() if has_tag_columns else ""
                    if not transaction._validate_date(date_value):
                        continue
                    if not name:
                        continue
                    if transaction._validate_amount(amount) is None:
                        continue
                    imported_rows.append(
                        {
                            "Date": date_value,
                            "Name": name,
                            "Transaction Description": description,
                            "Amount": amount,
                            "Tag_type": tag_type,
                            "Tag_name": tag_name,
                        }
                    )
        except Exception as exc:
            return f"[Error] {exc}"

        if not imported_rows:
            return "[Info] No valid transactions found in file."

        transactions = transaction._load_transactions()
        next_id = transaction._get_next_transaction_id(transactions)
        for row in imported_rows:
            tag_type = row.pop("Tag_type")
            tag_name = row.pop("Tag_name")
            row["ID"] = next_id
            transactions.append(row)
            if tag_type:
                transaction._link_tag_to_transaction(next_id, tag_type, tag_name)
            next_id = str(int(next_id) + 1)
        transaction._save_transactions(transactions)
        return f"[Success] Imported {len(imported_rows)} transaction(s)."


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
            anchor="w",
            padx=28,
            pady=(20, 4),
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(0, 12))

        form = tk.Frame(self, bg=BG)
        form.pack(padx=28, fill="x")

        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.name_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.amount_var = tk.StringVar()

        fields = [
            ("Date (YYYY-MM-DD)", self.date_var),
            ("Name", self.name_var),
            ("Description (optional)", self.desc_var),
            ("Amount (HK$)", self.amount_var),
        ]
        for label, variable in fields:
            tk.Label(
                form,
                text=label,
                bg=BG,
                fg=TEXT,
                font=("Helvetica Neue", 10, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(10, 3))
            tk.Entry(
                form,
                textvariable=variable,
                font=FONT,
                relief="solid",
                bd=1,
                highlightthickness=0,
            ).pack(fill="x", ipady=5)

        tk.Label(
            form,
            text="Assign Tag (optional)",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 3))
        self._tag_dict = safe_read_tags()
        options = ["— None —"] + [
            f"{value['Tag_id']}: {value['Tag_type']} – {value['Tag_name']}"
            for value in sorted(self._tag_dict.values(), key=lambda item: int(item["Tag_id"]))
        ]
        self.tag_combo = ttk.Combobox(form, values=options, state="readonly", font=FONT)
        self.tag_combo.current(0)
        self.tag_combo.pack(fill="x", ipady=4)

        button_row = tk.Frame(self, bg=BG)
        button_row.pack(pady=22)
        button(button_row, "Save Transaction", self._save, SUCCESS).pack(side="left", padx=6)
        button(button_row, "Cancel", self.destroy, DANGER).pack(side="left", padx=6)

    def _save(self):
        date_value = self.date_var.get().strip()
        name = self.name_var.get().strip()
        description = self.desc_var.get().strip()
        amount = self.amount_var.get().strip()

        if not transaction._validate_date(date_value):
            messagebox.showerror("Error", "Invalid date. Use YYYY-MM-DD.", parent=self)
            return
        if not name:
            messagebox.showerror("Error", "Name cannot be empty.", parent=self)
            return
        if transaction._validate_amount(amount) is None:
            messagebox.showerror("Error", "Amount must be a positive number.", parent=self)
            return

        transactions = transaction._load_transactions()
        new_id = transaction._get_next_transaction_id(transactions)
        transactions.append(
            {
                "ID": new_id,
                "Date": date_value,
                "Name": name,
                "Transaction Description": description,
                "Amount": amount,
            }
        )
        transaction._save_transactions(transactions)

        selection = self.tag_combo.get()
        if selection and not selection.startswith("—"):
            tag_id = selection.split(":")[0].strip()
            assignments = transaction._load_assignments()
            assignments.append({"ID": new_id, "TagID": tag_id})
            transaction._save_assignments(assignments)

        self.on_save()
        self.destroy()


class AddPeerBalanceDialog(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Record Peer Balance")
        self.geometry("460x560")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._recent_entries = adjustments.list_recent_peer_entries(limit=20)

        tk.Label(self, text="Peer Balance Entry", bg=BG, fg=TEXT, font=FONT_H).pack(
            anchor="w",
            padx=28,
            pady=(20, 4),
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(0, 12))

        quick_row = tk.Frame(self, bg=BG)
        quick_row.pack(fill="x", padx=28, pady=(0, 8))
        button(quick_row, "Duplicate Last", self._duplicate_last_entry, "#8b5cf6").pack(side="left", padx=(0, 6))
        button(quick_row, "Suggest Opposite", self._apply_opposite_suggestion, "#374151").pack(side="left")

        form = tk.Frame(self, bg=BG)
        form.pack(padx=28, fill="x")

        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.peer_var = tk.StringVar()
        self.direction_var = tk.StringVar(value="out")
        self.amount_var = tk.StringVar()
        self.desc_var = tk.StringVar()

        tk.Label(
            form,
            text="Date (YYYY-MM-DD)",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(8, 3))
        tk.Entry(form, textvariable=self.date_var, font=FONT, relief="solid", bd=1, highlightthickness=0).pack(
            fill="x", ipady=5
        )

        tk.Label(
            form,
            text="Peer",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 3))
        peer_options = self._build_peer_options()
        self.peer_combo = ttk.Combobox(form, textvariable=self.peer_var, values=peer_options, font=FONT)
        self.peer_combo.pack(fill="x", ipady=5)
        self.peer_combo.bind("<<ComboboxSelected>>", self._on_peer_change)
        self.peer_combo.bind("<FocusOut>", self._on_peer_change)
        if peer_options:
            self.peer_combo.set(peer_options[0])

        tk.Label(
            form,
            text="Recent Peers",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 9, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(8, 3))
        chips = tk.Frame(form, bg=BG)
        chips.pack(fill="x")
        for peer_name in self._recent_peer_names(limit=6):
            tk.Button(
                chips,
                text=peer_name,
                bg="#e5e7eb",
                fg=TEXT,
                relief="flat",
                bd=0,
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda peer=peer_name: self._select_recent_peer(peer),
            ).pack(side="left", padx=(0, 6), pady=(0, 2))

        tk.Label(
            form,
            text="Direction",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 3))
        direction_row = tk.Frame(form, bg=BG)
        direction_row.pack(fill="x")
        tk.Radiobutton(
            direction_row,
            text="I paid (Out)",
            value="out",
            variable=self.direction_var,
            bg=BG,
            fg=TEXT,
            selectcolor=BG,
            activebackground=BG,
            activeforeground=TEXT,
        ).pack(side="left")
        tk.Radiobutton(
            direction_row,
            text="I received (In)",
            value="in",
            variable=self.direction_var,
            bg=BG,
            fg=TEXT,
            selectcolor=BG,
            activebackground=BG,
            activeforeground=TEXT,
        ).pack(side="left", padx=(12, 0))

        tk.Label(
            form,
            text="Amount (HK$)",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 3))
        tk.Entry(form, textvariable=self.amount_var, font=FONT, relief="solid", bd=1, highlightthickness=0).pack(
            fill="x", ipady=5
        )

        tk.Label(
            form,
            text="Description (optional)",
            bg=BG,
            fg=TEXT,
            font=("Helvetica Neue", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 3))
        tk.Entry(form, textvariable=self.desc_var, font=FONT, relief="solid", bd=1, highlightthickness=0).pack(
            fill="x", ipady=5
        )

        hint = tk.Label(
            form,
            text="This creates a transaction and links the correct Balance + Peer tag automatically.",
            bg=BG,
            fg="#6b7280",
            font=("Helvetica Neue", 9),
            anchor="w",
            justify="left",
            wraplength=360,
        )
        hint.pack(fill="x", pady=(12, 0))

        self.suggestion_var = tk.StringVar(value="")
        tk.Label(
            form,
            textvariable=self.suggestion_var,
            bg=BG,
            fg="#8b5cf6",
            font=("Helvetica Neue", 9, "bold"),
            anchor="w",
            justify="left",
            wraplength=360,
        ).pack(fill="x", pady=(6, 0))

        button_row = tk.Frame(self, bg=BG)
        button_row.pack(pady=20)
        button(button_row, "Save Entry", self._save, SUCCESS).pack(side="left", padx=6)
        button(button_row, "Cancel", self.destroy, DANGER).pack(side="left", padx=6)

        self._apply_peer_suggestion_if_available()

    def _build_peer_options(self):
        names = []
        seen = set()
        for peer in adjustments.list_peer_names():
            key = peer.lower()
            if key not in seen:
                names.append(peer)
                seen.add(key)
        for entry in self._recent_entries:
            peer = entry["peer"]
            key = peer.lower()
            if key not in seen:
                names.append(peer)
                seen.add(key)
        return names

    def _recent_peer_names(self, limit=6):
        peers = []
        seen = set()
        for entry in self._recent_entries:
            peer = entry["peer"]
            key = peer.lower()
            if key in seen:
                continue
            peers.append(peer)
            seen.add(key)
            if len(peers) >= limit:
                break
        return peers

    def _find_last_entry_for_peer(self, peer_name):
        wanted = (peer_name or "").strip().lower()
        if not wanted:
            return None
        for entry in self._recent_entries:
            if entry["peer"].strip().lower() == wanted:
                return entry
        return None

    def _select_recent_peer(self, peer_name):
        self.peer_var.set(peer_name)
        self._apply_peer_suggestion_if_available()

    def _on_peer_change(self, _event=None):
        self._apply_peer_suggestion_if_available()

    def _apply_peer_suggestion_if_available(self):
        last = self._find_last_entry_for_peer(self.peer_var.get())
        if not last:
            self.suggestion_var.set("")
            return

        opposite = "in" if last["direction"] == "out" else "out"
        action_text = "received" if opposite == "in" else "paid"
        self.direction_var.set(opposite)
        if not self.amount_var.get().strip():
            self.amount_var.set(f"{last['amount']:.2f}")
        self.suggestion_var.set(
            f"Suggestion: set to {action_text} HK${last['amount']:.2f} (opposite of last entry on {last['date']})."
        )

    def _duplicate_last_entry(self):
        if not self._recent_entries:
            messagebox.showinfo("No recent entry", "No previous peer entries found.", parent=self)
            return
        last = self._recent_entries[0]
        self.date_var.set(datetime.today().strftime("%Y-%m-%d"))
        self.peer_var.set(last["peer"])
        self.direction_var.set(last["direction"])
        self.amount_var.set(f"{last['amount']:.2f}")
        self.desc_var.set(last["description"])
        self.suggestion_var.set(f"Duplicated last entry for {last['peer']} (date set to today).")

    def _apply_opposite_suggestion(self):
        peer = self.peer_var.get().strip()
        if not peer:
            messagebox.showinfo("Peer needed", "Choose a peer first.", parent=self)
            return
        last = self._find_last_entry_for_peer(peer)
        if not last:
            messagebox.showinfo("No history", "No previous entry found for this peer.", parent=self)
            return

        opposite = "in" if last["direction"] == "out" else "out"
        self.direction_var.set(opposite)
        self.amount_var.set(f"{last['amount']:.2f}")
        if not self.desc_var.get().strip():
            self.desc_var.set(f"Settlement with {peer}")
        self.suggestion_var.set(f"Applied opposite settlement based on {last['date']} entry.")

    def _save(self):
        date_value = self.date_var.get().strip()
        peer_name = self.peer_var.get().strip()
        amount = self.amount_var.get().strip()
        direction = self.direction_var.get().strip()
        description = self.desc_var.get().strip()

        if not transaction._validate_date(date_value):
            messagebox.showerror("Error", "Invalid date. Use YYYY-MM-DD.", parent=self)
            return
        if not peer_name:
            messagebox.showerror("Error", "Peer name cannot be empty.", parent=self)
            return
        if transaction._validate_amount(amount) is None:
            messagebox.showerror("Error", "Amount must be a positive number.", parent=self)
            return

        try:
            adjustments.record_peer_adjustment(
                date=date_value,
                peer_name=peer_name,
                amount=amount,
                direction=direction,
                description=description,
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)
            return

        self.on_save()
        self.destroy()