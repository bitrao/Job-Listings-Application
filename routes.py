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


@bp.route("/<category_url>/<int:entry_id>")
def job_page(category_url, entry_id):
    categories = load_categories()
    category = next((cat for cat in categories if cat["url"] == category_url), None)
    if category:
        csv_file_path = os.path.join("data", category["file"])
        try:
            data = pd.read_csv(csv_file_path)
            # Find the specific entry by its title
            entry = data.loc[data["id"] == entry_id].to_dict("records")[0]
        except (FileNotFoundError, IndexError):
            entry = None  # Handle missing entry case
        return render_template(
            "job.html", categories=categories, category=category, entry=entry
        )
    else:
        return "Category not found", 404
