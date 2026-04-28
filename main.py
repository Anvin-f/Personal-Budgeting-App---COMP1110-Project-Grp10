"""Backward-compatible entrypoint for the Tkinter GUI."""

import matplotlib
matplotlib.use("TkAgg")


from gui_app import BudgetApp, main


if __name__ == "__main__":
    main()
