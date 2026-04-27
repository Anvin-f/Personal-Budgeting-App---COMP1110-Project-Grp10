import tkinter as tk
from tkinter import messagebox, ttk

import core.settings as app_settings
import core.tags as tags

from ..base import Page
from ..constants import BG, BORDER, DANGER, FONT, FONT_H, SUCCESS, TEXT
from ..helpers import button, card, repaint_tree, safe_read_tags, zebra


class TagsPage(Page):
    def build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(top, text="🏷️  Tags", bg=BG, fg=TEXT, font=FONT_H).pack(side="left")

        buttons = tk.Frame(top, bg=BG)
        buttons.pack(side="right", anchor="s")
        button(buttons, "➕  Add", self._add_dialog, SUCCESS).pack(side="left", padx=4)
        button(buttons, "✏️  Edit", self._edit_selected, "#0ea5e9").pack(side="left", padx=4)
        button(buttons, "🗑️  Delete", self._delete_selected, DANGER).pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(6, 10))

        tag_card = card(self)
        tag_card.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        columns = ("ID", "Type", "Name")
        self.tree = ttk.Treeview(tag_card, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Type", text="Tag Type")
        self.tree.heading("Name", text="Tag Name")
        self.tree.column("ID", width=55, anchor="center")
        self.tree.column("Type", width=240)
        self.tree.column("Name", width=340)

        zebra(self.tree)
        scrollbar = ttk.Scrollbar(tag_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _event: self._edit_selected())

    def load(self):
        self.tree.delete(*self.tree.get_children())
        tag_dict = safe_read_tags()
        for value in sorted(tag_dict.values(), key=lambda item: int(item["Tag_id"])):
            self.tree.insert("", "end", values=(value["Tag_id"], value["Tag_type"], value["Tag_name"]))
        repaint_tree(self.tree)

    def _delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No selection", "Select a tag to delete.")
            return
        row = self.tree.item(selection[0], "values")
        tag_id = str(row[0])
        if app_settings.read_settings().get("confirm_delete", True):
            if not messagebox.askyesno("Confirm Delete", f"Delete tag '{row[1]} – {row[2]}'?"):
                return
        try:
            tags.id_delete_tag(tag_id)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
        self._on_tags_changed()

    def _add_dialog(self):
        AddTagDialog(self, on_save=self._on_tags_changed)

    def _edit_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No selection", "Select a tag to edit.")
            return
        row = self.tree.item(selection[0], "values")
        tag_id = str(row[0])
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
                font=("Helvetica Neue", 10, "bold"),
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
                font=("Helvetica Neue", 10, "bold"),
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