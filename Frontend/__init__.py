"""Tkinter GUI package for the Personal Budget Tracker."""

import matplotlib

matplotlib.use("TkAgg")

from .app import BudgetApp


def main():
    app = BudgetApp()
    app.mainloop()


__all__ = ["BudgetApp", "main"]