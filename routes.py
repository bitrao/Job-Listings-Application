from flask import Blueprint, render_template
import json
import pandas as pd
import os

# Create a Blueprint for routes
bp = Blueprint("routes", __name__)


def load_categories():
    with open("categories.json") as f:
        return json.load(f)["categories"]


@bp.route("/")
def index():
    categories = load_categories()
    return render_template("base.html", categories=categories)


@bp.route("/<category_url>")
def category_page(category_url):
    categories = load_categories()
    category = next((cat for cat in categories if cat["url"] == category_url), None)
    if category:
        # Load data from the corresponding CSV file
        csv_file_path = os.path.join("data", category["file"])
        try:
            data = pd.read_csv(csv_file_path)
        except FileNotFoundError:
            data = None  # Handle missing file case
        return render_template(
            "category.html",
            category=category,
            data=data,
            categories=categories,
        )
    else:
        return "Category not found", 404
