"""Learned link classifier: safe vs malicious.

The link is NEVER opened. The model sees only the text of the URL and learns from two views:

  A. numeric features (length, digits, entropy, subdomain depth, IP host, brand look-alike
     signals, risky words...) -> gradient boosted trees
  B. character n-grams of host + path -> logistic regression

The two probabilities are averaged. The brand and structure signals from url_analysis.py are
used here purely as *features*; the model learns how much each one matters.
"""

from __future__ import annotations

import math
import re
from urllib.parse import urlsplit

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from ..url_analysis import (FREE_HOSTING, SHORTENERS, SUSPICIOUS_TLDS, _is_ip, analyze_url,
                            _brand_issues as brand_issues, registrable_domain)

RISKY_WORDS = (
    "login", "signin", "verify", "verification", "secure", "update", "account", "bank", "kyc",
    "confirm", "wallet", "claim", "reward", "prize", "free", "bonus", "refund", "gift", "unlock",
    "suspend", "password", "otp", "payment", "support", "apply", "register", "winner", "lucky",
    "offer", "cashback", "recharge", "install", "apk", "helpdesk", "alert", "billing", "yojana",
)
COMMON_TLDS = {"com", "in", "org", "net", "edu", "gov", "io", "co", "ac", "uk", "us", "me", "app", "dev"}
_VOWELS = set("aeiou")


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = {c: s.count(c) for c in set(s)}
    return -sum(v / len(s) * math.log2(v / len(s)) for v in counts.values())


def _split(url: str):
    raw = url.strip()
    scheme_given = bool(re.match(r"^[a-z][a-z0-9+.-]*://", raw, re.I))
    try:
        p = urlsplit(raw if scheme_given else "//" + raw)
        host = (p.hostname or "").lower()
        return raw, scheme_given, p, host
    except ValueError:
        return raw, scheme_given, None, ""


def url_features(url: str) -> list:
    raw, scheme_given, p, host = _split(url)
    if p is None or not host:
        return [0.0] * 34
    path, query = p.path or "", p.query or ""
    is_ip = _is_ip(host)
    reg = host if is_ip else registrable_domain(host)
    labels = host.split(".")
    tld = labels[-1] if not is_ip else ""
    subs = max(len(labels) - len(reg.split(".")), 0) if not is_ip else 0
    letters = [c for c in host if c.isalpha()]
    kinds = [k for k, _ in brand_issues(host, reg)] if not is_ip else []
    host_tokens = re.split(r"[.\-]", host)
    low = raw.lower()
    return [
        min(len(raw), 200) / 200, min(len(host), 80) / 80, min(len(path), 120) / 120, min(len(query), 120) / 120,
        host.count(".") / 6, host.count("-") / 5,
        sum(c.isdigit() for c in host) / max(len(host), 1),
        _entropy(host.replace(".", "")) / 4.5,
        min(subs, 5) / 5,
        min(path.count("/"), 8) / 8, min(query.count("&") + (1 if query else 0), 8) / 8,
        1.0 if is_ip else 0.0,
        1.0 if "@" in (p.netloc or "") else 0.0,
        1.0 if ("xn--" in host or any(ord(c) > 127 for c in host)) else 0.0,
        1.0 if reg in SHORTENERS else 0.0,
        1.0 if (tld in SUSPICIOUS_TLDS and not is_ip) else 0.0,
        1.0 if any(host == d or host.endswith("." + d) for d in FREE_HOSTING) else 0.0,
        1.0 if p.port not in (None, 80, 443) else 0.0,
        1.0 if low.startswith("http://") else 0.0,
        1.0 if "exact" in kinds else 0.0, 1.0 if "homoglyph" in kinds else 0.0,
        1.0 if "typo" in kinds else 0.0, 1.0 if "embedded" in kinds else 0.0,
        min(sum(w in host for w in RISKY_WORDS), 4) / 4,
        min(sum(w in path.lower() + query.lower() for w in RISKY_WORDS), 4) / 4,
        min(low.count("%"), 6) / 6,
        max((len(t) for t in host_tokens), default=0) / 25,
        (sum(c in _VOWELS for c in letters) / len(letters)) if letters else 0.0,
        min(len(tld), 8) / 8 if tld else 0.0,
        1.0 if tld in COMMON_TLDS else 0.0,
        1.0 if "https" in host or "http" in host else 0.0,
        1.0 if host.startswith("www.") else 0.0,
        1.0 if path.lower().endswith((".apk", ".exe", ".php", ".zip")) else 0.0,
        1.0 if scheme_given else 0.0,
    ]


def _char_view(url: str) -> str:
    _, _, p, host = _split(url)
    if p is None:
        return url.lower()
    return (host + (p.path or "") + ("?" + p.query if p.query else "")).lower()[:200]


class UrlModel:
    def __init__(self):
        self.gbm = None
        self.vec = None
        self.lr = None

    def fit(self, urls, labels):
        urls = list(urls)
        y = np.array([1 if l == "malicious" else 0 for l in labels])
        x = np.array([url_features(u) for u in urls], dtype=float)
        self.gbm = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, max_depth=6,
                                                  l2_regularization=1.0, random_state=0).fit(x, y)
        self.vec = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), min_df=3, sublinear_tf=True,
                                   lowercase=False, max_features=50000)
        xc = self.vec.fit_transform([_char_view(u) for u in urls])
        self.lr = LogisticRegression(C=3.0, max_iter=3000).fit(xc, y)
        return self

    def predict_proba(self, urls) -> np.ndarray:
        """P(malicious) for each url."""
        urls = list(urls)
        a = self.gbm.predict_proba(np.array([url_features(u) for u in urls], dtype=float))[:, 1]
        b = self.lr.predict_proba(self.vec.transform([_char_view(u) for u in urls]))[:, 1]
        return (a + b) / 2.0

    def predict_one(self, url: str) -> float:
        return float(self.predict_proba([url])[0])

    def predict(self, urls) -> list:
        return ["malicious" if p >= 0.5 else "safe" for p in self.predict_proba(urls)]
