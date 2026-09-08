#!/usr/bin/env python3
"""Durable, local receipts for a confirmed Accelerate A/B-test change.

This helper deliberately has no network client.  It records the state needed
for a supported server-side restore and prevents a caller from treating an
unknown create result as permission to create a second experiment.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SAFE_SITE_KEY = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")


class RecoveryError(ValueError):
    """A receipt is missing, does not match, or cannot safely be used."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _payload_hash(payload: Any) -> str:
    return _sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def _data_root(data_root: str | Path | None = None) -> Path:
    if data_root is not None:
        return Path(data_root)
    configured = os.environ.get("ACCELERATE_TOOLKIT_DATA_DIR")
    if configured:
        return Path(configured)
    return Path.home() / ".config" / "accelerate-ai-toolkit" / "sites"


def _site_directory(site_key: str, data_root: str | Path | None = None) -> Path:
    if not isinstance(site_key, str) or not SAFE_SITE_KEY.fullmatch(site_key):
        raise RecoveryError("site key is not a valid per-site store key")
    return _data_root(data_root) / site_key


def receipt_path(site_key: str, block_id: str | int, data_root: str | Path | None = None) -> Path:
    block = str(block_id)
    if not block:
        raise RecoveryError("block id is required")
    # The block id need not be a safe filename, and is retained inside the receipt.
    return _site_directory(site_key, data_root) / "test-recovery" / f"{_sha256(block)[:24]}.json"


@contextmanager
def _receipt_lock(path: Path):
    """Serialize one block's receipt read-modify-write transitions."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    lock_path = path.with_name(path.name + ".lock")
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".receipt-", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        os.chmod(path, 0o600)
    except BaseException:
        # Do not delete an interrupted receipt with a permanent filesystem
        # operation. The private, owner-only temporary file is intentionally
        # retained for inspection or recoverable disposal.
        raise


def _read_receipt(path: Path) -> dict[str, Any]:
    try:
        mode = path.stat().st_mode & 0o777
    except FileNotFoundError as error:
        raise RecoveryError("no recovery receipt exists") from error
    if mode & 0o077:
        raise RecoveryError("recovery receipt permissions are too broad")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RecoveryError("recovery receipt cannot be read") from error
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise RecoveryError("recovery receipt has an unsupported format")
    return value


def _matching_receipt(
    site_key: str,
    block_id: str | int,
    request_id: str,
    data_root: str | Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    receipt = _read_receipt(receipt_path(site_key, block_id, data_root))
    if receipt.get("site", {}).get("key") != site_key:
        raise RecoveryError("recovery receipt belongs to a different site")
    if str(receipt.get("block", {}).get("id")) != str(block_id):
        raise RecoveryError("recovery receipt belongs to a different block")
    if receipt.get("request", {}).get("id") != request_id:
        raise RecoveryError("recovery receipt belongs to a different request")
    return receipt_path(site_key, block_id, data_root), receipt


def save_receipt(
    *,
    site_key: str,
    site_url: str,
    block_id: str | int,
    original_content: str,
    original_state: dict[str, Any],
    approved_payload: Any,
    request_id: str,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Persist an immutable pre-create receipt, or return its exact prior copy."""
    if not isinstance(site_url, str) or not site_url:
        raise RecoveryError("site URL is required")
    if not isinstance(original_content, str):
        raise RecoveryError("original content must be text")
    if not isinstance(original_state, dict):
        raise RecoveryError("original state must be an object")
    if not isinstance(request_id, str) or not request_id:
        raise RecoveryError("request id is required")

    path = receipt_path(site_key, block_id, data_root)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now(),
        "status": "prepared",
        "site": {"key": site_key, "url": site_url},
        "block": {
            "id": str(block_id),
            "original_content": original_content,
            "original_content_hash": _sha256(original_content),
            "original_state": original_state,
        },
        "request": {"id": request_id, "approved_payload_hash": _payload_hash(approved_payload)},
    }
    with _receipt_lock(path):
        if path.exists():
            existing = _read_receipt(path)
            existing_id = existing.get("request", {}).get("id")
            if existing_id == request_id:
                immutable = ("site", "block", "request")
                if all(existing.get(key) == receipt[key] for key in immutable):
                    return existing
                raise RecoveryError("same request does not match its immutable recovery receipt")
            if existing.get("status") not in {"restored", "completed"}:
                raise RecoveryError("an unresolved recovery receipt already exists for this block")
        _atomic_write(path, receipt)
        return receipt


def preflight_create(
    *,
    site_key: str,
    block_id: str | int,
    request_id: str,
    approved_payload: Any,
    current_original_content: str,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Verify the approved request still targets the exact original content."""
    _, receipt = _matching_receipt(site_key, block_id, request_id, data_root)
    if receipt.get("status") != "prepared":
        raise RecoveryError("create must not be retried; reconcile the existing receipt first")
    if receipt["request"]["approved_payload_hash"] != _payload_hash(approved_payload):
        raise RecoveryError("approved payload no longer matches the recovery receipt")
    if receipt["block"]["original_content_hash"] != _sha256(current_original_content):
        raise RecoveryError("block content changed after approval; do not overwrite it")
    return receipt


def record_create_outcome(
    *,
    site_key: str,
    block_id: str | int,
    request_id: str,
    outcome: str,
    create_result: dict[str, Any] | None = None,
    created_state_identity: dict[str, Any] | None = None,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Record a known create result or an unknown result without retrying it."""
    if outcome not in {"created", "unknown"}:
        raise RecoveryError("create outcome must be created or unknown")
    if outcome == "created":
        if not isinstance(create_result, dict) or not isinstance(create_result.get("current_content_hash"), str):
            raise RecoveryError("a known create result needs its current content hash")
        if not re.fullmatch(r"[a-f0-9]{64}", create_result["current_content_hash"]):
            raise RecoveryError("create result has an invalid current content hash")
        if not isinstance(created_state_identity, dict):
            raise RecoveryError("a known create result needs its state identity")
    path = receipt_path(site_key, block_id, data_root)
    with _receipt_lock(path):
        _, receipt = _matching_receipt(site_key, block_id, request_id, data_root)
        if receipt.get("status") != "prepared":
            raise RecoveryError("create outcome was already recorded")
        receipt["status"] = "created" if outcome == "created" else "outcome_unknown"
        if outcome == "created":
            receipt["create_result"] = {
                "current_content_hash": create_result["current_content_hash"],
                "state_identity": created_state_identity,
            }
        receipt["updated_at"] = _now()
        _atomic_write(path, receipt)
        return receipt


def record_completion_verification(
    *,
    site_key: str,
    block_id: str | int,
    request_id: str,
    observed_content: str,
    observed_state_identity: dict[str, Any],
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Archive a live test only after its created content and state read back exactly."""
    path = receipt_path(site_key, block_id, data_root)
    with _receipt_lock(path):
        _, receipt = _matching_receipt(site_key, block_id, request_id, data_root)
        if receipt.get("status") != "created":
            raise RecoveryError("only a known created test can be verified as completed")
        result = receipt.get("create_result", {})
        if (
            _sha256(observed_content) != result.get("current_content_hash")
            or observed_state_identity != result.get("state_identity")
        ):
            raise RecoveryError("created test does not match its stored result; reconcile or restore it")
        receipt["status"] = "completed"
        receipt["updated_at"] = _now()
        _atomic_write(path, receipt)
        return receipt


def restore_plan(
    *,
    site_key: str,
    block_id: str | int,
    request_id: str,
    current_content: str,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return the guarded restore data; a caller must invoke the supported producer operation."""
    _, receipt = _matching_receipt(site_key, block_id, request_id, data_root)
    if receipt.get("status") not in {"created", "outcome_unknown"}:
        raise RecoveryError("there is no created or unknown result to restore")
    return {
        "block_id": receipt["block"]["id"],
        "request_id": request_id,
        "expected_current_hash": _sha256(current_content),
        "original_content": receipt["block"]["original_content"],
        "original_state": receipt["block"]["original_state"],
    }


def record_restore_verification(
    *,
    site_key: str,
    block_id: str | int,
    request_id: str,
    observed_content: str,
    restored_state_matches: bool,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Only mark a restore complete after content and relevant state read back correctly."""
    path = receipt_path(site_key, block_id, data_root)
    with _receipt_lock(path):
        _, receipt = _matching_receipt(site_key, block_id, request_id, data_root)
        if _sha256(observed_content) != receipt["block"]["original_content_hash"] or not restored_state_matches:
            receipt["status"] = "recovery_required"
            receipt["updated_at"] = _now()
            _atomic_write(path, receipt)
            raise RecoveryError("restoration is not verified; recovery is still required")
        receipt["status"] = "restored"
        receipt["updated_at"] = _now()
        _atomic_write(path, receipt)
        return receipt


def public_status(receipt: dict[str, Any]) -> dict[str, Any]:
    """Return a safe status response without emitting original markup or state."""
    return {
        "status": receipt["status"],
        "site_key": receipt["site"]["key"],
        "block_id": receipt["block"]["id"],
        "request_id": receipt["request"]["id"],
    }


def _command_input() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        raise RecoveryError("expected one JSON object on standard input") from error
    if not isinstance(value, dict):
        raise RecoveryError("expected one JSON object on standard input")
    return value


def hook_preflight(event: dict[str, Any]) -> str:
    """Check a complete hook event if its host supplies the receipt context.

    Claude Code does not add site identity or a fresh block read to its standard
    hook event.  In that common case this is intentionally advisory rather than
    pretending the hook has verified a receipt.
    """
    tool_input = event.get("tool_input", {})
    if not isinstance(tool_input, dict) or tool_input.get("ability_name") != "accelerate/create-ab-test":
        return ""
    parameters = tool_input.get("parameters")
    if not isinstance(parameters, dict):
        # Older connector event shapes are advisory-only compatibility paths.
        parameters = tool_input.get("arguments", tool_input.get("input", {}))
    if not isinstance(parameters, dict):
        return "A/B test creation needs a durable recovery receipt before it can proceed."
    site_key = event.get("site_key") or os.environ.get("ACCELERATE_SITE_KEY")
    current_original_content = event.get("current_original_content")
    required = ("block_id", "request_id", "expected_content_hash")
    if not isinstance(site_key, str) or not isinstance(current_original_content, str) or not all(name in parameters for name in required):
        return (
            "A/B test creation needs the durable recovery receipt and a fresh block read. "
            "This hook cannot match the receipt without site and current-content context; follow the workflow preflight."
        )
    try:
        preflight_create(
            site_key=site_key,
            block_id=parameters["block_id"],
            request_id=parameters["request_id"],
            approved_payload=parameters,
            current_original_content=current_original_content,
        )
    except RecoveryError:
        # The CLI turns this into a non-zero PreToolUse result only when this
        # complete context exists. Standard connector events remain advisory.
        raise
    return "A/B test recovery receipt matches the approved request and fresh block read."


def main(argv: list[str]) -> int:
    commands = {"save", "preflight", "outcome", "verify-completion", "restore-plan", "verify-restore", "hook-preflight"}
    if len(argv) != 2 or argv[1] not in commands:
        print("usage: recovery.py {save|preflight|outcome|verify-completion|restore-plan|verify-restore|hook-preflight} < input.json", file=sys.stderr)
        return 2
    try:
        data = _command_input()
        command = argv[1]
        if command == "hook-preflight":
            try:
                message = hook_preflight(data)
            except RecoveryError as error:
                print(f"A/B test creation blocked by recovery preflight: {error}", file=sys.stderr)
                return 2
            if message:
                print(message)
            return 0
        if command == "save":
            receipt = save_receipt(**data)
            result = public_status(receipt)
        elif command == "preflight":
            receipt = preflight_create(**data)
            result = public_status(receipt)
        elif command == "outcome":
            receipt = record_create_outcome(**data)
            result = public_status(receipt)
        elif command == "verify-completion":
            receipt = record_completion_verification(**data)
            result = public_status(receipt)
        elif command == "restore-plan":
            result = restore_plan(**data)
        else:
            receipt = record_restore_verification(**data)
            result = public_status(receipt)
    except (RecoveryError, TypeError) as error:
        print(f"recovery: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
