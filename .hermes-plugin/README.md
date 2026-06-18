# Accelerate AI Toolkit — Hermes plugin

This directory makes the toolkit installable in Hermes. The skills themselves
live in the shared `../skills/` folder and are auto-registered at startup by
`__init__.py`; `plugin.yaml` is the manifest Hermes reads.

> **Status: in testing.** Claude Code is the supported, actively-used path. The
> Hermes manifest is standards-correct but not yet verified end-to-end —
> feedback welcome ([open an issue](https://github.com/humanmade/accelerate-ai-toolkit/issues)).

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/humanmade/accelerate-ai-toolkit/main/.hermes-plugin/install.sh | bash
```

This clones the repo to `~/.hermes/repos/accelerate-ai-toolkit` and symlinks
`.hermes-plugin/` into `~/.hermes/plugins/`. Launch Hermes and run `/plugins`
to confirm `accelerate-ai-toolkit` is loaded with its 16 skills.

## Connect your site

Every skill needs a live connection to your WordPress site through the
`wordpress` MCP server. Two steps:

1. **Credentials.** Run the `accelerate-connect` skill (ask *"connect my site"*).
   It generates a WordPress Application Password and saves it to
   `~/.config/accelerate-ai-toolkit/env` (chmod 600).
2. **MCP server.** Hermes configures MCP servers separately from this plugin
   manifest, so add the `wordpress` server to your Hermes MCP configuration:

   ```json
   {
     "wordpress": {
       "command": "npx",
       "args": ["-y", "@automattic/mcp-wordpress-remote@latest"],
       "env": {
         "WP_API_URL": "$WP_API_URL",
         "WP_API_USERNAME": "$WP_API_USERNAME",
         "WP_API_PASSWORD": "$WP_API_PASSWORD",
         "OAUTH_ENABLED": "false"
       }
     }
   }
   ```

   Make sure your shell exports the `WP_API_*` values — `accelerate-connect`
   prints the one-line shell-profile snippet that sources them from the env file.

See [`../docs/harness-support.md`](../docs/harness-support.md) for the full
per-harness reference.
