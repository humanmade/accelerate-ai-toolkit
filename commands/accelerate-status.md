---
description: Check whether the Accelerate AI Toolkit is connected to your WordPress site and able to fetch data.
---

Run a connection health check on the Accelerate AI Toolkit. Specifically:

1. Check whether the `mcp__wordpress__mcp-adapter-execute-ability` tool is available in this session. If it isn't, the MCP server hasn't started — tell the user the connection isn't wired up and suggest running `/accelerate-connect` followed by restarting their agent session (Claude Code or Codex).

2. If the tool is available, call `accelerate/get-audience-fields` (no required inputs, cheap and safe) as a ping. If it returns data, the connection is live.

3. Also call `accelerate/get-site-context` with `include_blocks: false` to grab basic site info (site name, URL) for the status report.

4. Present a single short status block:

```
## Accelerate connection

✅ Connected to [site name]
   URL: [site URL]
   Capabilities available: [count, e.g. "38 Accelerate capabilities"]
   Ready for questions.
```

Or, if something is wrong:

```
## Accelerate connection

❌ Not connected
   Reason: [what went wrong in plain English]
   Fix: run /accelerate-connect to set up credentials, then restart your agent session.
```

Keep the response under ~10 lines. This is a health check, not a report.

**Common failure modes to handle:**
- MCP server not running → tell them to run `/accelerate-connect` and then restart their agent session
- Authentication error → application password is wrong or expired; tell them to regenerate it via `/accelerate-connect`
- 404 on the endpoint → either Accelerate isn't installed on the site, the Abilities API feature flag isn't enabled, or the `WP_API_URL` is wrong (it must be the site root, e.g. `https://example.com`, with no `/wp-json/...` path)
- Permission error → the WordPress user account needs `edit_posts` for analytics and experimentation, or `manage_options` for broadcasts and exports; tell them to ask a site admin to grant an appropriate role
