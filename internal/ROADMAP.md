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

## v1.2 — Self-optimising skill loop

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch). Autoresearch lets an agent iterate on its own training code against a measurable outcome; we adapt the same loop pattern to marketing recommendations because Accelerate already ships the missing piece — measurable outcomes via Bayesian A/B test results.

**How it works:**

1. Skills make suggestions and create A/B tests.
2. Time passes; experiments reach statistical significance.
3. A new `accelerate-learn` skill reads recent experiment results, groups them by suggestion pattern (e.g. *"rewrite headline to match referrer intent"*, *"move CTA above fold"*), and computes hit-rate + average lift per pattern **on this specific site**.
4. Learnings are appended to `~/.config/accelerate-ai-toolkit/journal.md` — a per-site knowledge base.
5. Other skills consult the journal before recommending, prioritising patterns that have won here and de-prioritising patterns that have lost.
6. Over weeks, the toolkit's advice becomes tailored to the site's real audience instead of generic marketing playbooks.

**Why it's not in v1:** needs 2+ weeks of real usage to produce signal worth learning from. The journal contract (format, rotation, consultation rules) needs careful design before shipping.

**Open question for v1.2:** does learning happen automatically after every experiment completes (needs a WordPress-side hook), or only when the user explicitly runs `/accelerate-learn`? The manual option ships first; automation may follow.

**Blocked on upstream Accelerate changes** — see [`AR-ACC-DRAFT.md`](AR-ACC-DRAFT.md) for the full proposal (historical `list-experiments` discovery, `experiment_id`-addressable results, generic `annotations` primitive, read-only `view_accelerate_analytics` capability). `AR-CLAUDE.md` §5.1 maps each prereq to the toolkit features that depend on it.

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
