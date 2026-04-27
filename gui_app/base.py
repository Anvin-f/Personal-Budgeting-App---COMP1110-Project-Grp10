import tkinter as tk

from .constants import BG


class Page(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.build()
        self.load()

    def build(self):
        pass

    def load(self):
        pass