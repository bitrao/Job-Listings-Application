from flask import Blueprint, render_template
import json
import os

# Create a Blueprint for routes
bp = Blueprint("routes", __name__)


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
        # For simplicity, this is omitted. You can use pandas or csv module to load data.
        data_file = category["file"]
        return render_template(
            "category.html",
            category=category,
            data_file=data_file,
            categories=categories,
        )
    else:
        return "Category not found", 404


def load_categories():
    with open("categories.json") as f:
        return json.load(f)["categories"]
