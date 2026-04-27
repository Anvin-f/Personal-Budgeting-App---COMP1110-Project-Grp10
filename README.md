# Personal-Budgeting-App---COMP1110-Project-Grp10

A personal budgeting app with a Tkinter GUI for managing transactions, tags, budgets, and spending analysis.

---

## Key Features

### Transaction Input & Management
- Add, update, and delete transactions directly from the CLI.
- Import and export transactions via CSV files.
- Maintain a clean record of daily expenses.

### Data AnalysisS
- Line graph to track daily expenses over time
- Receive alerts when thresholds are exceeded
- Stay on top of financial goals with automated checks

### Category System
- Organize expenses into Bills, Needs, Wants to monitor spending
- Manage categories for easy visualisations and budget planning
- Create custom tags for organisation

### Balance Adjustments & Irregular Expenses
- Record peer-to-peer balance adjustments
- Handle one-time irregular expenses without affecting the reports
- Take peer adjustments into account, such as shared rent and paying each other back

---

## Installation

### Prerequisites

- **Python** 3.9 or higher

### Code Setup

```bash

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate      # On Windows

# Install dependencies
pip install -r requirements.txt

# If error occured when pip installing the entire file
# Try intalling the dependencies individually

```

### Run The App

```bash
python main.py
```

`gui.py` remains available as a backward-compatible GUI entrypoint.

---

## Project Structure

```
Personal-Budgeting-App---COMP1110-Project-Grp10/
│
├── main.py                 # GUI entry point
├── gui.py                  # Backward-compatible GUI wrapper
├── gui_app/                # GUI package split by feature
│   ├── app.py              # Main window and navigation
│   ├── base.py             # Shared page base class
│   ├── constants.py        # Shared theme and fonts
│   ├── helpers.py          # Shared Tkinter helper functions
│   └── pages/
│       ├── dashboard.py    # Dashboard page
│       ├── transactions.py # Transactions page and dialog
│       ├── tags.py         # Tags page and dialog
│       ├── budget.py       # Budgets page and dialog
│       └── analysis.py     # Analysis page
├── data/
│   ├── assignment.csv      # record of assignment of tags to transactions
│   ├── tags.csv            # tag information
│   └── transactions.csv    # transaction history        
│
├── core/
│   ├── transaction.py      # Transaction input & management
│   ├── adjustments.py      # Peer-to-peer & irregular expenses handling
│   ├── analysis.py         # Data analysis helpers
│   ├── alerts.py           # Rule-based alerts
│   └── utils.py            # Other functions
│
│
├── tests/                  # Test programs
│
├── README.md               
└── requirements.txt        # Record dependencies
```

---

## Database Structure
All transaction history are stored in csv files

### Database Schema

| Table Name | Column Name | Data Type | Description |
| :--- | :--- | :--- | :--- |
| `transactions` | `ID` | `int` | Primary Key |
| `transactions` | `Date` | `string` | Date of transaction |
| `transactions` | `Name` | `string` | Transaction name |
| `transactions` | `Description` | `string` | Addtional information of transaction |
| `transactions` | `Amount` | `decimal` | Transaction amount |
| `tags` | `TagID` | `int` | Primary Key |
| `tags` | `Name` | `string` | Name of tag |
| `tags` | `Description` | `string` | Tag Description |
| `assignment` | `ID` | `int` | Foriegn key of transactions |
| `assignment` | `TagID` | `int` | Foriegn key of tags |

---
