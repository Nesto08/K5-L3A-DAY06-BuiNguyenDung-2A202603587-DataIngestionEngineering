"""Evaluate retrieved evidence and preserve per-query traces."""

import re
import unicodedata
from collections import defaultdict
from typing import Any

def evaluate_query(question: dict[str, Any],
                   hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check gold source, page and evidence in top-3."""

    def normalize(text):
        text = unicodedata.normalize("NFC", str(text or ""))
        return re.sub(r"\s+", " ", text).strip().casefold()

    golds = question.get("gold_evidence", [])
    results = []

    for rank, hit in enumerate(hits[:3], 1):
        meta = hit.get("metadata") or {}
        text = normalize(hit.get("text", ""))

        matched = any(
            str(meta.get("document_id")) ==
            str(gold.get("source_id"))
            and str(meta.get("page")) ==
            str(gold.get("pdf_page"))
            and bool(normalize(gold.get("evidence_anchor")))
            and normalize(gold["evidence_anchor"]) in text
            for gold in golds
        )

        results.append({
            **hit,
            "rank": rank,
            "evidence_hit": matched
        })

    return {
        "id": question["question_id"],
        "split": question["split"],
        "question": question["question"],
        "gold_evidence": golds,
        "filter": question.get("metadata_filter"),
        "hit_at_1": bool(results and results[0]["evidence_hit"]),
        "hit_at_3": any(h["evidence_hit"] for h in results),
        "hits": results
    }

def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize Hit@1 and Hit@3 by strategy and split."""

    groups = defaultdict(list)

    for trace in traces:
        groups[(trace["strategy"], trace["split"])].append(trace)

    summary = {}

    for (strategy, split), items in groups.items():
        total = len(items)
        hit1 = sum(t["hit_at_1"] for t in items)
        hit3 = sum(t["hit_at_3"] for t in items)

        summary.setdefault(strategy, {})[split] = {
            "total": total,
            "hit_at_1_count": hit1,
            "hit_at_3_count": hit3,
            "hit_at_1": hit1 / total,
            "evidence_hit_at_3": hit3 / total
        }

    return summary