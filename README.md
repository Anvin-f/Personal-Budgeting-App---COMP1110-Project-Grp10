# Personal-Budgeting-App---COMP1110-Project-Grp10

A CLI budgeting app that integrates the best features from all existing competitors

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

## 📁 Project Structure

```
Personal-Budgeting-App---COMP1110-Project-Grp10/
│
├── main.py                 # entry point
├── cli.py                  # CLI logic
├── data/
│   └── transactions.csv    # Test sample
│
├── core/
│   ├── transaction.py      # Transaction input & management
│   ├── adjustments.py      # Peer-to-peer & irregular expenses handling
│   ├── analysis.py         # Data analysis
│   ├── alrets.py           # Rule-based alerts
│   └── utils.py            # Other functions
│
│
├── tests/                  # Test programs
│
├── README.md               
└── requirements.txt        # Record dependencies
```

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
