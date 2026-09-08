import copy
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE = Path(__file__).parents[1] / "scripts" / "verify-supervised.py"
SPEC = importlib.util.spec_from_file_location("verify_supervised", MODULE)
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def recorded_receipt(root):
    receipt = {
        "format": "accelerate-supervised-receipt/v1",
        "provenance": {
            "kind": "synthetic", "recorded_at": "2026-09-08T03:15:00Z",
            "toolkit_revision": "e136dbb", "producer_revision": "3e9f3b7",
            "wordpress_version": "6.9.0", "connector_version": "1.0.0",
            "mcp_adapter_version": "1.0.0", "host_version": "1.0.0",
        },
        "identity": {"run_id": "run-104", "experiment_id": 77, "site_url": "https://staging.example.test", "block_id": 12},
        "states": [
            {"state": state, "status": "complete", "evidence_id": f"state-{index}"}
            for index, state in enumerate(VERIFY.REQUIRED_STATES, 1)
        ],
        "control": {"content_hash": "sha256:" + "a" * 64},
        "challenger": {
            "content_hash": "sha256:" + "b" * 64,
            "approval": {"approved_at": "2026-09-08T03:12:00Z", "approved_by": "operator-31", "operation_id": "approval-8"},
        },
        "exposure": {
            "control": {"observed_count": 18, "observation_id": "sample-44"},
            "challenger": {"observed_count": 17, "observation_id": "sample-45"},
        },
        "application": {"applied_arm": "challenger", "readback_content_hash": "sha256:" + "b" * 64, "operation_id": "apply-19", "outcome": "winner"},
        "journal": {"entry_id": "journal-29", "experiment_id": 77, "applied_arm": "challenger", "outcome": "winner"},
        "failure_cases": {
            case: {"action": action, "evidence_id": f"case-{index}"}
            for index, (case, action) in enumerate(VERIFY.FAILURE_ACTIONS.items(), 1)
        },
        "editor": {"desktop": {"proof_id": "editor-desktop-10", "status": "observed"}, "narrow": {"proof_id": "editor-narrow-10", "status": "observed"}},
        "frontend": {"desktop": {"proof_id": "front-desktop-10", "status": "observed"}, "narrow": {"proof_id": "front-narrow-10", "status": "observed"}},
    }
    references = [item["evidence_id"] for item in receipt["states"]]
    references += ["approval-8", "sample-44", "sample-45", "apply-19", "journal-29"]
    references += [item["evidence_id"] for item in receipt["failure_cases"].values()]
    references += [item["proof_id"] for surface in ("editor", "frontend") for item in receipt[surface].values()]
    receipt["evidence"] = {}
    for reference in references:
        path = Path("evidence") / f"{reference}.txt"
        artifact = root / path
        artifact.parent.mkdir(exist_ok=True)
        artifact.write_text(f"recorded evidence: {reference}\n")
        receipt["evidence"][reference] = {
            "path": str(path),
            "sha256": "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
        }
    return receipt


class SupervisedReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.receipt = recorded_receipt(self.root)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_complete_recorded_receipt_is_accepted(self):
        self.assertEqual(VERIFY.verify(self.receipt, self.root), [])

    def test_missing_exposure_is_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["exposure"]["challenger"]["observed_count"] = 0
        self.assertIn("exposure.challenger.observed_count must be a positive integer", VERIFY.verify(receipt, self.root))

    def test_contradictory_application_and_journal_are_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["application"]["readback_content_hash"] = "sha256:" + "a" * 64
        receipt["journal"]["experiment_id"] = "experiment-other"
        errors = VERIFY.verify(receipt, self.root)
        self.assertIn("application readback hash does not match applied arm", errors)
        self.assertIn("journal experiment_id does not match identity", errors)

    def test_incomplete_or_duplicate_state_is_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["states"][-1]["status"] = "pending"
        receipt["states"].append({"state": "create", "status": "complete"})
        errors = VERIFY.verify(receipt, self.root)
        self.assertIn("state not complete: learn", errors)
        self.assertIn("duplicate state: create", errors)

    def test_unsafe_failure_handling_is_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["failure_cases"]["already_applied_winner"]["action"] = "create_again"
        self.assertIn(
            "failure_cases.already_applied_winner.action must be idempotent",
            VERIFY.verify(receipt, self.root),
        )

    def test_out_of_order_states_are_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["states"][3], receipt["states"][4] = receipt["states"][4], receipt["states"][3]
        self.assertIn("workflow states are out of order", VERIFY.verify(receipt, self.root))

    def test_missing_or_unobserved_artifacts_are_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["evidence"]["apply-19"]["sha256"] = "sha256:" + "0" * 64
        receipt["evidence"]["state-1"]["path"] = "../outside.txt"
        receipt["frontend"]["narrow"]["status"] = "unavailable"
        errors = VERIFY.verify(receipt, self.root)
        self.assertIn("evidence hash mismatch: apply-19", errors)
        self.assertIn("invalid evidence path: state-1", errors)
        self.assertIn("frontend.narrow proof is not observed", errors)

    def test_unreferenced_evidence_is_still_verified(self):
        receipt = copy.deepcopy(self.receipt)
        artifact = self.root / "evidence" / "performance.json"
        artifact.write_text("recorded performance\n")
        receipt["evidence"]["performance"] = {
            "path": "evidence/performance.json",
            "sha256": "sha256:" + "0" * 64,
        }
        self.assertIn("evidence hash mismatch: performance", VERIFY.verify(receipt, self.root))

    def test_receipt_path_is_accepted(self):
        receipt_path = self.root / "receipt.json"
        receipt_path.write_text(json.dumps(self.receipt))
        self.assertEqual(VERIFY.main(["verify-supervised.py", str(receipt_path)]), 0)

    def test_receipt_stdin_is_accepted(self):
        with patch.object(sys, "stdin", io.StringIO(json.dumps(self.receipt))):
            self.assertEqual(VERIFY.main(["verify-supervised.py", "-", str(self.root)]), 0)
