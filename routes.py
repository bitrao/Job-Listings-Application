from flask import Blueprint, render_template, request
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
    return render_template("home.html", categories=categories)


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
    

@bp.route("/create", methods=["GET", "POST"])
def create():
    categories = load_categories()
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        
        job_listing = {
            "title": title,
            "description": description,
        }

        category = category.replace("-", "_")
        
        csv_file_path = os.path.join("data", f"{category}.csv")
        df = pd.DataFrame([job_listing])
        if os.path.exists(csv_file_path):
            df.to_csv(csv_file_path, mode="a", header=False, index=False) 
        else:
            df.to_csv(csv_file_path, index=False)

        return render_template("create_job_listing.html", categories=categories, success=True)

    return render_template("create_job_listing.html", categories=categories)