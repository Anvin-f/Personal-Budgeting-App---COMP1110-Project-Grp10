import pytest

from Backend import adjustments
from Backend import transaction


@pytest.mark.usefixtures("isolated_transaction_files")
def test_record_peer_adjustment_links_balance_tag():
    new_id = adjustments.record_peer_adjustment(
        date="2026-04-15",
        peer_name="Alex",
        amount="120",
        direction="out",
        description="Shared rent advance",
    )

    transactions = transaction._load_transactions()
    assert len(transactions) == 1
    assert transactions[0]["ID"] == new_id
    assert transactions[0]["Name"].startswith("Balance Out")

    tags = transaction._load_tags()
    assignments = transaction._load_assignments()
    assert len(tags) == 1
    assert tags[0]["Tag_type"] == "Balance"
    assert tags[0]["Tag_name"] == "Peer:Alex"
    assert assignments == [{"ID": new_id, "TagID": tags[0]["Tag_id"]}]


@pytest.mark.usefixtures("isolated_transaction_files")
def test_record_irregular_expense_links_irregular_tag():
    new_id = adjustments.record_irregular_expense(
        date="2026-04-20",
        name="Laptop Repair",
        amount=850,
        description="One-off hardware fix",
    )

    tags = transaction._load_tags()
    assignments = transaction._load_assignments()
    assert len(tags) == 1
    assert tags[0]["Tag_type"] == "Irregular"
    assert tags[0]["Tag_name"] == "One-time"
    assert assignments == [{"ID": new_id, "TagID": tags[0]["Tag_id"]}]


@pytest.mark.usefixtures("isolated_transaction_files")
def test_calculate_peer_balances_net_logic():
    adjustments.record_peer_adjustment("2026-04-01", "Sam", 200, "out", "Rent split")
    adjustments.record_peer_adjustment("2026-04-10", "Sam", 75, "in", "Payback")

    balances = adjustments.calculate_peer_balances()
    assert "Sam" in balances
    assert balances["Sam"]["out"] == 200.0
    assert balances["Sam"]["in"] == 75.0
    assert balances["Sam"]["net"] == 125.0


@pytest.mark.usefixtures("isolated_transaction_files")
def test_record_peer_adjustment_accepts_direction_aliases():
    adjustments.record_peer_adjustment("2026-04-01", "Dana", 90, "paid", "Taxi")
    adjustments.record_peer_adjustment("2026-04-02", "Dana", 40, "received", "Refund")

    balances = adjustments.calculate_peer_balances()
    assert balances["Dana"]["out"] == 90.0
    assert balances["Dana"]["in"] == 40.0
    assert balances["Dana"]["net"] == 50.0


@pytest.mark.usefixtures("isolated_transaction_files")
def test_calculate_peer_balances_uses_metadata_before_name():
    transaction_id = adjustments.record_peer_adjustment("2026-04-01", "Mia", 55, "in", "Dinner")
    transactions = transaction._load_transactions()
    transactions[0]["Name"] = "Something Else"
    assert transactions[0]["ID"] == transaction_id
    transaction._save_transactions(transactions)

    balances = adjustments.calculate_peer_balances()
    assert balances["Mia"]["in"] == 55.0
    assert balances["Mia"]["out"] == 0.0


@pytest.mark.usefixtures("isolated_transaction_files")
def test_list_recent_peer_entries_returns_latest_first():
    adjustments.record_peer_adjustment("2026-04-01", "Alex", 120, "out", "Lunch")
    adjustments.record_peer_adjustment("2026-04-03", "Sam", 80, "in", "Payback")

    recent = adjustments.list_recent_peer_entries(limit=2)
    assert len(recent) == 2
    assert recent[0]["peer"] == "Sam"
    assert recent[0]["direction"] == "in"
    assert recent[0]["description"] == "Payback"
    assert recent[1]["peer"] == "Alex"


@pytest.mark.usefixtures("isolated_transaction_files")
def test_adjusted_spending_total_excludes_balance_and_irregular():
    base = transaction._load_transactions()
    base.append(
        {
            "ID": "1",
            "Date": "2026-04-01",
            "Name": "Groceries",
            "Transaction Description": "Weekly",
            "Amount": "100.00",
        }
    )
    transaction._save_transactions(base)

    adjustments.record_peer_adjustment("2026-04-02", "Kim", 50, "out", "Shared meal")
    adjustments.record_irregular_expense("2026-04-03", "Emergency Plumbing", 500, "One-off")

    assert adjustments.adjusted_spending_total() == 100.0
    assert adjustments.adjusted_spending_total(exclude_irregular=False, exclude_balance=False) == 650.0


@pytest.mark.usefixtures("isolated_transaction_files")
def test_record_peer_adjustment_rejects_invalid_direction():
    with pytest.raises(ValueError, match="direction"):
        adjustments.record_peer_adjustment("2026-04-01", "Alex", 20, "north")


@pytest.mark.usefixtures("isolated_transaction_files")
def test_record_peer_adjustment_rejects_empty_peer_name():
    with pytest.raises(ValueError, match="peer_name"):
        adjustments.record_peer_adjustment("2026-04-01", "   ", 20, "out")


@pytest.mark.usefixtures("isolated_transaction_files")
def test_adjusted_spending_total_rejects_inverted_date_range():
    with pytest.raises(ValueError, match="end_date"):
        adjustments.adjusted_spending_total(start_date="2026-04-10", end_date="2026-04-01")

