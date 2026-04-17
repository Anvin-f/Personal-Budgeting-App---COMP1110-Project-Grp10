import csv
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def link_tags():
    tag_link = {}
    with open('assignments.csv', mode = 'r') as f:
        reader = csv.DictReader(f)
        for line in reader:
            line_split = line.strip().split(',')
            ID = int(line_split[0])
            tag_ID = int(line_split[1])
            tag_link[ID] = tag_ID

    return tag_link

def definetag() :
    tags = set()
    tag_type = {}
    tag_name = {}
    with open('tags.csv', mode = 'r') as f:
        reader = csv.DictReader(f)
        for line in reader:
            line_split = line.strip().split(',')
            tag_ID = int(line_split[0])
            tag_type[tag_ID] = line_split[1]
            tag_name[tag_ID] = line_split[2]
            tags.add(tag_ID)
    
    return tags, tag_type, tag_name

def printspend(tag_name, category, total_spend, id) :
    print(f'{id}BREAKDOWN:\n')
    print(f'{id} total spending: {total_spend}\n')

    print(f'{id} Category Breakdown:')
    for i in category :
        print(f'{tag_name[i]}: {category[i]}')
    
    return

def printtop3(tag_name, category) :
    print("\nTop 3 Categories Spent:")
    fre = 0
    for i in category :
        fre += 1
        print(f'{tag_name[i]}: {category[i]}')

        if(fre == 3) :
            break 

    return

def show_summary(): 
    tag_link = link_tags()
    tags,tag_type, tag_name = definetag()

    total_spend_month = 0
    total_spend_week = 0
    total_spend_today = 0
    
    category_month = {}
    category_week = {}
    category_today = {}

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    week_cutoff = today - timedelta(days=6)
    
    with open('transactions.csv', mode = 'r') as f:
        reader = csv.DictReader(f)
        for line in reader:
            line_split = line.strip().split(',')
            transaction_id = int(line_split[0])
            transaction_date = datetime.strptime(line_split[1], "%Y-%m-%d")
            transaction_name = line_split[2]
            transaction_amount = int(line_split[4])

            # included in month or not
            if(today.month == transaction_date.month and today.year == transaction_date.year) :
                total_spend_month += transaction_amount
                if(tag_link[transaction_id] not in category_month) :
                    category_month[tag_link[transaction_id]] = transaction_amount
                else :
                    category_month[tag_link[transaction_id]] += transaction_amount

            # included in week or not
            if(transaction_date >= week_cutoff) :
                total_spend_week += transaction_amount
                if(tag_link[transaction_id] not in category_week) :
                    category_week[tag_link[transaction_id]] = transaction_amount
                else :
                    category_week[tag_link[transaction_id]] += transaction_amount

            # included in daily or not
            if(transaction_date >= today) :
                total_spend_today += transaction_amount
                if(tag_link[transaction_id] not in category_today) :
                    category_today[tag_link[transaction_id]] = transaction_amount
                else :
                    category_today[tag_link[transaction_id]] += transaction_amount
    
    printspend(tag_name, category_today, total_spend_today, "Daily")
    printspend(tag_name, category_week, total_spend_week, "Weekly")
    printspend(tag_name, category_month, total_spend_month, "Monthly")

    sorted_category = sorted(category_month.items(), key=lambda item: item[1], reverse=True)
    printtop3(tag_name, sorted_category)

    return

def line_graph(category_month) :
    category_month = dict(sorted(category_month.items(), key=lambda item: item[1], reverse=True))

    categories = list(category_month.keys())
    amounts = list(category_month.values())

    plt.clf() 
    plt.bar(categories, amounts, color='skyblue', edgecolor='navy')

    plt.xlabel('Category', fontsize=12)
    plt.ylabel('Amount Spent ($)', fontsize=12)
    plt.title('Monthly Spending Summary', fontsize=14)

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout() 
    plt.show()
    
    return

def bar_graph(spending_per_day) : 
    spending_per_day = sorted(spending_per_day.items())
    dates = [item[0] for item in spending_per_day]
    amounts = [item[1] for item in spending_per_day]

    plt.clf() 
    plt.bar(dates, amounts, color='teal')

    plt.xlabel('Date')
    plt.ylabel('Amount Spent ($)')
    plt.title('Daily Spending Summary')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    return

    
def show_graph():
    tag_link = link_tags()
    tags,tag_type, tag_name = definetag()
    
    category_month = {}
    spending_per_day = {}

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    thirtyday_cutoff = today - timedelta(days=29)
    
    with open('transactions.csv', mode = 'r') as f:
        reader = csv.DictReader(f)
        for line in reader:
            line_split = line.strip().split(',')
            transaction_id = int(line_split[0])
            transaction_date = datetime.strptime(line_split[1], "%Y-%m-%d")
            transaction_name = line_split[2]
            transaction_amount = int(line_split[4])

            # included in month or not
            if(today.month == transaction_date.month and today.year == transaction_date.year) :
                total_spend_month += transaction_amount
                if(tag_name[tag_link[transaction_id]] not in category_month) :
                    category_month[tag_name[tag_link[transaction_id]]] = transaction_amount
                else :
                    category_month[tag_name[tag_link[transaction_id]]] += transaction_amount
            
            if(transaction_date > thirtyday_cutoff):
                if(transaction_date not in spending_per_day) :
                    spending_per_day[transaction_date] = transaction_amount
                else :
                    spending_per_day[transaction_date] += transaction_amount
    
    line_graph(category_month)
    bar_graph(spending_per_day)
    
    return