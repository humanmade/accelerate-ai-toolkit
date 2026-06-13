# Changelog

## Unreleased

**Two install-doc corrections for source/headless setups, and `accelerate-test` create-flow hardening against two confirmed plugin gaps.**

- **Source checkouts need the MCP adapter installed manually.** Release builds of Accelerate bundle the WordPress MCP Adapter, but development checkouts do not — so the MCP route 404s even with the Abilities API feature flag on. `docs/installation.md` now documents the manual install (download `mcp-adapter.zip` from the WordPress/mcp-adapter releases, extract into `wp-content/plugins/`, `wp plugin activate mcp-adapter`) and the diagnostic tell: `/wp-json/wp-abilities/v1/abilities` lists the `accelerate/*` abilities while the MCP route 404s.
- **Headless / server-side callers must set a current user.** Every execution capability's permission callback evaluates the current WordPress user; over MCP that comes from the Application Password's user, but outside an authenticated request (WP-CLI `wp eval`, cron, custom automation) the current user is `0` and every call fails with a permission error. `docs/authentication.md` now tells those callers to set a user first (`wp_set_current_user()`, or `wp --user=admin`). Normal toolkit usage is unaffected.
- **`accelerate-test` backup step has a real fallback ladder.** `accelerate/get-variants` only returns content for blocks that *already* have variants — for a fresh block it returns an empty list, and no read ability exposes raw block content. The backup step now orders fallbacks explicitly: (a) `get-variants` if the block already has variants, (b) WP-CLI `wp post get <block_id> --field=content`, (c) ask the user to paste the current content from the editor — never guess or reconstruct it from memory.
- **`accelerate-test` now mandates an experiment-status verification after creation.** On current Accelerate versions `create-ab-test` can leave the experiment paused/draft (no start metas written), so no traffic is allocated and no results accrue — while everything *looks* created. The Creating flow now checks `experiment.status` via `get-variants` or `list-active-experiments`, refuses to tell the user the test is live unless status is `running`/`active`, and surfaces a plain-English instruction to start the test from the editor when it is paused. This is a skill-level guardrail (the `PostToolUse` hook still only checks for empty variants).
- **`source` annotation values are now defined unambiguously.** `accelerate-test` now spells out that `"ai"` = AI-generated one-shot (a human reviews before/while it goes live) and `"autopilot"` = AI-generated **and** part of a continuous unattended optimization loop (no human in the per-step loop) — and that `autopilot` *implies* `ai` (a superset, not a sibling), so anything surfacing provenance treats both as AI. Prevents two agents from diverging on what `source` means.
- **`AI:` prefix clarified to apply to the experiment title, not just variants.** A common mistake left the experiment title bare (e.g. `"Hero — reserve your seat"`) while only the variants were prefixed; the naming convention now states explicitly that both the experiment title and every variant title must start with `"AI: "`.

### Concept-driven testing — `accelerate-test` strategy rewrite

The variant-design and experiment-structure guidance now centres on **testing strategic concepts, not element-level levers**. The plumbing is unchanged (abilities, backup ladder, verification steps, annotations, `AI:` naming) — this is a strategy-layer upgrade that supersedes and integrates the earlier composed-visual, bold-challenger, effect-size, and anti-false-negative additions into one coherent system.

- **Variants are now concepts, not levers.** Each arm is a distinct strategic answer to "why should this visitor act?" — outcome / pain-relief framing vs social proof vs scarcity vs trust/safety — executed with full visual craft (imagery, color, typography, and CTA all serving the argument). The Planning flow opens with this principle and a progression ladder: on a fresh block, round 1 fields radically different concepts; only after a concept wins do later rounds refine within it. Grounded in the industry finding that most tests produce no measurable lift and the winners come from big strategic differences — with feature→outcome reframing named as the single highest-leverage move.
- **Evidence gate added.** Every concept must cite its grounding before it can run — audience composition (referrer/device/geo), on-page behavior, or the site's own language mined from its content and testimonials. A concept that can't name its evidence is not proposed. This supersedes intuition-led ideation.
- **Detectability (MDE) gate added before test creation.** Per-arm minimums (~25 conversions AND ~800+ visitors before any conclusion), a ~500 conversion-events/month floor for multi-arm tests, and a plausible-lift check: if a concept's realistic lift couldn't clear detection at the site's traffic, make it bolder or don't run it.
- **Arm count now scales with conversion volume.** With ample conversion volume, prefer ONE experiment with 3–5 distinct concept arms over a chain of 2-arm tests (each sequential test re-pays burn-in and calendar time). Low-volume sites stay at 2 bold arms. The honest constraint — more arms need proportionally more conversions — is stated plainly.
- **Stopping discipline tightened.** Declare a winner only on sustained ≥95% probability-to-be-best AND a lift worth caring about AND after per-arm minimums are met. Any reported lift over ~10% is treated as suspect (more likely error than miracle), with a confirmatory re-test recommended before big or irreversible decisions.
- **Losing is reframed as the system working.** Expectation-setting added (elite programs win ~8–20% of tests): a bold loser teaches a concept-level lesson; a timid loser teaches nothing. The existing anti-false-negative rule is integrated here, and outcomes are now recorded at the **concept** level ("which frame won"), not the micro-lever level.
- **Differentiation rubric reframed (`docs/design-standards.md`).** The Message dimension is now *concept distance*: Score 2 = a genuinely different strategic frame (a different motivation appealed to), Score 1 = the same frame reworded. Message and Visual/structural now read as one coherent system — the concept is what we argue, the composition is how we stage it — and the recently-added composed-visual Score 2 definition is preserved.

### Per-site memory and structure awareness

The toolkit now keeps a stable, per-site store that doesn't collide across sites, and grounds variant design in how a site *composes sections*, not only how it looks and speaks — so each testing pass builds on the last and variants can be structurally bold while staying unmistakably the same site.

- **Stable site key replaces the colliding hostname slug.** The journal/brand key used to derive from the site URL's hostname, so every site sharing a host (e.g. multiple local sites on `localhost`) collided and cross-contaminated each other's learning history. The canonical rule in `accelerate-learn` is now `<site-name-slug>-<theme-slug>-<url-hash>`: the slugified site name, the slugified active theme when the plugin exposes it (gracefully omitted on older plugins that don't, falling back to `<site-name-slug>-<url-hash>`), and a short stable hash of the full site URL. The theme is part of the key because a staging copy and its production original commonly share a name but differ in theme, and the design we optimize is tied to the theme. Bare hostname as the key is now explicitly banned.
- **Per-site subdirectory store.** Files moved from flat `journal-<slug>.json` / `brand-<slug>.md` names to a per-site subdirectory: `~/.config/accelerate-ai-toolkit/sites/<key>/journal.json`, `journal.md`, `brand.md`, and a new `palette.json`. The shared credentials `env` file is unchanged. Every skill and doc that referenced the old flat paths now points at `sites/<key>/` (`accelerate-test`, `accelerate-opportunities`, `accelerate-review`, `accelerate`, `docs/design-standards.md`, `docs/self-optimising.md`). Old flat journals are **abandoned, not migrated** — a site's first run under the new key starts fresh.
- **Richer learning journal (`schema_version` 2).** Each pattern now records a `compositions_tried` log — which structural recombinations were tested and how each did — plus carry-forward `notes`, so run N reads what run N-1 already settled and builds on it instead of re-testing it. The human-readable `journal.md` mirror summarizes the compositions.
- **Structural-vocabulary grounding in `accelerate-test` Planning.** A new step instructs the agent to learn the site's *structure*, not just its style: survey the site's existing synced patterns as a compositional palette (`get-site-context` lists them; `get-variants` returns each one's `raw_markup` and `inner_block_types`), see how the site already builds heroes, pricing, CTAs, and testimonials, then compose variants by recombining and extending that real vocabulary. This lets a variant be structurally very different from the control yet anchored to the site's design DNA, instead of a re-skin of one block. The surveyed palette is cached to `palette.json` so later passes reuse it.

### Decision discipline

Where the concept-driven rewrite made variant *design* stronger, this makes the agent's *decision discipline* binding. In practice agents declared winners on far too little data and read directional noise as signal — calling a "winner" off 7–10 conversions per arm, where the early leader routinely inverts as data accumulates. The Monitoring and Reviewing flows already carried per-arm minimums and an anti-false-negative rule; those are now hard gates the agent may not talk its way past, not guidance it can weigh against an exciting-looking number.

- **The stopping gate is now binding.** An agent MUST NOT declare a winner, conclude, harvest, or report any arm as winning / "the winner" / "+X% lift" unless **both** hold: every arm has crossed the per-arm minimums (~25 conversions AND ~800+ visitors), AND the leader is at ≥95% probability-to-be-best sustained across 2–3 consecutive checks. If either fails, the only valid conclusion is **"inconclusive — insufficient data"** and the test keeps running. Presenting an observed delta below the gate (e.g. "variant C is at 5.4% vs 3.9%") as a result or a reason to harvest is explicitly forbidden — a higher rate on a handful of conversions is noise, not evidence, and acting on it is worse than waiting.
- **"Not enough data" is no longer mistaken for "the tool is broken."** When a test isn't accumulating conversions fast enough to cross the gate, the correct response is to keep waiting, report it as still-resolving, or field fewer arms next time — never to conclude early and never to assume the platform or data pipeline is faulty. Added explicitly because agents had misattributed their own impatience to the tooling.
- **The bold-challenger rule binds on every round, not just the opener.** Refinement rounds (round 2+) must still field a composed (Visual Score 2) challenger: refining a winning concept means a fuller composition of that concept, never degrading to a single-lever tweak (e.g. changing only CTA button text on an otherwise identical block). A lone single-lever challenger is not permitted as the sole challenger in any round. This is tied to the existing anti-false-negative rule — a timid challenger cannot teach whether the concept works, so it may never stand alone.
- **Winner's-curse guard strengthened.** Any observed lift above ~10% is now treated as probably-an-error until confirmed; for durable or irreversible harvests, a confirmatory re-test of the apparent winner against control is recommended before applying.

## 1.4.3

**Fallback prose is now generic and jargon-free; `/accelerate-status` warns when Accelerate is out of date. All ability call shapes corrected against the upstream server registry.**

- **Fallback prose made generic across four skills.** The `accelerate-optimize-landing-page`, `accelerate-opportunities`, `accelerate-campaigns`, and `accelerate-diagnose` skills each contain a fallback block for when `accelerate/get-landing-pages` is unavailable. Previous wording cited an internal issue number and surfaced "known issue" language directly to marketers — both violations of Hard Rule 1. Fallbacks now proceed silently, show a single plain-English sentence only when the missing data materially affects the output ("Entry-page details aren't available on this site right now, so this view is based on top content and engagement instead."), and direct users to `/accelerate-status` if they want to investigate. No issue numbers, error text, or "known bug" language anywhere in skills/.
- **`/accelerate-status` Accelerate version detection.** A new detection layer warns when the connected site's Accelerate plugin is below the minimum supported version (4.2.0). Users running an older version are told which features require an upgrade before the session spends time on workflows that will silently fail. (Written by a parallel agent in `skills/accelerate-status/SKILL.md` — see that file for the layer details.)
- **Date window shapes corrected across all windowed call sites.** The `date_range` parameter is an object (`{preset: "30d"}` or `{start: "<ISO>", end: "<ISO>"}`) — bare strings like `"30d"` are rejected by the server. Every skill that makes windowed calls, plus `docs/ability-reference.md`, now uses the correct object form (`accelerate-connect` and `accelerate-learn` make no windowed calls and were untouched). A new "Common input shapes" section in `ability-reference.md` documents both forms and the two exceptions (`get-performance-summary` top-level `date_range_preset`; `get-content-diff` plain `{start, end}` objects with no preset support).
- **Exact-window rule added to the router skill.** `accelerate/SKILL.md` now states that any window the user names is served exactly — custom windows (e.g. "last 32 days") become ISO start/end objects, never silently rounded to a preset. Every answer confirms the window in a parenthetical.
- **`get-content-diff` documented with the true shape.** `post_ids` (array of integers) and `current_period` (`{start, end}` object, no presets) are required; `comparison_period` is optional. A literal example added to both the skill call and `ability-reference.md`.
- **`get-experiment-results` accepts `experiment_id`.** `block_id` OR `experiment_id` — at least one is required. Corrected in `ability-reference.md` and the abilities-reference skill.
- **`get-engagement-metrics` canonical key is `entity_id`.** All skill call sites updated from `post_id` to `entity_id`.
- **`get-audience-fields` now uses `fields` filter at relevant call sites.** `accelerate-personalize` and `accelerate-optimize-landing-page` now pass a targeted `fields` list rather than fetching the full payload. Field name corrections: `attributes.referer` (current referrer), `endpoint.Attributes.initialReferer` (first-touch). `endpoint.Attributes.referer` (non-existent) removed from all skills.
- **`list-experiments` date range semantics documented.** `date_range` filters on when experiments started, not when they were active.
- **`broadcast-content` gating note added.** The ability requires administrator access and cannot be called when the connected user is below that role, even if it appears in capability listings.
- **`get-source-breakdown` empty-sources fallback.** `accelerate-campaigns` and `accelerate-opportunities` now fall back to `get-traffic-breakdown` with `dimension: "referrer"` when `sources` is empty, with a plain note to the user.
- **Payload guidance added.** `get-site-context`: omit block data for analytics workflows; when creating/editing content prefer `blocks: "styled"` and use the new `patterns` list for reusable-block checks (`include_blocks: true` remains the fallback on older plugin versions). `get-audience-fields`: use `fields` filter for analytics workflows. `get-author-content`: default limit 50 is heavy — prefer 10–20 for routine use.
- **`accelerate-realtime` meta-commentary removed.** The leftover author note ("Actually:") in the spike investigation flow replaced with a clean instruction.
- **`accelerate-test` backup language clarified.** Model-internal steps are marked as such so WP-CLI commands don't surface to the user; the user-facing sentence stays plain.
- **`docs/maintenance.md` checklist item 7 added.** Ability-reference input shapes must be re-verified against `Helpers\get_date_range_with_preset_schema()` and per-ability registrations in altis-accelerate before each release.

## 1.4.2

**Stale shell environments no longer cause unexplainable connection failures.** Agents inherit env vars from the terminal they're launched in, so a terminal opened before credentials were saved (or updated) keeps feeding every new session the old values — "restart your session" advice loops forever. Found live: three Claude Code restarts in the same terminal kept re-inheriting a pre-1.3.0 bare-root `WP_API_URL` even though the env file on disk was correct.

- **`/accelerate-status` Layer 1 now detects stale environments.** When env vars are set, it compares the live value against the on-disk sources (`settings.local.json`, then the env file) and tells the user to open a new terminal / `exec zsh` instead of fruitlessly restarting — stopping before the lower layers test the wrong address.
- **`/accelerate-connect` step 8 splits the restart advice by agent.** Claude Code users restart the session (settings re-read at startup); shell-profile users (Codex) are told a new terminal window or `exec zsh` is required — restarting the agent in the same terminal re-inherits the old values.
- **`/accelerate-connect` re-links existing setups across folders.** `settings.local.json` is folder-scoped, so a connection made in one project silently didn't exist in another. The "already has credentials" path now checks the on-disk env file (not just the live shell), and offers a no-password re-link into the current folder's settings. Step 6a tells the user about the folder scoping upfront.
- **`/accelerate-status` Layer 8 fix line** mentions the new-terminal escape hatch for users who already restarted without effect.

## 1.4.1

**Healthy modern connectors no longer fail the connection probes.** The MCP Adapter's route is POST-only, so the `GET` used by the connect and status probes returns `405` when the connector is alive and well. The probe tables only recognised `200`/`401`, so a perfectly healthy adapter site fell through to the "unexpected response" error in `/accelerate-connect` and left `/accelerate-status` Layer 7 undefined — verified live against a production site running MCP Adapter 0.5.0.

- `/accelerate-connect` step 5b now treats `405`, `200`, or `401` as "route exists" for both the adapter and legacy routes, with a note explaining why `405` is the expected healthy signal.
- `/accelerate-status` Layer 7 accepts the same codes for full-URL and bare-root shapes, and the stale-config branch now requires legacy to be `404` before flagging the saved address as out of date.

## 1.4.0

**Commands are now skills.** Claude Code merged slash commands into the skills system and marks the `commands/` directory as legacy; this release completes the migration and removes the duplication it was causing — `/accelerate` previously appeared twice in the model's skill list (once from the command, once from the skill), wasting context and making routing ambiguous.

- **`commands/` directory removed.** `/accelerate` and `/accelerate-connect` were thin delegators to their same-named skills — and the connect delegator still described the pre-1.3 env-file-first credential flow. Both deleted; the skills already provide the same slash commands.
- **`/accelerate-status` is now a skill** (`skills/accelerate-status/SKILL.md`). Same slash name, same layered diagnostic, but the model can now invoke it on its own when it hits a connection problem, and the analyst agent's hand-off reference keeps working.
- **Root `plugin.json` removed.** It was a byte-identical copy of `.claude-plugin/plugin.json` that no agent reads — Claude Code reads `.claude-plugin/`, Codex reads `.codex-plugin/`. The maintenance checklist's version-sync step now covers the four real manifests.
- **`accelerate-abilities-reference` is now model-invocable** (dropped `disable-model-invocation`). The router and analyst agent both delegate to it; the flag was blocking exactly those consumers.
- **Manifest polish:** added `displayName: "Accelerate AI Toolkit"` to the Claude Code manifest, added an `argument-hint` to the router skill so the slash-command picker shows what to pass, and reworded the Gemini stub so it no longer promises "v1.1".

## 1.3.2

**Repo-level sync, hygiene, and resilience.** Catch-up sweep after #11–#13 to bring docs, model instructions, release manifests, and workflow assumptions back in line with the current upstream contract.

- **3-tier permission model** documented everywhere it was previously framed as 2 tiers. Added the `view_accelerate_analytics` capability (real read-only marketing role, no experiment-creation rights) to authentication, ability-reference, installation, and the router skill's permission-error guidance. Per-tier counts corrected: 27 view + 9 create + 3 manage = 39 (previously misreported as 35 + 3 = 38).
- **Install docs aligned** with the marketplace shipping. `docs/installation.md` now leads with `claude plugin install accelerate-ai-toolkit` and shows local-checkout as a fallback for Codex CLI and development. Roadmap entry marked as shipped.
- **Broken README link fixed** — `./prd/ROADMAP.md` (gitignored, doesn't ship) → `./internal/ROADMAP.md`.
- **Release versions synced to 1.3.2** across `plugin.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, and `package.json` (was 1.3.1 / 1.2.0 / 1.3.1 / 1.0.0 / 1.0.0).
- **Degraded-path fallbacks** added to the four skills that depend on `accelerate/get-landing-pages` — landing-page optimisation, opportunities, campaigns, diagnose. When the upstream bug `humanmade/accelerate#609` triggers, workflows continue with `get-top-content` + `get-engagement-metrics` + `search-content` instead of aborting.
- **New `docs/maintenance.md`** — a six-item checklist for re-verifying the upstream contract, ability count, per-tier counts, version manifests, README link integrity, and workflow fallbacks before each release.

Closes [#14](https://github.com/humanmade/accelerate-ai-toolkit/issues/14).

## 1.3.1

**`/accelerate-status` now reports the real Accelerate capability count.** Healthy connections previously surfaced "3 WordPress abilities" — that figure was the count of MCP wrapper tools, not the actual Accelerate surface, so it read as "barely working" when the toolkit was fully operational.

- Layer 9 (Live data check) now calls `mcp__wordpress__mcp-adapter-discover-abilities` first, filters to `accelerate/*`, and surfaces that count. Smoke tests against `get-site-context` and `get-audience-fields` still confirm the connection is usable.
- If `discover-abilities` errors but the smoke tests succeed, the status block stays confident — it just omits the count line rather than printing a misleading number.
- Synced docs to the current 39-ability registry: added `accelerate/list-experiments` (paginated historical experiment discovery) to `docs/ability-reference.md` and `skills/accelerate-abilities-reference/SKILL.md`, bumped the discovery section count and the total in `README.md`, `docs/installation.md`, `agents/accelerate-analyst.md`, and `docs/skill-development.md`.

Closes [#12](https://github.com/humanmade/accelerate-ai-toolkit/issues/12).

## 1.3.0

**No more mu-plugin workaround for the WordPress connector address.** Recent versions of the WordPress MCP Adapter changed their default route, which previously forced users to install a server-side PHP file to bring the toolkit back online. The upstream `@automattic/mcp-wordpress-remote` client now accepts a full connector URL in `WP_API_URL`; this release teaches the toolkit to use that.

- `/accelerate-connect` now probes both the modern adapter route and the legacy `wpmcp` route, then saves whichever full URL responds. The mu-plugin instructions are gone from the normal flow.
- `/accelerate-status` learns to recognise both legacy bare-root and new full-URL configs, derives the site root from whichever it finds, and tells you to rerun `/accelerate-connect` if your saved value is stale.
- Existing installs keep working: legacy `wordpress-mcp` sites with a bare-root saved value continue to pass status checks unchanged. Adapter sites that were saved as bare roots will be flagged once and fixed by a single rerun of `/accelerate-connect`.
- Documentation (`docs/authentication.md`, `docs/installation.md`, `docs/self-optimising.md`, `docs/examples/workflow-accelerate-learn.yml`) and the upstream-asks roadmap are updated to reflect the new contract.

Closes [#11](https://github.com/humanmade/accelerate-ai-toolkit/issues/11).

## 1.2.0

**Self-optimising recommendations.** The toolkit now learns what works on your specific site.

- New `/accelerate-learn` skill reads your completed A/B test results, classifies each by suggestion pattern, and writes a per-site learning journal.
- Other skills (opportunities, test planning, site review) consult the journal to tailor recommendations -- winning patterns get priority, losing patterns come with context.
- 15 canonical suggestion patterns tracked, with a strict 3-test minimum before any pattern influences recommendations.
- Optional weekly automation via a GitHub Actions template (`docs/examples/workflow-accelerate-learn.yml`) that creates a PR with journal updates for review.
- Tests created via the toolkit are now tagged with pattern annotations for reliable classification.
- Full guide at `docs/self-optimising.md`.

Also: updated AGENTS.md with current permission model (3-tier with `view_accelerate_analytics`), corrected hook documentation (command-based, not prompt-based), clarified skill invocation policy.

## 1.0.13

- Added a centralised output style guide (`docs/output-style.md`) so all skills present data consistently -- tables, priority cards, trend indicators, callouts, and hand-off prompts follow the same patterns.

## 1.0.12

- Added `/accelerate` command as a guaranteed entry point — type `/accelerate` followed by your question and the router fires every time, no reliance on auto-detection.
- Rewrote all skill descriptions to be 58% smaller and use natural trigger phrases instead of boilerplate. Skills should now auto-trigger more reliably even when many plugins are installed.

## 1.0.11

- Fixed the root cause of empty A/B test variants (upstream fix in Accelerate plugin). Creating tests, adding variants, updating variants, and creating personalization rules now correctly preserve content. The backup/verify/rollback safety net in the testing skill is kept as defence-in-depth.

## 1.0.10

- Fixed a bug where the A/B test safety hook interrupted Claude after every site data request, not just test creation calls. Claude now continues smoothly through multi-step analysis workflows without getting cut off.

## 1.0.9

- Credentials now persist reliably across session restarts. `/accelerate-connect` saves to Claude Code's `settings.local.json` (the documented mechanism for injecting environment variables into background processes) instead of relying on shell profile sourcing, which Claude Code doesn't read. The backup env file and Codex CLI shell profile flow are preserved for non-Claude-Code agents.
- `/accelerate-status` now detects when credentials are saved but the session needs a restart to load them.

## 1.0.8

- Setup and status diagnostics now detect shell tools that intercept Node.js commands (checks the actual binary path, not just the version number).
- `/accelerate-status` now separates "Accelerate not installed" from "WordPress connector not registered" instead of showing a generic message when both fail.
- Removed technical jargon from all user-facing diagnostic messages (connection checks, status output, README notes).
- Permission diagnostic now correctly describes the two-tier access model instead of a blanket "Editor or higher".

## 1.0.7

- A/B testing and landing page optimisation skills now check whether the target content is a reusable block before proposing changes. If it isn't, the toolkit explains the requirement and walks you through converting it -- instead of spending time on a hypothesis you can't test.

## 1.0.6

- The router skill can now properly delegate to workflow skills. Previously, all sub-skills blocked programmatic invocation, forcing the agent to work around the skill system. Setup (`/accelerate-connect`) and advanced reference remain manual-only.

## 1.0.5

- README and installation docs now explicitly mention the MCP Adapter bundling and endpoint compatibility note.

## 1.0.4

- `/accelerate-status` is now a layered diagnostic that checks environment variables, npx, site reachability, authentication, endpoint compatibility, and MCP tool availability in order. It reports the first failing layer with a specific fix instead of a generic "run /accelerate-connect".

## 1.0.3

- `/accelerate-connect` now checks that `npx` is working correctly before completing setup. If another tool in your shell is intercepting `npx`, the setup wizard explains the problem instead of failing silently.
- `/accelerate-status` diagnoses `npx` interception when the connection appears missing.
- Installation troubleshooting updated with workaround for `npx` interception (project-level override with the full binary path).

## 1.0.2

- `/accelerate-connect` now double-quotes all values in the credentials file, fixing a bug where Application Passwords (which always contain spaces) were truncated by shell word-splitting.

## 1.0.1

- `/accelerate-connect` now detects when your site's WordPress connector plugin uses a different address than expected (common with MCP Adapter 0.4.1+) and provides clear instructions to fix it, instead of failing silently.
- `/accelerate-status` gives better guidance when a connection fails due to this endpoint mismatch.
- Installation docs updated with troubleshooting for the most common first-run connection failure.

## 1.0.0

- Initial release: 12 skills covering site review, diagnosis, opportunities, landing page optimisation, A/B testing, personalisation, campaigns, content planning, and real-time monitoring.
