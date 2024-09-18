from flask import Blueprint, redirect, render_template, request, session, url_for
import pandas as pd
import os
import numpy as np
import pickle
from utils import *

# Create a Blueprint for routes
bp = Blueprint("routes", __name__)

category_mapping = {
    0: "accounting-finance",
    1: "engineering",
    2: "healthcare-nursing",
    3: "sales",
}

with open("classifiers/removed_words.txt", "r") as file:
    removed_words = file.read().splitlines()


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

        # Classify the content
        if request.form["button"] == "Classify":

            # Tokenize the content of the .txt file so as to input to the saved model
            # Here, as an example,  we just do a very simple tokenization
            tokenized_data = tokenize(description)
            tokenized_data = [word for word in tokenized_data if len(word) >= 2]
            tokenized_data = [
                word for word in tokenized_data if word not in removed_words
            ]

            with open("classifiers/tVectorizer.pkl", "rb") as f:
                tVectorizer = pickle.load(f)

            count_features = tVectorizer.transform([" ".join(tokenized_data)])

            # Load the LR model
            models = []
            for i in range(5):
                with open(f"classifiers/model_{i}.pkl", "rb") as file:
                    models.append(pickle.load(file))

            # Predict the label of tokenized_data
            y_pred = np.apply_along_axis(
                lambda x: np.argmax(np.bincount(x)),
                axis=0,
                arr=[model.predict(count_features).astype(int) for model in models],
            )
            y_pred = category_mapping[y_pred[0]]
            return render_template(
                "create_job_listing.html",
                categories=categories,
                prediction=y_pred,
                title=title,
                description=description,
            )
        elif request.form["button"] == "Save":
            category = request.form.get("category")

            if not category:
                return render_template(
                    "create_job_listing.html",
                    categories=categories,
                    prediction=category,
                    title=title,
                    description=description,
                    category_flag="Category must be selected.",
                )
            else:
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
                    "create_job_listing.html",
                    categories=categories,
                    success=True,
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
