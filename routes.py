from flask import Blueprint

# Create a Blueprint for routes
bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    return "Hello, Flask from routes.py!"
