import re
import math
from collections import Counter

# different categories of spam words
# grouping helps model understand "type" of spam, not just random words

URGENCY_WORDS = [
    "urgent", "act now", "limited time", "expires", "deadline", "immediately",
    "don't wait", "today only", "last chance", "hurry", "while supplies last",
    "respond now", "call now", "order now", "buy now"
]

FINANCIAL_WORDS = [
    "free", "win", "winner", "cash", "prize", "loan", "credit", "debt",
    "income", "earn", "salary", "investment", "profit", "money back",
    "guarantee", "no cost", "no fee", "affordable", "cheap", "discount",
    "save", "bonus", "reward", "million", "billion", "jackpot"
]

PHISHING_WORDS = [
    "verify", "confirm", "account", "password", "login", "suspended",
    "unusual activity", "security alert", "click here", "update required",
    "validate", "re-activate", "compromised", "locked", "unauthorized"
]

ADULT_WORDS = [
    "adult", "dating", "singles", "meet", "hot", "sexy", "explicit",
    "xxx", "18+", "mature"
]

# combine all lists → used for overall spam detection
ALL_SPAM_WORDS = URGENCY_WORDS + FINANCIAL_WORDS + PHISHING_WORDS + ADULT_WORDS


# ---------------- FEATURE EXTRACTION ----------------
# converts email into numbers (ML only understands numbers)
def extract_features(subject: str, body: str) -> dict:

    # lower version for matching words
    text = (subject + " " + body).lower()

    # original version (needed for caps, symbols etc.)
    full_text = subject + " " + body

    features = {}

    # ---------------- BASIC LENGTH FEATURES ----------------
    features["subject_length"] = len(subject)
    features["body_length"] = len(body)
    features["body_word_count"] = len(body.split())


    # ---------------- CAPS ANALYSIS ----------------
    # spam emails often SHOUT 😄
    upper_chars = sum(1 for c in full_text if c.isupper())
    alpha_chars = sum(1 for c in full_text if c.isalpha())

    # ratio instead of raw count → better scaling
    features["caps_ratio"] = upper_chars / max(alpha_chars, 1)

    # check if entire subject is uppercase
    features["subject_all_caps"] = int(subject == subject.upper() and len(subject) > 3)


    # ---------------- SYMBOL COUNTS ----------------
    features["exclamation_count"] = full_text.count("!")
    features["question_count"] = full_text.count("?")

    # currency symbols → often used in scams
    features["dollar_count"] = full_text.count("$") + full_text.count("£") + full_text.count("€")

    features["ellipsis_count"] = full_text.count("...")


    # ---------------- URL FEATURES ----------------
    url_pattern = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)
    urls = url_pattern.findall(full_text)

    features["url_count"] = len(urls)

    # shortened URLs = suspicious (used to hide real link)
    features["has_short_url"] = int(any(
        domain in u for u in urls
        for domain in ["bit.ly", "tinyurl", "goo.gl", "t.co", "ow.ly", "is.gd"]
    ))


    # ---------------- HTML FEATURES ----------------
    # spam emails often contain raw HTML
    features["html_tag_count"] = len(re.findall(r'<[^>]+>', body))

    features["has_html"] = int(bool(
        re.search(r'<html|<body|<table|<div', body, re.IGNORECASE)
    ))


    # ---------------- WORD CATEGORY COUNTS ----------------
    # count how many words from each spam category appear
    features["urgency_word_count"] = sum(1 for w in URGENCY_WORDS if w in text)
    features["financial_word_count"] = sum(1 for w in FINANCIAL_WORDS if w in text)
    features["phishing_word_count"] = sum(1 for w in PHISHING_WORDS if w in text)
    features["adult_word_count"] = sum(1 for w in ADULT_WORDS if w in text)

    # total spam words overall
    features["total_spam_words"] = sum(1 for w in ALL_SPAM_WORDS if w in text)


    # ---------------- SUBJECT TRICKS ----------------
    # normal emails often start with Re:/Fwd:
    features["subject_has_re_fwd"] = int(bool(re.match(r'^(re:|fwd:|fw:)', subject.lower())))

    features["subject_has_free"] = int("free" in subject.lower())

    # classic spam trick → "you won something"
    features["subject_has_winner"] = int(any(
        w in subject.lower() for w in ["winner", "won", "prize", "selected"]
    ))

    features["subject_exclamation"] = int("!" in subject)
    features["subject_question"] = int("?" in subject)


    # ---------------- NUMBER / SYMBOL DENSITY ----------------
    digit_count = sum(1 for c in full_text if c.isdigit())
    features["digit_ratio"] = digit_count / max(len(full_text), 1)

    special_chars = sum(1 for c in full_text if c in "!@#$%^&*()_+-=[]{}|;':\",./<>?")
    features["special_char_ratio"] = special_chars / max(len(full_text), 1)


    # ---------------- WORD REPETITION ----------------
    # spam often repeats same words again and again
    words = re.findall(r'\b\w+\b', text)

    if words:
        word_freq = Counter(words)
        most_common_count = word_freq.most_common(1)[0][1]

        # how dominant the most frequent word is
        features["word_repetition_score"] = most_common_count / max(len(words), 1)
    else:
        features["word_repetition_score"] = 0.0


    # ---------------- COMMON PATTERNS ----------------
    features["has_unsubscribe"] = int(
        "unsubscribe" in text or "opt-out" in text or "opt out" in text
    )

    features["has_dear"] = int(bool(re.search(r'\bdear\b', text)))

    # generic greeting → strong spam signal
    features["has_generic_greeting"] = int(bool(
        re.search(r'\bdear (customer|user|member|friend|sir|madam)\b', text)
    ))


    # ---------------- LINK ANALYSIS ----------------
    # extract domains from URLs
    domain_pattern = re.compile(r'https?://([^/\s]+)', re.IGNORECASE)
    domains = domain_pattern.findall(full_text)

    # number of unique domains (too many = suspicious)
    features["unique_link_domains"] = len(set(domains))

    return features


# convert feature dict → list (ML model expects list/array)
def feature_vector(subject: str, body: str) -> list:
    f = extract_features(subject, body)
    return list(f.values())


# return feature names (useful for debugging / analysis)
def feature_names() -> list:
    dummy = extract_features("", "")
    return list(dummy.keys())


# ---------------- USER-FACING EXPLANATION ----------------
# these are reasons shown in UI ("why this is spam")
def get_triggered_features(subject: str, body: str) -> list:

    f = extract_features(subject, body)
    reasons = []

    if f["caps_ratio"] > 0.35:
        reasons.append(f"High CAPS usage ({f['caps_ratio']*100:.0f}% of letters)")

    if f["subject_all_caps"]:
        reasons.append("Subject line is ALL CAPS")

    if f["exclamation_count"] >= 3:
        reasons.append(f"{f['exclamation_count']} exclamation marks")

    if f["dollar_count"] >= 2:
        reasons.append(f"{f['dollar_count']} currency symbols ($, £, €)")

    if f["url_count"] >= 3:
        reasons.append(f"{f['url_count']} URLs in body")

    if f["has_short_url"]:
        reasons.append("Contains shortened/obfuscated URL")

    if f["has_html"]:
        reasons.append("Contains raw HTML markup")

    if f["urgency_word_count"] >= 2:
        reasons.append(f"{f['urgency_word_count']} urgency trigger words")

    if f["financial_word_count"] >= 2:
        reasons.append(f"{f['financial_word_count']} financial trigger words")

    if f["phishing_word_count"] >= 2:
        reasons.append(f"{f['phishing_word_count']} phishing-related words")

    if f["subject_has_free"]:
        reasons.append('"FREE" in subject line')

    if f["subject_has_winner"]:
        reasons.append("Subject claims you won something")

    if f["has_generic_greeting"]:
        reasons.append('Generic greeting ("Dear Customer/User")')

    if f["digit_ratio"] > 0.15:
        reasons.append(f"High number density ({f['digit_ratio']*100:.0f}%)")

    if f["word_repetition_score"] > 0.12:
        reasons.append("Unusual word repetition detected")

    return reasons