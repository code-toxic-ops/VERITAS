"""Train, evaluate, save and load the VERITAS models."""

from __future__ import annotations

import csv
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict  # noqa: F401  (kept for tuning)

from . import synthetic
from .text_model import CLASSES, TextModel
from .url_model import UrlModel

BACKEND = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND / "data"
MODEL_DIR = BACKEND / "app" / "models"
TEXT_PATH = MODEL_DIR / "text_model.joblib"
URL_PATH = MODEL_DIR / "url_model.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"
HOLDOUT_PATH = DATA_DIR / "holdout.json"
FEEDBACK_PATH = DATA_DIR / "feedback.jsonl"
MODEL_VERSION = "1.0"


# ----------------------------------------------------------------------------- data
def _read_csv(path: Path, allowed_labels=None) -> list:
    rows = []
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.reader(fh):
            if len(r) < 2 or not r[0].strip():
                continue
            first, label = r[0].strip(), r[1].strip().lower()
            if first.lower() in {"message", "text", "url", "link", "example"} and label in {"label", "class", "category"}:
                continue
            if allowed_labels is not None and label not in allowed_labels:
                continue
            rows.append((first, label))
    return rows


def _write_csv(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)


def load_feedback() -> tuple:
    """User-confirmed examples saved by /api/feedback -> (message rows, url rows)."""
    msgs, urls = [], []
    if FEEDBACK_PATH.exists():
        for line in FEEDBACK_PATH.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("text") and r.get("label") in CLASSES:
                msgs.append((r["text"], r["label"]))
            if r.get("url") and r.get("url_label") in ("safe", "malicious"):
                urls.append((r["url"], r["url_label"]))
    return msgs, urls


def build_corpus(regenerate: bool = False, extra_messages=None, extra_urls=None, use_feedback: bool = False):
    msg_csv, url_csv = DATA_DIR / "messages.csv", DATA_DIR / "urls.csv"
    if regenerate or not msg_csv.exists():
        _write_csv(msg_csv, synthetic.generate_messages())
    if regenerate or not url_csv.exists():
        _write_csv(url_csv, synthetic.generate_urls())
    msgs, urls = _read_csv(msg_csv, CLASSES), _read_csv(url_csv, ("safe", "malicious"))
    for p in extra_messages or []:
        msgs += _read_csv(Path(p), CLASSES)
    for p in extra_urls or []:
        urls += _read_csv(Path(p), ("safe", "malicious"))
    if use_feedback:
        fm, fu = load_feedback()
        msgs += fm * 3   # a person's correction is worth more than one synthetic row
        urls += fu * 3
    return msgs, urls


# ------------------------------------------------------------------------ evaluation
def _holdout() -> dict:
    if HOLDOUT_PATH.exists():
        return json.loads(HOLDOUT_PATH.read_text(encoding="utf-8"))
    return {"messages": [], "urls": []}


def evaluate(text_model: TextModel, url_model: UrlModel) -> dict:
    h = _holdout()
    out: dict = {}
    if h["messages"]:
        y = [r["label"] for r in h["messages"]]
        pred = text_model.predict([r["text"] for r in h["messages"]])
        out["messages"] = {
            "n": len(y), "accuracy": round(accuracy_score(y, pred), 3),
            "macro_f1": round(f1_score(y, pred, average="macro"), 3),
            "labels": list(CLASSES), "confusion": confusion_matrix(y, pred, labels=list(CLASSES)).tolist(),
        }
        # the most important number for safety: how many real scams slip through as "genuine"
        scam_idx = [i for i, l in enumerate(y) if l in ("scam", "spam")]
        out["messages"]["missed_bad_as_genuine"] = int(sum(pred[i] == "genuine" for i in scam_idx))
        out["messages"]["genuine_flagged_as_bad"] = int(sum(1 for l, p in zip(y, pred) if l == "genuine" and p != "genuine"))
    if h["urls"]:
        y = [r["label"] for r in h["urls"]]
        pred = url_model.predict([r["url"] for r in h["urls"]])
        out["urls"] = {
            "n": len(y), "accuracy": round(accuracy_score(y, pred), 3),
            "macro_f1": round(f1_score(y, pred, average="macro"), 3),
            "labels": ["safe", "malicious"], "confusion": confusion_matrix(y, pred, labels=["safe", "malicious"]).tolist(),
        }
    return out


# -------------------------------------------------------------------------- training
def train_all(regenerate: bool = False, extra_messages=None, extra_urls=None, use_feedback: bool = False,
              verbose: bool = True) -> dict:
    msgs, urls = build_corpus(regenerate, extra_messages, extra_urls, use_feedback)
    if verbose:
        print(f"Training on {len(msgs)} messages and {len(urls)} URLs ...")

    # honest-ish internal check: 80/20 split of the training corpus (inflated, same generator)
    rng = np.random.RandomState(0)
    idx = rng.permutation(len(msgs))
    cut = int(len(msgs) * 0.8)
    tr, te = [msgs[i] for i in idx[:cut]], [msgs[i] for i in idx[cut:]]
    tm = TextModel().fit([t for t, _ in tr], [l for _, l in tr])
    internal = accuracy_score([l for _, l in te], tm.predict([t for t, _ in te]))

    text_model = TextModel().fit([t for t, _ in msgs], [l for _, l in msgs])
    url_model = UrlModel().fit([u for u, _ in urls], [l for _, l in urls])

    metrics = {
        "version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sklearn": sklearn.__version__,
        "messages_trained_on": len(msgs),
        "urls_trained_on": len(urls),
        "per_class": {c: sum(1 for _, l in msgs if l == c) for c in CLASSES},
        "internal_split_accuracy": round(float(internal), 3),
        "holdout": evaluate(text_model, url_model),
        "note": ("Trained on a synthetic template corpus plus any extra data supplied. "
                 "Holdout examples are kept out of training and provide a small sanity check, "
                 "not a production-grade benchmark. Validate on a larger representative dataset."),
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(text_model, TEXT_PATH, compress=3)
    joblib.dump(url_model, URL_PATH, compress=3)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    if verbose:
        print_metrics(metrics)
    return metrics


def print_metrics(m: dict) -> None:
    print(f"\nInternal split accuracy (optimistic): {m['internal_split_accuracy']}")
    ho = m.get("holdout", {})
    if "messages" in ho:
        h = ho["messages"]
        print(f"HOLDOUT messages  n={h['n']}  accuracy={h['accuracy']}  macro-F1={h['macro_f1']}")
        print(f"  scams/spam missed as genuine: {h['missed_bad_as_genuine']}   genuine wrongly flagged: {h['genuine_flagged_as_bad']}")
        print(f"  confusion (rows=true {h['labels']}):  {h['confusion']}")
    if "urls" in ho:
        h = ho["urls"]
        print(f"HOLDOUT urls      n={h['n']}  accuracy={h['accuracy']}  macro-F1={h['macro_f1']}  confusion={h['confusion']}")


# ---------------------------------------------------------------------------- loading
_lock = threading.Lock()
_cache: dict = {}


def _load_or_train() -> None:
    try:
        meta = json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}
        if meta.get("sklearn") != sklearn.__version__:
            raise RuntimeError("scikit-learn version changed; retraining")
        _cache["text"] = joblib.load(TEXT_PATH)
        _cache["url"] = joblib.load(URL_PATH)
        _cache["metrics"] = meta
    except Exception:  # missing, corrupt or built with another scikit-learn: just retrain (~seconds)
        _cache["metrics"] = train_all(verbose=False)
        _cache["text"] = joblib.load(TEXT_PATH)
        _cache["url"] = joblib.load(URL_PATH)


def _ensure() -> None:
    if "text" not in _cache:
        with _lock:
            if "text" not in _cache:
                _load_or_train()


def get_text_model() -> TextModel:
    _ensure()
    return _cache["text"]


def get_url_model() -> UrlModel:
    _ensure()
    return _cache["url"]


def get_metrics() -> dict:
    _ensure()
    return _cache["metrics"]


def reload_models() -> None:
    with _lock:
        _cache.clear()
