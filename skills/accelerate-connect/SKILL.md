---
name: accelerate-connect
description: Walks the user through connecting the Accelerate AI Toolkit to their WordPress site. Use when the user says they want to set up, connect, install, configure credentials, generate an application password, or when they report that the toolkit is not connected yet. Also use if another skill fails because the wordpress MCP connection is not available.
license: MIT
category: setup
parent: accelerate
disable-model-invocation: true
---

# Accelerate — Connect your site

Your job is to get the user's WordPress site talking to the toolkit. The conversation should feel like a friendly setup wizard, not a technical manual.

## What you're setting up

Three pieces of information need to land in `~/.config/accelerate-ai-toolkit/env`:

1. **Site URL** — the WordPress site root, in the form `https://their-site.com`. Not a full path, not `/wp-json/...`, just the site root.
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

Keep the normalised site-root value (no path, no trailing slash) in working memory — you'll write it as `WP_API_URL` in step 5. The `@automattic/mcp-wordpress-remote` client handles the endpoint routing internally; don't append any `/wp-json/...` path yourself.

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

### Step 5 — Write the env file

Use the Bash tool to write the credentials to `~/.config/accelerate-ai-toolkit/env`. The file format is a standard shell env file. **All values must be double-quoted** — Application Passwords contain spaces and unquoted values will break when the shell sources the file.

```
WP_API_URL="https://their-site.com"
WP_API_USERNAME="their_username"
WP_API_PASSWORD="abcd efgh ijkl mnop"
```

Commands to run (replace the placeholders with the real values):

```bash
mkdir -p ~/.config/accelerate-ai-toolkit
cat > ~/.config/accelerate-ai-toolkit/env <<'EOF'
WP_API_URL="<site_root_url>"
WP_API_USERNAME="<username>"
WP_API_PASSWORD="<app_password>"
EOF
chmod 600 ~/.config/accelerate-ai-toolkit/env
```

**Important:**
- **Double-quote every value.** Application Passwords always contain spaces (e.g. `Poy6 xelB xJzA wURe`). Without quotes, the shell interprets each space-separated chunk as a separate command and the password gets truncated.
- Use a single-quoted heredoc (`<<'EOF'`) so shell doesn't try to expand anything inside the heredoc itself.
- `chmod 600` is required — the file holds credentials.
- Do NOT echo the full password back to the user in chat after writing. Confirm by saying "Saved. ✓" instead.

### Step 6 — Add the env file to the user's shell profile

Detect the user's shell by checking the `SHELL` environment variable via Bash (`echo $SHELL`). Common values:

- `/bin/zsh` → profile file is `~/.zshrc`
- `/bin/bash` → profile file is `~/.bash_profile` (macOS) or `~/.bashrc` (Linux)
- `/bin/fish` → profile file is `~/.config/fish/config.fish`

Tell the user they need to source the env file from their shell profile so their agent (Claude Code or Codex) picks up the values next session. Show them the exact line to add:

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

Ask the user to add that line, save the profile, and **either** open a new terminal or run `source ~/.zshrc` (or equivalent) in any open terminals.

### Step 7 — Quick connection check

Before asking the user to restart, run two quick probes to catch the most common setup problems.

**7a — Verify npx is the real Node.js binary**

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

If npx looks genuine, continue to 7b.

**7b — Check site endpoints**

Use the Bash tool to test the site's REST endpoints:

```bash
SITE="<the normalised site root URL from step 2>"
USER="<the username from step 4>"
PASS="<the application password from step 4>"

# First check if Accelerate is installed
ACCEL=$(curl -s -o /dev/null -w '%{http_code}' -u "$USER:$PASS" "$SITE/wp-json/accelerate/v1" 2>/dev/null)
# Then check both known connection addresses
DEFAULT=$(curl -s -o /dev/null -w '%{http_code}' -u "$USER:$PASS" "$SITE/wp-json/wp/v2/wpmcp" 2>/dev/null)
ADAPTER=$(curl -s -o /dev/null -w '%{http_code}' -u "$USER:$PASS" "$SITE/wp-json/mcp/mcp-adapter-default-server" 2>/dev/null)

echo "accelerate=$ACCEL default=$DEFAULT adapter=$ADAPTER"
```

Interpret the results in order:

**Step 1 — Is Accelerate installed?**

If `accelerate` is `404`: Accelerate isn't active on this site, or the Abilities feature isn't turned on. Tell the user:

> "I can reach your site, but Accelerate doesn't seem to be active or its Abilities feature isn't turned on yet. Check that the Accelerate plugin is installed and active in your WordPress admin, and that the Abilities feature is enabled (see the installation guide for instructions)."

Stop here — no point checking connection addresses if Accelerate itself isn't running.

**Step 2 — Which connection address works?**

| default | adapter | What to tell the user |
|---------|---------|----------------------|
| 200/401 | any | Everything looks good. Proceed to step 8. |
| 404 | 200/401 | See "Connection address mismatch" guidance below. |
| 404 | 404 | Accelerate is installed but the WordPress connector isn't registered. Tell the user: *"Accelerate is running on your site, but the WordPress connector isn't responding. This usually means it needs to be activated separately. Check with your site administrator or see the installation guide."* |
| Other | Other | Tell the user the site returned an unexpected response and suggest they check the URL is correct and the site is reachable in a browser. |

**Connection address mismatch guidance:**

If only the second address responds (404 on default, 200/401 on adapter), tell the user in plain, friendly language:

> "Your site's connection is set up slightly differently than what the toolkit expects out of the box. This is a known compatibility issue with recent versions of the WordPress connector.
>
> To fix it, your site needs a small configuration tweak. Please ask your site administrator (or developer) to create a file called `endpoint-compat.php` in your site's `wp-content/mu-plugins/` folder with this content:"
>
> ```php
> <?php
> add_filter( 'mcp_adapter_default_server_config', function( $config ) {
>     $config['server_route_namespace'] = 'wp/v2';
>     $config['server_route']           = 'wpmcp';
>     return $config;
> } );
> ```
>
> "Once that file is in place, restart your agent session and run `/accelerate-status`. If you're not sure how to do this, forward these instructions to your developer — they'll know what to do."

**Important:** Do not offer to create this file yourself via SSH or WP-CLI. The user may not have server access, and creating PHP files on their server without clear developer involvement is not safe. Present the snippet and let them or their developer handle it.

### Step 8 — Remind them to restart their agent session

Tell them:

> "One last step — close your current agent session (Claude Code or Codex, whichever you're using) and start a new one. The agent reads the WordPress connection settings at startup, so the new credentials will only kick in next session. When you're back in, run `/accelerate-status` to confirm everything works."

## Things to watch for

- **Don't skip the chmod.** Credentials must not be world-readable.
- **Don't write the env file anywhere else.** The `.mcp.json` in the plugin root expects to find `WP_API_URL` (site root), `WP_API_USERNAME`, and `WP_API_PASSWORD` as environment variables, sourced from the `~/.config/accelerate-ai-toolkit/env` path.
- **`WP_API_URL` is the site root, nothing more.** Never write `/wp-json/...` into the env file. If the user pastes a full endpoint URL, strip it back to the scheme+host before writing.
- **Don't embed credentials in the plugin folder.** Never write to a `.env` or `env` file inside the repository; it must go in the user's home directory.
- **Never show the full password in chat output after writing it.** It's fine to show the first and last four characters for confirmation (e.g., `abcd **** **** mnop`), but never the whole string.

## If the user already has credentials

If the user already has `WP_API_URL` etc. set in their shell (check via `env | grep WP_API_` in a Bash call), tell them the connection is already configured and suggest running `/accelerate-status` to verify it's working. Offer to overwrite the existing config if they want to connect to a different site.
