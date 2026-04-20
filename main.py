import cli

help_message = """
--------------------------------------
   Personal Budgeting Tool CLI
--------------------------------------
 1.  add-transaction: Add a new transaction or input csv file
 2.  delete-transaction: Delete a transaction
 3.  list-transactions: List all transactions
 4.  show-summary: Show expense summary (includes alerts)
 5.  show-graph: Visualize expenses
 6.  reset-data: Clear all transaction history
 7.  add-tag: Add a new tag
 8.  delete-tag: Delete a tag
 9.  list-tags: List all tags
 10. edit-tags: Edit a tag
 11. check-alerts: Run all rule-based alerts
 12. add-budget: Set or update a monthly budget for a tag
 13. list-budgets: List all budgets
 14. delete-budget: Delete a budget
 0.  quit: quit application
--------------------------------------
Tip: You can enter the NUMBER or the COMMAND name.
"""

def main():
    while True:
        print(help_message)

        choice = input("Your Choice (0-10): ").strip().lower()

        if choice in ["0", "quit"]:
            print("Goodbye!")
            break

        elif choice == "help":
            continue

        elif choice in ["1", "add-transaction"]:
            cli.add_transaction()

        elif choice in ["2", "delete-transaction"]:
            cli.delete_transaction()

        elif choice in ["3", "list-transactions"]:
            cli.list_transactions()

        elif choice in ["4", "show-summary"]:
            cli.show_summary()

        elif choice in ["5", "show-graph"]:
            cli.show_graph()

        elif choice in ["6", "reset-data"]:
            confirm = input("Are you sure? (yes/no): ").strip().lower()
            if confirm == "yes":
                cli.reset_data()

        elif choice in ["7", "add-tag"]:
            cli.add_tag()

        elif choice in ["8", "delete-tag"]:
            cli.delete_tag()

        elif choice in ["9", "list-tags"]:
            cli.list_tags()

        elif choice in ["10", "edit-tags"]:
            cli.edit_tags()

        elif choice in ["11", "check-alerts"]:
            cli.check_alerts()

        elif choice in ["12", "add-budget"]:
            cli.add_budget()

        elif choice in ["13", "list-budgets"]:
            cli.list_budgets()

        elif choice in ["14", "delete-budget"]:
            cli.delete_budget()

        else:
            print(f"\n[Unknown Choice: {choice}]")
            print(f"\n{help_message}")

if __name__ == "__main__":
    main()