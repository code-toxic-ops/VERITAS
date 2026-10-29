"""Learned message classifier: genuine vs scam vs spam.

Features
  * word 1-2 grams (TF-IDF)  - what the message says
  * char 2-5 grams (TF-IDF)  - robust to typos, Hinglish and Devanagari
  * meta features            - which rule signals fired + simple shape statistics

The classifier is multinomial logistic regression, so training is fast, the output is a
proper probability for each class, and every prediction can be explained from its weights.
"""

from __future__ import annotations

import math
import re

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from ..rules import TEXT_RULES
from ..signals import rule_hits
from ..url_analysis import find_urls

CLASSES = ("genuine", "scam", "spam")

_AMOUNT = re.compile(
    r"(?:₹|rs\.?|inr|\$|usd|rupees?)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:lakh|lakhs|crore|k)\b)?"
    r"|\d[\d,]*\s?(?:₹|rs\.?|inr|rupees?|lakh|lakhs|crore)\b", re.I)
_PHONE = re.compile(r"(?<!\d)(?:\+?91[-\s]?|0)?[6-9]\d{4}[-\s]?\d{5}(?!\d)")
_NUM = re.compile(r"\d+")
# keep letters, digits, Devanagari and the placeholder tokens; everything else becomes a space
_PUNCT = re.compile(r"[^\w\u0900-\u097F]+", re.UNICODE)

FRIENDLY = {
    "urltoken": "a link", "amounttoken": "a money amount", "phonetoken": "a phone number",
    "numtoken": "a number",
}


def normalize(text: str) -> str:
    """Turn raw text into a stable form so the model learns *patterns*, not specific values."""
    pieces, last = [], 0
    for _, s, e in find_urls(text):
        pieces.append(text[last:s])
        pieces.append(" urltoken ")
        last = e
    pieces.append(text[last:])
    t = "".join(pieces)
    t = _AMOUNT.sub(" amounttoken ", t)
    t = _PHONE.sub(" phonetoken ", t)
    t = _NUM.sub(" numtoken ", t)
    t = t.lower()
    return " ".join(_PUNCT.sub(" ", t).split())


def meta_features(text: str) -> list:
    hits = rule_hits(text)
    vec = [1.0 if r.id in hits else 0.0 for r in TEXT_RULES]
    n = max(len(text), 1)
    letters = [c for c in text if c.isalpha()]
    caps = sum(c.isupper() for c in letters) / max(len(letters), 1)
    vec += [
        min(len(find_urls(text)), 5) / 5.0,
        min(text.count("!"), 8) / 8.0,
        caps,
        min(sum(c.isdigit() for c in text) / n * 5.0, 1.0),
        min(math.log1p(len(text)) / 8.0, 1.0),
        1.0 if _AMOUNT.search(text) else 0.0,
        1.0 if _PHONE.search(text) else 0.0,
    ]
    return vec


class TextModel:
    def __init__(self, C: float = 3.0):
        self.C = C
        self.word = None
        self.char = None
        self.clf = None
        self.classes_: list = []
        self._n_word = 0

    # -- training -------------------------------------------------------------------
    def _matrix(self, texts, fit: bool = False):
        norm = [normalize(t) for t in texts]
        meta = sparse.csr_matrix(np.array([meta_features(t) for t in texts], dtype=float))
        if fit:
            self.word = TfidfVectorizer(lowercase=False, token_pattern=r"\S+", ngram_range=(1, 2),
                                        min_df=2, sublinear_tf=True)
            self.char = TfidfVectorizer(analyzer="char_wb", lowercase=False, ngram_range=(2, 5),
                                        min_df=3, sublinear_tf=True, max_features=60000)
            xw = self.word.fit_transform(norm)
            xc = self.char.fit_transform(norm)
            self._n_word = xw.shape[1]
        else:
            xw, xc = self.word.transform(norm), self.char.transform(norm)
        return sparse.hstack([xw, xc, meta]).tocsr()

    def fit(self, texts, labels):
        x = self._matrix(list(texts), fit=True)
        self.clf = LogisticRegression(C=self.C, max_iter=4000, class_weight="balanced")
        self.clf.fit(x, list(labels))
        self.classes_ = list(self.clf.classes_)
        return self

    # -- inference ------------------------------------------------------------------
    def predict_proba(self, texts) -> np.ndarray:
        return self.clf.predict_proba(self._matrix(list(texts)))

    def predict_one(self, text: str) -> dict:
        p = self.predict_proba([text])[0]
        return {c: float(p[i]) for i, c in enumerate(self.classes_)}

    def predict(self, texts) -> list:
        p = self.predict_proba(texts)
        return [self.classes_[i] for i in p.argmax(axis=1)]

    def cues(self, text: str, target: str, top: int = 6) -> list:
        """Words and phrases that pushed the model toward `target` for this message."""
        if target not in self.classes_:
            return []
        x = self._matrix([text])
        row = x[0, : self._n_word].toarray().ravel()
        coef = self.clf.coef_[self.classes_.index(target)][: self._n_word]
        contrib = row * coef
        names = self.word.get_feature_names_out()
        order = np.argsort(-contrib)
        chosen: list = []
        for i in order:
            if contrib[i] <= 0.02 or len(chosen) >= top * 2:
                break
            chosen.append(names[i])
        # prefer longer phrases; drop single words already covered by a chosen phrase
        phrases = [c for c in chosen if " " in c]
        singles = [c for c in chosen if " " not in c and not any(c in p.split() for p in phrases)]
        out: list = []
        for c in phrases + singles:
            friendly = " ".join(FRIENDLY.get(w, w) for w in c.split())
            if friendly not in out:
                out.append(friendly)
            if len(out) >= top:
                break
        return out
