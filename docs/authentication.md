# Authentication

How the Accelerate AI Toolkit authenticates against your WordPress site, where credentials are stored, and how to rotate them.

---

## The short version

The toolkit uses **WordPress Application Passwords** — a feature built into WordPress 5.6+. These are scoped passwords that work with the REST API (and therefore the WordPress MCP Adapter) without compromising your main login.

Credentials live in `~/.config/accelerate-ai-toolkit/env`, a plain-text file with `chmod 600` permissions. Your shell profile sources the file on startup and your agent (Claude Code or Codex) picks up the values via environment variables when it launches the WordPress MCP server. Four variables are passed through:

- `WP_API_URL` — the **full WordPress MCP connector URL** (e.g. `https://example.com/wp-json/mcp/mcp-adapter-default-server`). `/accelerate-connect` probes the site at setup time and saves whichever connector route responds. A bare site root (`https://example.com`) is still accepted as a backwards-compatibility fallback for legacy `wordpress-mcp` installs, but new setups always store the full URL.
- `WP_API_USERNAME` — your WordPress username
- `WP_API_PASSWORD` — the Application Password
- `OAUTH_ENABLED=false` — tells the upstream client to use the Application Password flow instead of its new OAuth default (set automatically by the toolkit's `.mcp.json`, not by you)

---

## What's stored, and where

Credentials are stored in two places. Which one matters depends on your agent.

### Claude Code: `.claude/settings.local.json` (primary)

For Claude Code users, credentials are saved in the project's `.claude/settings.local.json` under the `env` key:

```json
{
  "env": {
    "WP_API_URL": "https://your-site.com/wp-json/mcp/mcp-adapter-default-server",
    "WP_API_USERNAME": "your_wp_username",
    "WP_API_PASSWORD": "abcd efgh ijkl mnop",
    "OAUTH_ENABLED": "false"
  }
}
```

Claude Code reads this file at startup and injects these values into the environment for all MCP server processes. This is the reliable, documented mechanism — it survives session restarts without any shell profile changes.

This file is automatically gitignored by Claude Code and is never committed.

### `~/.config/accelerate-ai-toolkit/env` (backup / Codex CLI)

A standard shell env file is also written as a backup and for Codex CLI users:

```
WP_API_URL="https://your-site.com/wp-json/mcp/mcp-adapter-default-server"
WP_API_USERNAME="your_wp_username"
WP_API_PASSWORD="abcd efgh ijkl mnop"
```

`WP_API_URL` is the full URL of the WordPress MCP connector that responded during `/accelerate-connect`. For sites running the modern MCP Adapter that's `…/wp-json/mcp/mcp-adapter-default-server`; legacy `wordpress-mcp` sites store `…/wp-json/wp/v2/wpmcp` instead. The upstream [`@automattic/mcp-wordpress-remote`](https://www.npmjs.com/package/@automattic/mcp-wordpress-remote) client uses this URL as-is when it includes a path; a bare-root value is treated as legacy compatibility and routed to the old `wp/v2/wpmcp` endpoint.

Permissions: `600` (read/write for you only).

### Shell profile (Codex CLI only)

Codex CLI users need to source the env file from their shell profile so credentials load into future sessions:

```bash
[ -f ~/.config/accelerate-ai-toolkit/env ] && set -a && . ~/.config/accelerate-ai-toolkit/env && set +a
```

**Claude Code users do not need this line.** Claude Code reads credentials from `settings.local.json` directly.

### The toolkit's `.mcp.json`

Inside the repo, `.mcp.json` uses shell variable expansion to wire the env values into the MCP client, plus a hard-coded `OAUTH_ENABLED: "false"` to opt out of upstream's OAuth default:

```json
{
  "mcpServers": {
    "wordpress": {
      "command": "npx",
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

No credentials live in the repo — only references to env vars that get filled in at launch.

### Why `OAUTH_ENABLED: "false"`

[`@automattic/mcp-wordpress-remote`](https://github.com/Automattic/mcp-wordpress-remote) now defaults to OAuth authentication, which requires a browser callback loop. That's a lot of friction for a marketer who just wants to paste a password and go. The toolkit explicitly sets `OAUTH_ENABLED` to `false` so the simpler Application Password path continues to work end-to-end. OAuth support is tracked as a future improvement in `ROADMAP.md`.

---

## Generating an Application Password

You'll normally do this during `/accelerate-connect`, which walks you through it. If you want to do it manually:

1. Log into your WordPress site as the user you want the toolkit to act as.
2. Go to **Users → Profile** (sometimes called **Users → Your Profile**).
3. Scroll to the **Application Passwords** section near the bottom.
4. Enter a recognisable name (e.g. `Accelerate AI Toolkit`).
5. Click **Add New Application Password**.
6. WordPress will show you a password that looks like `abcd efgh ijkl mnop`. **Copy it immediately** — it's the only time you'll see it.
7. Paste it into `/accelerate-connect` (or directly into `~/.config/accelerate-ai-toolkit/env` if you're doing it manually).

---

## Required WordPress capabilities

The toolkit calls Accelerate capabilities that map to two WordPress capability tiers:

| Tier | WordPress capability | What it unlocks |
|---|---|---|
| Analytics + experiments | `edit_posts` | All 35 analytics and experimentation capabilities — performance summaries, top content, traffic breakdowns, engagement metrics, attribution, realtime, author stats, taxonomy breakdowns, audiences, personalisation rules, variant management, A/B test creation and review |
| Admin | `manage_options` | Stopping experiments, broadcasting content site-wide, exporting raw event data |

Any WordPress role with `edit_posts` (Editor, Author, Contributor with publishing, and above) can use the analytics and experimentation side of the toolkit. Only administrators can stop experiments, run broadcasts, or export raw events.

If a capability call fails with a permission error, the toolkit will surface this and tell you to ask your site administrator for the right role.

### A note on read vs write

Accelerate currently does not split read-only analytics into its own WordPress capability — the underlying permission callback for analytics queries is the same `edit_posts` check used for creating experiments. In practice this means a contributor who can read analytics can also create A/B tests.

If your team needs a strict read-only marketing role, the current workaround is to trust users with `edit_posts` on the analytics side and rely on the admin tier (`manage_options`) to gate broadcasts and exports. A dedicated read-only capability is tracked as a future upstream improvement in `ROADMAP.md`.

---

## Rotating credentials

To change the Application Password without touching anything else:

1. Log into WordPress.
2. **Users → Profile → Application Passwords**.
3. Revoke the old `Accelerate AI Toolkit` password.
4. Generate a new one.
5. Edit `~/.config/accelerate-ai-toolkit/env` and replace the `WP_API_PASSWORD` value.
6. Start a new agent session (env vars are read at launch).

To switch to a different site entirely, re-run `/accelerate-connect`. It will overwrite the env file.

---

## Security notes

- **The env file permissions matter.** `chmod 600` ensures only your user account can read it. The `/accelerate-connect` command sets this automatically; if you create the file manually, don't skip it.
- **The password is not your WordPress login password.** It's a dedicated credential you can revoke any time without affecting your main account.
- **HTTPS is required in production.** WordPress won't accept Application Password authentication over plain HTTP unless the site explicitly declares itself as a local development environment. This is a WordPress core security measure, not something the toolkit enforces.
- **No credentials leave your machine except over HTTPS to your own site.** The toolkit does not phone home, does not send credentials to third parties, and has no telemetry in v1.
- **Do not commit the env file.** The toolkit's `.gitignore` excludes `.env*` patterns inside the repo, but the canonical location is `~/.config/accelerate-ai-toolkit/env` — outside any repository.

---

## Revoking access

To completely cut the toolkit off from a site:

1. In WordPress: **Users → Profile → Application Passwords → Revoke** the `Accelerate AI Toolkit` entry.
2. On your machine: `rm ~/.config/accelerate-ai-toolkit/env`.
3. Remove the sourcing line from your shell profile.

The next agent session will have no credentials to use and will fail cleanly with a "not connected" status.
