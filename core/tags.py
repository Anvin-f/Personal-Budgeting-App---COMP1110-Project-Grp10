import core.transaction as transaction

def _validate_tag_name(name, tags, exclude_id=None):
   
    name_lower = name.lower()
    for t in tags:
        if t["TagID"] == exclude_id:
            continue
        if t["Tag Name"].lower() == name_lower:
            return False
    return True

#----------------------------------------------------------------

def add_tag():

    print("\n---Add a new tag---")
    tags = transaction._load_tags()

    while True:
        name = input("Tag name: ").strip()
        if not name:
            print("[Error] Tag name cannot be empty.")
            continue
        if not _validate_tag_name(name, tags):
            print(f"[Error] Tag '{name}' already exists.")
            continue
        break
        
    description = input("Tag Description (optional, press Enter to skip): ").strip()

    new_tagid = transaction._get_next_tag_id(tags)
    new_tag = {
        "TagID": new_tagid,
        "Tag Name": name,
        "Tag Description": description    }
    tags.append(new_tag)
    transaction._save_tags(tags)
    print(f"[Success] Tag '{name}' (ID {new_tagid}) created.")

    return

def delete_tag():

    print("\n---Delete a tag---")
    transaction._list_all_tags()
    tags = transaction._load_tags()

    if not tags:
        return

    tag_id_input = input("Enter TagID to delete (or 'cancel'): ").strip()
    if tag_id_input.lower() == "cancel":
        return
    
    tag = next((t for t in tags if t["TagID"] == tag_id_input), None)
    if not tag:
        print(f"[Error] No tag with ID '{tag_id_input}'.")
        return
    
    #confirm deletion
    confirm = input(f"Delete tag '{tag['Tag Name']}'? This will remove it from all transactions. (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Deletion cancelled.")
        return
    
    #remove tag
    tags = [t for t in tags if t["TagID"] != tag_id_input]
    transaction._save_tags(tags)

    #remove assignments for this tag
    assignments = transaction._load_assignments()
    assignments = [a for a in assignments if a["TagID"] != tag_id_input]
    transaction._save_assignments(assignments)

    print(f"[Success] Tag '{tag['Tag Name']}' (ID {tag_id_input}) deleted.")

    return

def list_tags():
    print("\n---List of Tags---")
    transaction._list_all_tags()
    return

def edit_tags():
    print("\n---Edit a tag---")
    transaction._list_all_tags()
    tags = transaction._load_tags()

    if not tags:
        return

    tag_id_input = input("Enter TagID to edit (or 'cancel'): ").strip()

    if tag_id_input.lower() == "cancel":
        return
    
    tag = next((t for t in tags if t["TagID"] == tag_id_input), None)
    if not tag:
        print(f"[Error] No tag with ID '{tag_id_input}'.")
        return
    
    print(f"\nCurrent name: {tag['Tag Name']}")
    print(f"Current description: {tag['Tag Description']}\n")

    new_name = input(f"New name for '{tag['Tag Name']}' (press Enter to keep current): ").strip()
    new_tag_description = input("New description (press Enter to keep current): ").strip()

    # validate new name 
    if new_name:
        if not _validate_tag_name(new_name, tags, exclude_id=tag["TagID"]):
            print(f"[Error] Tag '{new_name}' already exists.")
            return
        tag["Tag Name"] = new_name

    if new_tag_description:
        tag["Tag Description"] = new_tag_description

    transaction._save_tags(tags)
    print(f"[Success] Tag '{tag['Tag Name']}' (ID {tag_id_input}) updated.")

    return