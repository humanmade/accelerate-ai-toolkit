# Harness support

How the toolkit installs and connects on each supported agent. **Claude Code is the supported, actively-used path**; the rest are in testing — the manifests follow each agent's current standard, but they haven't all been verified end-to-end. Feedback welcome: [open an issue](https://github.com/humanmade/accelerate-ai-toolkit/issues).

## The two things that must work

Every agent needs both halves:

1. **Skills load.** All skills live in the shared `/skills/` directory as `SKILL.md` files. Every supported agent auto-discovers them — there's nothing per-agent to do here.
2. **The WordPress connection.** Each skill is useless without a live link to your site through the `wordpress` MCP server (`@automattic/mcp-wordpress-remote`). *This* is the part that differs per agent. `/accelerate-connect` wires it; the table below is the reference.

Credentials always live in one place — `~/.config/accelerate-ai-toolkit/env` (chmod 600), written by `/accelerate-connect`. Each agent's MCP server definition points back at those values; secrets are never committed to the repo.

## At a glance

| Agent | Manifest | MCP server config | Auto-configured? |
|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` (+ `marketplace.json`) | bundled `.mcp.json` reads env / `.claude/settings.local.json` | ✅ ships with the plugin |
| Codex CLI | `.codex-plugin/plugin.json` | `~/.codex/config.toml` `[mcp_servers.wordpress]` (TOML) | ⚠️ `/accelerate-connect` writes it (Codex does **not** read `.mcp.json`) |
| Cursor | `.cursor-plugin/plugin.json` (+ `marketplace.json`) | `.cursor/mcp.json` (`envFile` → the env file) | ⚠️ `/accelerate-connect` writes it |
| Gemini CLI | `gemini-extension.json` | `mcpServers` block **inside** the manifest | ✅ ships with the extension |
| GitHub Copilot | root `plugin.json` | bundled `.mcp.json` (auto-loaded on install) | ✅ ships with the plugin |
| Hermes | `.hermes-plugin/` (`plugin.yaml` + `__init__.py`) | configured separately in Hermes | ⚠️ manual — see `.hermes-plugin/README.md` |

---

## Claude Code (supported)

```bash
claude plugin install accelerate-ai-toolkit
/accelerate-connect
/accelerate-status
```

The bundled `.mcp.json` reads `WP_API_URL` / `WP_API_USERNAME` / `WP_API_PASSWORD` from `.claude/settings.local.json` (written by `/accelerate-connect`, folder-scoped, gitignored). Nothing else to configure.

## Codex CLI

Install the plugin from the Codex `/plugins` flow (or local path), then run `/accelerate-connect`. Codex configures MCP servers in `~/.codex/config.toml` and **does not read `.mcp.json`**, so `/accelerate-connect` registers the server using Codex's own command (it owns the TOML merge and escaping):

```bash
codex mcp add wordpress \
  --env WP_API_URL="$WP_API_URL" --env WP_API_USERNAME="$WP_API_USERNAME" \
  --env WP_API_PASSWORD="$WP_API_PASSWORD" --env OAUTH_ENABLED=false \
  -- npx -y @automattic/mcp-wordpress-remote@latest
```

That writes a `[mcp_servers.wordpress]` block into `~/.codex/config.toml`. Verify with `codex mcp list` (or `codex doctor` for a full config/auth/runtime check). On older Codex without the `mcp add` subcommand, `/accelerate-connect` falls back to writing the TOML block directly (file locked to `600` because it holds credentials). After connecting, **open a new terminal** (or `exec zsh`) so the shell-profile env line loads, then start a fresh Codex session.

## Cursor

Install via the Cursor plugin marketplace (or `~/.cursor/plugins/local/` for testing). Cursor reads `SKILL.md` files natively, so skills appear automatically. MCP servers live in `.cursor/mcp.json`; `/accelerate-connect` writes the `wordpress` server with an `envFile` pointing at the shared env file:

```json
{
  "mcpServers": {
    "wordpress": {
      "command": "npx",
      "args": ["-y", "@automattic/mcp-wordpress-remote@latest"],
      "envFile": "/Users/you/.config/accelerate-ai-toolkit/env"
    }
  }
}
```

Like Claude's `settings.local.json`, this is folder-scoped — rerun `/accelerate-connect` from another project to wire it there too.

## Gemini CLI

```bash
gemini extensions install https://github.com/humanmade/accelerate-ai-toolkit
```

This is the most self-contained path: the `wordpress` server is declared in `gemini-extension.json`'s `mcpServers` block and registers on install. It reads `$WP_API_URL` / `$WP_API_USERNAME` / `$WP_API_PASSWORD` from the shell, so run `/accelerate-connect` (for credentials) and make sure the env-file shell-profile line is in place, then start a fresh session.

## GitHub Copilot (CLI + VS Code agent mode)

Copilot loads the root `plugin.json`, auto-discovers `skills/*/SKILL.md`, and auto-loads the bundled `.mcp.json` on install — so the `wordpress` server comes up with no extra file. Run `/accelerate-connect` for credentials and ensure they're exported in the shell (the shell-profile line). If a server name collides with one you already have, the plugin's definition wins.

## Hermes

```bash
curl -fsSL https://raw.githubusercontent.com/humanmade/accelerate-ai-toolkit/main/.hermes-plugin/install.sh | bash
```

`.hermes-plugin/__init__.py` auto-registers every skill from `../skills/` at startup. Hermes configures MCP servers **separately** from the plugin manifest, so add the `wordpress` server to your Hermes MCP config manually — the exact block is in [`.hermes-plugin/README.md`](../.hermes-plugin/README.md). Run `/accelerate-connect` for credentials first.

---

## What we deliberately don't ship

- **No telemetry.** The toolkit phones home to nobody. (Shopify's reference toolkit ships `cursor-hooks.json` / `copilot-hooks.json` purely for usage telemetry — we don't.)
- **No per-agent safety hooks.** The Claude-only `hooks/hooks.json` adds a backup/verify safety net for A/B-test creation; on every other agent the same guardrails live in the skill prose (`skills/accelerate-test/SKILL.md`), so they apply everywhere without agent-specific hook files.

## Validating the manifests

Run the repo's own gate — it checks every hard file (manifests, MCP configs, the Hermes plugin, scripts), not skill content:

```bash
bash scripts/validate.sh
```

It parses all manifests, enforces one shared version, checks `provides_skills` against `skills/`, sanity-checks the `wordpress` MCP server shape, and — if `claude` is on your PATH — runs the official **`claude plugin validate --strict ./`**.

What's available per vendor, beyond that script:

| Vendor | Official check | Notes |
|---|---|---|
| Claude Code | `claude plugin validate [--strict] <path>` | True manifest validator; `--strict` fails on unrecognized fields. Used inside `validate.sh`. |
| Codex CLI | `codex doctor [--json]`, `codex mcp list`, `codex plugin list` | Diagnostics + config parse-checks, not a standalone file linter. |
| MCP configs | — | No official validator for the *client* `mcpServers` shape (the published MCP JSON Schema covers protocol messages, not this config block); `validate.sh` does a structural check instead. |
| Cursor / Gemini / Hermes | none published | Covered by the generic parse + structural checks in `validate.sh`. |

## Verified-vs-theoretical

The Claude Code path is exercised continuously. The other manifests were built against each agent's current published standard (2026-06), but treat them as **theoretically correct until a real install confirms otherwise**. Two specifics worth a live check: whether Gemini/Copilot register the bundled MCP server exactly as documented on first install, and whether your Codex build inherits shell env into the MCP subprocess (we inline the values in `config.toml` so it works either way).
