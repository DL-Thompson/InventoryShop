from flask import Blueprint, render_template, request, session
from flask.ext.login import login_required, current_user
import database.database_functions as db
from datetime import datetime
from database.models import PurchasedItem

main_views = Blueprint('main_views', __name__, template_folder='templates')

@main_views.route('/')
def show():
    return render_template('index.html')

@main_views.route('/shop', methods=['GET', 'POST'])
@login_required
def shop():
    inventory_list = db.get_total_inventory_list()
    return render_template("shop.html", inventory_list=inventory_list)


@main_views.route('/order_confirm', methods=['GET', 'POST'])
@login_required
def order_confirm():
    if request.method == 'POST':
        order_list = {}
        for item in request.form:
            if request.form[item] and int(request.form[item]) > 0:
                order_list[item] = request.form[item]
        order_items_list = db.get_inventory_from_quantity_named_list(order_list)
    total = 0
    for item in order_items_list:
        total = total + (item.price * int(order_list[item.name]))
    return render_template("order.html", order_items_list=order_items_list, item_quantity_list=order_list, total=total)

@main_views.route('/order_submit', methods=['GET', 'POST'])
@login_required
def order_submit():
    if request.method == 'POST':
        user_district = current_user.district
        order_list = {}
        for item in request.form:
            if request.form[item] and int(request.form[item]) > 0:
                order_list[item] = request.form[item]
        order_items_list = db.get_purchase_list(order_list)
        success = db.place_order(user_district, order_list)
        total = 0
        for item in order_items_list:
            total = total + (order_items_list[item].price * int(order_list[item]))
        if success:
            db.save_order_to_history(current_user, order_list, total)
            return render_template("order_complete.html", order_items_list=order_items_list, order_list=order_list, total=total, error=None)
        else:
            error = "Sorry! There was an issue placing your order. Please try again."
            return render_template("order_complete.html", order_items_list=None, order_list=None, total=0, error=error)

@main_views.route('/user_info')
@login_required
def user_info():
    user = db.get_user(current_user.id)
    order_history = db.get_user_order_history(user)
    order_id_name_lists = {}
    order_totals = {}
    for order in order_history:
        order_id_name_lists[order] = order_history[order]['order']['order_list']
        order_totals[order] = order_history[order]['order']['total']
    all_order_name_quantity_lists = {}
    for order_date in order_id_name_lists:
        all_order_name_quantity_lists[order_date] = db.get_inventory_from_quantity_named_list(order_id_name_lists[order_date])
    order_list = {}
    for order in all_order_name_quantity_lists:
        order_list[order] = {}
        for item in all_order_name_quantity_lists[order]:
            quantity_ordered = int(all_order_name_quantity_lists[order][item])
            order_list[order][item.name] = PurchasedItem(item.name, quantity_ordered, item.description, item.price, item.type)
    return render_template("user_info.html", user=user, order_list=order_list, order_totals=order_totals)
