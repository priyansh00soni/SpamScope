import numpy as np
from scipy.sparse import hstack, csr_matrix

# loads trained model (tfidf + scaler + classifier)
from model.trainer import load_model

# handcrafted features (caps %, links, etc.)
from model.features import feature_vector, get_triggered_features


# we keep model in memory so we don’t reload it every time
_model = None


def get_model():
    global _model

    # lazy loading → load only once when needed
    if _model is None:
        _model = load_model()

    return _model


# ---------------- MAIN PREDICTION ----------------
def predict(subject: str, body: str) -> dict:

    # get trained model bundle
    bundle = get_model()

    # combine subject + body (same way as training)
    text = subject + " " + body


    # ---------------- TEXT FEATURES ----------------
    # convert text → tfidf vector (same transformation as training)
    tfidf_vec = bundle["tfidf"].transform([text])


    # ---------------- HANDCRAFTED FEATURES ----------------
    # manually computed features (numbers like caps %, links, etc.)
    hand_vec = np.array([feature_vector(subject, body)])

    # scale them using same scaler used in training
    hand_scaled = csr_matrix(bundle["scaler"].transform(hand_vec))


    # ---------------- FINAL INPUT ----------------
    # combine both feature types into one input
    X = hstack([tfidf_vec, hand_scaled])


    # ---------------- MODEL PREDICTION ----------------
    # predicted label → 0 (ham) or 1 (spam)
    label = bundle["clf"].predict(X)[0]

    # probability for both classes [ham_prob, spam_prob]
    proba = bundle["clf"].predict_proba(X)[0]


    # find index of spam class (usually 1, but safer this way)
    spam_idx = list(bundle["clf"].classes_).index(1)

    # probability that email is spam
    spam_prob = float(proba[spam_idx])

    # final decision
    is_spam = label == 1


    # ---------------- RESPONSE ----------------
    return {
        "verdict": "spam" if is_spam else "ham",

        # confidence = how sure we are about final decision
        # (if spam → use spam_prob, else → 1 - spam_prob)
        "confidence": round(spam_prob if is_spam else 1 - spam_prob, 4),

        # raw spam probability (useful for debugging / UI)
        "spam_probability": round(spam_prob, 4),

        # reasons shown to user (like caps, links, etc.)
        "triggered_features": get_triggered_features(subject, body),
    }


# ---------------- MODEL INFO ----------------
def model_stats() -> dict:
    bundle = get_model()

    return {
        # how much data was used
        "training_size": bundle.get("training_size"),
        "test_size": bundle.get("test_size"),

        # performance
        "train_accuracy": bundle.get("train_acc"),
        "test_accuracy": bundle.get("test_acc"),

        # size of vocabulary (how many words model knows)
        "tfidf_vocab_size": len(bundle["tfidf"].vocabulary_),
    }