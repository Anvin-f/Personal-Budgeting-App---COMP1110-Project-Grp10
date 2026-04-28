"""Base Page class that all content pages inherit from."""

import tkinter as tk

from .constants import BG


class Page(tk.Frame):
    """A single 'page' managed by the notebook."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.build()
        self.load()

    def build(self):
        """Override: create widgets once."""
        pass

    def load(self):
        """Override: refresh data every time the page is shown."""
        pass