import os
import re
import joblib
import pandas as pd
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

CATEGORIES = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s!?*]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    data_path = os.path.join("data", "train.csv")
    if not os.path.exists(data_path):
        print("❌ Put 'train.csv' inside the 'data/' folder first!")
        return

    print("1/4 Loading Jigsaw dataset (159,571 comments)...")
    df = pd.read_csv(data_path)
    df["clean_comment"] = df["comment_text"].fillna("").apply(clean_text)

    X_train_text, X_val_text, y_train, y_val = train_test_split(
        df["clean_comment"], df[CATEGORIES], test_size=0.15, random_state=42
    )

    print("2/4 Extracting Word-level & Character-level TF-IDF features...")
    word_vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), max_features=50000, sublinear_tf=True
    )
    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 5), max_features=50000, sublinear_tf=True
    )

    X_train_word = word_vectorizer.fit_transform(X_train_text)
    X_train_char = char_vectorizer.fit_transform(X_train_text)
    X_train_features = hstack([X_train_word, X_train_char])

    X_val_word = word_vectorizer.transform(X_val_text)
    X_val_char = char_vectorizer.transform(X_val_text)
    X_val_features = hstack([X_val_word, X_val_char])

    os.makedirs("models", exist_ok=True)
    joblib.dump(word_vectorizer, "models/word_vectorizer.joblib")
    joblib.dump(char_vectorizer, "models/char_vectorizer.joblib")

    print("3/4 Training 6 independent Logistic Regression classifiers...")
    auc_scores = []
    for cat in CATEGORIES:
        clf = LogisticRegression(C=2.0, max_iter=1000, solver="lbfgs")
        clf.fit(X_train_features, y_train[cat])

        val_preds = clf.predict_proba(X_val_features)[:, 1]
        auc = roc_auc_score(y_val[cat], val_preds)
        auc_scores.append(auc)
        print(f"   ✅ {cat:15s} -> ROC-AUC: {auc:.4f}")

        joblib.dump(clf, f"models/{cat}_model.joblib")

    print(f"\n4/4 Done! Mean ROC-AUC: {np.mean(auc_scores):.4f}")
    print("All vectorizers and 6 models are saved in 'models/'.")


if __name__ == "__main__":
    main()