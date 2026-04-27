import csv

import pytest

from core import transaction


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


def test_link_tag_to_transaction_creates_tag_and_assignment(isolated_transaction_files):
    transaction._link_tag_to_transaction("1", "Needs", "Coffee")

    tags = transaction._load_tags()
    assignments = transaction._load_assignments()

    assert len(tags) == 1
    assert tags[0]["Tag_type"] == "Needs"
    assert tags[0]["Tag_name"] == "Coffee"

    assert len(assignments) == 1
    assert assignments[0] == {"ID": "1", "TagID": tags[0]["Tag_id"]}


def test_link_tag_to_transaction_reuses_tag_and_skips_duplicate_assignment(isolated_transaction_files):
    transaction._link_tag_to_transaction("1", "Needs", "Coffee")
    transaction._link_tag_to_transaction("1", "needs", "coffee")

    tags = transaction._load_tags()
    assignments = transaction._load_assignments()

    assert len(tags) == 1
    assert len(assignments) == 1
