# Personal Budgeting App

A desktop personal budgeting application built with Tkinter. The app helps track transactions, manage tags and budgets, review spending trends, and optionally chat with an AI assistant using your financial data context.

## Features

- Transaction management with CSV import support
- Tag and category management (for example Bills, Needs, Wants, custom tags)
- Monthly budget tracking with alert indicators
- Analysis and summary pages for spending trends
- Settings page for UI options and API key storage
- Optional AI assistant panel that answers questions using your app data

## Tech Stack

- Python (Tkinter desktop GUI)
- Matplotlib (embedded charts)
- OpenAI Python SDK (used to call the configured chat endpoint)
- Pytest (automated tests)

## Requirements

- Python 3.10+
- A virtual environment is recommended

Install dependencies:

```bash
pip install -r requirements.txt
```

Current dependency list is intentionally minimal and matches actual imports in this repository.

## Quick Start

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### macOS/Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Running Tests

```bash
pytest
```

Main test files are under `tests/` and cover transaction logic, adjustment logic, and CSV robustness scenarios.

## AI Assistant Setup

The AI assistant tab is optional.

1. Open the app.
2. Go to Settings.
3. Enter your API key.

The assistant builds context from your local transactions, tags, assignments, budgets, and selected profile fields.

## Data Files

The app stores data in CSV and JSON files under `data/`:

- `transactions.csv`: transaction records
- `tags.csv`: tag definitions
- `assignment.csv`: transaction-to-tag mapping
- `budget.csv`: budget configuration by tag and period
- `settings.json`: UI and profile/API settings

## Project Structure

```text
.
|-- main.py
|-- requirements.txt
|-- Backend/
|   |-- transaction.py
|   |-- tags.py
|   |-- alerts.py
|   |-- adjustments.py
|   |-- settings.py
|   `-- chatbot.py
|-- Frontend/
|   |-- app.py
|   |-- base.py
|   |-- constants.py
|   |-- helpers.py
|   `-- pages/
|       |-- dashboard.py
|       |-- transactions.py
|       |-- tags.py
|       |-- budget.py
|       |-- analysis.py
|       |-- summary.py
|       |-- chatbot.py
|       `-- settings.py
|-- data/
|   |-- transactions.csv
|   |-- tags.csv
|   |-- assignment.csv
|   |-- budget.csv
|   `-- settings.json
`-- tests/
	|-- conftest.py
	|-- unit/
	|   |-- test_transaction.py
	|   `-- test_adjustments.py
	|-- integration/
	|   `-- test_import_csv.py
	`-- helpers/
		`-- case_generator.py
```

## Notes

- Currency formatting in the app is currently oriented around HKD labels.
- The GUI depends on Tkinter support in your Python installation.

