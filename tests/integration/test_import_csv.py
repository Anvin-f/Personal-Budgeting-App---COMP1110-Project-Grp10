import csv

import pytest

from core import transaction
from tests.helpers import case_generator as gen


@pytest.fixture
def generated_import_files(tmp_path):
    normal = tmp_path / "normal.csv"
    logic = tmp_path / "logic.csv"
    duplicates = tmp_path / "duplicates.csv"

    gen.generate_normal(str(normal), count=10)
    gen.generate_logic_edge_cases(str(logic))
    gen.generate_duplicates(str(duplicates))

    return {
        "normal": normal,
        "logic": logic,
        "duplicates": duplicates,
    }


def _read_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


@pytest.mark.usefixtures("isolated_transaction_files")
def test_generated_normal_import_adds_expected_count(generated_import_files, capsys, monkeypatch):
    csv_path = generated_import_files["normal"]
    monkeypatch.setattr("builtins.input", lambda _: str(csv_path))

    transaction.add_transaction_from_csv()
    output = capsys.readouterr().out

    assert "imported 10 transaction" in output.lower()
    assert len(transaction._load_transactions()) == 10


@pytest.mark.usefixtures("isolated_transaction_files")
def test_generated_logic_import_skips_invalid_blank_row(generated_import_files, capsys, monkeypatch):
    csv_path = generated_import_files["logic"]
    monkeypatch.setattr("builtins.input", lambda _: str(csv_path))

    transaction.add_transaction_from_csv()
    output = capsys.readouterr().out

    rows = transaction._load_transactions()
    assert len(rows) >= 2
    assert any(row["Name"] == "Space Test" for row in rows)
    assert any(row["Name"] == "Case Test" for row in rows)
    assert "skipping line" in output.lower()


@pytest.mark.usefixtures("isolated_transaction_files")
def test_generated_duplicates_keep_distinct_transaction_ids(generated_import_files, capsys, monkeypatch):
    csv_path = generated_import_files["duplicates"]
    monkeypatch.setattr("builtins.input", lambda _: str(csv_path))

    transaction.add_transaction_from_csv()
    _ = capsys.readouterr()

    rows = transaction._load_transactions()
    assert len(rows) == 3
    assert [row["ID"] for row in rows] == ["1", "2", "3"]


@pytest.mark.usefixtures("isolated_transaction_files")
def test_import_file_not_found_reports_error_and_no_mutation(capsys, monkeypatch):
    missing = "Z:/definitely/not/found.csv"
    monkeypatch.setattr("builtins.input", lambda _: missing)

    transaction.add_transaction_from_csv()
    output = capsys.readouterr().out

    assert "file not found" in output.lower()
    assert transaction._load_transactions() == []
    assert transaction._load_tags() == []
    assert transaction._load_assignments() == []


@pytest.mark.usefixtures("isolated_transaction_files")
def test_import_creates_consistent_assignment_foreign_keys(capsys, tmp_path, monkeypatch):
    csv_path = tmp_path / "fk_integrity.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(["Date", "Name", "Transaction Description", "Amount", "Tag_type", "Tag_name"])
        writer.writerow(["2026-02-01", "Lunch", "", "60", "Needs", "Food"])
        writer.writerow(["2026-02-02", "Bus", "", "12", "Needs", "Transport"])

    monkeypatch.setattr("builtins.input", lambda _: str(csv_path))

    transaction.add_transaction_from_csv()
    _ = capsys.readouterr()

    transactions = _read_csv_rows(transaction.TRANSACTIONS_FILE)
    tags = _read_csv_rows(transaction.TAGS_FILE)
    assignments = _read_csv_rows(transaction.ASSIGNMENT_FILE)

    transaction_ids = {row["ID"] for row in transactions}
    tag_ids = {row["Tag_id"] for row in tags}
    assert len(transactions) == 2
    assert len(tags) == 2
    assert len(assignments) == 2
    assert {row["ID"] for row in assignments}.issubset(transaction_ids)
    assert {row["TagID"] for row in assignments}.issubset(tag_ids)
