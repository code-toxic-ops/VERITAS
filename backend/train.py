"""Train VERITAS text and URL models from backend/data and optional labelled CSV files.

Usage from backend/: python train.py
Optional extra corpora: python train.py --messages path/to/messages.csv --urls path/to/urls.csv
"""
from __future__ import annotations
import argparse
from app.ml.training import train_all


def main() -> None:
    parser = argparse.ArgumentParser(description="Train VERITAS scam, spam and URL classifiers")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate synthetic starter corpus")
    parser.add_argument("--messages", action="append", default=[], help="CSV with message,label columns (repeatable)")
    parser.add_argument("--urls", action="append", default=[], help="CSV with URL,safe|malicious columns (repeatable)")
    parser.add_argument("--use-feedback", action="store_true", help="Include user-confirmed corrections from data/feedback.jsonl")
    args = parser.parse_args()
    train_all(regenerate=args.regenerate, extra_messages=args.messages, extra_urls=args.urls,
              use_feedback=args.use_feedback, verbose=True)


if __name__ == "__main__":
    main()
