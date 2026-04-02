import cli

help_message = """
Personal Budgeting Tool CLI

Commands:
add-transaction: Add a new transaction or input csv file
delete-transaction: Delete a transaction
list-transactions: List all transactions
show-summary: Show expense summary
show-graph: Visualize expenses 
reset-data: Clear all transaction history
quit: quit application
"""

def main():
    cli_command = ""
    while cli_command != "quit":

        if cli_command  == "add-transaction":
            cli.add_transaction()
        elif cli_command == "delete-transaction":
            cli.delete_transaction()
        elif cli_command == "list-transactions":
            cli.list_transactions()
        elif cli_command == "show-summary":
            cli.show_summary()
        elif cli_command == "show-graph":
            cli.show_graph()
        elif cli_command == "add-tag":
            cli.add_tag()
        elif cli_command == "delete-tag":
            cli.delete_tag()
        elif cli_command == "list-tags":
            cli.list_tags()
        elif cli_command == "reset-data":
            cli.reset_data()
        else:
            print(help_message)

        cli_command = input("Your Command: ")

if __name__ == "__main__":
    main()