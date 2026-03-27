import core.transaction as transaction
import core.analysis as analysis
import core.utils as utils

#have to support csv and manual input
def add_transaction():
    print("How would you like to add a transaction?")
    print("1. Manual input")
    print("2. Input from a CSV file")
    choice = input("Enter your choice (1 or 2): ")

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

#alerts should be shown on the summary
def show_summary(): 
    analysis.show_summary()
    return
    
def show_graph():
    analysis.show_graph()
    return

def reset_data():
    utils.reset_data()
    return
