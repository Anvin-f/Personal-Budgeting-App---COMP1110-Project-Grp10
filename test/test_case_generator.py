import csv
import os
import random
from datetime import datetime, timedelta

TRANSACTION_FIELDS = ["ID", "Date", "Name", "Transaction Description", "Amount"]
TAG_FIELDS         = ["TagID", "Tag Type", "Tag Name"]
ASSIGNMENT_FIELDS  = ["ID", "TagID"]
IMPORT_FIELDS      = ["Date", "Name", "Transaction Description", "Amount", "Tag Type", "Tag Name"]

transaction_name_list = ["McDonalds", "KFC", "Starbucks", "Bus", "MTR", "H&M", "UNIQLO"]
transaction_description_list = ["Lunch", "Dinner", "Coffee", "Transport", "Clothes", "Snacks"]
tag_name_list = ["Food", "Shopping", "Commuting", "Travel", "Entertainment"]
tag_type_list = ["Bills", "Needs", "Wants"]

def save_to_csv(file_path, header, data):
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)

def write_import_csv(file_name, rows):
    save_to_csv(file_name, IMPORT_FIELDS, rows)

def generate_normal(file_name="tests/normal_import.csv", count=10):
    rows = []
    start_date = datetime(2026, 1, 1)
    for i in range(count):
        date = (start_date + timedelta(days=random.randint(0, 100))).strftime("%Y-%m-%d")
        name = random.choice(transaction_name_list)
        desc = random.choice(transaction_description_list)
        amount = round(random.uniform(10.0, 500.0), 2)
        t_type = random.choice(tag_type_list)
        t_name = random.choice(tag_name_list)
        rows.append([date, name, desc, amount, t_type, t_name])
    write_import_csv(file_name, rows)
    print(f"[Success] {file_name} generated.")

def generate_empty(file_name="tests/empty_fields_import.csv"):
    rows = [
        ["2026-05-01", "Rent", "", "8000.00", "Bills", "Housing"],
        ["2026-05-02", "Gift", "Birthday", "200.00", "", ""],
        ["2026-05-03", "Water", "Bill", "50.00", "Bills", ""],
    ]
    write_import_csv(file_name, rows)
    print(f"[Success] {file_name} generated.")

def generate_negative_amount(file_name="tests/negative_amount_import.csv"):
    rows = [
        ["2026-06-01", "Refund Error", "Test", "-50.00", "Wants", "Food"],
        ["2026-06-02", "Zero Cost", "Test", "0.00", "Wants", "Gift"],
    ]
    write_import_csv(file_name, rows)
    print(f"[Success] {file_name} generated.")

def generate_invalid_date(file_name="tests/invalid_date_import.csv"):
    rows = [
        ["2026/01/01", "Wrong Format", "Test", "10.00", "Wants", "Food"],
        ["NotADate", "String Date", "Test", "10.00", "Wants", "Food"],
    ]
    write_import_csv(file_name, rows)
    print(f"[Success] {file_name} generated.")

def generate_extreme_amount(file_name="tests/extreme_amount_import.csv"):
    rows = [
        ["2026-07-01", "High Value", "Test", "999999.99", "Wants", "Luck"],
        ["2026-07-02", "Invalid Num", "Test", "ABC", "Wants", "Food"],
    ]
    write_import_csv(file_name, rows)
    print(f"[Success] {file_name} generated.")

def generate_logic_edge_cases(file_name="tests/logic_edge_import.csv"):
    rows = [
        ["2026-08-01", "Space Test", "Description", "50.00", "Wants", " Food "],
        ["2026-08-01", "Case Test", "Description", "50.00", "Wants", "food"],
        ["2026-08-02", "Special Char", "Emoji test 🍔", "45.50", "Wants", "Dinner&Social"],
        ["2026-08-02", "CSV Escape", "Comma, in, desc", "100.00", "Needs", "Grocery"],
    ]
    write_import_csv(file_name, rows)
    print(f"[Success] {file_name} generated.")

def generate_duplicates(file_name="tests/duplicate_import.csv"):
    row = ["2026-09-01", "Repeat", "Duplicate Row", "10.00", "Wants", "Misc"]
    rows = [row, row, row]
    write_import_csv(file_name, rows)
    print(f"[Success] {file_name} generated.")

def generate_long_strings(file_name="tests/long_strings_import.csv"):
    rows = [
        ["2026-10-01", "A" * 50, "B" * 200, "99.00", "Wants", "C" * 30],
    ]
    write_import_csv(file_name, rows)
    print(f"[Success] {file_name} generated.")

if __name__ == '__main__':
    if not os.path.exists("tests"):
        os.makedirs("tests")
    
    generate_normal()
    generate_empty()
    generate_negative_amount()
    generate_invalid_date()
    generate_extreme_amount()
    generate_logic_edge_cases()
    generate_duplicates()
    generate_long_strings()