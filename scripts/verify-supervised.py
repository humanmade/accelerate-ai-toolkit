#!/usr/bin/env python3
"""Validate a recorded supervised Accelerate improvement-cycle receipt.

Usage: python3 scripts/verify-supervised.py [receipt.json|-]
"""

import json
import re
import sys
from hashlib import sha256
from pathlib import Path


REQUIRED_STATES = (
    "connect", "choose", "approve", "create", "observe", "resolve", "apply", "learn"
)
PROVENANCE = {"synthetic", "live"}
HASH = re.compile(r"sha256:[0-9a-f]{64}$")
FAILURE_ACTIONS = {
    "empty_or_partial_response": "withheld",
    "permission_denied": "withheld",
    "untrusted_page_instruction": "withheld",
    "concurrent_edit": "withheld",
    "interrupted_or_ambiguous_write": "recovery_required",
    "recovery_failure": "escalated",
    "already_applied_winner": "idempotent",
}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def evidence_id(value):
    return nonempty(value) or isinstance(value, int) and not isinstance(value, bool)


def verify(receipt, base):
    base = Path(base).resolve()
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    require(isinstance(receipt, dict), "receipt must be an object")
    if not isinstance(receipt, dict):
        return errors
    require(receipt.get("format") == "accelerate-supervised-receipt/v1", "unsupported receipt format")
    provenance = receipt.get("provenance")
    require(isinstance(provenance, dict), "missing provenance")
    if isinstance(provenance, dict):
        kind = provenance.get("kind")
        require(kind in PROVENANCE, "provenance.kind must be synthetic or live")
        for field in ("recorded_at", "toolkit_revision", "producer_revision", "wordpress_version", "connector_version", "mcp_adapter_version", "host_version"):
            require(nonempty(provenance.get(field)), f"missing provenance.{field}")

    identity = receipt.get("identity")
    require(isinstance(identity, dict), "missing identity")
    if isinstance(identity, dict):
        require(nonempty(identity.get("run_id")), "missing identity.run_id")
        require(evidence_id(identity.get("experiment_id")), "missing identity.experiment_id")
        require(nonempty(identity.get("site_url")), "missing identity.site_url")
        require(evidence_id(identity.get("block_id")), "missing identity.block_id")

    states = receipt.get("states")
    require(isinstance(states, list), "states must be a list")
    if isinstance(states, list):
        observed = {}
        ordered = []
        for item in states:
            if not isinstance(item, dict) or not nonempty(item.get("state")):
                errors.append("every state must have a name")
                continue
            state = item["state"]
            if state in REQUIRED_STATES:
                ordered.append(state)
            if state in observed:
                errors.append(f"duplicate state: {state}")
            observed[state] = item
        for state in REQUIRED_STATES:
            require(observed.get(state, {}).get("status") == "complete", f"state not complete: {state}")
            require(nonempty(observed.get(state, {}).get("evidence_id")), f"missing state evidence: {state}")
        require(ordered == list(REQUIRED_STATES), "workflow states are out of order")

    control = receipt.get("control")
    challenger = receipt.get("challenger")
    for name, arm in (("control", control), ("challenger", challenger)):
        require(isinstance(arm, dict), f"missing {name}")
        if isinstance(arm, dict):
            require(isinstance(arm.get("content_hash"), str) and HASH.fullmatch(arm["content_hash"]), f"invalid {name}.content_hash")
    if isinstance(control, dict) and isinstance(challenger, dict):
        require(control.get("content_hash") != challenger.get("content_hash"), "control and challenger content hashes must differ")
    if isinstance(challenger, dict):
        approval = challenger.get("approval")
        require(isinstance(approval, dict), "missing challenger.approval")
        if isinstance(approval, dict):
            for field in ("approved_at", "approved_by", "operation_id"):
                require(nonempty(approval.get(field)), f"missing challenger.approval.{field}")

    exposure = receipt.get("exposure")
    require(isinstance(exposure, dict), "missing exposure")
    if isinstance(exposure, dict):
        for arm_name in ("control", "challenger"):
            arm = exposure.get(arm_name)
            require(isinstance(arm, dict), f"missing exposure.{arm_name}")
            if isinstance(arm, dict):
                count = arm.get("observed_count")
                require(isinstance(count, int) and count > 0, f"exposure.{arm_name}.observed_count must be a positive integer")
                require(nonempty(arm.get("observation_id")), f"missing exposure.{arm_name}.observation_id")

    application = receipt.get("application")
    require(isinstance(application, dict), "missing application")
    if isinstance(application, dict):
        applied = application.get("applied_arm")
        require(applied in {"control", "challenger"}, "application.applied_arm must be control or challenger")
        readback = application.get("readback_content_hash")
        require(nonempty(readback), "missing application.readback_content_hash")
        require(isinstance(readback, str) and HASH.fullmatch(readback), "invalid application.readback_content_hash")
        expected = control.get("content_hash") if applied == "control" and isinstance(control, dict) else challenger.get("content_hash") if applied == "challenger" and isinstance(challenger, dict) else None
        if expected:
            require(readback == expected, "application readback hash does not match applied arm")
        require(nonempty(application.get("operation_id")), "missing application.operation_id")
        require(nonempty(application.get("outcome")), "missing application.outcome")

    journal = receipt.get("journal")
    require(isinstance(journal, dict), "missing journal")
    if isinstance(journal, dict):
        require(nonempty(journal.get("entry_id")), "missing journal.entry_id")
        require(nonempty(journal.get("outcome")), "missing journal.outcome")
        if isinstance(identity, dict):
            require(journal.get("experiment_id") == identity.get("experiment_id"), "journal experiment_id does not match identity")
        if isinstance(application, dict):
            require(journal.get("applied_arm") == application.get("applied_arm"), "journal applied_arm does not match application")
            require(journal.get("outcome") == application.get("outcome"), "journal outcome does not match application")

    failures = receipt.get("failure_cases")
    require(isinstance(failures, dict), "missing failure_cases")
    if isinstance(failures, dict):
        for case, action in FAILURE_ACTIONS.items():
            result = failures.get(case)
            require(isinstance(result, dict), f"missing failure_cases.{case}")
            if isinstance(result, dict):
                require(result.get("action") == action, f"failure_cases.{case}.action must be {action}")
                require(nonempty(result.get("evidence_id")), f"missing failure_cases.{case}.evidence_id")

    for surface in ("editor", "frontend"):
        proof = receipt.get(surface)
        require(isinstance(proof, dict), f"missing {surface} proof")
        if isinstance(proof, dict):
            for viewport in ("desktop", "narrow"):
                item = proof.get(viewport)
                require(isinstance(item, dict) and nonempty(item.get("proof_id")), f"missing {surface}.{viewport}.proof_id")
                if isinstance(item, dict):
                    require(item.get("status") == "observed", f"{surface}.{viewport} proof is not observed")

    evidence = receipt.get("evidence")
    require(isinstance(evidence, dict), "missing evidence map")
    references = []
    if isinstance(states, list):
        references += [item.get("evidence_id") for item in states if isinstance(item, dict)]
    if isinstance(challenger, dict) and isinstance(challenger.get("approval"), dict):
        references.append(challenger["approval"].get("operation_id"))
    if isinstance(exposure, dict):
        references += [arm.get("observation_id") for arm in exposure.values() if isinstance(arm, dict)]
    if isinstance(application, dict):
        references.append(application.get("operation_id"))
    if isinstance(journal, dict):
        references.append(journal.get("entry_id"))
    if isinstance(failures, dict):
        references += [result.get("evidence_id") for result in failures.values() if isinstance(result, dict)]
    for surface in ("editor", "frontend"):
        if isinstance(receipt.get(surface), dict):
            references += [item.get("proof_id") for item in receipt[surface].values() if isinstance(item, dict)]
    for reference in references:
        item = evidence.get(str(reference)) if isinstance(evidence, dict) else None
        require(isinstance(item, dict), f"missing evidence artifact: {reference}")
        if not isinstance(item, dict):
            continue
        path, digest = item.get("path"), item.get("sha256")
        valid_path = isinstance(path, str) and path and not Path(path).is_absolute() and ".." not in Path(path).parts
        require(valid_path, f"invalid evidence path: {reference}")
        require(isinstance(digest, str) and HASH.fullmatch(digest), f"invalid evidence hash: {reference}")
        if valid_path and isinstance(digest, str) and HASH.fullmatch(digest):
            artifact = (base / path).resolve()
            try:
                artifact.relative_to(base)
                actual = "sha256:" + sha256(artifact.read_bytes()).hexdigest()
                require(actual == digest, f"evidence hash mismatch: {reference}")
            except (OSError, ValueError):
                errors.append(f"missing evidence artifact: {reference}")
    return errors


def main(argv):
    if len(argv) > 3:
        print("usage: verify-supervised.py [receipt.json|-] [artifact-directory]", file=sys.stderr)
        return 2
    source = argv[1] if len(argv) >= 2 else "-"
    base = Path(argv[2]) if len(argv) == 3 else Path(source).parent
    if source == "-" and len(argv) != 3:
        print("INVALID: stdin receipts require an artifact directory", file=sys.stderr)
        return 2
    try:
        raw = sys.stdin.read() if source == "-" else Path(source).read_text()
        receipt = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: cannot read receipt: {exc}", file=sys.stderr)
        return 2
    errors = verify(receipt, base.resolve())
    if errors:
        print("INVALID supervised receipt:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print("VALID supervised receipt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
