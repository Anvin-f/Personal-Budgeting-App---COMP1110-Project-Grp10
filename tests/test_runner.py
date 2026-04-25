import pytest
import os
import csv
import shutil
from unittest.mock import patch
from tests import test_case_generator as gen
from core import transaction


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    temp_dir = "tests/temp_data"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    transaction.TRANSACTIONS_FILE = os.path.join(temp_dir, "test_transactions.csv")
    transaction.TAGS_FILE = os.path.join(temp_dir, "test_tags.csv")
    transaction.ASSIGNMENT_FILE = os.path.join(temp_dir, "test_assignment.csv")

    files_to_init = {
        transaction.TRANSACTIONS_FILE: transaction.TRANSACTION_FIELDS,
        transaction.TAGS_FILE: transaction.TAG_FIELDS,
        transaction.ASSIGNMENT_FILE: transaction.ASSIGNMENT_FIELDS
    }
    for f_path, fields in files_to_init.items():
        with open(f_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(fields)

    gen.generate_normal(os.path.join(temp_dir, "normal.csv"), count=10)
    gen.generate_empty(os.path.join(temp_dir, "empty.csv"))
    gen.generate_negative_amount(os.path.join(temp_dir, "negative.csv"))
    gen.generate_invalid_date(os.path.join(temp_dir, "invalid.csv"))
    gen.generate_extreme_amount(os.path.join(temp_dir, "extreme.csv"))
    gen.generate_logic_edge_cases(os.path.join(temp_dir, "logic.csv"))
    gen.generate_duplicates(os.path.join(temp_dir, "duplicates.csv"))

    yield

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


SCENARIOS = [
    ("tests/temp_data/normal.csv", True, "Normal"),
    ("tests/temp_data/empty.csv", False, "Empty Fields"),
    ("tests/temp_data/negative.csv", False, "Negative Amount"),
    ("tests/temp_data/invalid.csv", False, "Invalid Date"),
    ("tests/temp_data/extreme.csv", False, "Extreme/Invalid Amount"),
    ("tests/temp_data/logic.csv", True, "Specific Edge Case"),
    ("tests/temp_data/duplicates.csv", True, "Duplicates"),
]


@pytest.mark.parametrize("csv_path, should_pass, label", SCENARIOS)
def test_import_robustness(csv_path, should_pass, label, capsys):
    with patch('builtins.input', return_value=csv_path):
        try:
            transaction.add_transaction_from_csv()
            captured = capsys.readouterr().out

            if not should_pass:
                assert any(word in captured for word in ["[Error]", "Error reading", "Skipping", "Warning", "invalid"])
            else:
                assert "[Success]" in captured or "Imported" in captured

        except Exception as e:
            pytest.fail(f"FAILED: {label} crashed with {type(e).__name__}: {e}")


def test_data_integrity():
    if os.path.exists(transaction.TRANSACTIONS_FILE):
        with open(transaction.TRANSACTIONS_FILE, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 1