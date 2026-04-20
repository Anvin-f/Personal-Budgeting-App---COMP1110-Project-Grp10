import cli

help_message = """
--------------------------------------
   Personal Budgeting Tool CLI
--------------------------------------
 1. Add Transaction (Manual/CSV) [add-transaction]
 2. Delete Transaction           [delete-transaction]
 3. List Transactions            [list-transactions]
 4. Show Summary                 [show-summary]
 5. Show Graph                   [show-graph]
 6. Reset Data                   [reset-data]
 7. Add Tag                      [add-tag]
 8. Delete Tag                   [delete-tag]
 9. List Tags                    [list-tags]
 10. Edit Tags                   [edit-tags]
 0. Quit                         [quit]
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

        else:
            print(f"\n[Unknown Choice: {choice}]")
            print(f"\n{help_message}")

if __name__ == "__main__":
    main()