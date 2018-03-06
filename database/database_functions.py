import json
from collections import OrderedDict

import couchdb
import requests

from datetime import datetime

from models import User, InventoryItem
from models import InventoryListItem
from models import OrderHistoryEntry
from models import PurchasedItem

CLOUDANT_DB = {
    "cloudant" : {
        "host" : "https://lucast.cloudant.com",
        "username" : {
            "warehouse1" : "whowsetraptedifiduchirch",
            "warehouse2" : "rgenclogenteredgerderint"
        },
        "password" : {
            "warehouse1" : "d52f2cff43ea9491b8656a71140754eba9293cc6",
            "warehouse2" : "bba4a7100d41515183736c799c26dd87451b3e07"
                      },
        "url" : {
            "warehouse1" : "https://whowsetraptedifiduchirch:d52f2cff43ea9491b8656a71140754eba9293cc6@lucast.cloudant.com",
            "warehouse2" : "https://rgenclogenteredgerderint:bba4a7100d41515183736c799c26dd87451b3e07@lucast.cloudant.com"
        }
    },
    "bluemix" : {
        "host": "9141363c-640f-4bd2-8e0c-76130902481d-bluemix.cloudant.com",
        "username": "9141363c-640f-4bd2-8e0c-76130902481d-bluemix",
        "password": "d31ef436e7f64d02469512b42c85c85408cdd0ebca2ba1111a8afc68b05f5b35",
        "url": "https://9141363c-640f-4bd2-8e0c-76130902481d-bluemix:d31ef436e7f64d02469512b42c85c85408cdd0ebca2ba1111a8afc68b05f5b35@9141363c-640f-4bd2-8e0c-76130902481d-bluemix.cloudant.com",
        "url_find" : "https://9141363c-640f-4bd2-8e0c-76130902481d-bluemix:d31ef436e7f64d02469512b42c85c85408cdd0ebca2ba1111a8afc68b05f5b35@9141363c-640f-4bd2-8e0c-76130902481d-bluemix.cloudant.com/company/_find"
    }
}

database_list = ["company", "warehouse1", "warehouse2"]
warehouse_list = ["warehouse1", "warehouse2"]

json_total_inventory = OrderedDict([("selector", {"class":"inventory"}), ("fields", ["_id", "quantity", "warehouse", "description", "warehouse", "price", "type", "name"])])


def get_user(userid):
    db = get_cloudant_db("company")
    if userid in db:
        doc = db[userid]
        return User(doc)
    return None

def insert_user(username, password, district):
    db = get_cloudant_db("company")
    db.save({"_id": username, "password": password, "district": district, "orders": {}})
    if username in db:
        return True
    return False

def get_total_inventory_list():
    response = requests.post(CLOUDANT_DB['bluemix']['url_find'], json=json_total_inventory)
    response_dict = json.loads(response.text)
    inventory_dict = {}
    for row in response_dict['docs']:
        if row['type'] not in inventory_dict:
            inventory_dict[row['type']] = [InventoryListItem(row['name'], row['quantity'], row['description'], row['price'], row['type'])]
        else:
            matched_item = False
            for item in inventory_dict[row['type']]:
                if item.name == row['name']:
                    item.add_quantity(row['quantity'])
                    matched_item = True
            if matched_item == False:
                inventory_dict[row['type']].append(InventoryListItem(row['name'], row['quantity'], row['description'], row['price'], row['type']))
    for type in inventory_dict:
        inventory_dict[type].sort(key=lambda item: item.name)
    return inventory_dict

def get_inventory_from_quantity_named_list(order_list):
    inventory_list = get_total_inventory_list()
    full_order_list = {}
    for type in inventory_list:
        for item in inventory_list[type]:
            if item.name in order_list.keys():
                full_order_list[item] = order_list[item.name]
    return full_order_list

def get_purchase_list(order_list):
    inventory_list = get_total_inventory_list()
    full_order_list = {}
    for type in inventory_list:
        for item in inventory_list[type]:
            if item.name in order_list.keys():
                full_order_list[item.name] = PurchasedItem(item.name, order_list[item.name], item.description, item.price, item.type)
    return full_order_list

def place_order(district, order_list):
    warehouse = find_customer_warehouse(district)
    db = get_cloudant_db(warehouse)
    order_successes = {}
    success = False
    for item, quantity in order_list.iteritems():
        item_id = convert_item_id(warehouse, item)
        if quantity > db[item_id]['quantity']:
            #check to see if other db can supply some quantity
            total_quantity = db[item_id]['quantity']
            for db_name in warehouse_list:
                if db_name == warehouse:
                    continue
                other_db = get_cloudant_db(db_name)
                other_item_id = convert_item_id(db_name, item)
                total_quantity +=  other_db[other_item_id]['quantity']
            if int(quantity) > int(total_quantity):
                success = False
                break
            else:
                #there is enough quantity in all warehouses to supply the order
                success = place_order_multiple(db, warehouse, item, quantity)
        else:
            success = update_item_quantity(db, item_id, -int(quantity))
        if success == False:
            break
        order_successes[item] = success
    if success == False:
        for item in order_successes:
            item_id = convert_item_id(warehouse, item)
            quantity = order_list[item]
            success = update_item_quantity(db, item, quantity)
        return False
    else:
        return True

def place_order_multiple(current_warehouse_db, current_warehouse, item_name, quantity):
    total_ordered = 0
    warehouse_ordered_list = {}
    #deduct quantity from the customers primary warehouse
    quantity_left = int(quantity)
    db_first_quantity = current_warehouse_db[convert_item_id(current_warehouse, item_name)]['quantity']
    success = False
    if db_first_quantity != 0:
        success = update_item_quantity(current_warehouse_db, convert_item_id(current_warehouse, item_name), -int(db_first_quantity))
    if success == False and db_first_quantity != 0:
        return False
    elif success == True and db_first_quantity > 0:
        total_ordered += db_first_quantity
        warehouse_ordered_list[current_warehouse] = db_first_quantity
        quantity_left = quantity_left - db_first_quantity
    #quantity has been deducted from the customers original warehouse, now deduct from other warehouses
    for warehouse in warehouse_list:
        if warehouse == current_warehouse:
            continue
        other_warehouse_db = get_cloudant_db(warehouse)
        other_warehouse_quantity =  other_warehouse_db[convert_item_id(warehouse, item_name)]['quantity']
        quantity_to_order = 0
        if quantity_left > other_warehouse_quantity:
            quantity_to_order = other_warehouse_quantity
        else:
            quantity_to_order = quantity_left
        success = update_item_quantity(other_warehouse_db, convert_item_id(warehouse, item_name), -int(quantity_to_order))
        if success:
            quantity_left = quantity_left - quantity_to_order
            total_ordered += quantity_to_order
            warehouse_ordered_list[warehouse] = quantity_to_order
    #some order failed, reverse all orders
    if int(total_ordered) != int(quantity):
        for wh in warehouse_ordered_list:
            revert_db = get_cloudant_db(wh)
            update_item_quantity(revert_db, convert_item_id(wh, item_name), warehouse_ordered_list[wh])
        return False
    else:
        #order succeeded
        return True
    return True

def save_order_to_history(current_user, order_list, total):
    db = get_cloudant_db("company")
    if current_user.id in db:
        doc = db[current_user.id]
        user_order_list = doc['orders']
        new_order_id = len(user_order_list) + 1
        order_time = str(datetime.now().strftime('%m-%d-%Y %I:%M:%S'))
        order = OrderHistoryEntry(current_user.id, new_order_id, order_list, order_time, total)
        doc['orders'][new_order_id] = order_time
        db.save(doc)
        save_success = save_order_entry(db, order)
        if save_success == False:
            doc['orders'].pop(new_order_id, None)
            db.save(doc)
            return False
        return True
    else:
        return False

def save_order_entry(db, order_entry):
    order_id = order_entry.date
    db.save({"_id" : order_id, "order" : order_entry.return_json_dict(), "ordered_by" : order_entry.user_id})
    if order_id in db:
        return True
    return False

def get_user_order_history(user):
    user_id = user.id
    db = get_cloudant_db("company")
    order_history = {}
    for order_count, order_id in user.orders.iteritems():
        if order_id in db:
            order_history[order_id] = db[order_id]
    return order_history

def get_warehouse_inventory_list(warehouse):
    db = get_cloudant_db(warehouse)
    inventory_list = {}
    for doc_id in db:
        doc = db[doc_id]
        if doc['type'] not in inventory_list:
            inventory_list[doc['type']] = [InventoryItem(doc['_id'], doc['quantity'], doc['description'], doc['warehouse'], doc['price'], doc['type'], doc['name'])]
        else:
            inventory_list[doc['type']].append(InventoryItem(doc['_id'], doc['quantity'], doc['description'], doc['warehouse'], doc['price'], doc['type'], doc['name']))
    return inventory_list


def update_item_quantity(db, doc_id, quantity):
    try:
        doc = None
        if doc_id in db:
            doc = db[doc_id]
            if (doc['quantity'] + quantity) < 0:
                #print 'quantity < 0 error'
                return False
            else:
                doc['quantity'] = doc['quantity'] + quantity
                db.save(doc)
                return True
        else:
            return False
        pass
    except couchdb.http.ResourceConflict:
        print 'Error: Document conflict error for document id: ', doc_id
        return False

def find_customer_warehouse(district):
    district = int(district)
    if district == 1:
        return 'warehouse1'
    elif district == 2:
        return 'warehouse2'
    return None

def convert_item_id(warehouse, name):
    if warehouse == "warehouse1":
        return "wh1-" + name
    elif warehouse == "warehouse2":
        return "wh2-" + name

def get_cloudant_db(database_name):
    db = None
    if database_name == "company":
        try:
            db_connect = couchdb.Server(CLOUDANT_DB['bluemix']['url'])
            db_connect.resource.credentials = (CLOUDANT_DB['bluemix']['username'], CLOUDANT_DB['bluemix']['password'])
            db = db_connect['company']
        except:
            print "Error: Failed to load company database."
            return None
        return db
    try:
        if database_name == "warehouse1":
            db_connect = couchdb.Server(CLOUDANT_DB['cloudant']['url']['warehouse1'])
            db_connect.resource.credentials = (CLOUDANT_DB['cloudant']['username']['warehouse1'], CLOUDANT_DB['cloudant']['password']['warehouse1'])
            db = db_connect['warehouse1']
        elif database_name == "warehouse2":
            db_connect = couchdb.Server(CLOUDANT_DB['cloudant']['url']['warehouse2'])
            db_connect.resource.credentials = (CLOUDANT_DB['cloudant']['username']['warehouse2'], CLOUDANT_DB['cloudant']['password']['warehouse2'])
            db = db_connect['warehouse2']
    except:
        print "Error: Failed to load warehouse database: ", database_name
        return None
    if database_name not in database_list:
        print "Error: Attempted to load incorrect database name."
    return db
