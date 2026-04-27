# Installation

The Accelerate AI Toolkit ships as a vendor-agnostic plugin that currently supports Claude Code and Codex CLI. These instructions cover both.

---

## Prerequisites

Before you install the toolkit, confirm you have:

- **A WordPress site running [Accelerate](https://www.accelerateplugin.com/) 4.1 or newer**. The Abilities API feature flag must be enabled (see [Enabling the Abilities API](#enabling-the-abilities-api) below). Accelerate bundles the WordPress MCP Adapter, so you do **not** need to install a separate `wordpress-mcp` plugin even if the upstream `@automattic/mcp-wordpress-remote` README mentions one. `/accelerate-connect` probes both the modern adapter route and the legacy `wpmcp` route, then saves the full URL of whichever responds — no server-side configuration is required.
- **WordPress 6.9 or newer.** The Abilities API requires WordPress core's `wp_register_ability()` function.
- **A recent Node.js LTS runtime.** The toolkit uses `@automattic/mcp-wordpress-remote` as its MCP client, which runs on Node via `npx`. The upstream client doesn't document a specific minimum version; if you're on a current Node LTS you're fine.
- **An agent that supports plugins:**
  - [Claude Code](https://claude.com/claude-code), or
  - [Codex CLI](https://github.com/openai/codex)
- **A WordPress account with `edit_posts`** on the target site for analytics and experimentation, or `manage_options` (administrator) if you want the toolkit to broadcast content or export raw events. See [authentication.md](./authentication.md#required-wordpress-capabilities) for the full capability breakdown.

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/humanmade/accelerate-ai-toolkit.git
cd accelerate-ai-toolkit
```

Marketplace installs are planned for v1.1 (see [ROADMAP.md](../ROADMAP.md)). Until then, installing from a local checkout is the supported path.

---

## Step 2 — Install into your agent

### Claude Code

From inside the toolkit directory:

```bash
claude
```

Then, inside the Claude Code session:

```
/plugin install ./
```

Confirm the plugin loaded by running:

```
/plugin list
```

You should see `accelerate-ai-toolkit` in the list.

### Codex CLI

From inside the toolkit directory:

```bash
codex
```

Then, inside the Codex session:

```
/plugins
```

Choose "Install from local path" and point it at the toolkit directory. Codex will pick up `.codex-plugin/plugin.json` and register the skills from `./skills/`.

---

## Step 3 — Connect your site

Inside your agent session, run:

```
/accelerate-connect
```

This walks you through:

1. Your WordPress site URL
2. Generating a dedicated Application Password (instructions provided by the command)
3. Saving credentials to `~/.config/accelerate-ai-toolkit/env` with restrictive permissions
4. Adding a line to your shell profile so the credentials load into future sessions

See [authentication.md](./authentication.md) for the full details on what's being stored and why.

---

## Step 4 — Verify

Restart your agent session (the MCP server picks up credentials at launch), then run:

```
/accelerate-status
```

A healthy response looks like:

```
✅ Connected to [your site name]
   URL: [your site URL]
   Accelerate capabilities available: 39
   Ready for questions.
```

If you see an error, see [Troubleshooting](#troubleshooting) below.

---

## Step 5 — Ask your first question

Try:

> "How is my site performing this week?"

The router skill will call the right Accelerate capabilities and produce a summary.

---

## Enabling the Abilities API

The Accelerate Abilities API is currently behind a feature flag. On your site:

**Via WordPress admin** — ask your site administrator to flip the flag in Accelerate's settings (the exact UI depends on your Accelerate version).

**Via WP-CLI** — if you have SSH / WP-CLI access:

```bash
wp option update accelerate_abilities_api_enabled 1
```

Without this flag, the abilities are not exposed through the MCP adapter and `/accelerate-status` will report "no capabilities available".

---

## Troubleshooting

### "MCP server not running" or the `mcp__wordpress__*` tool isn't available

The credentials didn't load, or the server couldn't start. Check these in order:

1. **Did you source the env file in your shell profile?** The line from `/accelerate-connect` should be in `~/.zshrc`, `~/.bash_profile`, or equivalent.
2. **Did you restart your agent session** after adding the line?
3. **Try running `env | grep WP_API_`** in a terminal. You should see three variables.
4. **Is `npx` working correctly?** Open a terminal and run `npx --version`. If this fails or returns unexpected output, another tool in your shell is intercepting `npx`. Common causes include shell proxy tools, custom aliases, or non-standard Node.js shim configurations. To work around this, find the real `npx` binary path (e.g. `which -a npx` or check your Node.js install directory) and create a project-level `.mcp.json` override in any directory where you run Claude Code:

   ```json
   {
     "mcpServers": {
       "wordpress": {
         "command": "/absolute/path/to/npx",
         "args": ["-y", "@automattic/mcp-wordpress-remote@latest"],
         "env": {
           "WP_API_URL": "${WP_API_URL}",
           "WP_API_USERNAME": "${WP_API_USERNAME}",
           "WP_API_PASSWORD": "${WP_API_PASSWORD}",
           "OAUTH_ENABLED": "false"
         }
       }
     }
   }
   ```

   Replace `/absolute/path/to/npx` with the real binary path (e.g. `/usr/local/bin/npx` or `~/.nvm/versions/node/v22.x.x/bin/npx`).

### "Authentication failed" / 401 errors

The Application Password is wrong or has been revoked. Re-run `/accelerate-connect` and generate a fresh one.

### "Not found" / 404 errors on the connection

If you set up the toolkit before v1.3, your saved `WP_API_URL` may still be a bare site root from the older "site-root only" contract. Recent versions of the WordPress MCP Adapter no longer respond at the legacy `wp/v2/wpmcp` route that bare-root values fall back to.

**Fix:** re-run `/accelerate-connect`. It will probe the connector routes, save the full working URL, and the 404s should clear after restarting your agent session. This is a one-time migration — new installs go through this path automatically.

If `/accelerate-status` reports that the connector address check passed, the 404 is caused by something else:
- Accelerate isn't installed on the site you pointed at.
- The Abilities API feature flag isn't enabled (see [Enabling the Abilities API](#enabling-the-abilities-api)).
- The site URL is wrong — check that the `WP_API_URL` value saved in `.claude/settings.local.json` (or `~/.config/accelerate-ai-toolkit/env`) matches the connector URL the WordPress MCP Adapter exposes on your site.

### "Permission denied" when a skill tries to fetch data

Your WordPress account lacks the required capability. Accelerate currently uses `edit_posts` as the permission floor for all analytics and experimentation capabilities, and `manage_options` for broadcasts, exports, and stopping experiments. Ask your site admin to grant you an Editor role (or higher) for the analytics side, or administrator access if you need broadcasts/exports. See [authentication.md](./authentication.md#required-wordpress-capabilities) for the full tier breakdown.

### Application Passwords section is missing from your profile

Either:
- WordPress is older than 5.6 — update.
- Your site is HTTP-only in production — Application Passwords require HTTPS. For local development, set `define( 'WP_ENVIRONMENT_TYPE', 'local' );` in `wp-config.php`.

---

## Uninstalling

To remove the toolkit:

1. In Claude Code: `/plugin uninstall accelerate-ai-toolkit`. In Codex: use the plugins UI.
2. Delete the credentials file: `rm ~/.config/accelerate-ai-toolkit/env`
3. Remove the `. ~/.config/accelerate-ai-toolkit/env` line from your shell profile.
4. Optionally, revoke the Application Password in WordPress (Users → Profile → Application Passwords → Revoke).
5. Delete the cloned repository.
