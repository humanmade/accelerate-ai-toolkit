#!/usr/bin/env python3
"""Merge a bounded Accelerate learning refresh into one site journal.

The helper deliberately has no network code. A skill supplies the experiments it
actually read; this module makes the local merge idempotent, site-scoped, and
safe when two refreshes finish at the same time.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


JOURNAL_SCHEMA_VERSION = 4

PATTERN_NAMES = {
    "headline_match_intent": "Rewrite headline to match what visitors searched for",
    "headline_clarity": "Rewrite headline for clarity",
    "cta_above_fold": "Move the main call-to-action higher on the page",
    "cta_copy": "Rewrite button or link text to be more specific",
    "social_proof": "Add social proof near the call-to-action",
    "testimonial": "Add a customer testimonial near the call-to-action",
    "urgency_copy": "Add urgency or scarcity language",
    "simplify_hero": "Simplify the hero section (remove clutter)",
    "pricing_display": "Change how pricing is shown (default period, anchoring)",
    "personalize_referrer": "Personalise content by traffic source",
    "personalize_geo": "Personalise content by visitor location",
    "personalize_device": "Personalise content by device type",
    "hero_image": "Change the hero image",
    "form_fields": "Change form field count or layout",
    "other": "Other / unclassified",
}

LISTING_IDENTITY_FIELDS = (
    "experiment_id",
    "block_id",
    "test_id",
    "type",
    "status",
    "title",
    "goal",
    "started_at",
    "ended_at",
    "has_winner",
    "winner_variant_index",
    "annotations",
    "updated_at",
    "result_revision",
)


class JournalError(ValueError):
    """A journal or refresh input cannot safely be merged."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def listing_fingerprint(experiment: Mapping[str, Any]) -> str:
    """Fingerprint only fields the producer exposes in its history listing."""
    return _hash({field: experiment.get(field) for field in LISTING_IDENTITY_FIELDS})


def _detail_fingerprint(result: Any) -> str | None:
    return _hash(result) if result is not None else None


def _require_site(site: Mapping[str, Any]) -> dict[str, Any]:
    key = site.get("key")
    url = site.get("url")
    if not isinstance(key, str) or not key or not isinstance(url, str) or not url:
        raise JournalError("site.key and site.url are required")
    return {
        "key": key,
        "name": site.get("name") if isinstance(site.get("name"), str) else "",
        "theme": site.get("theme") if isinstance(site.get("theme"), str) else None,
        "url": url,
    }


def _empty_journal(site: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": JOURNAL_SCHEMA_VERSION,
        "site": _require_site(site),
        "last_updated": None,
        "iteration_counter": 0,
        "stats": {
            "total_experiments_considered": 0,
            "concluded_with_winner": 0,
            "concluded_without_winner": 0,
            "patterns_with_signal": 0,
        },
        "listing_coverage": {"complete": False, "reason": "not yet refreshed"},
        "experiments": {},
        "patterns": [],
    }


def _load_journal(path: Path, site: Mapping[str, Any], rebuild: bool) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return _empty_journal(site), None
    try:
        journal = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise JournalError("journal is unreadable; leave it unchanged and rebuild explicitly") from error
    if journal.get("schema_version") != JOURNAL_SCHEMA_VERSION and not rebuild:
        raise JournalError(
            f"journal schema {journal.get('schema_version')!r} needs an explicit bounded rebuild before incremental refresh"
        )
    stored_site = journal.get("site")
    expected_site = _require_site(site)
    if not isinstance(stored_site, dict) or (
        stored_site.get("key") != expected_site["key"] or stored_site.get("url") != expected_site["url"]
    ):
        raise JournalError("journal belongs to a different site")
    if journal.get("schema_version") != JOURNAL_SCHEMA_VERSION:
        return _empty_journal(site), _canonical(journal) + "\n"
    if not isinstance(journal.get("experiments"), dict):
        raise JournalError("journal experiment records are invalid; leave it unchanged and rebuild explicitly")
    return journal, None


def _as_rate(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _lift_percent(result: Any, winner_index: Any, outcome: str) -> float | None:
    if outcome != "win" or not isinstance(result, Mapping) or not isinstance(result.get("variants"), list):
        return None
    variants = result["variants"]
    if not isinstance(winner_index, int) or winner_index <= 0 or winner_index >= len(variants):
        return None
    control = variants[0] if isinstance(variants[0], Mapping) else {}
    winner = variants[winner_index] if isinstance(variants[winner_index], Mapping) else {}
    baseline = _as_rate(control.get("conversion_rate"))
    winning_rate = _as_rate(winner.get("conversion_rate"))
    if baseline is None or winning_rate is None or baseline == 0:
        return None
    return round(((winning_rate - baseline) / baseline) * 100, 4)


def _outcome(listing: Mapping[str, Any], evidence: str) -> str:
    if evidence == "manual_selection":
        return "manual_selection"
    if evidence == "unknown_selection":
        return "unknown_selection"
    if not listing.get("has_winner"):
        return "inconclusive"
    return "win" if listing.get("winner_variant_index") != 0 else "loss"


def _normalise_record(raw: Mapping[str, Any]) -> dict[str, Any]:
    listing = raw.get("experiment", raw)
    if not isinstance(listing, Mapping):
        raise JournalError("each refresh record needs an experiment listing")
    experiment_id = listing.get("experiment_id")
    if isinstance(experiment_id, bool) or not isinstance(experiment_id, int) or experiment_id <= 0:
        raise JournalError("each refresh record needs a positive experiment_id")
    pattern_id = raw.get("pattern_id", "other")
    if pattern_id not in PATTERN_NAMES:
        pattern_id = "other"
    # The producer's completed state and applied content do not reveal whether a
    # human picked a variant or a verdict was statistically proven. Callers may
    # label only evidence they observed in the current supervised session.
    evidence = raw.get("evidence", "unknown_selection")
    if evidence not in {"proven_result", "manual_selection", "unknown_selection"}:
        raise JournalError("evidence must be proven_result, manual_selection, or unknown_selection")
    result = raw.get("result")
    outcome = _outcome(listing, evidence)
    list_fingerprint = listing_fingerprint(listing)
    result_revision = listing.get("result_revision")
    return {
        "experiment_id": experiment_id,
        "block_id": listing.get("block_id"),
        "pattern_id": pattern_id,
        "summary": raw.get("summary") if isinstance(raw.get("summary"), str) else "",
        "outcome": outcome,
        "evidence": evidence,
        "ended_at": listing.get("ended_at"),
        "listing_fingerprint": list_fingerprint,
        "result_revision": result_revision if isinstance(result_revision, str) and result_revision else None,
        "detail_fingerprint": _detail_fingerprint(result),
        "fingerprint": _hash(
            {
                "listing": list_fingerprint,
                "result_revision": result_revision,
                "detail": _detail_fingerprint(result),
                "pattern_id": pattern_id,
                "evidence": evidence,
            }
        ),
        "lift_percent": _lift_percent(result, listing.get("winner_variant_index"), outcome),
    }


def _record_sort_key(record: Mapping[str, Any]) -> tuple[str, int]:
    return (record.get("ended_at") if isinstance(record.get("ended_at"), str) else "", int(record["experiment_id"]))


def _derive_patterns(records: list[dict[str, Any]], prior_patterns: Any) -> list[dict[str, Any]]:
    prior_notes = {
        pattern.get("pattern_id"): pattern.get("notes")
        for pattern in prior_patterns if isinstance(pattern, Mapping) and isinstance(pattern.get("pattern_id"), str)
    } if isinstance(prior_patterns, list) else {}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["pattern_id"], []).append(record)
    patterns = []
    for pattern_id in sorted(grouped):
        rows = sorted(grouped[pattern_id], key=_record_sort_key)
        wins = sum(row["outcome"] == "win" for row in rows)
        losses = sum(row["outcome"] == "loss" for row in rows)
        inconclusive = sum(row["outcome"] == "inconclusive" for row in rows)
        manual = sum(row["outcome"] == "manual_selection" for row in rows)
        unknown = sum(row["outcome"] == "unknown_selection" for row in rows)
        decisive = wins + losses
        hit_rate = round(wins / decisive, 6) if decisive else None
        lifts = [row["lift_percent"] for row in rows if row["outcome"] == "win" and row["lift_percent"] is not None]
        if decisive < 3:
            status = "inconclusive"
        elif hit_rate >= 0.75:
            status = "won"
        elif hit_rate <= 0.25:
            status = "lost"
        else:
            status = "mixed"
        winning_rows = [row for row in rows if row["outcome"] == "win"]
        patterns.append(
            {
                "pattern_id": pattern_id,
                "display_name": PATTERN_NAMES[pattern_id],
                "status": status,
                "tests_total": len(rows),
                "tests_won": wins,
                "tests_lost": losses,
                "tests_inconclusive": inconclusive,
                "tests_manual_selection": manual,
                "tests_unknown_selection": unknown,
                "hit_rate": hit_rate,
                "avg_lift_percent": round(sum(lifts) / len(lifts), 4) if lifts else None,
                "last_tested_at": rows[-1].get("ended_at"),
                "last_winning_block": winning_rows[-1].get("block_id") if winning_rows else None,
                "compositions_tried": [
                    {
                        "block_id": row.get("block_id"),
                        "experiment_id": row["experiment_id"],
                        "summary": row.get("summary", ""),
                        "outcome": row["outcome"],
                        "evidence": row["evidence"],
                        "ended_at": row.get("ended_at"),
                    }
                    for row in rows
                ],
                "notes": prior_notes.get(pattern_id),
            }
        )
    return patterns


def _refresh_stats(journal: dict[str, Any]) -> None:
    records = list(journal["experiments"].values())
    patterns = _derive_patterns(records, journal.get("patterns"))
    journal["patterns"] = patterns
    journal["stats"] = {
        "total_experiments_considered": len(records),
        "concluded_with_winner": sum(record["outcome"] in {"win", "loss"} for record in records),
        "concluded_without_winner": sum(record["outcome"] == "inconclusive" for record in records),
        "patterns_with_signal": sum(pattern["tests_won"] + pattern["tests_lost"] >= 1 for pattern in patterns),
    }
    journal["iteration_counter"] = max(int(journal.get("iteration_counter", 0)), len(records))


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    temporary = Path(temporary_name)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory_descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def _render_summary(journal: Mapping[str, Any]) -> str:
    site_name = journal["site"].get("name") or journal["site"]["key"]
    stats = journal["stats"]
    lines = [
        f"# Learning journal -- {site_name}",
        "",
        f"Last updated: {journal['last_updated']}",
        "",
        f"Summary: {stats['total_experiments_considered']} experiments analysed, "
        f"{stats['concluded_with_winner']} with a proven verdict, "
        f"{stats['concluded_without_winner']} inconclusive.",
        "",
    ]
    for heading, statuses in (
        ("Patterns that win on your site", {"won"}),
        ("Patterns that haven't worked here", {"lost"}),
        ("Mixed results", {"mixed"}),
        ("Not enough data yet", {"inconclusive"}),
    ):
        matching = [pattern for pattern in journal["patterns"] if pattern["status"] in statuses]
        if not matching:
            continue
        lines.extend([f"## {heading}", ""])
        for pattern in matching:
            decisive = pattern["tests_won"] + pattern["tests_lost"]
            rate = f"{pattern['hit_rate'] * 100:.0f}%" if pattern["hit_rate"] is not None else "not established"
            lines.extend([f"### {pattern['display_name']}", f"- Won {pattern['tests_won']} of {decisive} decisive tests ({rate})"])
            if pattern["avg_lift_percent"] is not None:
                lines.append(f"- Average improvement: {pattern['avg_lift_percent']:+g}%")
            if pattern["tests_manual_selection"]:
                lines.append(f"- {pattern['tests_manual_selection']} manually selected result is recorded separately from test evidence")
            if pattern["tests_unknown_selection"]:
                lines.append(f"- {pattern['tests_unknown_selection']} historical selection has no recorded decision evidence")
            lines.append("")
    coverage = journal.get("listing_coverage", {})
    if not coverage.get("complete"):
        lines.extend(["## Coverage", "", "This is a partial historical view: " + str(coverage.get("reason", "the refresh reached its stated limit")) + ".", ""])
    return "\n".join(lines)


def merge_journal(
    journal_path: Path,
    summary_path: Path,
    payload: Mapping[str, Any],
    rebuild: bool = False,
) -> dict[str, int]:
    """Merge one bounded refresh. The lock covers read, merge, and both writes."""
    site = _require_site(payload.get("site", {}))
    raw_records = payload.get("experiments", [])
    if not isinstance(raw_records, list):
        raise JournalError("experiments must be a list")
    coverage = payload.get("listing_coverage", {})
    if not isinstance(coverage, Mapping) or not isinstance(coverage.get("complete"), bool):
        raise JournalError("listing_coverage.complete must state whether history was fully covered")

    journal_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = journal_path.with_name(journal_path.name + ".lock")
    lock_descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        os.fchmod(lock_descriptor, 0o600)
        fcntl.flock(lock_descriptor, fcntl.LOCK_EX)
        journal, backup_content = _load_journal(journal_path, site, rebuild)
        if backup_content is not None:
            old_version = json.loads(backup_content).get("schema_version", "unknown")
            backup_path = journal_path.with_name(f"{journal_path.name}.schema-{old_version}.backup")
            if backup_path.exists():
                raise JournalError(f"rebuild backup already exists at {backup_path}")
            _atomic_write(backup_path, backup_content)
        added = changed = unchanged = 0
        for raw in raw_records:
            if not isinstance(raw, Mapping):
                raise JournalError("each experiment record must be an object")
            record = _normalise_record(raw)
            key = str(record["experiment_id"])
            previous = journal["experiments"].get(key)
            if isinstance(previous, Mapping) and previous.get("fingerprint") == record["fingerprint"]:
                unchanged += 1
                continue
            journal["experiments"][key] = record
            if previous is None:
                added += 1
            else:
                changed += 1
        journal["site"] = site
        journal["listing_coverage"] = dict(coverage)
        journal["last_updated"] = payload.get("observed_at") if isinstance(payload.get("observed_at"), str) else _utc_now()
        _refresh_stats(journal)
        _atomic_write(journal_path, json.dumps(journal, indent=2, ensure_ascii=False) + "\n")
        _atomic_write(summary_path, _render_summary(journal))
        return {"added": added, "changed": changed, "unchanged": unchanged}
    finally:
        try:
            fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
        finally:
            os.close(lock_descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["merge"])
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        receipt = merge_journal(args.journal, args.summary, payload, rebuild=args.rebuild)
    except (JournalError, OSError, json.JSONDecodeError) as error:
        print(f"learning journal unchanged: {error}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
