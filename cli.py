import core.transaction as transaction
import core.analysis as analysis
import core.utils as utils
import core.tags as tags

#have to support csv and manual input
def add_transaction():
    transaction.add_transaction()
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

def add_tag():
    tags.add_tag()
    return

def delete_tag():
    tags.delete_tag()
    return

def list_tags():
    tags.list_tags()
    return