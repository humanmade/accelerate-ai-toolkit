#!/usr/bin/env bash
# PreToolUse hook filter: only output a backup reminder for create-ab-test calls.
# For all other ability calls, exit silently so Claude continues uninterrupted.

INPUT=$(cat)
ABILITY=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('ability_name',''))" 2>/dev/null)

if [ "$ABILITY" = "accelerate/create-ab-test" ]; then
  echo "IMPORTANT: This is an A/B test creation call. Before proceeding, confirm you have saved a backup of the target block's current content (the full post_content of the block_id). If you have not fetched and stored the original content yet, deny this call and fetch it first."
fi
