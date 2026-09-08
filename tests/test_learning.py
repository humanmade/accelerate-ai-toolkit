"""Behavioural tests for the local, bounded learning journal merge."""

from __future__ import annotations

import importlib.util
import json
import multiprocessing
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("learning", ROOT / "scripts" / "learning.py")
learning = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(learning)


def payload(*records, site_key="example-12345678", site_url="https://example.test"):
    return {
        "site": {"key": site_key, "name": "Example", "theme": "Example Theme", "url": site_url},
        "experiments": list(records),
        "listing_coverage": {"complete": True, "pages_fetched": 1, "pages_total": 1},
        "observed_at": "2026-09-08T00:00:00Z",
    }


def record(
    experiment_id, *, winner=1, result_revision="a", control=0.1, challenger=0.2, evidence="proven_result", annotations=None
):
    return {
        "experiment": {
            "experiment_id": experiment_id,
            "block_id": 50,
            "type": "abtest",
            "status": "completed",
            "ended_at": "2026-09-01T00:00:00Z",
            "has_winner": winner is not None,
            "winner_variant_index": winner,
            "annotations": annotations if annotations is not None else {"toolkit:pattern": "headline_clarity"},
            "result_revision": result_revision,
        },
        "pattern_id": "headline_clarity",
        "summary": "A clearer hero",
        "evidence": evidence,
        "result": {"variants": [{"conversion_rate": control}, {"conversion_rate": challenger}]},
    }


def merge_in_process(journal_name, summary_name, refresh):
    learning.merge_journal(Path(journal_name), Path(summary_name), refresh)


class LearningJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal = Path(self.tmp.name) / "journal.json"
        self.summary = Path(self.tmp.name) / "journal.md"

    def tearDown(self):
        self.tmp.cleanup()

    def read_journal(self):
        return json.loads(self.journal.read_text(encoding="utf-8"))

    def test_duplicate_refresh_keeps_one_composition(self):
        refresh = payload(record(10))
        self.assertEqual({"added": 1, "changed": 0, "unchanged": 0}, learning.merge_journal(self.journal, self.summary, refresh))
        self.assertEqual({"added": 0, "changed": 0, "unchanged": 1}, learning.merge_journal(self.journal, self.summary, refresh))
        journal = self.read_journal()
        self.assertEqual(["10"], list(journal["experiments"]))
        self.assertEqual(1, len(journal["patterns"][0]["compositions_tried"]))

    def test_changed_result_replaces_the_existing_identity(self):
        learning.merge_journal(self.journal, self.summary, payload(record(10, result_revision="one")))
        receipt = learning.merge_journal(self.journal, self.summary, payload(record(10, result_revision="two", challenger=0.3)))
        self.assertEqual({"added": 0, "changed": 1, "unchanged": 0}, receipt)
        journal = self.read_journal()
        self.assertEqual(1, journal["stats"]["total_experiments_considered"])
        self.assertEqual(200.0, journal["experiments"]["10"]["lift_percent"])
        prior_listing_fingerprint = journal["experiments"]["10"]["listing_fingerprint"]
        receipt = learning.merge_journal(
            self.journal,
            self.summary,
            payload(record(10, result_revision="two", challenger=0.3, annotations={"toolkit:pattern": "cta_copy"})),
        )
        self.assertEqual({"added": 0, "changed": 1, "unchanged": 0}, receipt)
        self.assertNotEqual(prior_listing_fingerprint, self.read_journal()["experiments"]["10"]["listing_fingerprint"])

    def test_zero_baseline_has_no_infinite_lift(self):
        learning.merge_journal(self.journal, self.summary, payload(record(10, control=0, challenger=0.2)))
        journal = self.read_journal()
        self.assertEqual("win", journal["experiments"]["10"]["outcome"])
        self.assertIsNone(journal["experiments"]["10"]["lift_percent"])
        self.assertIsNone(journal["patterns"][0]["avg_lift_percent"])

    def test_manual_selection_is_visible_but_not_test_evidence(self):
        learning.merge_journal(self.journal, self.summary, payload(record(10, evidence="manual_selection")))
        journal = self.read_journal()
        pattern = journal["patterns"][0]
        self.assertEqual("manual_selection", journal["experiments"]["10"]["outcome"])
        self.assertEqual(0, pattern["tests_won"] + pattern["tests_lost"])
        self.assertEqual(1, pattern["tests_manual_selection"])

    def test_unproven_historical_winner_is_not_counted_as_a_win(self):
        uncertain = record(10, evidence="unknown_selection")
        learning.merge_journal(self.journal, self.summary, payload(uncertain))
        pattern = self.read_journal()["patterns"][0]
        self.assertEqual("unknown_selection", self.read_journal()["experiments"]["10"]["outcome"])
        self.assertEqual(0, pattern["tests_won"] + pattern["tests_lost"])
        self.assertEqual(1, pattern["tests_unknown_selection"])

    def test_interrupted_atomic_write_keeps_the_old_journal(self):
        learning.merge_journal(self.journal, self.summary, payload(record(10)))
        original = self.journal.read_text(encoding="utf-8")
        with patch.object(learning.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                learning.merge_journal(self.journal, self.summary, payload(record(11)))
        self.assertEqual(original, self.journal.read_text(encoding="utf-8"))

    def test_concurrent_merges_keep_both_experiments(self):
        first = payload(record(10))
        second = payload(record(11))
        jobs = [
            multiprocessing.Process(target=merge_in_process, args=(str(self.journal), str(self.summary), first)),
            multiprocessing.Process(target=merge_in_process, args=(str(self.journal), str(self.summary), second)),
        ]
        for job in jobs:
            job.start()
        for job in jobs:
            job.join(10)
            self.assertEqual(0, job.exitcode)
        self.assertEqual({"10", "11"}, set(self.read_journal()["experiments"]))

    def test_site_identity_prevents_cross_contamination(self):
        learning.merge_journal(self.journal, self.summary, payload(record(10)))
        with self.assertRaisesRegex(learning.JournalError, "different site"):
            learning.merge_journal(
                self.journal,
                self.summary,
                payload(record(11), site_key="other-12345678", site_url="https://other.test"),
            )

    def test_older_schema_requires_explicit_rebuild_and_is_backed_up(self):
        legacy = {"schema_version": 3, "site": payload()["site"], "patterns": []}
        self.journal.write_text(json.dumps(legacy), encoding="utf-8")
        with self.assertRaisesRegex(learning.JournalError, "explicit bounded rebuild"):
            learning.merge_journal(self.journal, self.summary, payload(record(10)))
        learning.merge_journal(self.journal, self.summary, payload(record(10)), rebuild=True)
        self.assertEqual(4, self.read_journal()["schema_version"])
        backup = self.journal.with_name("journal.json.schema-3.backup")
        self.assertEqual(legacy, json.loads(backup.read_text(encoding="utf-8")))

    def test_new_file_is_private(self):
        learning.merge_journal(self.journal, self.summary, payload(record(10)))
        self.assertEqual(0o600, os.stat(self.journal).st_mode & 0o777)
        self.assertEqual(0o600, os.stat(self.summary).st_mode & 0o777)



if __name__ == "__main__":
    unittest.main()
