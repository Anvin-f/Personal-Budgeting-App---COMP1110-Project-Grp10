import csv
import os 
from datetime import datetime

# constants
TRANSACTIONS_FILE = "data/transactions.csv"
TAGS_FILE         = "data/tags.csv"
ASSIGNMENT_FILE   = "data/assignment.csv"

TRANSACTION_FIELDS = ["ID", "Date", "Name", "Transaction Description", "Amount"]
TAG_FIELDS        = ["Tag_id", "Tag_type", "Tag_name"]
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
        max_id = max(int(t["Tag_id"]) for t in tags)
        return str(max_id + 1)

def add_transaction_from_csv():
    print("\n---Import Transactions from CSV File---")
    print(f'Please ensure your CSV file has the following columns:\n "Date", "Name", "Transaction Description (optional)", "Amount", "Tag_type", "Tag_name"\n')
    print(f'[Example CSV Format]\nDate,Name,Transaction Description,Amount,Tag_type,Tag_name\n2026-01-01,Groceries,Weekly grocery shopping,150.00,Bills,Weekly Groceries\n2026-01-02,Coffee,,4.50,Needs,Coffee\n')
    print(f'[Info] Transactions will be tagged if the tag type and tag name already exists.\n New tags will be created for any non-existing tag types and tag names in the CSV.\n')
    print(f'[Info] After importing, you can edit Tag Types and Tag Names in the "Edit Tags" section of the main menu.\n')
    print(f'[Example CSV File Path] \nMac: /Users/username/Downloads/transactions.csv\n Windows: C:\\Users\\username\\Downloads\\transactions.csv\n')
    
    file_path = input("Enter the path to your CSV file: ").strip()
    if not os.path.isfile(file_path):
        print("[Error] File not found. Please check the path and try again.")
        return
    
    imported_rows = []

    try:
        # Use a tolerant UTF-8 reader so CSV imports do not fail on odd bytes.
        with open(file_path, mode='r', newline='', encoding='utf-8-sig', errors='replace') as file:
            reader = csv.DictReader(file)

            required_columns = {"Date", "Name", "Amount"}
            file_columns = set(reader.fieldnames or [])
            if not required_columns.issubset(file_columns):
                print(f"[Error] CSV is missing required column(s): {required_columns - file_columns}")
                return
            
            has_tag_type = "Tag_type" in file_columns  
            has_tag_name = "Tag_name" in file_columns  
            if not has_tag_type or not has_tag_name:
                print("[Warning] CSV missing 'Tag_type' or 'Tag_name' column. Tags will be skipped for all transactions.")
            
            for line_num, row in enumerate(reader, start=2):

                date = (row.get("Date") or "").strip()
                name = (row.get("Name") or "").strip()
                transaction_description = (row.get("Transaction Description") or "").strip()
                amount = (row.get("Amount") or "").strip()
                tag_type = (row.get("Tag_type") or "").strip()
                tag_name = (row.get("Tag_name") or "").strip()

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

                if not tag_type:
                    print(f"[Warning] Line {line_num} missing 'Tag_type'. This transaction will be imported without tags.\n")

                if tag_type and not tag_name:
                    print(f"[Warning] Line {line_num} missing 'Tag_name'. This transaction will be imported with the tag type '{tag_type}' and without a specific tag name.\\n")

                
                imported_rows.append({
                    "Date": date,
                    "Name": name,
                    "Transaction Description": transaction_description,
                    "Amount": amount,
                    "Tag_type": tag_type,
                    "Tag_name": tag_name
                    
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
        tag_type = row.pop("Tag_type")
        tag_name = row.pop("Tag_name")
        row["ID"] = next_transaction_id
        transactions.append(row)

        if tag_type:
            _link_tag_to_transaction(next_transaction_id, tag_type, tag_name)

        else:
            print(f"  [Info] Transaction '{row['Name']}' has no Tag_Type, skipping tag linkage.")
        
        next_transaction_id = str(int(next_transaction_id) + 1)
    
    _save_transactions(transactions)
    print(f"\n[Success] Imported {len(imported_rows)} transaction(s)!")
    print("Imported Transactions:")    #display imported transactions with their assigned tags (if any)
    for row in imported_rows:
        tag_info = ""
        if row.get("Tag_type") and row.get("Tag_name"):
            tag_info = f" [Tag: {row['Tag_type']} - {row['Tag_name']}]"
        elif row.get("Tag_type"):
            tag_info = f" [Tag Type only: {row['Tag_type']}]"
        else:
            tag_info = " [No tag]"
        print(f"  ID {row['ID']}: {row['Date']} | {row['Name']} | ${row['Amount']}{tag_info}")

def _link_tag_to_transaction(transaction_id, tag_type, tag_name):
    all_tags = _load_tags()
    assignments = _load_assignments() or []

    existing_tag = None  #to check if tag already exists
    for tag in all_tags:
        if tag["Tag_type"].lower() == tag_type.lower() and tag["Tag_name"].lower() == tag_name.lower():
            existing_tag = tag
            break
    
    if existing_tag is None:
        new_tag_id = _get_next_tag_id(all_tags)
        new_tag = {
            "Tag_id": new_tag_id,
            "Tag_type": tag_type,   
            "Tag_name": tag_name
        }
        all_tags.append(new_tag)
        _save_tags(all_tags)
        print(f"  [Info] Created new tag '{tag_type} - {tag_name}' with Tag_id {new_tag_id}.")
        tag_id_to_use = new_tag_id
    else:
        tag_id_to_use = existing_tag["Tag_id"]
    
    #check if this transaction is already linked to this tag to avoid duplicate assignment
    already_linked = any(
        assignment["ID"] == str(transaction_id) and assignment["TagID"] == tag_id_to_use
        for assignment in assignments
    )
    
    if not already_linked:
        assignments.append({"ID": str(transaction_id), "TagID": tag_id_to_use})
        _save_assignments(assignments)
        print(f"  [Info] Linked transaction {transaction_id} to tag '{tag_type} - {tag_name}'.")
    else:
        print(f"  [Info] Transaction {transaction_id} already linked to tag '{tag_type} - {tag_name}'.")



