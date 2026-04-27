from datetime import datetime, timedelta
from collections import defaultdict

from core.alerts import (
    read_transactions_csv,
    read_tags_csv,
    read_assignments_csv,
    read_budget_csv,
    _build_tag_map,
    _current_month_transactions,
    _sum_by_tag,
)
import core.settings as app_settings


def build_financial_context():
    transactions = read_transactions_csv()
    tags = read_tags_csv()
    assignments = read_assignments_csv()
    budgets = read_budget_csv()

    today = datetime.today()
    tag_map = _build_tag_map(assignments)

    month_txns = _current_month_transactions(transactions, today)
    spent_by_tag = _sum_by_tag(month_txns, tag_map)
    total_spent_month = sum(
        float(t.get("Amount", 0)) for t in month_txns if _safe_float(t.get("Amount"))
    )

    cutoff = today - timedelta(days=30)
    recent_txns = [
        t for t in transactions
        if _parse_date(t.get("Date")) and _parse_date(t.get("Date")) >= cutoff
    ]

    budget_lines = []
    for (tag_id, period), amount in sorted(budgets.items(), key=lambda x: int(x[0][0])):
        if period != "monthly":
            continue
        tag_name = tags.get(tag_id, {}).get("Tag_name", f"Tag {tag_id}")
        spent = spent_by_tag.get(tag_id, 0.0)
        remaining = amount - spent
        pct = (spent / amount * 100) if amount > 0 else 0
        status = "OVER" if spent > amount else ("WARNING" if pct >= 80 else "OK")
        budget_lines.append(
            f"  - {tag_name}: Budget HK${amount:.2f}, Spent HK${spent:.2f}, "
            f"Remaining HK${remaining:.2f} ({pct:.1f}%) [{status}]"
        )

    recent_sorted = sorted(recent_txns, key=lambda x: x.get("Date", ""), reverse=True)[:15]
    txn_lines = []
    for t in recent_sorted:
        tid = t.get("ID", "")
        tag_id = tag_map.get(tid)
        tag_name = tags.get(tag_id, {}).get("Tag_name", "Uncategorized") if tag_id else "Uncategorized"
        amount = _safe_float(t.get("Amount")) or 0.0
        txn_lines.append(
            f"  - {t.get('Date', '?')} | {t.get('Name', '?')} | "
            f"HK${amount:.2f} | {tag_name}"
        )

    tag_lines = [
        f"  - ID {tid}: {info.get('Tag_type', '?')} / {info.get('Tag_name', '?')}"
        for tid, info in sorted(tags.items(), key=lambda x: int(x[0]))
    ]

    # All-time spending by category
    all_tag_map = _build_tag_map(assignments)
    all_spent_by_tag = defaultdict(float)
    for t in transactions:
        tid = t.get("ID")
        if tid in all_tag_map:
            amount = _safe_float(t.get("Amount"))
            if amount is not None:
                all_spent_by_tag[all_tag_map[tid]] += amount

    category_lines = []
    for tag_id, total in sorted(all_spent_by_tag.items(), key=lambda x: -x[1]):
        tag_name = tags.get(tag_id, {}).get("Tag_name", f"Tag {tag_id}")
        category_lines.append(f"  - {tag_name}: HK${total:.2f} total all time")

    month_str = today.strftime("%B %Y")
    # Build profile section if available
    profile = app_settings.read_settings()
    profile_lines = []
    if profile.get("profile_name"):
        profile_lines.append(f"Name: {profile.get('profile_name')}")
    if profile.get("profile_job"):
        profile_lines.append(f"Profession: {profile.get('profile_job')}")
    if profile.get("profile_monthly_income"):
        profile_lines.append(f"Monthly Income: HK${profile.get('profile_monthly_income')}")

    # Build context with profile section
    month_str = today.strftime("%B %Y")
    context_lines = [
        "You are a helpful personal finance assistant embedded in a budgeting app.",
        f"All amounts are in HK$ (Hong Kong Dollars). Today is {today.strftime('%Y-%m-%d')}.",
    ]

    if profile_lines:
        context_lines.append("## User Profile")
        for line in profile_lines:
            context_lines.append(f"  - {line}")
        context_lines.append("")

    context_lines.extend([
        f"## Current Month ({month_str})",
        f"Total spent: HK${total_spent_month:.2f}",
        f"Number of transactions this month: {len(month_txns)}",
        "",
        "## Monthly Budget Status",
        chr(10).join(budget_lines) if budget_lines else "  No budgets set.",
        "",
        "## Recent Transactions (Last 30 Days, newest first)",
        chr(10).join(txn_lines) if txn_lines else "  No recent transactions.",
        "",
        "## All-Time Spending by Category",
        chr(10).join(category_lines) if category_lines else "  No categorized spending.",
        "",
        "## Transaction Categories (Tags)",
        chr(10).join(tag_lines) if tag_lines else "  No tags defined.",
        "",
        f"Total transactions on record: {len(transactions)}",
        "",
        "Answer the user's questions about their spending, budgets, and transactions using the data above.",
        "Be concise and helpful. Always prefix amounts with HK$."
    ])

    context = chr(10).join(context_lines)

    return context


def get_chat_response(api_key, messages, system_context):
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    full_messages = [{"role": "system", "content": system_context}] + messages
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=full_messages,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
