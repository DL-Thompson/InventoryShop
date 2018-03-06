from flask.ext.login import UserMixin
from datetime import datetime

class User(UserMixin):
    def __init__(self, doc):
        self.id = doc['_id']
        self.password = doc['password']
        self.district = doc['district']
        order_history = doc['orders']
        new_history = {}
        for order_id in order_history:
           new_history[int(order_id)] = order_history[order_id]
        self.orders = new_history
    def __repr__(self):
        return "(User id: " + str(self.id) + " Password: " + str(self.password) + " District: " + str(self.district) + ")" + "Orders: " + str(self.orders)
    def __str__(self):
        return "(User id: " + str(self.id) + " Password: " + str(self.password) + " District: " + str(self.district) + ")" + "Orders: " + str(self.orders)

class OrderHistoryEntry():
    def __init__(self, user_id, order_id, order_list, timestamp, total):
        self.user_id = user_id
        self.order_id = order_id
        self.order_list = order_list
        self.date = str(timestamp)
        self.total = total
    def return_json_dict(self):
        json_dict = {}
        json_dict['user_id'] = self.user_id
        json_dict['order_id'] = self.order_id
        json_dict['order_list'] = self.order_list
        json_dict['date'] = self.date
        json_dict['total'] = self.total
        return json_dict
    def __repr(self):
        return "Order - User: " + str(self.user_id) + " Time: " + str(self.date) + " OrderNum: " + str(self.order_id) + " Items: " + str(self.order_list)
    def __str__(self):
        return "Order - User: " + str(self.user_id) + " Time: " + str(self.date) + " OrderNum: " + str(self.order_id) + " Items: " + str(self.order_list)

class InventoryItem():
    def __init__(self, id, quantity, description, warehouse, price, type, name):
        self.id = id
        self.quantity = quantity
        self.description = description
        self.warehouse = warehouse
        self.price = price
        self.type = type
        self.name = name
    def add_quantity(self, amount):
        self.quantity += amount
    def remove_quantity(self, amount):
        if (self.quantity - amount) > 0:
            self.quantity -= amount
        else:
            print "Error: Item " + str(self.id) + " would have negative quantity if reduced."
    def __repr__(self):
        return "(Id: " + str(self.id) + " Name: " + str(self.name) + " Quantity: " + str(self.quantity) + " Warehouse: " + str(self.warehouse) + " Price: " + str(self.price) + " Type: " + str(self.type) + ")"
    def __str__(self):
        return "(Id: " + str(self.id) + " Name: " + str(self.name) + " Quantity: " + str(self.quantity) + " Warehouse: " + str(self.warehouse) + " Price: " + str(self.price) + " Type: " + str(self.type) + ")"

class InventoryListItem():
    def __init__(self, name, quantity, description, price, type):
        self.quantity = quantity
        self.description = description
        self.price = price
        self.type = type
        self.name = name
    def add_quantity(self, amount):
        self.quantity += amount
    def remove_quantity(self, amount):
        if (self.quantity - amount) > 0:
            self.quantity -= amount
        else:
            print "Error: Item " + str(self.id) + " would have negative quantity if reduced."
    def __repr__(self):
        return "(Name: " + str(self.name) + " Quantity: " + str(self.quantity) + " Price: " + str(self.price) + " Type: " + str(self.type) + ")"
    def __str__(self):
        return "(Name: " + str(self.name) + " Quantity: " + str(self.quantity) + " Price: " + str(self.price) + " Type: " + str(self.type) + ")"

class PurchasedItem(InventoryListItem):
    def __init__(self, id, quantity, description, price, type):
        self.total = float(price) * float(quantity)
        InventoryListItem.__init__(self, id, quantity, description, price, type)


