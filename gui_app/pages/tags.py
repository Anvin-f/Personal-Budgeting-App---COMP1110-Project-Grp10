import tkinter as tk
from tkinter import messagebox, ttk

import core.settings as app_settings
import core.tags as tags

from ..base import Page
from ..constants import BG, BORDER, DANGER, FONT, FONT_H, SUCCESS, TEXT, FONT_FAMILY
from ..helpers import button, card, repaint_tree, safe_read_tags, zebra, bind_tree_sort


class TagsPage(Page):
    def build(self):
        self._selected_ids = set()  # tag IDs selected via checkbox

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(top, text="🏷️  Tags", bg=BG, fg=TEXT, font=FONT_H).pack(side="left")

        buttons = tk.Frame(top, bg=BG)
        buttons.pack(side="right", anchor="s")
        button(buttons, "➕  Add", self._add_dialog, SUCCESS).pack(side="left", padx=4)
        button(buttons, "✏️  Edit", self._edit_selected, "#0ea5e9").pack(side="left", padx=4)
        button(buttons, "☑  Select All", self._select_all_toggle, "#374151").pack(side="left", padx=4)
        button(buttons, "🗑️  Delete", self._delete_selected, DANGER).pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 10))

        tag_card = card(self)
        tag_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        columns = ("☐", "ID", "Type", "Name")
        self.tree = ttk.Treeview(tag_card, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("☐", text="☐")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Type", text="Tag Type")
        self.tree.heading("Name", text="Tag Name")
        self.tree.column("☐", width=30, anchor="center")
        self.tree.column("ID", width=55, anchor="center")
        self.tree.column("Type", width=240)
        self.tree.column("Name", width=340)

        zebra(self.tree)
        scrollbar = ttk.Scrollbar(tag_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _event: self._edit_selected())
        self.tree.bind("<Button-1>", self._on_click_check_column)

        # column sorting
        bind_tree_sort(self.tree, "☐", 0)
        bind_tree_sort(self.tree, "ID", 1, parse_fn=lambda v: int(v))
        bind_tree_sort(self.tree, "Type", 2)
        bind_tree_sort(self.tree, "Name", 3)

    def load(self):
        zebra(self.tree)
        self.tree.delete(*self.tree.get_children())
        tag_dict = safe_read_tags()
        # preserve checkbox states if possible
        checked = self._selected_ids.copy()
        for value in sorted(tag_dict.values(), key=lambda item: int(item["Tag_id"])):
            tid = value["Tag_id"]
            mark = "✓" if tid in checked else ""
            self.tree.insert("", "end", values=(mark, tid, value["Tag_type"], value["Tag_name"]))
        repaint_tree(self.tree)

    # ── checkbox handling ──────────────────────────────────────────────────
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
        if values[0] == "✓":
            values[0] = ""
            self._selected_ids.discard(str(values[1]))
        else:
            values[0] = "✓"
            self._selected_ids.add(str(values[1]))
        self.tree.item(item, values=values)

    def _select_all_toggle(self):
        """Toggle select all / deselect all."""
        children = self.tree.get_children("")
        if not children:
            return
        all_checked = all(self.tree.item(ch, "values")[0] == "✓" for ch in children)
        for ch in children:
            vals = list(self.tree.item(ch, "values"))
            if all_checked:
                vals[0] = ""
                self._selected_ids.discard(str(vals[1]))
            else:
                vals[0] = "✓"
                self._selected_ids.add(str(vals[1]))
            self.tree.item(ch, values=vals)

    # ── delete logic ────────────────────────────────────────────────────────
    def _delete_selected(self):
        """Delete checked tags, or fallback to single selected row."""
        if self._selected_ids:
            ids_to_delete = self._selected_ids.copy()
            count = len(ids_to_delete)
        else:
            # fallback to tree selection
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("No selection", "Select tags to delete.")
                return
            ids_to_delete = set()
            for sel in selection:
                row = self.tree.item(sel, "values")
                ids_to_delete.add(str(row[1]))  # ID column
            count = len(ids_to_delete)

        if app_settings.read_settings().get("confirm_delete", True):
            if not messagebox.askyesno("Confirm Delete", f"Delete {count} selected tag(s)?"):
                return

        for tid in ids_to_delete:
            try:
                tags.id_delete_tag(tid)
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to delete tag {tid}: {exc}")
        self._selected_ids.clear()
        self._on_tags_changed()

    # ── dialogs ─────────────────────────────────────────────────────────────
    def _add_dialog(self):
        AddTagDialog(self, on_save=self._on_tags_changed)

    def _edit_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No selection", "Select a tag to edit.")
            return
        row = self.tree.item(selection[0], "values")
        tag_id = str(row[1])   # index 1 is ID (index 0 is checkbox)
        EditTagDialog(self, tag_id=tag_id, on_save=self._on_tags_changed)

    def _on_tags_changed(self):
        self.load()
        top = self.winfo_toplevel()
        pages = getattr(top, "_pages", {})
        transactions_page = pages.get("Transactions") if isinstance(pages, dict) else None
        if transactions_page and hasattr(transactions_page, "load"):
            transactions_page.load()


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
            anchor="w",
            padx=28,
            pady=(20, 4),
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(0, 12))

        form = tk.Frame(self, bg=BG)
        form.pack(padx=28, fill="x")

        self.type_var = tk.StringVar()
        self.name_var = tk.StringVar()
        for label, variable in (("Tag Type", self.type_var), ("Tag Name", self.name_var)):
            tk.Label(
                form,
                text=label,
                bg=BG,
                fg=TEXT,
                font=(FONT_FAMILY, 10, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(10, 3))
            tk.Entry(form, textvariable=variable, font=FONT, relief="solid", bd=1).pack(fill="x", ipady=5)

        button_row = tk.Frame(self, bg=BG)
        button_row.pack(pady=22)
        button(button_row, "Save Tag", self._save, SUCCESS).pack(side="left", padx=6)
        button(button_row, "Cancel", self.destroy, DANGER).pack(side="left", padx=6)

    def _save(self):
        tag_type = self.type_var.get().strip()
        tag_name = self.name_var.get().strip()
        if not tag_type or not tag_name:
            messagebox.showerror("Error", "Both fields are required.", parent=self)
            return
        tag_dict = safe_read_tags()
        new_id = tags.get_next_tag_id(tag_dict) if tag_dict else "1"
        tag_dict[new_id] = {"Tag_id": new_id, "Tag_type": tag_type, "Tag_name": tag_name}
        tags.write_tag_csv(tag_dict)
        self.on_save()
        self.destroy()


class EditTagDialog(tk.Toplevel):
    def __init__(self, parent, tag_id, on_save):
        super().__init__(parent)
        self.tag_id = str(tag_id)
        self.on_save = on_save
        self.title("Edit Tag")
        self.geometry("380x280")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        tag_dict = safe_read_tags()
        row = tag_dict.get(self.tag_id)
        if not row:
            messagebox.showerror("Error", "Tag not found.", parent=self)
            self.destroy()
            return

        tk.Label(self, text=f"Edit Tag #{self.tag_id}", bg=BG, fg=TEXT, font=FONT_H).pack(
            anchor="w",
            padx=28,
            pady=(20, 4),
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(0, 12))

        form = tk.Frame(self, bg=BG)
        form.pack(padx=28, fill="x")

        self.type_var = tk.StringVar(value=row.get("Tag_type", ""))
        self.name_var = tk.StringVar(value=row.get("Tag_name", ""))

        for label, variable in (("Tag Type", self.type_var), ("Tag Name", self.name_var)):
            tk.Label(
                form,
                text=label,
                bg=BG,
                fg=TEXT,
                font=(FONT_FAMILY, 10, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(10, 3))
            tk.Entry(form, textvariable=variable, font=FONT, relief="solid", bd=1).pack(fill="x", ipady=5)

        button_row = tk.Frame(self, bg=BG)
        button_row.pack(pady=22)
        button(button_row, "Save Changes", self._save, SUCCESS).pack(side="left", padx=6)
        button(button_row, "Cancel", self.destroy, DANGER).pack(side="left", padx=6)

    def _save(self):
        tag_type = self.type_var.get().strip()
        tag_name = self.name_var.get().strip()
        if not tag_type or not tag_name:
            messagebox.showerror("Error", "Both fields are required.", parent=self)
            return

        tag_dict = safe_read_tags()
        if self.tag_id not in tag_dict:
            messagebox.showerror("Error", "Tag not found.", parent=self)
            return

        tag_dict[self.tag_id]["Tag_type"] = tag_type
        tag_dict[self.tag_id]["Tag_name"] = tag_name
        tags.write_tag_csv(tag_dict)
        self.on_save()
        self.destroy()