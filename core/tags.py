import csv

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

def id_delete_tag(tag_id):
    d= read_tag_csv()
    del d[tag_id]
    write_tag_csv(d)
