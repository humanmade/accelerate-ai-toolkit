---
description: Check whether the Accelerate AI Toolkit is connected to your WordPress site and able to fetch data. Diagnoses the specific failure layer if something is wrong.
---

Run a layered connection diagnostic on the Accelerate AI Toolkit. Check each layer in order and **stop at the first failure** — report the specific problem and its fix, not a generic "run /accelerate-connect".

## Layer 1 — Environment variables

Use the Bash tool:

```bash
echo "WP_API_URL=${WP_API_URL:-NOT_SET}" && echo "WP_API_USERNAME=${WP_API_USERNAME:-NOT_SET}" && echo "WP_API_PASSWORD=${WP_API_PASSWORD:+SET}"
```

If any variable is `NOT_SET`:

```
❌ Credentials not loaded
   Missing: [list which variables are missing]
   Fix: run /accelerate-connect to set up your site credentials, then restart your agent session.
```

Stop here. Do not proceed to further layers.

## Layer 2 — npx availability

Use the Bash tool:

```bash
command -v npx 2>/dev/null && npx --version 2>&1 | head -1 || echo "NOT_FOUND"
```

If npx is not found or returns unexpected output:

```
❌ Cannot start the site connector
   The `npx` command is missing or being intercepted by another tool in your shell.
   Fix: open a regular terminal and run `npx --version`. If it works there but not here,
   see the troubleshooting section in the installation guide.
```

Stop here.

## Layer 3 — Site reachability

Use the Bash tool:

```bash
curl -s -o /dev/null -w '%{http_code}' "$WP_API_URL/wp-json/" 2>/dev/null
```

If the response is not `200`:

```
❌ Cannot reach your site
   URL: [WP_API_URL]
   Response: [http status or "no response"]
   Fix: check that the URL is correct and the site is reachable in a browser.
   The URL should be the site root (e.g. https://example.com) with no /wp-json path.
```

Stop here.

## Layer 4 — Authentication

Use the Bash tool:

```bash
curl -s -o /dev/null -w '%{http_code}' -u "$WP_API_USERNAME:$WP_API_PASSWORD" "$WP_API_URL/wp-json/wp/v2/users/me" 2>/dev/null
```

If the response is `401` or `403`:

```
❌ Authentication failed
   Your application password was rejected by the site. It may be wrong, expired, or revoked.
   Fix: run /accelerate-connect and generate a fresh application password.
```

Stop here.

## Layer 5 — MCP endpoint

Use the Bash tool:

```bash
DEFAULT=$(curl -s -o /dev/null -w '%{http_code}' -u "$WP_API_USERNAME:$WP_API_PASSWORD" "$WP_API_URL/wp-json/wp/v2/wpmcp" 2>/dev/null)
ADAPTER=$(curl -s -o /dev/null -w '%{http_code}' -u "$WP_API_USERNAME:$WP_API_PASSWORD" "$WP_API_URL/wp-json/mcp/mcp-adapter-default-server" 2>/dev/null)
echo "default=$DEFAULT adapter=$ADAPTER"
```

If `default` is `404` and `adapter` is `200` or `401`:

```
❌ Endpoint mismatch
   Your site's WordPress connector plugin uses a different address than the toolkit expects.
   This is common with recent connector plugin versions.
   Fix: run /accelerate-connect — the setup wizard detects this and provides instructions
   for your site administrator to resolve it.
```

If both are `404`:

```
❌ No connection point found on your site
   Neither expected address responded. This usually means Accelerate isn't installed,
   or the Abilities feature hasn't been turned on yet.
   Fix: check that Accelerate is active on your site and the Abilities feature is enabled.
   See the installation guide for instructions.
```

Stop here.

## Layer 6 — MCP tool availability

Check whether the `mcp__wordpress__mcp-adapter-execute-ability` tool is available in this session.

If it is not available but all previous layers passed:

```
❌ Site is reachable but the connector isn't running
   Your credentials and site are fine, but the background connector process hasn't started.
   Fix: restart your agent session (close and reopen Claude Code or Codex). The connector
   starts automatically when the session begins.
```

Stop here.

## Layer 7 — Live data check

If all layers pass, call `accelerate/get-site-context` with `include_blocks: false` to grab basic site info, and call `accelerate/get-audience-fields` as a capability ping.

Present the healthy status:

```
✅ Connected to [site name]
   URL: [site URL]
   Capabilities available: [count, e.g. "38 Accelerate capabilities"]
   Ready for questions.
```

If the capability call fails with a permission error:

```
⚠️  Connected to [site name] with limited access
   URL: [site URL]
   Your account doesn't have permission for some features.
   Most analytics and testing features need Editor access or higher.
   Ask your site administrator to check your WordPress role.
```

## Output rules

- Keep the final output to **one status block** — whichever layer you stopped at.
- Use ✅, ❌, or ⚠️ as the status indicator.
- Always include a **Fix:** line with a specific action.
- Never show raw HTTP status codes, curl output, or technical details to the user. Translate everything into plain English.
- This is a diagnostic, not a report. Be concise.
