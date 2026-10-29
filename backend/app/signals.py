"""Rule signals: human-readable evidence AND input features for the learned models.

In the legacy detector these regex rules *were* the detector, each with a hand-set
weight. In VERITAS they no longer decide anything. They do two jobs:

  1. They name the exact phrase that looks suspicious so the UI can explain it.
  2. Whether each rule fired is fed to the text model as one input feature, so the
     model *learns* how much each signal matters from labelled data.
"""

from __future__ import annotations

import re

from .rules import TEXT_RULES

_NEGATION = re.compile(
    r"\b(?:do\s+not|don'?t|dont|never|should\s+not|shouldn'?t|won'?t|will\s+not|not)\b", re.I
)


def is_negated(text: str, start: int) -> bool:
    """True if the match sits in a warning sentence like 'Never share your OTP'."""
    prefix = text[:start]
    sentence_start = max(prefix.rfind(c) for c in ".!?\n") + 1
    return bool(_NEGATION.search(prefix[sentence_start:]))


def rule_hits(text: str) -> dict:
    """Return {rule_id: [(start, end), ...]} for every text rule that fires."""
    found: dict = {}
    for rule in TEXT_RULES:
        hits = []
        for pattern in rule.patterns:
            for m in pattern.finditer(text):
                if rule.negatable and is_negated(text, m.start()):
                    continue
                hits.append((m.start(), m.end()))
        if hits:
            found[rule.id] = hits
    return found


def utf16_index(text: str, idx: int) -> int:
    """JavaScript strings are UTF-16, so convert Python code-point offsets."""
    return len(text[:idx].encode("utf-16-le")) // 2


def snippet(text: str, start: int, end: int) -> str:
    s = " ".join(text[start:end].split())
    return s if len(s) <= 100 else s[:97] + "..."


def merge_spans(spans: list) -> list:
    """spans: [(start, end, tag)] -> merged, non-overlapping [[start, end, {tags}]]."""
    merged: list = []
    for start, end, tag in sorted(spans, key=lambda s: (s[0], s[1])):
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
            merged[-1][2].add(tag)
        else:
            merged.append([start, end, {tag}])
    return merged


def impact_label(points: int) -> str:
    """Words, not numbers: how much a signal matters when it appears."""
    if points >= 25:
        return "major"
    if points >= 12:
        return "notable"
    return "minor"
