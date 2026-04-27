import core.transaction as transaction
import core.analysis as analysis
import core.utils as utils
import core.tags as tags
import core.alerts as alerts

#have to support csv and manual input
def add_transaction():
    print(f"\nHow would you like to add a transaction?\n")
    print("1. Manual input")
    print("2. Input from a CSV file")
    choice = input("\nEnter your choice (1 or 2): ")

    if choice == '1':
        transaction.add_transaction()
    elif choice == '2':
        transaction.add_transaction_from_csv()
    else: 
        print("Invalid choice. Returning to main menu.")
    return

def delete_transaction():
    transaction.delete_transaction()
    return 

def list_transactions():
    transaction.list_transactions()
    return
    
def show_graph():
    analysis.show_graph()
    return

def reset_data():
    utils.reset_data()
    return

def add_tag():
    tags.add_tag()
    return

def delete_tag():
    tags.delete_tag()
    return

def list_tags():
    tags.list_tags()
    return

#alerts

def check_alerts():
    alerts.check_all_alerts()

def add_budget():
    alerts.add_budget()

def list_budgets():
    alerts.list_budgets()

def delete_budget():
    alerts.delete_budget()

# Modify the existing show_summary to also show alerts:
def show_summary():
    analysis.show_summary()
    alerts.check_all_alerts()
    return
