---
name: accelerate-connect
description: Connect the toolkit to your WordPress site. Set up credentials, generate an application password. Also triggered when the site connection is missing.
license: MIT
category: setup
parent: accelerate
disable-model-invocation: true
---

# Accelerate — Connect your site

Your job is to get the user's WordPress site talking to the toolkit. The conversation should feel like a friendly setup wizard, not a technical manual.

## What you're setting up

Three pieces of information need to land in `~/.config/accelerate-ai-toolkit/env`:

1. **Connection URL** (`WP_API_URL`) — the **full** WordPress MCP server URL, e.g. `https://their-site.com/wp-json/mcp/mcp-adapter-default-server` for sites running the MCP Adapter, or `https://their-site.com/wp-json/wp/v2/wpmcp` for legacy `wordpress-mcp` sites. The user only ever gives you the bare site address; this skill probes the site and saves whichever full URL responds.
2. **Username** — the WordPress username to authenticate as
3. **Application password** — a WordPress Application Password (not their login password)

Once those are set, the `.mcp.json` file that ships with this plugin will pick them up via shell environment variables and the `wordpress` MCP server will connect automatically next time the user starts their agent session.

## The conversation

Walk the user through these steps one at a time. Wait for a response before moving to the next step. Be patient and don't assume technical knowledge.

### Step 1 — Welcome

Explain briefly what's about to happen, in plain language:

> "To connect your site, we need three things: your site's web address, your WordPress username, and a special password that only this toolkit will use. I'll guide you through generating that password in a moment. It takes about two minutes."

### Step 2 — Ask for the site URL

Ask:

> "What's the web address of your WordPress site? For example: `https://mysite.com`"

Accept whatever they give you and **normalise it to the site root**:
- Strip any trailing slash.
- If they pasted something ending in `/wp-json/...` or `/wp-admin`, strip that back to the site root and politely confirm (*"I'll use `https://mysite.com` as the site address — sound right?"*).
- If they gave you something with a content path like `https://mysite.com/blog`, confirm whether that's the correct WordPress root or whether the WordPress install lives at `https://mysite.com`.
- If they omitted `https://`, assume `https://`.

Keep the normalised site-root value (no path, no trailing slash) in working memory as `SITE_ROOT`. You'll combine it with the connector path detected in step 7b to build the full `WP_API_URL` saved in step 5.

### Step 3 — Generate an Application Password

Tell the user:

> "Now we'll create a dedicated password for this toolkit. This lets you revoke access later without changing your main login.
>
> 1. Open your site's admin area in a browser: `<their-site>/wp-admin`
> 2. Go to **Users → Profile** (or **Users → Your Profile**)
> 3. Scroll down to the **Application Passwords** section near the bottom
> 4. Type `Accelerate AI Toolkit` as the name
> 5. Click **Add New Application Password**
> 6. WordPress will show you a password that looks like `abcd efgh ijkl mnop`. Copy it exactly as shown, spaces and all.
>
> Let me know once you've got it."

If they report the Application Passwords section is missing, it usually means either:
- Their WordPress is older than 5.6 — tell them they need to update.
- The site is served over plain HTTP in production — Application Passwords require HTTPS. For local development they can set `WP_ENVIRONMENT_TYPE` to `local` in `wp-config.php` to bypass this. Suggest they ask their site administrator for help.

### Step 4 — Collect username and password

Ask:

> "Great. What's your WordPress username? And please paste the application password you just copied."

Collect both. The username goes into `WP_API_USERNAME`. The password goes into `WP_API_PASSWORD` **exactly as WordPress displayed it** — do not strip the spaces.

### Step 5 — Verify the environment and discover the connector URL

Before saving anything, run two quick checks. Both must pass before you can write a working configuration.

**5a — Verify npx is the real Node.js binary**

Use the Bash tool:

```bash
NPX_PATH=$(command -v npx 2>/dev/null)
NPX_VER=$(npx --version 2>&1 | head -1)
NPX_REAL=$(realpath "$NPX_PATH" 2>/dev/null || echo "$NPX_PATH")
echo "path=$NPX_REAL version=$NPX_VER"
```

Check **both** conditions:
1. The version output looks like a semver number (e.g. `10.8.2`), not an error or "Unknown command"
2. The resolved path is inside a standard Node.js location (the path contains `node`, `npm`, `nvm`, `fnm`, `volta`, or is in `/usr/local/bin`, `/usr/bin`, or a Homebrew prefix)

If npx is missing, returns a non-semver version, or resolves to an unexpected location, tell the user:

> "The toolkit needs a working copy of `npx` (part of Node.js) to connect to your site, but the `npx` in your current shell doesn't appear to be the standard Node.js version. This usually happens when another tool in your shell is intercepting the command.
>
> To check: open a regular terminal and run `npx --version`. If that works and shows a version number, your agent's shell has something overriding it. See the troubleshooting section in the installation guide for how to point the toolkit at the real `npx` binary."

If npx looks genuine, continue to 5b.

**5b — Probe the site to discover the connector URL**

Use the Bash tool to test the site's REST endpoints:

```bash
SITE="<the normalised site root from step 2>"
USER="<the username from step 4>"
PASS="<the application password from step 4>"

# Is Accelerate active?
ACCEL=$(curl -s -o /dev/null -w '%{http_code}' -u "$USER:$PASS" "$SITE/wp-json/accelerate/v1" 2>/dev/null)
# Which MCP connector route responds?
ADAPTER=$(curl -s -o /dev/null -w '%{http_code}' -u "$USER:$PASS" "$SITE/wp-json/mcp/mcp-adapter-default-server" 2>/dev/null)
LEGACY=$(curl -s -o /dev/null -w '%{http_code}' -u "$USER:$PASS" "$SITE/wp-json/wp/v2/wpmcp" 2>/dev/null)

echo "accelerate=$ACCEL adapter=$ADAPTER legacy=$LEGACY"
```

Interpret the results in order:

**Is Accelerate installed?**

If `accelerate` is `404`: Accelerate isn't active on this site, or the Abilities feature isn't turned on. Tell the user:

> "I can reach your site, but Accelerate doesn't seem to be active or its Abilities feature isn't turned on yet. Check that the Accelerate plugin is installed and active in your WordPress admin, and that the Abilities feature is enabled (see the installation guide for instructions)."

Stop here. Do not save credentials.

**Which connector responds?**

Pick the connector URL using this priority — adapter wins when both respond, since `mcp-adapter` is the actively maintained route:

| adapter | legacy | Action |
|---------|--------|--------|
| 200/401 | any | Set `WP_API_URL="$SITE/wp-json/mcp/mcp-adapter-default-server"`. Proceed to step 6. |
| 404 | 200/401 | Set `WP_API_URL="$SITE/wp-json/wp/v2/wpmcp"`. Proceed to step 6. |
| 404 | 404 | Stop. Accelerate is running but no MCP connector responded. Tell the user: *"Accelerate is running on your site, but the WordPress connector isn't responding. This usually means the MCP Adapter plugin needs to be installed or activated. Check with your site administrator or see the installation guide."* |
| Other | Other | Stop. Tell the user the site returned an unexpected response and suggest they check the URL is correct and the site is reachable in a browser. |

Keep the chosen full URL in working memory as `WP_API_URL`. You'll write it in step 6.

### Step 6 — Save credentials

Save credentials in **two places** so they work across all supported agents.

**6a — Claude Code settings (primary)**

This is what Claude Code reads when it starts the WordPress connector. Use the Bash tool to write the credentials into the project's `.claude/settings.local.json` (this file is gitignored and never committed):

```bash
# Read existing settings.local.json if it exists, merge env vars in
python3 -c "
import json, os, sys
path = '.claude/settings.local.json'
data = {}
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
data.setdefault('env', {})
data['env']['WP_API_URL'] = sys.argv[1]
data['env']['WP_API_USERNAME'] = sys.argv[2]
data['env']['WP_API_PASSWORD'] = sys.argv[3]
data['env']['OAUTH_ENABLED'] = 'false'
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
" "<full_connector_url>" "<username>" "<app_password>"
```

Replace the three placeholders with the values from steps 4 and 5b. `<full_connector_url>` is the full URL chosen in step 5b — never the bare site root.

**6b — Backup env file (for Codex CLI and other agents)**

Also write a standard env file for non-Claude-Code contexts:

```bash
mkdir -p ~/.config/accelerate-ai-toolkit
cat > ~/.config/accelerate-ai-toolkit/env <<'EOF'
WP_API_URL="<full_connector_url>"
WP_API_USERNAME="<username>"
WP_API_PASSWORD="<app_password>"
EOF
chmod 600 ~/.config/accelerate-ai-toolkit/env
```

**Important:**
- **Double-quote every value** in the env file. Application Passwords contain spaces.
- `chmod 600` is required — the file holds credentials.
- Do NOT echo the full password back to the user in chat after writing. Confirm by saying "Saved. ✓" instead.
- The `.claude/settings.local.json` file is automatically gitignored by Claude Code. Do not commit it.

### Step 7 — Shell profile (Codex CLI users only)

If the user is using **Codex CLI** (not Claude Code), they also need to source the env file from their shell profile so Codex picks up the values. Tell them:

> "Since you're using Codex, you'll also need to add a line to your shell profile so the credentials load automatically."

Show the appropriate line based on their shell:

For zsh / bash:
```bash
[ -f ~/.config/accelerate-ai-toolkit/env ] && set -a && . ~/.config/accelerate-ai-toolkit/env && set +a
```

For fish:
```fish
if test -f ~/.config/accelerate-ai-toolkit/env
    for line in (cat ~/.config/accelerate-ai-toolkit/env)
        set -gx (string split -m 1 '=' $line)
    end
end
```

**If the user is using Claude Code, skip this step entirely** — Claude Code reads credentials from `settings.local.json` and doesn't need shell profile changes.

### Step 8 — Remind them to restart their agent session

Tell them:

> "One last step — close your current agent session (Claude Code or Codex, whichever you're using) and start a new one. The agent reads the WordPress connection settings at startup, so the new credentials will only kick in next session. When you're back in, run `/accelerate-status` to confirm everything works."

## Things to watch for

- **Don't skip the chmod.** Credentials must not be world-readable.
- **Don't write the env file anywhere else.** The `.mcp.json` in the plugin root expects `WP_API_URL`, `WP_API_USERNAME`, and `WP_API_PASSWORD` as environment variables, sourced from the `~/.config/accelerate-ai-toolkit/env` path.
- **`WP_API_URL` is the full connector URL.** It must include the `/wp-json/...` path discovered in step 5b. Never save just the site root — the toolkit's status check will flag it as stale and tell the user to rerun this skill.
- **Don't embed credentials in the plugin folder.** Never write to a `.env` or `env` file inside the repository; it must go in the user's home directory.
- **Never show the full password in chat output after writing it.** It's fine to show the first and last four characters for confirmation (e.g., `abcd **** **** mnop`), but never the whole string.

## If the user already has credentials

If the user already has `WP_API_URL` etc. set in their shell (check via `env | grep WP_API_` in a Bash call), tell them the connection is already configured and suggest running `/accelerate-status` to verify it's working. Offer to overwrite the existing config if they want to connect to a different site.
