import csv
import random
from datetime import datetime, timedelta

IMPORT_FIELDS = ["Date", "Name", "Transaction Description", "Amount", "Tag_type", "Tag_name"]

transaction_name_list = ["McDonalds", "KFC", "Starbucks", "Bus", "MTR", "H&M", "UNIQLO"]
transaction_description_list = ["Lunch", "Dinner", "Coffee", "Transport", "Clothes", "Snacks"]
tag_name_list = ["Food", "Shopping", "Commuting", "Travel", "Entertainment"]
tag_type_list = ["Bills", "Needs", "Wants"]


def save_to_csv(file_path, header, data):
    with open(file_path, "w", newline="", encoding="utf-8") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(header)
        writer.writerows(data)


def write_import_csv(file_name, rows):
    save_to_csv(file_name, IMPORT_FIELDS, rows)


def generate_normal(file_name, count=30):
    rows = []
    start_date = datetime(2026, 1, 1)
    for _ in range(count):
        date = (start_date + timedelta(days=random.randint(0, 100))).strftime("%Y-%m-%d")
        name = random.choice(transaction_name_list)
        desc = random.choice(transaction_description_list)
        amount = round(random.uniform(10.0, 500.0), 2)
        t_type = random.choice(tag_type_list)
        t_name = random.choice(tag_name_list)
        rows.append([date, name, desc, amount, t_type, t_name])
    write_import_csv(file_name, rows)


def generate_logic_edge_cases(file_name):
    rows = [
        ["2026-08-01", "Space Test", "Description", "50.00", "Wants", " Food "],
        ["2026-08-01", "Case Test", "Description", "50.00", "Wants", "food"],
        ["2026-08-02", "Special Char", "Emoji tests 🍔", "45.50", "Wants", "Dinner&Social"],
        ["2026-08-02", "CSV Escape", "Comma, in, desc", "100.00", "Needs", "Grocery"],
        ["", "", "", "", "", ""],
    ]
    write_import_csv(file_name, rows)


def generate_duplicates(file_name):
    row = ["2026-09-01", "Repeat", "Duplicate Row", "10.00", "Wants", "Misc"]
    rows = [row, row, row]
    write_import_csv(file_name, rows)
