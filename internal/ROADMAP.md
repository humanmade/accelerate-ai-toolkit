# Roadmap

Live document of what's planned for the Accelerate AI Toolkit after v1. Items move up as scope firms up. File an issue if you want to bump priority on something.

---

## v1.1 — Wider reach

- **Design guardrails for variant proposals.** New `docs/design-standards.md` reference ensures that proposed A/B test variants are different enough from the control to be worth testing, consistent with the site's design system (slug-first principle), and free of generic AI patterns. Inspired by [Impeccable](https://github.com/pbakaus/impeccable), adapted for WordPress block-level reality. Per-site brand context files (`~/.config/accelerate-ai-toolkit/brand-<site-slug>.md`) map `get-site-context` output to the preset slugs the model should use in block markup.
- **Claude Code marketplace submission.** The manifest (`.claude-plugin/marketplace.json`) is already in place as a prep artifact — the remaining work is publishing it so users can install with `/plugin marketplace add` instead of cloning the repo.
- **Codex CLI marketplace submission.** Same idea for `.codex-plugin/`.
- **Cursor manifest.** Convert `.cursor-plugin/` from stub to working manifest, referencing the shared `/skills/` directory.
- **Gemini extension.** Same for `gemini-extension.json`.
- **`/accelerate-update`** slash command to pull the latest skills without reinstalling.

## v1.2 — Self-optimising skill loop (shipped)

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch). The toolkit learns what works on your specific site and tailors future suggestions accordingly.

- **`/accelerate-learn`** reads completed experiment results, classifies each by suggestion pattern, writes findings to a per-site learning journal, and teaches other skills to consult it.
- **Journal** lives as two files at `~/.config/accelerate-ai-toolkit/`: a JSON source of truth and a human-readable markdown summary. Private by default. Never sent anywhere.
- **Four pattern states** — `won`, `lost`, `mixed`, `inconclusive` — with strict rules (minimum 3 decisive tests before classification; 75%+ hit rate for won; 25% or lower for lost; everything else is mixed). `won` patterns boost recommendations. `lost` patterns are demoted with advisory context, not silently excluded.
- **Pattern taxonomy** — 15 canonical suggestion types. Tests created via the toolkit are tagged with `annotations['toolkit:pattern']` so classification is a pure dictionary lookup.
- **Optional automation** via GitHub Actions template at `docs/examples/workflow-accelerate-learn.yml`. Runs weekly, creates a PR with the updated journal.

Upstream prerequisites shipped in Accelerate PR #605: `list-experiments` ability with pagination and annotation filters, `experiment_id` addressing on `get-experiment-results`, generic annotations primitive on `create-ab-test`, `view_accelerate_analytics` capability.

See `docs/self-optimising.md` for the full guide.

## v2 — Scale

- **Caching layer** for expensive analytics queries. Some abilities hit ClickHouse; repeat calls inside a single session are wasteful. Session-scoped cache with a plain-English "data freshness" indicator.
- **Opt-in anonymous telemetry** so we can see which skills get used and which don't. Strictly opt-in, strictly anonymous, documented in `docs/telemetry.md`.
- **Community skill marketplace.** A `/skills/community/` directory and a submission flow so power users can share custom workflows (e.g. *"holiday sale campaign launcher"*, *"newsletter performance audit"*).
- **Multi-site awareness.** For agencies running many Accelerate installs, a site switcher that swaps which `~/.config/accelerate-ai-toolkit/env` profile is active.

## Upstream asks (not in this repo)

These are improvements the toolkit would benefit from but that live in other codebases. Tracked here so they don't get lost.

- **Real read-only permission tier in Accelerate.** Today `can_view_analytics()` and `can_create_experiments()` both resolve to `current_user_can('edit_posts')` in `../altis-accelerate/inc/abilities/namespace.php:88–101`, which means a marketer with read-only intent must still be granted experiment-creation permissions to use the toolkit. A dedicated capability (e.g. `view_accelerate_analytics` mapped to a new WordPress role or granted additively) would let teams hand out analytics access without handing out A/B-test-creation access. Upstream PR to altis-accelerate.
- **OAuth-first onboarding.** Upstream `@automattic/mcp-wordpress-remote` has moved to OAuth as its default auth mode; the toolkit currently opts out via `OAUTH_ENABLED: "false"` for non-technical-user simplicity. A future v1.x could add an OAuth path inside `/accelerate-connect` for users who prefer it, while keeping the Application Password path as the default.
- **Endpoint auto-discovery.** `@automattic/mcp-wordpress-remote` hardcodes the REST endpoint path as `/wp/v2/wpmcp`, but the WordPress MCP Adapter plugin (0.4.1+) registers at `/mcp/mcp-adapter-default-server`. This forces users to deploy a mu-plugin to remap the route. The MCP Adapter already exposes its routes via the REST API index at `/wp-json/` — the upstream client should probe the index and discover the correct endpoint automatically. Until then, `/accelerate-connect` detects the mismatch and guides the user through the mu-plugin fix.

## Ideas on the back burner

- Integration with Google Search Console for off-site context alongside on-site Accelerate data.
- Integration with email tools (Mailchimp, Campaign Monitor) so the `accelerate-campaigns` skill can close the loop on attribution.
- A lightweight web dashboard that mirrors the conversational experience for users who prefer clicking to typing.
