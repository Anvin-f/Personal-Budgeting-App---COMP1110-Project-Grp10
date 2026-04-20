import cli

help_message = """
Personal Budgeting Tool CLI

Commands:
add-transaction: Add a new transaction or input csv file
delete-transaction: Delete a transaction
list-transactions: List all transactions
show-summary: Show expense summary (includes alerts)
show-graph: Visualize expenses
reset-data: Clear all transaction history
add-tag: Add a new tag
delete-tag: Delete a tag
list-tags: List all tags
edit-tags: Edit a tag
check-alerts: Run all rule-based alerts
add-budget: Set or update a monthly budget for a tag
list-budgets: List all budgets
delete-budget: Delete a budget
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
        elif cli_command == "check-alerts":
            cli.check_alerts()
        elif cli_command == "add-budget":
            cli.add_budget()
        elif cli_command == "list-budgets":
            cli.list_budgets()
        elif cli_command == "delete-budget":
            cli.delete_budget()
        else:
            print(help_message)

        cli_command = input("Your Command: ")

if __name__ == "__main__":
    main()