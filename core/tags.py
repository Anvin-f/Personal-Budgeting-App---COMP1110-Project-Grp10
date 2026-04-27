import core.transaction as transaction
import csv

def _validate_tag_name(name, tags, exclude_id=None):
   
    name_lower = name.lower()
    for t in tags:
        if t["TagID"] == exclude_id:
            continue
        if t["Tag Name"].lower() == name_lower:
            return False
    return True

csvpath = 'data/tags.csv'

def get_next_tag_id(tags_dict):
    max_id = max(int(tag['Tag_id']) for tag in tags_dict.values())
    return str(max_id + 1)


def read_tag_csv():
     tagDic = {}
     with open(csvpath, mode ='r')as file:
        csvFile = csv.DictReader(file)
        for i in csvFile:
            tagDic[i["Tag_id"]] = i
     return tagDic

def write_tag_csv(tagDic):
    sorted_tags = sorted(tagDic.values(), key=lambda x: int(x['Tag_id']))
    with open(csvpath, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Tag_id", "Tag_type", "Tag_name"])
        writer.writeheader()
        writer.writerows(sorted_tags)

def add_tag():
    tagDic = read_tag_csv()
    id = get_next_tag_id(tagDic)
    tagDic[id] = {"Tag_id": id, "Tag_type":input("Tag_type:"), "Tag_name":input("Tag_name:")}
    write_tag_csv(tagDic)

def delete_tag():
    list_tags()
    id_delete_tag(input("Enter tag ID to delete: "))

def id_delete_tag(tag_id):
    d= read_tag_csv()
    del d[tag_id]
    write_tag_csv(d)

def list_tags():
    with open(csvpath, mode ='r')as file:
        for i in csv.reader(file):
            print(i)

def get_tags(tag_id):
    return read_tag_csv()[tag_id]
