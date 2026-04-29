from datetime import datetime

import Backend.transaction as transaction


BALANCE_TAG_TYPE = "Balance"
IRREGULAR_TAG_TYPE = "Irregular"
IRREGULAR_TAG_NAME = "One-time"
PEER_TAG_PREFIX = "Peer:"
PEER_META_PREFIX = "peer_balance:"


def _normalize_direction(direction):
    text = str(direction).strip().lower()
    aliases = {
        "out": "out",
        "pay": "out",
        "paid": "out",
        "sent": "out",
        "in": "in",
        "receive": "in",
        "received": "in",
        "got": "in",
    }
    normalized = aliases.get(text)
    if normalized is None:
        raise ValueError("direction must be one of: out/in/paid/received")
    return normalized


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not transaction._validate_date(text):
        return None
    return datetime.strptime(text, "%Y-%m-%d")


def _date_to_string(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def _add_transaction(date, name, amount, description=""):
    date_text = _date_to_string(date)
    if not transaction._validate_date(date_text):
        raise ValueError("date must be in YYYY-MM-DD format")

    amount_value = transaction._validate_amount(str(amount))
    if amount_value is None:
        raise ValueError("amount must be a non-negative number")

    name_text = str(name).strip()
    if not name_text:
        raise ValueError("name cannot be empty")

    transactions = transaction._load_transactions()
    new_id = transaction._get_next_transaction_id(transactions)
    transactions.append(
        {
            "ID": new_id,
            "Date": date_text,
            "Name": name_text,
            "Transaction Description": str(description).strip(),
            "Amount": f"{amount_value:.2f}",
        }
    )
    transaction._save_transactions(transactions)
    return new_id


def _balance_meta(direction):
    return f"{PEER_META_PREFIX}{direction}"


def _infer_balance_direction(row):
    description = (row.get("Transaction Description") or "").strip().lower()
    if description.startswith(f"{PEER_META_PREFIX}in"):
        return "in"
    if description.startswith(f"{PEER_META_PREFIX}out"):
        return "out"

    name_text = (row.get("Name") or "").strip().lower()
    if name_text.startswith("balance in"):
        return "in"
    if name_text.startswith("balance out"):
        return "out"
    return "out"


def _strip_balance_meta(description):
    text = (description or "").strip()
    lowered = text.lower()
    if not lowered.startswith(PEER_META_PREFIX):
        return text
    parts = text.split(";", 1)
    return parts[1].strip() if len(parts) > 1 else ""


def _safe_sort_key_for_row(row):
    date_text = (row.get("Date") or "").strip()
    if transaction._validate_date(date_text):
        date_key = date_text
    else:
        date_key = "0000-00-00"
    tx_id = row.get("ID") or "0"
    try:
        id_key = int(tx_id)
    except (TypeError, ValueError):
        id_key = 0
    return (date_key, id_key)


def list_peer_names(include_unknown=False):
    names = set()
    for tag in transaction._load_tags():
        if (tag.get("Tag_type") or "").strip().lower() != BALANCE_TAG_TYPE.lower():
            continue
        tag_name = (tag.get("Tag_name") or "").strip()
        if not tag_name.startswith(PEER_TAG_PREFIX):
            continue
        peer = tag_name[len(PEER_TAG_PREFIX) :].strip()
        if peer:
            names.add(peer)
    if include_unknown:
        names.add("Unknown")
    return sorted(names, key=str.lower)


def list_recent_peer_entries(limit=10):
    transaction_to_tags = _build_tag_index()
    entries = []

    for row in sorted(transaction._load_transactions(), key=_safe_sort_key_for_row, reverse=True):
        transaction_id = row.get("ID")
        if not transaction_id:
            continue

        tags_for_transaction = transaction_to_tags.get(transaction_id, [])
        if not _has_tag_type(tags_for_transaction, BALANCE_TAG_TYPE):
            continue

        amount = transaction._validate_amount(row.get("Amount", ""))
        if amount is None:
            continue

        peer = "Unknown"
        for tag in tags_for_transaction:
            tag_name = tag.get("Tag_name", "")
            if tag_name.startswith(PEER_TAG_PREFIX):
                peer = tag_name[len(PEER_TAG_PREFIX) :].strip() or "Unknown"
                break

        entries.append(
            {
                "id": str(transaction_id),
                "date": (row.get("Date") or "").strip(),
                "peer": peer,
                "direction": _infer_balance_direction(row),
                "amount": amount,
                "description": _strip_balance_meta(row.get("Transaction Description", "")),
            }
        )

        if len(entries) >= max(0, int(limit)):
            break

    return entries


def record_peer_adjustment(date, peer_name, amount, direction="out", description=""):
    peer = str(peer_name).strip()
    if not peer:
        raise ValueError("peer_name cannot be empty")

    direction_text = _normalize_direction(direction)

    prefix = "Balance Out" if direction_text == "out" else "Balance In"
    transaction_name = f"{prefix} - {peer}"
    clean_description = str(description).strip()
    meta = _balance_meta(direction_text)
    full_description = f"{meta}; {clean_description}" if clean_description else meta
    transaction_id = _add_transaction(date, transaction_name, amount, full_description)

    transaction._link_tag_to_transaction(
        transaction_id,
        BALANCE_TAG_TYPE,
        f"{PEER_TAG_PREFIX}{peer}",
    )
    return transaction_id


def record_irregular_expense(date, name, amount, description=""):
    transaction_id = _add_transaction(date, name, amount, description)
    transaction._link_tag_to_transaction(transaction_id, IRREGULAR_TAG_TYPE, IRREGULAR_TAG_NAME)
    return transaction_id


def _build_tag_index():
    tags = {tag["Tag_id"]: tag for tag in transaction._load_tags()}
    transaction_to_tags = {}
    for assignment in transaction._load_assignments():
        transaction_id = assignment.get("ID")
        tag_id = assignment.get("TagID")
        tag = tags.get(tag_id)
        if not transaction_id or not tag:
            continue
        transaction_to_tags.setdefault(transaction_id, []).append(tag)
    return transaction_to_tags


def _has_tag_type(tags_for_transaction, tag_type):
    wanted = str(tag_type).strip().lower()
    return any(tag.get("Tag_type", "").strip().lower() == wanted for tag in tags_for_transaction)


def calculate_peer_balances():
    transaction_to_tags = _build_tag_index()
    balances = {}

    for row in transaction._load_transactions():
        transaction_id = row.get("ID")
        if not transaction_id:
            continue
        tags_for_transaction = transaction_to_tags.get(transaction_id, [])
        if not _has_tag_type(tags_for_transaction, BALANCE_TAG_TYPE):
            continue

        amount = transaction._validate_amount(row.get("Amount", ""))
        if amount is None:
            continue

        peer = "Unknown"
        for tag in tags_for_transaction:
            tag_name = tag.get("Tag_name", "")
            if tag_name.startswith(PEER_TAG_PREFIX):
                peer = tag_name[len(PEER_TAG_PREFIX) :].strip() or "Unknown"
                break

        entry = balances.setdefault(peer, {"out": 0.0, "in": 0.0, "net": 0.0})
        direction = _infer_balance_direction(row)
        if direction == "in":
            entry["in"] += amount
        else:
            entry["out"] += amount
        entry["net"] = entry["out"] - entry["in"]

    return balances


def adjusted_spending_total(start_date=None, end_date=None, exclude_irregular=True, exclude_balance=True):
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start and end and end < start:
        raise ValueError("end_date cannot be earlier than start_date")

    transaction_to_tags = _build_tag_index()
    total = 0.0

    for row in transaction._load_transactions():
        date_value = _parse_date(row.get("Date"))
        if date_value is None:
            continue
        if start and date_value < start:
            continue
        if end and date_value > end:
            continue

        amount = transaction._validate_amount(row.get("Amount", ""))
        if amount is None:
            continue

        tags_for_transaction = transaction_to_tags.get(row.get("ID", ""), [])
        if exclude_irregular and _has_tag_type(tags_for_transaction, IRREGULAR_TAG_TYPE):
            continue
        if exclude_balance and _has_tag_type(tags_for_transaction, BALANCE_TAG_TYPE):
            continue

        total += amount

    return round(total, 2)
