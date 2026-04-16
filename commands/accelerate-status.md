---
description: Check whether the Accelerate AI Toolkit is connected to your WordPress site and able to fetch data. Diagnoses the specific failure layer if something is wrong.
---

Run a layered connection diagnostic on the Accelerate AI Toolkit. Check each layer in order and **stop at the first failure** -- report the specific problem and its fix, not a generic "run /accelerate-connect".

## Layer 1 -- Credentials

Use the Bash tool:

```bash
echo "WP_API_URL=${WP_API_URL:-NOT_SET}" && echo "WP_API_USERNAME=${WP_API_USERNAME:-NOT_SET}" && echo "WP_API_PASSWORD=${WP_API_PASSWORD:+SET}"
```

If any variable is `NOT_SET`:

```
❌ Credentials not loaded
   Missing: [list which are missing, in plain English: "site address", "username", or "password"]
   Fix: run /accelerate-connect to set up your site credentials, then restart your agent session.
```

Stop here. Do not proceed to further layers.

## Layer 2 -- Node.js connector

Use the Bash tool:

```bash
NPX_PATH=$(command -v npx 2>/dev/null)
NPX_VER=$(npx --version 2>&1 | head -1)
NPX_REAL=$(realpath "$NPX_PATH" 2>/dev/null || echo "$NPX_PATH")
echo "path=$NPX_REAL version=$NPX_VER"
```

Check both:
1. The version output looks like a semver number (e.g. `10.8.2`), not an error
2. The resolved path is inside a standard Node.js location (contains `node`, `npm`, `nvm`, `fnm`, `volta`, or is in `/usr/local/bin`, `/usr/bin`, or a Homebrew prefix)

If npx is missing, returns a non-semver version, or resolves to an unexpected location:

```
❌ Cannot start the site connector
   The toolkit uses a Node.js tool to connect to your site, but it doesn't appear to be
   available in your current shell -- another tool may be intercepting it.
   Fix: open a regular terminal and run `npx --version`. If it shows a version number there,
   see the troubleshooting section in the installation guide for how to fix this.
```

Stop here.

## Layer 3 -- Site reachability

Use the Bash tool:

```bash
curl -s -o /dev/null -w '%{http_code}' "$WP_API_URL/wp-json/" 2>/dev/null
```

If the response is not `200`:

```
❌ Cannot reach your site
   URL: [the site address, without showing the variable name]
   Fix: check that the address is correct and the site is reachable in a browser.
   It should be the site root (e.g. https://example.com) with no extra path.
```

Stop here.

## Layer 4 -- Authentication

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

## Layer 5a -- Accelerate installed

Use the Bash tool:

```bash
curl -s -o /dev/null -w '%{http_code}' -u "$WP_API_USERNAME:$WP_API_PASSWORD" "$WP_API_URL/wp-json/accelerate/v1" 2>/dev/null
```

If the response is `404`:

```
❌ Accelerate not found on your site
   Your site is reachable and your credentials work, but Accelerate doesn't appear to be
   active or the Abilities feature isn't turned on yet.
   Fix: check that Accelerate is installed and active in your WordPress admin, and that
   the Abilities feature is enabled. See the installation guide for instructions.
```

Stop here.

## Layer 5b -- Connection address

Use the Bash tool:

```bash
DEFAULT=$(curl -s -o /dev/null -w '%{http_code}' -u "$WP_API_USERNAME:$WP_API_PASSWORD" "$WP_API_URL/wp-json/wp/v2/wpmcp" 2>/dev/null)
ADAPTER=$(curl -s -o /dev/null -w '%{http_code}' -u "$WP_API_USERNAME:$WP_API_PASSWORD" "$WP_API_URL/wp-json/mcp/mcp-adapter-default-server" 2>/dev/null)
echo "default=$DEFAULT adapter=$ADAPTER"
```

If `default` is `404` and `adapter` is `200` or `401`:

```
❌ Connection address mismatch
   Accelerate is running on your site, but the WordPress connector is using a different
   address than the toolkit expects. This is common with recent connector versions.
   Fix: run /accelerate-connect -- the setup wizard detects this and provides instructions
   for your site administrator to resolve it.
```

If both are `404`:

```
❌ WordPress connector not responding
   Accelerate is running but the WordPress connector isn't registered. This usually means
   it needs to be activated separately.
   Fix: check with your site administrator, or see the installation guide for setup details.
```

Stop here.

## Layer 6 -- Live tool availability

Check whether the `mcp__wordpress__mcp-adapter-execute-ability` tool is available in this session.

If it is not available but all previous layers passed:

```
❌ Site is reachable but the connector isn't running in this session
   Your credentials and site are fine, but the background connector process hasn't started.
   Fix: restart your agent session (close and reopen Claude Code or Codex). The connector
   starts automatically when the session begins.
```

Stop here.

## Layer 7 -- Live data check

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
   Your account doesn't have permission for some features. Analytics and testing require
   a WordPress role that can edit content (e.g. Editor, Author). Some admin actions
   (stopping tests, broadcasts, exports) require an administrator role.
   Ask your site administrator to check your role.
```

## Output rules

- Keep the final output to **one status block** -- whichever layer you stopped at.
- Use ✅, ❌, or ⚠️ as the status indicator.
- Always include a **Fix:** line with a specific action.
- **Never show raw HTTP status codes, curl output, variable names (WP_API_URL etc.), or technical terms (endpoint, MCP, API, connector plugin) to the user.** The bash commands use these internally; the messages shown to the user must be plain English.
- This is a diagnostic, not a report. Be concise.
