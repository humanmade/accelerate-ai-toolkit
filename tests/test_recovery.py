#!/usr/bin/env python3
"""Focused coverage for scripts/recovery.py."""

from __future__ import annotations

import json
import multiprocessing
import os
import queue
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import recovery  # noqa: E402


def _race_save_worker(root: str, request_id: str, entered_write, release_write, results) -> None:
    """Hold the first write so an unlocked implementation deterministically races."""
    original_write = recovery._atomic_write

    def held_write(path, value) -> None:
        entered_write.put(request_id)
        if not release_write.wait(timeout=5):
            raise RuntimeError("test did not release receipt write")
        original_write(path, value)

    recovery._atomic_write = held_write
    try:
        recovery.save_receipt(
            site_key="example-co-theme-a1b2c3d4",
            site_url="https://example.test",
            block_id="race-block",
            original_content="original",
            original_state={"experiment": None},
            approved_payload={"request": request_id},
            request_id=request_id,
            data_root=root,
        )
    except recovery.RecoveryError:
        results.put((request_id, "rejected"))
    else:
        results.put((request_id, "saved"))


class RecoveryReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.kwargs = {
            "site_key": "example-co-theme-a1b2c3d4",
            "site_url": "https://example.test",
            "block_id": "42",
            "original_content": "<!-- wp:paragraph --><p>Original</p><!-- /wp:paragraph -->",
            "original_state": {"experiment": None},
            "approved_payload": {"variants": [{"content": "Original"}, {"content": "Challenger"}]},
            "request_id": "request-123",
            "data_root": self.root,
        }

    def tearDown(self) -> None:
        subprocess.run(["trash", str(self.root)], check=True)

    def save(self) -> dict:
        return recovery.save_receipt(**self.kwargs)

    def created_result(self) -> dict:
        return {"current_content_hash": recovery._sha256("created markup")}

    def created_identity(self) -> dict:
        return {"experiment_id": 77, "request_id": "request-123"}

    def test_receipt_is_private_and_reloads_after_restart(self) -> None:
        self.save()
        path = recovery.receipt_path(self.kwargs["site_key"], self.kwargs["block_id"], self.root)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)

        receipt = recovery.preflight_create(
            site_key=self.kwargs["site_key"],
            block_id="42",
            request_id="request-123",
            approved_payload=self.kwargs["approved_payload"],
            current_original_content=self.kwargs["original_content"],
            data_root=self.root,
        )
        self.assertEqual(receipt["status"], "prepared")

    def test_changed_original_blocks_create(self) -> None:
        self.save()
        with self.assertRaisesRegex(recovery.RecoveryError, "changed after approval"):
            recovery.preflight_create(
                site_key=self.kwargs["site_key"], block_id="42", request_id="request-123",
                approved_payload=self.kwargs["approved_payload"], current_original_content="A concurrent edit",
                data_root=self.root,
            )

    def test_wrong_site_or_request_cannot_use_receipt(self) -> None:
        self.save()
        with self.assertRaises(recovery.RecoveryError):
            recovery.preflight_create(
                site_key="another-site-a1b2c3d4", block_id="42", request_id="request-123",
                approved_payload=self.kwargs["approved_payload"], current_original_content=self.kwargs["original_content"],
                data_root=self.root,
            )
        with self.assertRaisesRegex(recovery.RecoveryError, "different request"):
            recovery.preflight_create(
                site_key=self.kwargs["site_key"], block_id="42", request_id="other-request",
                approved_payload=self.kwargs["approved_payload"], current_original_content=self.kwargs["original_content"],
                data_root=self.root,
            )

    def test_unknown_outcome_never_allows_a_second_create(self) -> None:
        self.save()
        recovery.record_create_outcome(
            site_key=self.kwargs["site_key"], block_id="42", request_id="request-123", outcome="unknown", data_root=self.root,
        )
        with self.assertRaisesRegex(recovery.RecoveryError, "must not be retried"):
            recovery.preflight_create(
                site_key=self.kwargs["site_key"], block_id="42", request_id="request-123",
                approved_payload=self.kwargs["approved_payload"], current_original_content=self.kwargs["original_content"],
                data_root=self.root,
            )

    def test_same_request_save_does_not_reset_an_unknown_outcome(self) -> None:
        self.save()
        recovery.record_create_outcome(
            site_key=self.kwargs["site_key"], block_id="42", request_id="request-123", outcome="unknown", data_root=self.root,
        )
        receipt = self.save()
        self.assertEqual(receipt["status"], "outcome_unknown")

    def test_recovery_required_blocks_a_replacement_request(self) -> None:
        self.save()
        recovery.record_create_outcome(
            site_key=self.kwargs["site_key"], block_id="42", request_id="request-123", outcome="created",
            create_result=self.created_result(), created_state_identity=self.created_identity(), data_root=self.root,
        )
        with self.assertRaises(recovery.RecoveryError):
            recovery.record_restore_verification(
                site_key=self.kwargs["site_key"], block_id="42", request_id="request-123",
                observed_content="still changed", restored_state_matches=False, data_root=self.root,
            )
        replacement = dict(self.kwargs, request_id="request-456")
        with self.assertRaisesRegex(recovery.RecoveryError, "unresolved"):
            recovery.save_receipt(**replacement)

    def test_restore_is_not_claimed_until_content_and_state_match(self) -> None:
        self.save()
        recovery.record_create_outcome(
            site_key=self.kwargs["site_key"], block_id="42", request_id="request-123", outcome="created",
            create_result=self.created_result(), created_state_identity=self.created_identity(), data_root=self.root,
        )
        with self.assertRaisesRegex(recovery.RecoveryError, "not verified"):
            recovery.record_restore_verification(
                site_key=self.kwargs["site_key"], block_id="42", request_id="request-123",
                observed_content="still changed", restored_state_matches=False, data_root=self.root,
            )
        path = recovery.receipt_path(self.kwargs["site_key"], "42", self.root)
        self.assertEqual(recovery._read_receipt(path)["status"], "recovery_required")

    def test_restore_plan_binds_current_hash_and_original_state(self) -> None:
        self.save()
        recovery.record_create_outcome(
            site_key=self.kwargs["site_key"], block_id="42", request_id="request-123", outcome="created",
            create_result=self.created_result(), created_state_identity=self.created_identity(), data_root=self.root,
        )
        plan = recovery.restore_plan(
            site_key=self.kwargs["site_key"], block_id="42", request_id="request-123",
            current_content="changed", data_root=self.root,
        )
        self.assertEqual(plan["original_content"], self.kwargs["original_content"])
        self.assertEqual(plan["original_state"], {"experiment": None})
        self.assertNotEqual(plan["expected_current_hash"], recovery._sha256(self.kwargs["original_content"]))

    def test_only_verified_completion_allows_a_new_request(self) -> None:
        self.save()
        recovery.record_create_outcome(
            site_key=self.kwargs["site_key"], block_id="42", request_id="request-123", outcome="created",
            create_result=self.created_result(), created_state_identity=self.created_identity(), data_root=self.root,
        )
        receipt = recovery.record_completion_verification(
            site_key=self.kwargs["site_key"], block_id="42", request_id="request-123",
            observed_content="created markup", observed_state_identity=self.created_identity(), data_root=self.root,
        )
        self.assertEqual(receipt["status"], "completed")
        replacement = dict(self.kwargs, request_id="request-456")
        self.assertEqual(recovery.save_receipt(**replacement)["status"], "prepared")

    def test_hook_preflight_uses_recorded_parameters_envelope(self) -> None:
        parameters = {
            "block_id": 42,
            "request_id": "request-123",
            "expected_content_hash": recovery._sha256(self.kwargs["original_content"]),
            "variants": [{"content": "Original"}, {"content": "Challenger"}],
        }
        receipt_input = dict(self.kwargs, approved_payload=parameters)
        recovery.save_receipt(**receipt_input)
        recorded_envelope = {
            "tool_input": {
                "ability_name": "accelerate/create-ab-test",
                "parameters": parameters,
            },
            "site_key": self.kwargs["site_key"],
            "current_original_content": self.kwargs["original_content"],
        }
        command = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts" / "recovery.py"), "hook-preflight"]
        environment = dict(os.environ, ACCELERATE_TOOLKIT_DATA_DIR=str(self.root))
        with patch.dict(os.environ, {"ACCELERATE_TOOLKIT_DATA_DIR": str(self.root)}):
            self.assertIn("matches", recovery.hook_preflight(recorded_envelope))
            allowed = subprocess.run(
                command, input=json.dumps(recorded_envelope), text=True, capture_output=True, env=environment, check=False,
            )
            self.assertEqual(allowed.returncode, 0)
            recorded_envelope["current_original_content"] = "concurrent edit"
            with self.assertRaisesRegex(recovery.RecoveryError, "changed after approval"):
                recovery.hook_preflight(recorded_envelope)
            blocked = subprocess.run(
                command, input=json.dumps(recorded_envelope), text=True, capture_output=True, env=environment, check=False,
            )
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("blocked by recovery preflight", blocked.stderr)

    def test_two_processes_cannot_replace_a_new_receipt(self) -> None:
        context = multiprocessing.get_context("spawn")
        entered_write = context.Queue()
        release_write = context.Event()
        results = context.Queue()
        first = context.Process(target=_race_save_worker, args=(str(self.root), "request-a", entered_write, release_write, results))
        second = context.Process(target=_race_save_worker, args=(str(self.root), "request-b", entered_write, release_write, results))
        first.start()
        self.assertEqual(entered_write.get(timeout=5), "request-a")
        second.start()
        try:
            # With no lock, the second process reaches the held write too; this
            # test then releases both and observes two incorrect successes.
            try:
                entered_write.get(timeout=1)
            except queue.Empty:
                pass
            release_write.set()
            first.join(timeout=5)
            second.join(timeout=5)
        finally:
            release_write.set()
        self.assertEqual(first.exitcode, 0)
        self.assertEqual(second.exitcode, 0)
        outcomes = [results.get(timeout=5), results.get(timeout=5)]
        saved = [request_id for request_id, outcome in outcomes if outcome == "saved"]
        self.assertEqual(len(saved), 1)
        receipt = recovery._read_receipt(recovery.receipt_path(self.kwargs["site_key"], "race-block", self.root))
        self.assertEqual(receipt["request"]["id"], saved[0])


if __name__ == "__main__":
    unittest.main()
