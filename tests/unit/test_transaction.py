import csv

import pytest

from Backend import transaction


def _write_rows(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerows(rows)


def test_validate_date_accepts_iso_date():
    assert transaction._validate_date("2026-04-27") is True


def test_validate_date_rejects_non_iso_date():
    assert transaction._validate_date("27/04/2026") is False


@pytest.mark.parametrize(
    "amount, expected",
    [
        ("0", 0.0),
        ("13.50", 13.5),
        ("-1", None),
        ("abc", None),
    ],
)
def test_validate_amount(amount, expected):
    assert transaction._validate_amount(amount) == expected


def test_get_next_transaction_id_for_empty_and_existing():
    assert transaction._get_next_transaction_id([]) == "1"
    rows = [{"ID": "1"}, {"ID": "6"}, {"ID": "3"}]
    assert transaction._get_next_transaction_id(rows) == "7"


@pytest.mark.usefixtures("isolated_transaction_files")
def test_link_tag_to_transaction_creates_tag_and_assignment():
    transaction._link_tag_to_transaction("1", "Needs", "Coffee")

    tags = transaction._load_tags()
    assignments = transaction._load_assignments()

    assert len(tags) == 1
    assert tags[0]["Tag_type"] == "Needs"
    assert tags[0]["Tag_name"] == "Coffee"

    assert len(assignments) == 1
    assert assignments[0] == {"ID": "1", "TagID": tags[0]["Tag_id"]}


@pytest.mark.usefixtures("isolated_transaction_files")
def test_link_tag_to_transaction_reuses_tag_and_skips_duplicate_assignment():
    transaction._link_tag_to_transaction("1", "Needs", "Coffee")
    transaction._link_tag_to_transaction("1", "needs", "coffee")

    tags = transaction._load_tags()
    assignments = transaction._load_assignments()

    assert len(tags) == 1
    assert len(assignments) == 1


@pytest.mark.usefixtures("isolated_transaction_files")
def test_add_transaction_from_csv_rejects_missing_required_columns(capsys, tmp_path, monkeypatch):
    csv_path = tmp_path / "missing_cols.csv"
    _write_rows(
        csv_path,
        [
            ["Date", "Name", "Transaction Description", "Tag_type", "Tag_name"],
            ["2026-01-01", "Coffee", "", "Needs", "Coffee"],
        ],
    )
    monkeypatch.setattr("builtins.input", lambda _: str(csv_path))

    transaction.add_transaction_from_csv()
    output = capsys.readouterr().out

    assert "missing required column" in output.lower()
    assert transaction._load_transactions() == []


@pytest.mark.usefixtures("isolated_transaction_files")
def test_add_transaction_from_csv_skips_invalid_and_imports_valid_rows(capsys, tmp_path, monkeypatch):
    csv_path = tmp_path / "mixed_rows.csv"
    _write_rows(
        csv_path,
        [
            ["Date", "Name", "Transaction Description", "Amount", "Tag_type", "Tag_name"],
            ["2026-01-01", "Groceries", "Weekly", "150", "Needs", "Food"],
            ["bad-date", "Coffee", "", "40", "Needs", "Coffee"],
            ["2026-01-03", "Refund", "", "-10", "Bills", "Utility"],
            ["2026-01-04", "Transport", "MTR", "35", "", ""],
            ["2026-01-05", "Dining", "Team dinner", "220", "Wants", "Food"],
        ],
    )
    monkeypatch.setattr("builtins.input", lambda _: str(csv_path))

    transaction.add_transaction_from_csv()
    output = capsys.readouterr().out

    rows = transaction._load_transactions()
    assert len(rows) == 3
    assert rows[0]["ID"] == "1"
    assert rows[1]["ID"] == "2"
    assert rows[2]["ID"] == "3"
    assert "imported 3 transaction" in output.lower()


@pytest.mark.usefixtures("isolated_transaction_files")
def test_add_transaction_from_csv_handles_invalid_bytes_without_crashing(capsys, tmp_path, monkeypatch):
    csv_path = tmp_path / "bad_encoding.csv"
    raw = (
        b"Date,Name,Transaction Description,Amount,Tag_type,Tag_name\n"
        b"2026-01-01,Cafe,desc,12.5,Needs,Coffee\n"
        b"2026-01-02,BadByte,\x8d,15.0,Wants,Misc\n"
    )
    csv_path.write_bytes(raw)
    monkeypatch.setattr("builtins.input", lambda _: str(csv_path))

    transaction.add_transaction_from_csv()
    output = capsys.readouterr().out

    rows = transaction._load_transactions()
    assert len(rows) >= 1
    assert any(row["Name"] == "Cafe" for row in rows)
    assert "error reading csv" not in output.lower()


@pytest.mark.usefixtures("isolated_transaction_files")
def test_add_transaction_from_csv_reuses_tag_case_insensitively(capsys, tmp_path, monkeypatch):
    csv_path = tmp_path / "tag_reuse.csv"
    _write_rows(
        csv_path,
        [
            ["Date", "Name", "Transaction Description", "Amount", "Tag_type", "Tag_name"],
            ["2026-01-01", "Coffee", "", "20", "Needs", "Coffee"],
            ["2026-01-02", "Coffee2", "", "30", "needs", "coffee"],
        ],
    )
    monkeypatch.setattr("builtins.input", lambda _: str(csv_path))

    transaction.add_transaction_from_csv()
    _ = capsys.readouterr()

    tags = transaction._load_tags()
    assignments = transaction._load_assignments()
    assert len(tags) == 1
    assert len(assignments) == 2

