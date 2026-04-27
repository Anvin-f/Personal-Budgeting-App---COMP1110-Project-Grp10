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


def _list_all_tags():
    tags = _load_tags()
    if not tags:
        print("No Tags Found.")
    else:
        print("Avalibale Tags:")
        for tag in tags:
            print(f"{tag['Tag_id']}. {tag['Tag_type']} - {tag['Tag_name']}")

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
        
        if tag_id_input == ['']:
            print("No tags assigned.")
            break

        for tag_id in tag_id_input:
            matching = [t for t in tags if t["Tag_id"] == tag_id]

            if not matching:
                print(f"[Error] No tag with TagID '{tag_id}'. Skipped.")
                continue

            #check to avoid duplicate assignment
            already_assigned = [a for a in assignments if a['ID'] == transaction_id and a['TagID'] == tag_id]
            if already_assigned:
                print(f"  [Warning] Tag '{matching[0]['Tag_type']}' is already assigned to transaction #{transaction_id}. Skipping duplicate.")
                continue
            
            assignments.append({"ID": transaction_id, "TagID": tag_id})
            assigned_count += 1
            assigned_tags.append(matching[0]["Tag_type"])
            print(f"  [Success] Assigned tag '{matching[0]['Tag_type']}' to transaction #{transaction_id}.")

        if assigned_count > 0:
            _save_assignments(assignments)
            print(f"\n[Success] Assigned {assigned_count} tag(s) to Transaction #{transaction_id}: {', '.join(assigned_tags)}")
            break
        else:
            print("No valid tags assigned. Please try again or press Enter to skip.")

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
        with open(file_path, mode='r', newline='') as file:
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
            print(f"{transaction['ID']}. {transaction['Date']}, {transaction['Name']} ,{transaction['Transaction Description']}- {transaction['Amount']}")



