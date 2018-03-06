from flask import Flask
import os

from blueprints.login_views import login_views
from blueprints.main_views import main_views

app = Flask(__name__)
app.secret_key = ""

app.register_blueprint(main_views)
app.register_blueprint(login_views)

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port))
