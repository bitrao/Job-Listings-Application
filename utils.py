import json
import pandas as pd
import sklearn
from nltk.tokenize import sent_tokenize, RegexpTokenizer
from itertools import chain
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import os


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
            data = pd.read_csv(csv_file_path)
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
