import csv
import os 
from datetime import datetime

# constants
TRANSACTIONS_FILE = "data/transactions.csv"
TAGS_FILE         = "data/tags.csv"
ASSIGNMENT_FILE   = "data/assignment.csv"

TRANSACTION_FIELDS = ["ID", "Date", "Name", "Transaction Description", "Amount"]
TAG_FIELDS        = ["TagID", "Tag_Type", "Tag_Name"]
ASSIGNMENT_FIELDS = ["ID", "TagID"]

# --------------------------------------------------------------
# Functions for validating transaction data, loading/saving transactions, tags, and assignments

def _validate_date(date):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False
    
def _validate_amount(amount):
    try:
        value = float(amount)
        return None if value < 0 else value
    except ValueError:
        return None

def _load_transactions():
    transactions = []
    try:
        with open(TRANSACTIONS_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                transactions.append(row)
    except Exception as e:
        print(f"Error loading transactions: {e}")
    return transactions

def _save_transactions(transactions):
    try:
        with open(TRANSACTIONS_FILE, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=TRANSACTION_FIELDS)
            writer.writeheader()
            for transaction in transactions:
                writer.writerow(transaction)
    except Exception as e:
        print(f"Error saving transactions: {e}")

def _load_tags():
    tags = []
    try:
        with open(TAGS_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                tags.append(row)
    except Exception as e:
        print(f"Error loading tags: {e}")
    return tags

def _save_tags(tags):
    try:
        with open(TAGS_FILE, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=TAG_FIELDS)
            writer.writeheader()
            for tag in tags:
                writer.writerow(tag)
    except Exception as e:
        print(f"Error saving tags: {e}")

def _load_assignments():
    assignments = []
    try:
        with open(ASSIGNMENT_FILE, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                assignments.append(row)
    except Exception as e:
        print(f"Error loading tag assignments: {e}")
    return assignments

def _save_assignments(assignments):
    try:
        with open(ASSIGNMENT_FILE, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=ASSIGNMENT_FIELDS)
            writer.writeheader()
            for assignment in assignments:
                writer.writerow(assignment)
    except Exception as e:
        print(f"Error saving tag assignments: {e}")


def _list_all_tags():
    tags = _load_tags()
    if not tags:
        print("No Tags Found.")
    else:
        print("Avalibale Tags:")
        for tag in tags:
            print(f"{tag['TagID']}. {tag['Tag_Type']} - {tag['Tag_Name']}")

def _get_next_transaction_id(transactions):
    if not transactions:
        return "1"
    else:
        max_id = max(int(t["ID"]) for t in transactions)
        return str(max_id + 1)

def _get_next_tag_id(tags):
    if not tags:
        return "1"
    else:
        max_id = max(int(t["TagID"]) for t in tags)
        return str(max_id + 1)

# --------------------------------------------------------------
# Transaction management functions

def add_transaction():

    print("\n---Add New Transaction---")

    while True:
        date = input("\nEnter date (YYYY-MM-DD): ").strip()
        if _validate_date(date):
            break
        print("\n[Error] Invalid date format. Please enter in YYYY-MM-DD format.")
    
    while True:
        name = input("\nEnter transaction name (e.g. Lunch): ").strip()
        if name:
            break
        print("\n[Error] Transaction name cannot be empty. Please enter a valid name.")

    transaction_description = input("\nEnter transaction description (optional, press Enter to skip): ").strip()

    while True:
        amount = input("\nEnter transaction amount (positive number): ").strip()
        valid_amount = _validate_amount(amount)
        if valid_amount is not None:
            break
        print("\n[Error] Invalid amount. Please enter a positive number.")
    
    transactions = _load_transactions()
    new_id = _get_next_transaction_id(transactions)

    new_transaction = {
        "ID": new_id,
        "Date": date,
        "Name": name,
        "Transaction Description": transaction_description,
        "Amount": amount
    }

    transactions.append(new_transaction)
    _save_transactions(transactions)
    print(f"\n[Success] Transaction #{new_id} '{name}' added successfully!")

    
    # offer tags to transaction(allow multiple tags)
    tags = _load_tags()
    if tags:
        tag_choice = input("\nWould you like to tag this transaction? (y/n): ").strip().lower()
        if tag_choice == "y":
            _assign_tags_to_transaction(new_id, tags)
    else:
        print("[Error] No tags found. Check that data/tags.csv exists and has data.")


def _assign_tags_to_transaction(transaction_id, tags):
    _list_all_tags()
    assignments = _load_assignments() or []
    assigned_count = 0
    assigned_tags = []

    while True:
        tag_id_input = input(f"\nEnter TagID(s) to tag transaction #{transaction_id} (separated by ';' if multiple, e.g. '1;2') or press Enter to skip: ").strip().split(';')
        
        if not tag_id_input:
            print("No tags assigned.")
            break

        for tag_id in tag_id_input:
            matching = [t for t in tags if t["TagID"] == tag_id]

            if not matching:
                print(f"[Error] No tag with TagID '{tag_id}'. Skipped.")
                continue

            #check to avoid duplicate assignment
            already_assigned = [a for a in assignments if a["ID"] == transaction_id and a["TagID"] == tag_id]
            if already_assigned:
                print(f"  [Warning] Tag '{matching[0]['Tag Name']}' is already assigned to transaction #{transaction_id}. Skipping duplicate.")
                continue
            
            assignments.append({"ID": transaction_id, "TagID": tag_id})
            assigned_count += 1
            assigned_tags.append(matching[0]["Tag_Type"])
            print(f"  [Success] Assigned tag '{matching[0]['Tag_Type']}' to transaction #{transaction_id}.")

        if assigned_count > 0:
            _save_assignments(assignments)
            print(f"\n[Success] Assigned {assigned_count} tag(s) to Transaction #{transaction_id}: {', '.join(assigned_tags)}")
            break
        else:
            print("No valid tags assigned. Please try again or press Enter to skip.")

def add_transaction_from_csv():
    print("\n---Import Transactions from CSV File---")
    print(f'Please ensure your CSV file has the following columns:\n "Date", "Name", "Transaction Description (optional)", "Amount", "Tag_Type(optional, separated by ";")"\n')
    print(f'[Note] Separate multiple tags with semicolons, e.g. "Bills;Needs"\n')
    print(f'[Example CSV Format]\nDate,Name,Transaction Description,Amount,Tag_Type\n2026-01-01,Groceries,Weekly grocery shopping,150.00,Bills;Needs\n2026-01-02,Coffee,,4.50,Needs\n')
    print(f'[Info] Transactions will be tagged if the tag name already exists. New tags will be created for any non-existing tag names in the CSV.\n')
    print(f'[Info] After importing, you can edit Tag Types and Tag Names in the "Edit Tags" section of the main menu.\n')
    
    file_path = input("Enter the path to your CSV file: ").strip()
    if not os.path.isfile(file_path):
        print("[Error] File not found. Please check the path and try again.")
        return
    
    imported_rows = []

    try:
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)

            required_columns = {"Date", "Name", "Amount"}
            file_columns = set(reader.fieldnames or [])
            if not required_columns.issubset(file_columns):
                print(f"[Error] CSV is missing required column(s): {required_columns - file_columns}")
                return
            
            for line_num, row in enumerate(reader, start=2):

                date = row.get("Date", "").strip()
                name = row.get("Name", "").strip()
                transaction_description = row.get("Transaction Description", "").strip()
                amount = row.get("Amount", "").strip()
                tags = row.get("Tag_Type", "").strip()

                if not _validate_date(date):
                    print(f"[Error] Skipping line {line_num} with invalid date: {date}")
                    continue

                if not name:
                    print(f"[Error] Skipping line {line_num} with empty transaction name.")
                    continue

                valid_amount = _validate_amount(amount)
                if valid_amount is None:
                    print(f"[Error] Skipping line {line_num} with invalid amount: {amount}")
                    continue

                tag_names = []
                if tags:
                    tag_names = [t.strip() for t in tags.split(';') if t.strip()]

                imported_rows.append({
                    "Date": date,
                    "Name": name,
                    "Transaction Description": transaction_description,
                    "Amount": amount,
                    "Tag_Type": tag_names,
                    
                })

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return    
        
    if not imported_rows:
        print("[Info] No valid transactions found in the CSV file.")
        return

    transactions = _load_transactions()
    next_transaction_id = _get_next_transaction_id(transactions)
    
    for row in imported_rows:
        tags_name = row.pop("Tag_Type")
        row["ID"] = next_transaction_id
        transactions.append(row)

        if tags_name:
            _link_tags_by_name(next_transaction_id, tags_name)

        next_transaction_id = str(int(next_transaction_id) + 1)
    
    _save_transactions(transactions)
    print(f"\n[Success] Imported {len(imported_rows)} transaction(s)!")

def _link_tags_by_name(transaction_id, tag_names):
    all_tags = _load_tags()
    assignments = _load_assignments() or []
    name_to_id = {t["Tag_Type"]: t["TagID"] for t in all_tags}
    num_of_tags_added = 0

    for tag_name in tag_names:
        tag_id = name_to_id.get(tag_name.lower())
        if tag_id is None:
            tag_id = _get_next_tag_id(all_tags)
            new_tag = {"TagID": tag_id, "Tag_Type": tag_name, "Tag_Name": ""}
            all_tags.append(new_tag)
            name_to_id[tag_name.lower()] = tag_id
            print(f"  [Info] Created new tag '{tag_name}' with ID {tag_id}.")
        else:
            already = any(
            a["ID"] == str(transaction_id) and a["TagID"] == tag_id
            for a in assignments
        )
            if not already:
                assignments.append({"ID": str(transaction_id), "TagID": tag_id})
                num_of_tags_added += 1

    if num_of_tags_added > 0:
        _save_assignments(assignments)


def delete_transaction():
    print("\n--- Delete Transaction ---\n")
    list_transactions()

    transactions = _load_transactions()
    if not transactions:
        print("[Info] No transactions to delete.")
        return

    while True:
        id_input = input("\nEnter a ID to delete (or 'cancel' to go back): ").strip()
        if id_input.lower() == "cancel":
            print("Deletion cancelled.")
            return
        
        matching = [t for t in transactions if t["ID"] == id_input]
        if matching:
            t = matching[0]
            print(f"\nAbout to delete:")
            print(f"  ID {t['ID']}  |  {t['Date']}  |  {t['Name']}  |  HK${t['Amount']}")

            confirm = input("Confirm? (yes / no): ").strip().lower()
            if confirm == "yes":
                transactions = [t for t in transactions if t["ID"] != id_input]
                _save_transactions(transactions)

                assignments = _load_assignments()
                assignments = [a for a in assignments if a["ID"] != id_input]
                _save_assignments(assignments)

                print(f"[Success] Transaction #{id_input} deleted (and its tag assignments removed).")
            else:
                print("Deletion cancelled.")
            
        else:
            print(f"[Error] No transaction with ID '{id_input}'. Try again.")

def list_transactions(): #list all transactions
    print("Transaction List:")
    transactions = _load_transactions()
    if not transactions:
        print("No transactions found.")
    else:
        for transaction in transactions:
            print(f"{transaction['ID']}. {transaction['Name']} ,{transaction['Transaction Description']}- {transaction['Amount']}")



