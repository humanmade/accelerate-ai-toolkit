#!/usr/bin/env bash
# PreToolUse filter. The helper receives the hook event on standard input, so
# block markup never becomes a shell argument or is interpolated into a command.
# A standard Claude hook event lacks site identity and a fresh block read; when
# those are absent the helper accurately emits an advisory instead of claiming
# it has enforced receipt validation.

python3 "${CLAUDE_PLUGIN_ROOT}/scripts/recovery.py" hook-preflight
