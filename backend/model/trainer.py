import pickle
import os
import numpy as np

# classic ML imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# for combining sparse + dense features
from scipy.sparse import hstack, csr_matrix

# our custom features (like caps %, links, etc.)
from model.features import feature_vector, feature_names

# small dataset (since this is not production-level training)
from data.sample_data import get_training_data


# where trained model will be stored
MODEL_PATH = os.path.join(os.path.dirname(__file__), "spam_model.pkl")


def train(emails=None, save=True):

    # if no external data given → use default dataset
    if emails is None:
        emails = get_training_data()

    print(f"Loaded {len(emails)} emails from dataset...")

    # combine subject + body → one text per email
    texts = [s + " " + b for s, b, _ in emails]

    # handcrafted features (numbers like caps %, links, etc.)
    hand = np.array([feature_vector(s, b) for s, b, _ in emails])

    # labels → 0 = ham, 1 = spam
    labels = np.array([l for _, _, l in emails])


    # ---------------- TRAIN / TEST SPLIT ----------------
    # we split indices instead of data directly (cleaner control)
    idx = list(range(len(texts)))

    # stratify → keeps spam/ham ratio same in both sets
    tr_idx, te_idx = train_test_split(
        idx, test_size=0.2, random_state=42, stratify=labels
    )


    # ---------------- TEXT FEATURES (TF-IDF) ----------------
    # converts words into numbers (importance-based)
    tfidf = TfidfVectorizer(
        ngram_range=(1, 2),      # use single words + pairs ("click here")
        max_features=5000,       # limit size (avoid huge memory)
        sublinear_tf=True,       # smoother scaling
        stop_words="english"     # ignore common words (the, is, etc.)
    )

    # fit only on training data (important to avoid data leakage)
    tfidf.fit([texts[i] for i in tr_idx])

    # convert text → numeric vectors
    tfidf_tr = tfidf.transform([texts[i] for i in tr_idx])
    tfidf_te = tfidf.transform([texts[i] for i in te_idx])


    # ---------------- HANDCRAFTED FEATURES ----------------
    # normalize values between 0–1 (ML models prefer this)
    scaler = MinMaxScaler()

    hand_tr = csr_matrix(scaler.fit_transform(hand[tr_idx]))
    hand_te = csr_matrix(scaler.transform(hand[te_idx]))


    # ---------------- FINAL FEATURE MATRIX ----------------
    # combine text features + handcrafted features
    X_tr = hstack([tfidf_tr, hand_tr])
    X_te = hstack([tfidf_te, hand_te])

    y_tr = labels[tr_idx]
    y_te = labels[te_idx]


    # ---------------- MODEL ----------------
    # simple + reliable classifier
    clf = LogisticRegression(
        C=1.0,           # regularization strength
        max_iter=1000,   # allow more iterations (avoid convergence issues)
        solver="lbfgs"
    )

    clf.fit(X_tr, y_tr)


    # ---------------- EVALUATION ----------------
    train_acc = accuracy_score(y_tr, clf.predict(X_tr))
    test_acc  = accuracy_score(y_te, clf.predict(X_te))

    print(f"Train accuracy : {train_acc*100:.2f}%")
    print(f"Test accuracy  : {test_acc*100:.2f}%")

    # detailed metrics (precision, recall, etc.)
    print(classification_report(y_te, clf.predict(X_te), target_names=["ham", "spam"]))


    # ---------------- SAVE EVERYTHING ----------------
    # we save not just model, but whole pipeline
    bundle = {
        "tfidf": tfidf,
        "scaler": scaler,
        "clf": clf,
        "feature_names": feature_names(),
        "training_size": len(tr_idx),
        "test_size": len(te_idx),
        "train_acc": round(train_acc, 4),
        "test_acc": round(test_acc, 4),
    }

    if save:
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(bundle, f)
        print(f"Model saved → {MODEL_PATH}")

    return bundle


def load_model():

    # if model file not found → train from scratch
    if not os.path.exists(MODEL_PATH):
        print("No saved model found. Training from dataset...")
        return train()

    # otherwise just load it (fast)
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)