# Authentication

How the Accelerate AI Toolkit authenticates against your WordPress site, where credentials are stored, and how to rotate them.

---

## The short version

The toolkit uses **WordPress Application Passwords** — a feature built into WordPress 5.6+. These are scoped passwords that work with the REST API (and therefore the WordPress MCP Adapter) without compromising your main login.

Credentials live in `~/.config/accelerate-ai-toolkit/env`, a plain-text file with `chmod 600` permissions. Your shell profile sources the file on startup and your agent (Claude Code or Codex) picks up the values via environment variables when it launches the WordPress MCP server. Four variables are passed through:

- `WP_API_URL` — the WordPress **site root** (e.g. `https://example.com`), not a full endpoint path
- `WP_API_USERNAME` — your WordPress username
- `WP_API_PASSWORD` — the Application Password
- `OAUTH_ENABLED=false` — tells the upstream client to use the Application Password flow instead of its new OAuth default (set automatically by the toolkit's `.mcp.json`, not by you)

---

## What's stored, and where

### `~/.config/accelerate-ai-toolkit/env`

A shell env file with three values:

```
WP_API_URL="https://your-site.com"
WP_API_USERNAME="your_wp_username"
WP_API_PASSWORD="abcd efgh ijkl mnop"
```

`WP_API_URL` is the site root — no `/wp-json/...`, no trailing slash. The upstream [`@automattic/mcp-wordpress-remote`](https://www.npmjs.com/package/@automattic/mcp-wordpress-remote) client handles endpoint routing internally.

Permissions: `600` (read/write for you only).

### Why the `env` file

- **Survives plugin updates.** If you re-clone the toolkit repository, credentials aren't affected.
- **Not in the repository.** The toolkit's `.gitignore` excludes `.env*` files inside the repo, but we keep them outside the repo entirely to eliminate the possibility of leaks.
- **Single source of truth.** Both Claude Code and Codex CLI can read the same env file via shell sourcing.

### Your shell profile

One line gets added to your shell profile (`~/.zshrc`, `~/.bash_profile`, or fish config):

```bash
[ -f ~/.config/accelerate-ai-toolkit/env ] && set -a && . ~/.config/accelerate-ai-toolkit/env && set +a
```

The `set -a` / `set +a` pair exports every variable the file sets, so child processes (including the agent's MCP server) inherit them.

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
