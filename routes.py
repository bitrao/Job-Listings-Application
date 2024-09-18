from flask import Blueprint, redirect, render_template, request, session, url_for
import json
import pandas as pd
import os

# Create a Blueprint for routes
bp = Blueprint("routes", __name__)

def load_categories():
    with open("categories.json") as f:
        return json.load(f)["categories"]


# Load data from all CSV files
def load_all_data():
    categories = load_categories()
    all_data = []
    for category in categories:
        csv_file_path = os.path.join("data", category["file"])
        try:
            data = pd.read_csv(csv_file_path)[0:2]
            all_data.append(
                {
                    "display_name": category["display_name"],
                    "url": category["url"],
                    "data": data,
                }
            )
        except FileNotFoundError:
            all_data[category["display_name"]] = None
    return all_data



@bp.route("/")
def index():
    categories = load_categories()
    all_data = load_all_data()
    return render_template("home.html", categories=categories, all_data=all_data)


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


@bp.route("/create", methods=["GET", "POST"])
def create():
    categories = load_categories()
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]

        category = category.replace("-", "_")

        csv_file_path = os.path.join("data", f"{category}.csv")
        # get the last id
        try:
            data = pd.read_csv(csv_file_path)
            last_id = data["id"].max() + 1
        except FileNotFoundError:
            last_id = 1

        job_listing = {
            "id": last_id,
            "title": title,
            "description": description,
        }

        df = pd.DataFrame([job_listing])
        if os.path.exists(csv_file_path):
            df.to_csv(csv_file_path, mode="a", header=False, index=False)
        else:
            df.to_csv(csv_file_path, index=False)

        return render_template(
            "create_job_listing.html", categories=categories, success=True
        )

    return render_template("create_job_listing.html", categories=categories)


@bp.route("/login")
def login():
    session["is_logged_in"] = True
    
    return redirect(url_for("routes.index"))


@bp.route("/logout")
def logout():
    session.pop("is_logged_in", None)
    return redirect(url_for("routes.index"))