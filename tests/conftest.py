import csv

import pytest

from Backend import transaction


def _init_csv(path, headers):
    with open(path, "w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=headers)
        writer.writeheader()


@pytest.fixture
def isolated_transaction_files(tmp_path, monkeypatch):
    transactions_file = tmp_path / "transactions.csv"
    tags_file = tmp_path / "tags.csv"
    assignments_file = tmp_path / "assignment.csv"

    _init_csv(transactions_file, transaction.TRANSACTION_FIELDS)
    _init_csv(tags_file, transaction.TAG_FIELDS)
    _init_csv(assignments_file, transaction.ASSIGNMENT_FIELDS)

    monkeypatch.setattr(transaction, "TRANSACTIONS_FILE", str(transactions_file))
    monkeypatch.setattr(transaction, "TAGS_FILE", str(tags_file))
    monkeypatch.setattr(transaction, "ASSIGNMENT_FILE", str(assignments_file))

    return {
        "transactions": transactions_file,
        "tags": tags_file,
        "assignments": assignments_file,
    }

