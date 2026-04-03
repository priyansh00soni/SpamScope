import os
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), "spam_ham_dataset.csv")


def get_training_data():
    """
    Load from the real dataset CSV.
    Returns list of (subject, body, label) tuples — label 1=spam, 0=ham.
    The dataset has a single 'text' column that starts with 'Subject: ...'
    so we split it out. Body becomes everything after the first line.
    """
    df = pd.read_csv(DATA_PATH)
    df = df[["label", "text"]].dropna()

    data = []
    for _, row in df.iterrows():
        label = 1 if row["label"].strip().lower() == "spam" else 0
        text = row["text"].replace("\\r\\n", "\n").replace("\\r", "\n")
        lines = text.strip().split("\n", 1)
        subject = lines[0].replace("Subject:", "").strip() if lines else ""
        body = lines[1].strip() if len(lines) > 1 else ""
        data.append((subject, body, label))

    return data
