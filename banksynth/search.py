"""Deterministic, typo-tolerant field search without a remote service."""
from difflib import SequenceMatcher
import re
from banksynth.catalog import FIELDS, LABELS


def normalize(text):
    return ' '.join(re.findall(r'[a-z0-9]+', text.casefold()))


def search_fields(query, fields=FIELDS):
    query = normalize(query)
    if not query:
        return list(fields)
    scored = []
    for f in fields:
        name = normalize(f.name)
        label = normalize(f.label)
        full = normalize(f'{f.table} {name} {LABELS[f.table]}')
        if query in name or query in normalize(f.id):
            score = 2 + (query == name)
        elif query in full:
            score = 1.5
        else:
            ratio = max(SequenceMatcher(None, query, candidate).ratio() for candidate in (name, label, full))
            token_score = sum(max(SequenceMatcher(None, q, w).ratio() for w in full.split()) for q in query.split()) / len(query.split())
            score = max(ratio, token_score * .94)
            if score < .68:
                continue
        scored.append((score, f))
    return [f for _, f in sorted(scored, key=lambda item: -item[0])]
