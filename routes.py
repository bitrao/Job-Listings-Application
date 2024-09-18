from flask import Blueprint, redirect, render_template, request, session, url_for
import json
import pandas as pd
import os
import numpy as np
import pickle
import sklearn
from nltk.tokenize import sent_tokenize, RegexpTokenizer
from itertools import chain
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

# Create a Blueprint for routes
bp = Blueprint("routes", __name__)

category_mapping = {
    0: "accounting-finance",
    1: "engineering",
    2: "healthcare-nursing",
    3: "sales",
}

with open("removed_words.txt", "r") as file:
    removed_words = file.read().splitlines()


def tokenize(text):
    # make the text lowercase
    text_lc = text.lower()

    # segment the string into sentences
    sentences = sent_tokenize(text_lc)

    # tokenize using regex pattern
    pattern = r"[a-zA-Z]+(?:[-'][a-zA-Z]+)?"
    tokenizer = RegexpTokenizer(
        pattern
    )  # create a tokenizer object that uses the pattern.
    tokens = [
        tokenizer.tokenize(sentence) for sentence in sentences
    ]  # tokenize each sentence

    # flatten the list
    tokens_res = list(chain.from_iterable(tokens))

    return tokens_res


def gen_docVecs(wv, tk_txts, tfidf=[]):  # generate vector representation for documents
    docs_vectors = pd.DataFrame()  # creating empty final dataframe
    # stopwords = nltk.corpus.stopwords.words('english') # removing stop words

    for i in range(0, len(tk_txts)):
        tokens = list(set(tk_txts[i]))  # get the list of distinct words of the document

        temp = (
            pd.DataFrame()
        )  # creating a temporary dataframe(store value for 1st doc & for 2nd doc remove the details of 1st & proced through 2nd and so on..)
        for w_ind in range(
            0, len(tokens)
        ):  # looping through each word of a single document and spliting through space
            try:
                word = tokens[w_ind]
                word_vec = wv[
                    word
                ]  # if word is present in embeddings(goole provides weights associate with words(300)) then proceed

                if tfidf:
                    word_weight = float(tfidf[i][word])
                else:
                    word_weight = 1
                temp = pd.concat(
                    [temp, pd.Series(word_vec * word_weight).to_frame().T],
                    ignore_index=True,
                )  # if word is present then append it to temporary dataframe
            except:
                pass
        doc_vector = (
            temp.sum().to_frame().T
        )  # take the sum of each column(w0, w1, w2,........w300)
        docs_vectors = pd.concat(
            [docs_vectors, doc_vector], ignore_index=True
        )  # append each document value to the final dataframe
    return docs_vectors


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

        # Classify the content
        if request.form["button"] == "Classify":

            # Tokenize the content of the .txt file so as to input to the saved model
            # Here, as an example,  we just do a very simple tokenization
            tokenized_data = tokenize(description)
            tokenized_data = [word for word in tokenized_data if len(word) >= 2]
            tokenized_data = [
                word for word in tokenized_data if word not in removed_words
            ]

            with open("tVectorizer.pkl", "rb") as f:
                tVectorizer = pickle.load(f)

            count_features = tVectorizer.transform([" ".join(tokenized_data)])

            # Load the LR model
            models = []
            for i in range(5):
                with open(f"model_{i}.pkl", "rb") as file:
                    models.append(pickle.load(file))

            # Predict the label of tokenized_data
            y_pred = np.apply_along_axis(
                lambda x: np.argmax(np.bincount(x)),
                axis=0,
                arr=[model.predict(count_features).astype(int) for model in models],
            )
            print([model.predict(count_features).astype(int) for model in models])
            print(y_pred)
            y_pred = category_mapping[y_pred[0]]
            print(y_pred)
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

                return render_template(
                    "create_job_listing.html",
                    categories=categories,
                    prediction=category,
                    title=title,
                    description=description,
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
