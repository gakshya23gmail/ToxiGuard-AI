import os
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple
import joblib
from scipy.sparse import hstack

CATEGORIES = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

THRESHOLDS = {
    "toxic": 0.75,
    "severe_toxic": 0.75,
    "obscene": 0.70,
    "threat": 0.65,
    "insult": 0.75,
    "identity_hate": 0.80,
}

LOG_FILE = "moderation_log.json"

# Load trained TF-IDF vectorizers and 6 Logistic Regression classifiers
word_vec = joblib.load("models/word_vectorizer.joblib")
char_vec = joblib.load("models/char_vectorizer.joblib")
classifiers = {cat: joblib.load(f"models/{cat}_model.joblib") for cat in CATEGORIES}


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s!?*]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def analyze_and_log(
    text: str,
    platform: str = "Manual Test",
    author: str = "User",
    action_taken: str = "Evaluated",
) -> Dict:
    """
    Runs ToxiGuard 6-category inference, applies tuned thresholds,
    and saves the event to moderation_log.json for the live dashboard.
    """
    cleaned = clean_text(text)
    features = hstack([word_vec.transform([cleaned]), char_vec.transform([cleaned])])

    scores: Dict[str, float] = {}
    for cat in CATEGORIES:
        prob = float(classifiers[cat].predict_proba(features)[0][1])
        scores[cat] = round(prob, 4)

    flagged: List[str] = [cat for cat in CATEGORIES if scores[cat] >= THRESHOLDS[cat]]
    is_toxic = len(flagged) > 0

    if is_toxic and action_taken == "Evaluated":
        action_taken = "Hidden from Users"
    elif not is_toxic and action_taken == "Evaluated":
        action_taken = "Published"

    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform,
        "author": author,
        "comment": text,
        "is_toxic": is_toxic,
        "flagged_categories": flagged,
        "scores": scores,
        "action": action_taken,
    }

    append_log(record)
    return record


def append_log(record: Dict):
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.insert(0, record)  # newest first
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs[:200], f, indent=2)