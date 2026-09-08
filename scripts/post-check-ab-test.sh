#!/usr/bin/env bash
# PostToolUse filter. Keep this advisory because hook output cannot prove the
# server-side restore or its read-back. The workflow records the response and
# verifies the block and experiment state before it reports a result.

python3 -c '
import json, sys
try:
    event = json.load(sys.stdin)
except json.JSONDecodeError:
    raise SystemExit(0)
if event.get("tool_input", {}).get("ability_name") == "accelerate/create-ab-test":
    print("A/B test creation needs a fresh block and experiment read now. Record a known response; on any timeout or malformed result, mark the outcome unknown and reconcile it. Only report restoration after the supported restore operation and read-back both match the receipt.")
'
