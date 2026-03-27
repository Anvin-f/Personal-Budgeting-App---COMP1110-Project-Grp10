import csv
import os 
from datetime import datetime

# constants
TRANSACTIONS_FILE = "data/transactions.csv"
TAGS_FILE         = "data/tags.csv"
ASSIGNMENT_FILE   = "data/assignment.csv"

TRANSACTION_FIELDS = ["ID", "Date", "Name", "Description", "Amount"]
TAG_FIELDS        = ["TagID", "Name", "Description"]
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
            writer = csv.DictWriter(file, fieldnames=TRANSACTION_FIELDS))
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
            print(f"{tag['TagID']}. {tag['Name']} - {tag['Description']}")

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
# Tag management functions

def create_tag():



def delete_tag():




def edit_tag():



# --------------------------------------------------------------
# Transaction management functions

def add_transaction():

    print("Add New Transaction")

    while True:
        date = input("Enter date (YYYY-MM-DD): ").strip()
        if _validate_date(date):
            break
        print("Invalid date format. Please enter in YYYY-MM-DD format.")
    
    while True:
        name = input("Enter transaction name (e.g. Lunch): ").strip()
        if name:
            break
        print("Transaction name cannot be empty. Please enter a valid name.")

    description = input("Enter transaction description (optional, press Enter to skip): ").strip()

    while True:
        amount = input("Enter transaction amount (positive number): ").strip()
        valid_amount = _validate_amount(amount)
        if valid_amount is not None:
            break
        print("Invalid amount. Please enter a positive number.")
    
    transactions = _load_transactions()
    new_id = _get_next_transaction_id(transactions)

    new_transaction = {
        "ID": new_id,
        "Date": date,
        "Name": name,
        "Description": description,
        "Amount": amount
    }

    transactions.append(new_transaction)
    _save_transactions(transactions)
    print("Transaction added successfully!")

    
    # offer tags to transaction(allow multiple tags)---------------------------
    print("Would you like to add tags to this transaction? (y/n)")
    choice = input().strip().lower()
    if choice == 'y':
        _list_all_tags()
        tag_ids = input("Enter tag IDs to assign (separated by ';'): ").strip().split(';')
        tags = _load_tags()
        valid_tag_ids = {tag['TagID'] for tag in tags}
        assignments = _load_assignments()

        for tag_id in tag_ids:
            if tag_id in valid_tag_ids:
                assignment = {"ID": new_id, "TagID": tag_id}
                assignments.append(assignment)
            else:
                print(f"Tag ID {tag_id} is invalid and will be skipped.")
        
        _save_assignments(assignments)
        print("Tags assigned successfully!")
    else:
        print("No tags assigned to this transaction.")


def add_transaction_from_csv():
    print("Import Transactions from CSV File")
    print("Please ensure your CSV file has the following columns: Date, Name, Description (optional), Amount, Tags(optional, separated by ';')")

    file_path = input("Enter the path to your CSV file: ").strip()
    if not os.path.isfile(file_path):
        print("File not found. Please check the path and try again.")
        return
    
    imported_rows = []

    try:
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                date = row.get("Date", "").strip()
                name = row.get("Name", "").strip()
                description = row.get("Description", "").strip()
                amount = row.get("Amount", "").strip()
                tags = row.get("Tags").strip()

                if not _validate_date(date):
                    print(f"Skipping row with invalid date: {date}")
                    continue
                if not name:
                    print("Skipping row with empty transaction name.")
                    continue
                valid_amount = _validate_amount(amount)
                if valid_amount is None:
                    print(f"Skipping row with invalid amount: {amount}")
                    continue

                imported_rows.append({
                    "Date": date,
                    "Name": name,
                    "Description": description,
                    "Amount": amount,
                    "Tags": tags
                })
        
        if not imported_rows:
            print("No valid transactions found in the CSV file.")
            return
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    transactions = _load_transactions()
    
    for row in imported_rows:
        tags = row.pop("Tags")
        row["ID"] = _get_next_transaction_id(transactions)
        transactions.append(row)

    # link tagsID to transaction ID and save to assignment.csv


    _save_transactions(transactions)



def delete_transaction():





    return 



def list_transactions(): #list all transactions
    print("Transaction List:")
    transactions = _load_transactions()
    if not transactions:
        print("No transactions found.")
    else:
        for transaction in transactions:
            print(f"{transaction['ID']}. {transaction['Name']} ,{transaction['Description']}- {transaction['Amount']}")


    #list transactions by date, name, amount, tag, etc. (allow sorting and filtering) ??

