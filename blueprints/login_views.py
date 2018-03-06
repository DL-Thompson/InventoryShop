import md5

from flask import Blueprint, render_template, request, session, redirect, current_app, url_for
from flask.ext.login import LoginManager, login_user, logout_user

from database import database_functions as db

login_views = Blueprint('login_views', __name__, template_folder='templates')

login_manager = LoginManager()
login_manager.login_view = "/login"

@login_views.record_once
def on_load(state):
    login_manager.init_app(state.app)

@login_views.route('/login', methods =["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error="You must login first.")
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        print "Login - User: ", username, " Pass: ", password
        if username and password:
            user = db.get_user(username)
            if user and hash_password(password, current_app.secret_key) == user.password:
                login_user(user, remember=True)
        return render_template("index.html")

@login_views.route('/register', methods=['GET', 'POST'])
def register():
    db.get_total_inventory_list()
    error = None
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password = hash_password(password, current_app.secret_key)
        district = request.form['district']
        if username and password and district:
            user = db.get_user(username)
            if user:
                error = "Username already exists!"
                return render_template("register.html", error=error)
            else:
                success = db.insert_user(username, password, district)
                user = db.get_user(username)
                if success:
                    login_user(user, remember=True)
                return render_template("index.html")
        else:
            error = "Registration Error: Field missing!"
    return render_template("register.html", error=error)

@login_views.route("/logout")
def logout():
    logout_user()
    return redirect("/")

@login_manager.user_loader
def load_user(userid):
    return db.get_user(userid)

def hash_password(password, secret_key):
    salted_password = password + secret_key
    return md5.new(salted_password).hexdigest()

