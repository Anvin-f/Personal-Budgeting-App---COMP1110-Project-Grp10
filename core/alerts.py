import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict
import core.adjustments as adjustments

# constants
TRANSACTIONS_FILE = "data/transactions.csv"
TAGS_FILE         = "data/tags.csv"
ASSIGNMENT_FILE   = "data/assignment.csv"
BUDGET_FILE       = "data/budget.csv"
BUDGET_FIELDS = ["Tag_id", "Period", "Amount"]

# ── CSV readers ─────────────────────────────────────────────────────────
def read_transactions_csv():
    """Load all transactions from CSV into a list of dicts."""
    transactions = []
    if not os.path.isfile(TRANSACTIONS_FILE):
        return transactions
    try:
        with open(TRANSACTIONS_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                transactions.append(row)
    except Exception as e:
        print(f"[Error] Failed to read transactions: {e}")
    return transactions

def read_tags_csv():
    """Load all tags into a dict keyed by Tag_id."""
    tagDic = {}
    if not os.path.isfile(TAGS_FILE):
        return tagDic
    try:
        with open(TAGS_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                tagDic[row["Tag_id"]] = row
    except Exception as e:
        print(f"[Error] Failed to read tags: {e}")
    return tagDic

def read_assignments_csv():
    """Load all tag assignments into a list of dicts."""
    assignments = []
    if not os.path.isfile(ASSIGNMENT_FILE):
        return assignments
    try:
        with open(ASSIGNMENT_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                assignments.append(row)
    except Exception as e:
        print(f"[Error] Failed to read assignments: {e}")
    return assignments

def read_budget_csv():
    """Load budgets into a dict (tag_id, period) -> amount."""
    budgetDic = {}
    if not os.path.isfile(BUDGET_FILE):
        return budgetDic
    try:
        with open(BUDGET_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    key = (row["Tag_id"], row["Period"].lower().strip())
                    budgetDic[key] = float(row["Amount"])
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"[Error] Failed to read budgets: {e}")
    return budgetDic

def write_budget_csv(budgetDic):
    """Save budgets back to CSV."""
    rows = [
        {"Tag_id": tag_id, "Period": period, "Amount": f"{amount:.2f}"}
        for (tag_id, period), amount in budgetDic.items()
    ]
    sorted_rows = sorted(rows, key=lambda x: (int(x["Tag_id"]), x["Period"]))
    with open(BUDGET_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=BUDGET_FIELDS)
        writer.writeheader()
        writer.writerows(sorted_rows)

# ── Shared helpers ──────────────────────────────────────────────────────
def _build_tag_map(assignments):
    """Map transaction_id -> first TagID for budget attribution."""
    tag_map = {}
    for a in assignments:
        tid = a.get("ID")
        if tid and tid not in tag_map:
            tag_map[tid] = a.get("TagID")
    return tag_map

def _days_in_month(date):
    """Return number of days in the month of the given date."""
    if date.month == 12:
        next_month = datetime(date.year + 1, 1, 1)
    else:
        next_month = datetime(date.year, date.month + 1, 1)
    first = datetime(date.year, date.month, 1)
    return (next_month - first).days

def _current_month_transactions(transactions, reference_date):
    """Filter transactions falling in the reference year/month."""
    result = []
    for t in transactions:
        try:
            tdate = datetime.strptime(t["Date"], "%Y-%m-%d")
        except (ValueError, KeyError):
            continue
        if tdate.year == reference_date.year and tdate.month == reference_date.month:
            result.append(t)
    return result

def _sum_by_tag(transactions, tag_map):
    """Sum amounts by TagID for the given transactions."""
    totals = defaultdict(float)
    for t in transactions:
        tid = t.get("ID")
        if tid in tag_map:
            try:
                totals[tag_map[tid]] += float(t["Amount"])
            except (ValueError, KeyError):
                continue
    return totals

def _parse_transaction(t):
    """Try to extract (date, amount, name) or None on failure."""
    try:
        tdate = datetime.strptime(t["Date"], "%Y-%m-%d")
        amount = float(t["Amount"])
        name = t.get("Name", "").strip().lower()
        if not name:
            return None
        return tdate, amount, name
    except (ValueError, KeyError):
        return None

# ── Original alerts ─────────────────────────────────────────────────────
def pace_alert():
    """Check if each budget category is on pace."""
    print("\n--- Pace Alerts (PocketGuard-inspired) ---")
    transactions = read_transactions_csv()
    tags = read_tags_csv()
    assignments = read_assignments_csv()
    budgets = read_budget_csv()
    if not budgets:
        print("[Info] No budgets set. Use 'add-budget' to create one.")
        return
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    tag_map = _build_tag_map(assignments)
    month_txns = _current_month_transactions(transactions, today)
    spent_by_tag = _sum_by_tag(month_txns, tag_map)
    days_in_month = _days_in_month(today)
    days_elapsed = today.day
    days_remaining = days_in_month - days_elapsed
    alerts_fired = 0
    for (tag_id, period), budget_amount in budgets.items():
        if period != "monthly":
            continue
        spent = spent_by_tag.get(tag_id, 0.0)
        expected = (days_elapsed / days_in_month) * budget_amount
        tag_name = tags.get(tag_id, {}).get("Tag_name", f"Tag {tag_id}")
        safe_per_day = (budget_amount - spent) / days_remaining if days_remaining > 0 else 0
        if spent > budget_amount:
            over = spent - budget_amount
            print(f"[Critical] '{tag_name}' is OVER monthly budget by HK${over:.2f} "
                  f"(HK${spent:.2f} / HK${budget_amount:.2f}).")
            alerts_fired += 1
        elif spent > expected * 1.3:
            print(f"[Warning] '{tag_name}' spending far exceeds pace: "
                  f"HK${spent:.2f} of HK${budget_amount:.2f} by day {days_elapsed}/{days_in_month} "
                  f"(expected ~HK${expected:.2f}). Safe/day: HK${safe_per_day:.2f}.")
            alerts_fired += 1
        elif spent > expected * 1.1:
            print(f"[Info] '{tag_name}' slightly ahead of pace: "
                  f"HK${spent:.2f} of HK${budget_amount:.2f}. Safe/day: HK${safe_per_day:.2f}.")
            alerts_fired += 1
    if alerts_fired == 0:
        print("[OK] All budgeted categories are on pace.")

def in_my_pocket_alert():
    """Show how much is safe to spend for the rest of the month."""
    print("\n--- In My Pocket (PocketGuard-inspired) ---")
    transactions = read_transactions_csv()
    budgets = read_budget_csv()
    if not budgets:
        print("[Info] No budgets set. Use 'add-budget' to create one.")
        return
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    month_txns = _current_month_transactions(transactions, today)
    total_spent = 0.0
    for t in month_txns:
        try:
            total_spent += float(t["Amount"])
        except (ValueError, KeyError):
            continue
    total_budget = sum(
        amount for (tag_id, period), amount in budgets.items() if period == "monthly"
    )
    remaining = total_budget - total_spent
    days_in_month = _days_in_month(today)
    days_remaining = max(1, days_in_month - today.day)
    days_remaining_week = min(7, days_remaining)
    safe_per_day = remaining / days_remaining
    safe_per_week = safe_per_day * days_remaining_week
    print(f"Total monthly budget:     HK${total_budget:.2f}")
    print(f"Spent this month so far:  HK${total_spent:.2f}")
    print(f"Remaining:                HK${remaining:.2f}")
    print(f"Days left in month:       {days_remaining}")
    print()
    if remaining < 0:
        print(f"[Critical] You are OVER total budget by HK${abs(remaining):.2f}!")
    else:
        print(f"Safe to spend today:          HK${safe_per_day:.2f}")
        print(f"Safe to spend next {days_remaining_week} days:   HK${safe_per_week:.2f}")
        if safe_per_day < (total_budget / days_in_month) * 0.5:
            print("[Warning] Daily safe amount is less than half your normal pace. Slow down.")

def _detect_subscriptions(transactions):
    """Group recurring charges by (name, amount) and frequency."""
    groups = defaultdict(list)
    for t in transactions:
        parsed = _parse_transaction(t)
        if parsed is None:
            continue
        tdate, amount, name = parsed
        groups[(name, round(amount, 2))].append(tdate)
    subscriptions = []
    for (name, amount), dates in groups.items():
        if len(dates) < 3:
            continue
        dates.sort()
        gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
        monthly = sum(1 for g in gaps if 28 <= g <= 33)
        weekly  = sum(1 for g in gaps if 6  <= g <= 8)
        yearly  = sum(1 for g in gaps if 360 <= g <= 370)
        frequency = None
        threshold = len(gaps) * 0.7
        if   monthly >= threshold: frequency = "monthly"
        elif weekly  >= threshold: frequency = "weekly"
        elif yearly  >= threshold: frequency = "yearly"
        if frequency:
            subscriptions.append({
                "name": name, "amount": amount,
                "dates": dates, "frequency": frequency
            })
    return subscriptions

def subscription_alert():
    """Detect and list recurring charges."""
    print("\n--- Subscription Manager (PocketGuard-inspired) ---")
    transactions = read_transactions_csv()
    subscriptions = _detect_subscriptions(transactions)
    if not subscriptions:
        print("[Info] No recurring charges detected (need 3+ occurrences with consistent gaps).")
        return
    est_monthly = 0.0
    for sub in subscriptions:
        if   sub["frequency"] == "monthly": est_monthly += sub["amount"]
        elif sub["frequency"] == "weekly":  est_monthly += sub["amount"] * 4.33
        elif sub["frequency"] == "yearly":  est_monthly += sub["amount"] / 12
    print(f"Detected {len(subscriptions)} recurring charge(s). "
          f"Estimated monthly cost: HK${est_monthly:.2f}\n")
    for sub in subscriptions:
        last = sub["dates"][-1].strftime("%Y-%m-%d")
        print(f"  - {sub['name'].title()}: HK${sub['amount']:.2f} "
              f"({sub['frequency']}), last seen {last}")

def price_hike_alert():
    """Warn about subscription price changes >5%."""
    print("\n--- Subscription Price Hike Alerts (Rocket Money-inspired) ---")
    transactions = read_transactions_csv()
    by_name = defaultdict(list)
    for t in transactions:
        parsed = _parse_transaction(t)
        if parsed is None:
            continue
        tdate, amount, name = parsed
        by_name[name].append((tdate, amount))
    alerts_fired = 0
    for name, records in by_name.items():
        if len(records) < 3:
            continue
        records.sort()
        dates = [d for d, _ in records]
        amounts = [a for _, a in records]
        gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
        if not gaps:
            continue
        monthly_like = sum(1 for g in gaps if 28 <= g <= 33) >= len(gaps) * 0.5
        if not monthly_like:
            continue
        prev = amounts[0]
        for i in range(1, len(amounts)):
            if amounts[i] != prev and prev > 0:
                change_pct = ((amounts[i] - prev) / prev) * 100
                if abs(change_pct) >= 5:
                    direction = "up" if change_pct > 0 else "down"
                    date_str = records[i][0].strftime("%Y-%m-%d")
                    print(f"[Warning] '{name.title()}' price went {direction} "
                          f"from HK${prev:.2f} to HK${amounts[i]:.2f} "
                          f"({change_pct:+.1f}%) on {date_str}.")
                    alerts_fired += 1
            prev = amounts[i]
    if alerts_fired == 0:
        print("[OK] No subscription price changes detected.")

def duplicate_alert():
    """Flag duplicate transactions on the same day with same name and amount."""
    print("\n--- Duplicate Transaction Alerts (Monarch/Copilot-inspired) ---")
    transactions = read_transactions_csv()
    groups = defaultdict(list)
    for t in transactions:
        parsed = _parse_transaction(t)
        if parsed is None:
            continue
        tdate, amount, name = parsed
        date_str = tdate.strftime("%Y-%m-%d")
        groups[(date_str, name, round(amount, 2))].append(t)
    alerts_fired = 0
    for (date, name, amount), txns in groups.items():
        if len(txns) > 1:
            ids = ", ".join(t["ID"] for t in txns)
            print(f"[Warning] Possible duplicate on {date}: "
                  f"{len(txns)}x '{name.title()}' at HK${amount:.2f} (IDs: {ids}).")
            alerts_fired += 1
    if alerts_fired == 0:
        print("[OK] No duplicate transactions detected.")

# ── NEW ALERTS (for sidebar badge) ──────────────────────────────────────
def historical_comparison_alert():
    """Compare current month spending to same period last month."""
    transactions = read_transactions_csv()
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    this_month_start = today.replace(day=1)
    last_month = this_month_start - timedelta(days=1)
    last_month_start = last_month.replace(day=1)
    last_month_end = last_month_start.replace(day=min(today.day, _days_in_month(last_month_start)))

    def sum_up_to(transactions, start, end):
        total = 0.0
        for t in transactions:
            try:
                d = datetime.strptime(t["Date"], "%Y-%m-%d")
                amount = float(t["Amount"])
            except:
                continue
            if start <= d <= end:
                total += amount
        return total

    this_total = sum_up_to(transactions, this_month_start, today)
    last_total = sum_up_to(transactions, last_month_start, last_month_end)
    if last_total > 0:
        diff_pct = (this_total - last_total) / last_total * 100
        if diff_pct > 30:
            print(f"[Warning] Total spending this month (HK${this_total:.2f}) is {diff_pct:.0f}% higher than "
                  f"same period last month (HK${last_total:.2f}).")

def high_value_alert():
    """Flag transactions that are more than 3x the average transaction amount."""
    transactions = read_transactions_csv()
    amounts = []
    for t in transactions:
        try:
            amounts.append(float(t["Amount"]))
        except:
            pass
    if not amounts:
        return
    avg = sum(amounts) / len(amounts)
    if avg == 0:
        return
    for t in transactions:
        try:
            amount = float(t["Amount"])
            if amount > avg * 3:
                print(f"[Warning] High-value transaction: {t['Date']} \"{t['Name']}\" (HK${amount:.2f}) "
                      f"is {amount/avg:.1f}x your average (HK${avg:.2f}).")
        except:
            continue

def consecutive_overpace_alert():
    """Warn if any budget category exceeds its daily pace for 3 consecutive days."""
    transactions = read_transactions_csv()
    tags = read_tags_csv()
    assignments = read_assignments_csv()
    budgets = read_budget_csv()
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today.replace(day=1)
    days_in_month = _days_in_month(today)

    tag_map = _build_tag_map(assignments)
    daily = defaultdict(lambda: defaultdict(float))
    for t in transactions:
        try:
            d = datetime.strptime(t["Date"], "%Y-%m-%d")
            if d < month_start or d > today:
                continue
            tid = t.get("ID")
            if tid not in tag_map:
                continue
            tag_id = tag_map[tid]
            daily[d.day][tag_id] += float(t["Amount"])
        except:
            continue

    for (tag_id, period), budget_amount in budgets.items():
        if period != "monthly":
            continue
        tag_name = tags.get(tag_id, {}).get("Tag_name", f"Tag {tag_id}")
        daily_pace = budget_amount / days_in_month
        cumulative = 0.0
        consecutive = 0
        for day in range(1, today.day + 1):
            cumulative += daily[day].get(tag_id, 0.0)
            if cumulative > daily_pace * day:
                consecutive += 1
            else:
                consecutive = 0
            if consecutive >= 3:
                print(f"[Critical] '{tag_name}' has exceeded daily pace for 3 consecutive days "
                      f"(around day {day-2}‑{day}). Consider slowing down.")
                break

def peer_balance_reminder():
    """Remind about overdue peer balances based on recent activity."""
    balances = adjustments.calculate_peer_balances()
    recent = adjustments.list_recent_peer_entries(limit=50)
    latest = {}
    for entry in recent:
        peer = entry["peer"]
        if peer not in latest:
            latest[peer] = entry["date"]
    for peer, bal in balances.items():
        net = bal["net"]
        if net <= 0:
            continue
        last_date = latest.get(peer)
        if last_date:
            try:
                last_dt = datetime.strptime(last_date, "%Y-%m-%d")
                days_passed = (datetime.today() - last_dt).days
            except:
                days_passed = 999
            if days_passed > 14:
                print(f"[Warning] {peer} owes you HK${net:.2f} with no recent activity (last: {last_date}). "
                      f"Consider following up.")
            elif days_passed > 7:
                print(f"[Info] {peer} still owes you HK${net:.2f} (last activity: {last_date}).")
        else:
            print(f"[Info] {peer} owes you HK${net:.2f}. No recent activity recorded.")

def large_transaction_alert(threshold=5000):
    """Flag transactions exceeding a fixed threshold."""
    transactions = read_transactions_csv()
    for t in transactions:
        try:
            amount = float(t["Amount"])
            if amount > threshold:
                print(f"[Warning] Large transaction: {t['Date']} \"{t['Name']}\" "
                      f"(HK${amount:.2f}) exceeds HK${threshold:.0f}.")
        except:
            continue

def budget_80_percent_alert():
    """Warn when a budget category reaches 80% spent."""
    budgets = read_budget_csv()
    tags = read_tags_csv()
    transactions = read_transactions_csv()
    assignments = read_assignments_csv()
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    tag_map = _build_tag_map(assignments)
    month_txns = _current_month_transactions(transactions, today)
    spent_by_tag = _sum_by_tag(month_txns, tag_map)
    for (tag_id, period), budget_amount in budgets.items():
        if period != "monthly":
            continue
        spent = spent_by_tag.get(tag_id, 0.0)
        if budget_amount > 0:
            pct = (spent / budget_amount) * 100
            if 80 <= pct < 100:
                tag_name = tags.get(tag_id, {}).get("Tag_name", f"Tag {tag_id}")
                print(f"[Warning] '{tag_name}' budget usage at {pct:.0f}% "
                      f"(HK${spent:.2f} / HK${budget_amount:.2f}).")

# ── Unified alert runners ───────────────────────────────────────────────
def check_all_alerts():
    """Run all original alerts (for Dashboard old-style table)."""
    print("\n========== Rule-Based Alerts ==========")
    pace_alert()
    in_my_pocket_alert()
    subscription_alert()
    price_hike_alert()
    duplicate_alert()
    # new alerts are excluded from here
    print("\n=======================================\n")

def check_new_alerts():
    """Run only the new six rules and print results."""
    print("\n========== New Rule-Based Alerts ==========")
    historical_comparison_alert()
    high_value_alert()
    consecutive_overpace_alert()
    peer_balance_reminder()
    large_transaction_alert()
    budget_80_percent_alert()
    print("\n==========================================\n")

# Budget management functions (unchanged)
def add_budget():
    """CLI: add or update a budget entry."""
    tags = read_tags_csv()
    if not tags:
        print("[Error] No tags available. Please create a tag first.")
        return
    print("\n--- Add / Update Budget ---")
    print("Available tags:")
    for tid, tag in sorted(tags.items(), key=lambda x: int(x[0])):
        print(f"  {tid}. {tag['Tag_type']} - {tag['Tag_name']}")
    tag_id = input("\nEnter Tag_id: ").strip()
    if tag_id not in tags:
        print(f"[Error] Tag_id '{tag_id}' not found.")
        return
    period = input("Enter period [monthly]: ").strip().lower() or "monthly"
    if period != "monthly":
        print("[Info] Only 'monthly' budgets are currently supported.")
        return
    amount_str = input("Enter budget amount (HK$): ").strip()
    try:
        amount = float(amount_str)
        if amount < 0: raise ValueError
    except ValueError:
        print("[Error] Invalid amount.")
        return
    budgets = read_budget_csv()
    budgets[(tag_id, period)] = amount
    write_budget_csv(budgets)
    print(f"[Success] Budget set: {tags[tag_id]['Tag_name']} - HK${amount:.2f} ({period})")

def list_budgets():
    """CLI: list all budgets."""
    budgets = read_budget_csv()
    tags = read_tags_csv()
    if not budgets:
        print("[Info] No budgets found.")
        return
    print("\n--- Budgets ---")
    for (tag_id, period), amount in sorted(budgets.items(), key=lambda x: int(x[0][0])):
        tag_name = tags.get(tag_id, {}).get("Tag_name", f"Tag {tag_id}")
        print(f"  {tag_id}. {tag_name} - HK${amount:.2f} ({period})")

def delete_budget():
    """CLI: delete a budget."""
    budgets = read_budget_csv()
    if not budgets:
        print("[Info] No budgets to delete.")
        return
    list_budgets()
    tag_id = input("\nEnter Tag_id of budget to delete: ").strip()
    period = input("Enter period [monthly]: ").strip().lower() or "monthly"
    if (tag_id, period) not in budgets:
        print(f"[Error] No budget found for Tag_id '{tag_id}' period '{period}'.")
        return
    del budgets[(tag_id, period)]
    write_budget_csv(budgets)
    print("[Success] Budget deleted.")