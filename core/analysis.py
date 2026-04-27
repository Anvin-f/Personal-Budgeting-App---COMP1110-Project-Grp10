import csv
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def link_tags():
    tag_link = {}
    with open('data/assignment.csv', mode='r') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if not row:
                continue
            ID = int(row[0])
            tag_ID = int(row[1])
            tag_link[ID] = tag_ID
    return tag_link

def definetag():
    tags = set()
    tag_type = {}
    tag_name = {}
    with open('data/tags.csv', mode='r') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if not row:
                continue
            tag_ID = int(row[0])
            tag_type[tag_ID] = row[1]
            tag_name[tag_ID] = row[2]
            tags.add(tag_ID)
    return tags, tag_type, tag_name

def printspend(tag_name, category, total_spend, ids):
    print(f'{ids} BREAKDOWN:\n')
    print(f'{ids} total spending: {total_spend}\n')
    print(f'{ids} Category Breakdown:')
    for tag_id in category:
        print(f'{tag_name[tag_id]}: {category[tag_id]}')
    return

def printtop3(tag_name, category):
    print("\nTop 3 Categories Spent:")
    fre = 0
    for tag_id, amount in category:
        print(f'{tag_name[tag_id]}: {amount}')
        fre += 1
        if fre == 3:
            break
    return

def show_summary():
    tag_link = link_tags()
    tags, tag_type, tag_name = definetag()

    total_spend_month = 0
    total_spend_week = 0
    total_spend_today = 0

    category_month = {}
    category_week = {}
    category_today = {}

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    week_cutoff = today - timedelta(days=6)

    with open('data/transactions.csv', mode='r') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if not row:
                continue
            transaction_id = int(row[0])
            transaction_date = datetime.strptime(row[1], "%Y-%m-%d")
            transaction_name = row[2]
            transaction_amount = float(row[4])

            # check if included in current month
            if today.month == transaction_date.month and today.year == transaction_date.year:
                total_spend_month += transaction_amount
                if tag_link.get(transaction_id) is None:
                    continue
                tag_id = tag_link[transaction_id]
                if tag_id not in category_month:
                    category_month[tag_id] = transaction_amount
                else:
                    category_month[tag_id] += transaction_amount

            # check if included in current week
            if transaction_date >= week_cutoff:
                total_spend_week += transaction_amount
                if tag_link.get(transaction_id) is None:
                    continue
                tag_id = tag_link[transaction_id]
                if tag_id not in category_week:
                    category_week[tag_id] = transaction_amount
                else:
                    category_week[tag_id] += transaction_amount

            # check if included today
            if transaction_date >= today:
                total_spend_today += transaction_amount
                if tag_link.get(transaction_id) is None:
                    continue
                tag_id = tag_link[transaction_id]
                if tag_id not in category_today:
                    category_today[tag_id] = transaction_amount
                else:
                    category_today[tag_id] += transaction_amount

    printspend(tag_name, category_today, total_spend_today, "Daily")
    printspend(tag_name, category_week, total_spend_week, "Weekly")
    printspend(tag_name, category_month, total_spend_month, "Monthly")

    sorted_category = sorted(category_month.items(), key=lambda item: item[1], reverse=True)
    printtop3(tag_name, sorted_category)

    return

def line_graph(category_month):
    category_month = dict(sorted(category_month.items(), key=lambda item: item[1], reverse=True))
    categories = list(category_month.keys())
    amounts = list(category_month.values())

    plt.clf()
    plt.plot(categories, amounts, color='skyblue', marker='o', linestyle='-')
    plt.xlabel('Category', fontsize=12)
    plt.ylabel('Amount Spent ($)', fontsize=12)
    plt.title('Monthly Spending Summary', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

    return

def bar_graph(spending_per_day):
    spending_per_day = sorted(spending_per_day.items())
    dates = [item[0] for item in spending_per_day]
    amounts = [item[1] for item in spending_per_day]

    plt.clf()
    plt.bar(dates, amounts, color='teal')
    plt.xlabel('Date')
    plt.ylabel('Amount Spent ($)')
    plt.title('Daily Spending Summary')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    return

def show_graph():
    tag_link = link_tags()
    tags, tag_type, tag_name = definetag()

    category_month = {}
    spending_per_day = {}

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    thirtyday_cutoff = today - timedelta(days=29)

    with open('data/transactions.csv', mode='r') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if not row:
                continue
            transaction_id = int(row[0])
            transaction_date = datetime.strptime(row[1], "%Y-%m-%d")
            transaction_name = row[2]
            transaction_amount = float(row[4])

            # check if included in current month
            if today.month == transaction_date.month and today.year == transaction_date.year:
                if tag_link.get(transaction_id) is None:
                    continue
                tag_id = tag_link[transaction_id]
                cat_name = tag_name.get(tag_id, "Unknown")
                if cat_name not in category_month:
                    category_month[cat_name] = transaction_amount
                else:
                    category_month[cat_name] += transaction_amount

            # check if within last 30 days
            if transaction_date >= thirtyday_cutoff:
                day_str = transaction_date.strftime('%Y-%m-%d')
                if day_str not in spending_per_day:
                    spending_per_day[day_str] = transaction_amount
                else:
                    spending_per_day[day_str] += transaction_amount

    line_graph(category_month)
    bar_graph(spending_per_day)

    return