#!/usr/bin/env bash
# PostToolUse hook filter: only output verification instructions for successful
# create-ab-test calls. For all other ability calls, exit silently so Claude
# continues uninterrupted.

INPUT=$(cat)
ABILITY=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('ability_name',''))" 2>/dev/null)

if [ "$ABILITY" = "accelerate/create-ab-test" ]; then
  echo "IMPORTANT: A/B test was just created. You MUST now verify the block content was saved correctly. Fetch the block content and check that no variant is empty (self-closing <!-- wp:altis/variant .../-->  tags with no inner content). If any variant is empty, immediately restore the backup you saved earlier and tell the user the test creation failed and the original content has been restored. Do not report success until verification passes."
fi
