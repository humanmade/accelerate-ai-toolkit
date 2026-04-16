# AR-CLAUDE.md

**Design document for v1.2 — self-optimising skill loop (autoresearch integration)**

| Field | Value |
|---|---|
| Status | Design — not yet implemented |
| Owner | Human Made |
| Last updated | 2026-04-12 |
| Target release | v1.2 |
| Inspiration | [`karpathy/autoresearch`](https://github.com/karpathy/autoresearch) |
| Prerequisite | v1.0 shipped, twelve skills in place, `../altis-accelerate/` Abilities API live |

This document is a standalone brief. It is **not code**. No skills, workflow templates, or documentation referenced here have been written yet. When implementation starts, this file is the input. When v1.2 ships, the items in the "Implementation checklist" section become the sign-off.

---

## 1. TL;DR

Accelerate ships a set of generic marketing playbooks. v1.2 makes them **self-optimising per site**: the toolkit reads the site's completed A/B test results, classifies each experiment into one of ~15 canonical "suggestion patterns" (rewrite headline, move CTA, add social proof, etc.), records hit rate and lift in a per-site journal file, and teaches the other skills to consult that journal before recommending. A marketer who has been using the toolkit for six weeks sees suggestions tailored to what has actually worked on their site, not the generic playbook.

The loop runs manually by default (`/accelerate-learn`), and optionally on a weekly schedule via a GitHub Actions workflow template we ship under `docs/examples/`. The marketer's default monitoring path is the agent itself — *"what have you learned about my site lately?"* — no GitHub account required.

---

## 2. Context and motivation

### 2.1 The gap this fills

Every skill in v1.0 is a generic playbook. `accelerate-optimize-landing-page` tells every user the same ordered list of things to try on a bouncing landing page. `accelerate-test` proposes the same kind of hypotheses to everyone. `accelerate-opportunities` applies the same five rules to everyone's data.

This is correct for month one of using the toolkit. By month three it's weak: the toolkit already has ~5–10 concluded experiments per active site, each of which is a signal about what actually works for *this* audience. That signal sits in Accelerate's ClickHouse database and in the user's experiment history, but no skill currently reads it back to improve future recommendations.

### 2.2 Why now

Three things are true at the same time:

- **Accelerate already ships the measurable outcome.** `get-experiment-results` returns Bayesian `has_winner` and per-variant `probability_to_be_best`. We don't need to build a significance layer — we consume one that's already there.
- **Karpathy's autoresearch demonstrated the loop pattern publicly.** The idea of an agent iterating against a fixed metric, keeping wins, and dropping losses is now a vocabulary people understand.
- **`anthropics/claude-code-action@v1`** is GA (August 2025), which makes scheduled agent runs via GitHub Actions a five-minute setup instead of a custom-integration project.

Combined, the design space is unusually small. Almost everything we need exists; we're wiring it together.

### 2.3 What v1.2 is NOT

- Not a cross-site learning system. Each site has its own journal. A pattern that wins on site A does not automatically apply to site B. Explicit non-goal.
- Not a recommendation engine that shows up in the WordPress admin UI. Output is the journal file plus an in-agent summary.
- Not continuous real-time learning. Even in the "automated" variant, the loop runs weekly at most — WordPress A/B tests take 7–14 days per experiment, and running the loop faster than that wastes Claude credits with no signal.
- Not a replacement for the existing mutation skills. `accelerate-learn` is read-only — it never creates, modifies, or stops experiments. The existing `accelerate-test` and `accelerate-personalize` skills remain the only surfaces that mutate site state, and their confirmation-before-mutation rules are unchanged.

---

## 3. What autoresearch actually is

This is the most misunderstood part of the problem space, so it's worth being precise.

`karpathy/autoresearch` is a **~630-line Python repo** that demonstrates an autonomous loop for LLM training experiments on a single GPU. Not a library. Not a framework. Not a service. A repo template that a researcher clones, installs (`uv sync`, requires Python 3.10+, PyTorch, NVIDIA GPU), and runs.

The repo ships three files that together define the loop:

- **`prepare.py`** — frozen. Data prep and utility code the agent never touches.
- **`train.py`** — the mutation surface. This is the only file the agent modifies.
- **`program.md`** — human-editable spec. Contains the research objective, constraints, and stopping criteria. The agent reads this at the start of each iteration and respects it as guardrails.

A single "experiment" inside autoresearch looks like this:

1. Agent reads `train.py` and the git log.
2. Agent hypothesises a change (e.g. "reduce learning rate from 1e-3 to 9e-4").
3. Agent modifies `train.py`.
4. Agent runs training with a fixed 5-minute budget.
5. Training finishes; validation loss is measured as `val_bpb`.
6. If `val_bpb` improved: agent runs `git commit`.
7. If `val_bpb` stalled or worsened: agent runs `git reset --hard`.
8. Agent loops.

Karpathy's overnight run drove val_bpb from 0.9979 to 0.9697 over 126 experiments. A two-day run reached ~700 experiments and produced a cumulative 11% efficiency improvement on the nanoGPT leaderboard.

**Key sources:**

- Repo README: <https://github.com/karpathy/autoresearch>
- Data Science Dojo write-up: <https://datasciencedojo.com/blog/karpathy-autoresearch-explained/>
- SkyPilot on distributed runs: <https://blog.skypilot.co/scaling-autoresearch/>
- Fortune on the Karpathy Loop: <https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/>

### 3.1 Authority for the "not a dependency" claim

Autoresearch is **not installable as a package**. There is nothing on npm, PyPI, or Packagist. You cannot `composer require` it. The useful thing is the loop pattern; the code is a concrete reference implementation for a specific domain (ML training) and does not generalise without rewriting.

This is what we mean when we say we're "inspired by" autoresearch — we're porting the pattern, not depending on the repo.

---

## 4. What ports, what doesn't

### 4.1 What ports cleanly

- **Hypothesis → mutate → measure → keep-or-discard loop.** Domain-agnostic.
- **A journal file as persistent memory.** Autoresearch uses git commits + `results.tsv`; we use a single markdown file plus (optionally) the user's own git repo when running under GitHub Actions.
- **A human-editable program.md equivalent.** In our case, the `accelerate-learn` skill body itself plus the pattern taxonomy constitute the spec. The user does not edit a `program.md` file directly — they don't need to, because they don't tune the loop, they consume its output.
- **Metric-driven ratchet.** Keep what wins, demote what loses. We implement it per-pattern rather than per-commit.
- **Opt-in automation.** Autoresearch runs autonomously overnight once a human kicks it off. Our loop is manual by default and scheduled as an opt-in.

### 4.2 What breaks, and the workaround for each

| Autoresearch assumption | Breaks because | Our workaround |
|---|---|---|
| 5-minute experiments | WordPress A/B tests take 7–14 days to reach Bayesian significance | Run the loop weekly at most. Throughput is ~4 learnings/month, not ~100/night. That's fine — the value per learning is much higher. |
| Deterministic metric (val_bpb) | Conversion rate is stochastic; point improvements may be noise | Lean on Accelerate's own Bayesian engine. Only count experiments that return `has_winner: true`. The significance layer already exists upstream. |
| Fully autonomous | A bad variant shown to real users cannot be reverted | `accelerate-learn` is read-only. It writes a journal file, never mutates experiments. All mutations still go through the existing confirmation-gated skills. |
| `git reset --hard` rollback | Reverting a marketing change has real-world cost (reputation, lost conversions) | Not applicable — the loop never makes marketing changes. It only updates the recommendation priority for future suggestions. |
| Runs on user's local GPU overnight | Marketers don't have GPUs and don't run processes overnight | Either run the loop manually from inside the agent (no compute needed beyond Claude API) or schedule it on GitHub Actions (free tier has 2,000 min/month, plenty for a weekly run) |
| Pure code mutation | WordPress state is split across posts, options, custom tables, and plugin-managed entities | Not applicable — we don't mutate site state at all. |

The pattern survives the port. What we lose is real-time feedback; what we gain is a loop that's safe to run at a marketer's cadence.

### 4.3 Community adoption (for context)

Three Claude Code plugin forks apply the autoresearch pattern to engineering metrics, all published in the first 30 days after the original repo landed:

- <https://github.com/uditgoenka/autoresearch> — general optimisation target
- <https://github.com/proyecto26/autoresearch-ai-plugin> — Claude Code plugin
- <https://github.com/drivelineresearch/autoresearch-claude-code> — Driveline Research fork

MindStudio published a conceptual blog post on applying the pattern to landing page copy testing (<https://www.mindstudio.ai/blog/self-improving-ab-testing-agent-landing-pages-ad-copy>), but there's no working implementation attached.

**No published production case study** adapts autoresearch to a WordPress / marketing A/B testing context. v1.2 will be the first meaningful reference implementation — not a follower. Plan accordingly in the docs (we get to define the template, which means we should get it right).

---

## 5. Verified infrastructure facts

Things the plan relies on that have been checked against primary sources.

| Fact | Source |
|---|---|
| `anthropics/claude-code-action@v1` exists and is GA | <https://github.com/anthropics/claude-code-action>, <https://github.com/marketplace/actions/claude-code-action-official> |
| Action supports `schedule` and `workflow_dispatch` triggers, needs only `anthropic_api_key` and `prompt` as minimum | Action README, confirmed via WebFetch |
| Action auto-detects execution mode; no `mode: agent` parameter needed | Action README ("Intelligent Mode Detection") |
| GitHub Actions scheduled workflows: *"The shortest interval you can run scheduled workflows is once every 5 minutes."* | <https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule> |
| GitHub Actions scheduled workflows: *"Scheduled workflows run on the latest commit on the default branch."* | <https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule> |
| `get-experiment-results` returns a **richer payload than I first documented**: `block_id`, `experiment_type`, `goal`, `status`, `started_at` (ISO 8601), `ended_at` (ISO 8601 or null), `traffic_percentage`, `confidence_threshold`, `has_winner`, `winner_variant_index`, `variants` (each with `impressions`, `conversions`, `conversion_rate`, `p_value`, `probability_to_beat_control`, `is_winner`), `recommendation`, `edit_url`. The learning loop can use `ended_at` directly as the journal's `last_tested_at` field. | `../altis-accelerate/inc/abilities/execution.php:1296–1435` |
| `get-experiment-results` **silently falls back to "most recent completed experiment for this block"** when no active experiment is running on that block. For a block that has had multiple experiments over time, only the latest is retrievable — older experiments on the same block are invisible via this ability. This is the motivation for prereq 2 in §5.1 below. | `../altis-accelerate/inc/abilities/execution.php:1358–1372` |
| An internal `Experiments\Experiment::query()` method already exists with support for `subject_post_id`, `test_id`, `status`, `per_page`, `order_by`. This is the substrate for a proper `list-experiments` ability (prereq 1 in §5.1) — upstream does not need to build a new model layer, only expose the existing one as an ability. | referenced from `../altis-accelerate/inc/abilities/execution.php:1360–1370` (the Experiment model lives in the plugin's experiments subsystem) |
| `get-site-context.site` returns only `name`, `description`, `url`, `language`, `has_theme_json`. **No stable site slug or site ID.** Per-site journal filenames must be derived from `url` by the toolkit today, which is what prereq 6 in §5.1 addresses. | `../altis-accelerate/inc/abilities/discovery.php:1215–1225` |
| `create-ab-test` stores only `_xb_abtest`, `_xb_type`, `_xb_goal`, `_xb_traffic_percentage`, `_xb_hypothesis` as post meta. **No generic annotations, labels, or tags primitive exists** — consumers have nowhere to attach structured metadata that can be read back. This is the motivation for Prereq 3 in §5.1: a universal bag-of-strings metadata primitive, not a toolkit-specific field. | `../altis-accelerate/inc/abilities/execution.php:676–685` |
| `list-active-experiments` **returns all experiments the site has ever created, not just active ones.** It queries `wp_block` posts filtered on `_xb_abtest` / `_xb_personalization` meta existence. `stop-experiment` at `execution.php:1591–1676` does not delete those meta flags when it ends a test, so stopped and declared-winner experiments stay in the result set. The ability's `output_schema` includes a `status` field that callers can filter on. Silent limits: `posts_per_page: 100` (older experiments are dropped once a site crosses 100 total), no date filter on input, no pagination. | `../altis-accelerate/inc/abilities/discovery.php:200–280`, `../altis-accelerate/inc/abilities/execution.php:1591–1676` |
| `query-events` exists for raw event queries | `../altis-accelerate/inc/abilities/query.php:37` |
| `wp_register_ability` permission callbacks for all execution abilities resolve to `edit_posts` or `manage_options` | `../altis-accelerate/inc/abilities/namespace.php:88–112` |
| No `.github/workflows/` folder currently in the toolkit repo | verified via `ls` |
| No `accelerate-learn` skill currently exists | verified via `ls skills/` |
| The original v1 ROADMAP mentioned a placeholder skill file that was never actually written | confirmed via repo state |

### 5.1 Upstream prerequisites

The current Accelerate ability surface has several gaps that bound what v1.2's learning loop can reliably claim. This section catalogues each gap as an ideal upstream addition. v1.2 ships a heuristic bridge over these gaps; the robust version is gated on them landing. Numbering follows the parallel AR-CODEX design doc so the two documents cross-reference cleanly.

**Framing.** The goal is not to turn the WordPress plugin into a generic agent runtime — see "Non-goals for upstream" at the end of this section. Upstream should provide clean experiment history, metadata, events, and permissions. The toolkit should own learning interpretation and the user-facing experience.

#### Prereq 1 — First-class historical experiments surface

The current `list-active-experiments` ability happens to return historical experiments as a side effect (see §5 verified facts), but it is capped at `posts_per_page: 100`, has no date filter, and has no pagination. `get-experiment-results` requires a `block_id` and falls back to "the most recent completed experiment for that block" when no active one is running, which hides older experiments on the same block completely.

**What upstream should add:** a new `accelerate/list-experiments` ability.

Proposed input schema:

- `status` — enum: `active` / `completed` / `paused` / `all`
- `type` — enum: `abtest` / `personalization` / `all`
- `date_range` — `since` and `until` (ISO 8601)
- `post_id` — convenience filter for "experiments for this specific block"
- `subject_post_id` — the post/page the experiment runs on
- `annotation_key` + `annotation_value` — see Prereq 3, filter by any annotation key/value pair (e.g. `annotation_key=toolkit:pattern&annotation_value=headline_match_intent`)
- `offset` + `limit` — pagination

Proposed output per item: stable `experiment_id`, `block_id` (subject), `subject_post_id`, `started_at`, `ended_at`, `status`, `type`, `goal`, `winner_variant_index`, `has_winner`, `annotations` (the generic bag from Prereq 3).

**Good news from source inspection:** the internal `Experiments\Experiment::query()` method already supports `subject_post_id`, `test_id`, `status`, `per_page`, and `order_by`. The ability is therefore a thin wrapper around existing model code, not a new storage layer. Upstream lift is small.

Proposed location: `../altis-accelerate/inc/abilities/discovery.php`, alongside (or replacing) `list-active-experiments`. The current ability can be kept as a thin alias for `list-experiments` with `status: active`.

#### Prereq 2 — Experiment results addressable by experiment ID

Today `get-experiment-results` takes only `block_id`. When multiple experiments have been run on the same block over time, only the latest completed one is retrievable via this ability (`execution.php:1358–1372`). For a learning loop that needs to walk a site's full history, this is a hard wall.

**What upstream should add:** accept an optional `experiment_id` input on `accelerate/get-experiment-results`, which takes precedence when provided. Keep the `block_id` path as a convenience for the common "most recent experiment on this block" case. Require exactly one of the two to be provided. The internal Experiment model already supports fetching by experiment row, so the change is small.

This also removes the ambiguity where the same block has a running experiment and historical completed ones — callers can explicitly request *which* experiment they want results for.

#### Prereq 3 — Generic annotations/labels on experiments

Today the `hypothesis` field on `create-ab-test` is free text, and there is no structured metadata on experiments at all — no way for a consumer to attach machine-readable annotations, labels, tags, or origin information to a test for later retrieval. Any classification later must parse free text, which is fragile, ambiguous, and unstable across phrasings.

**What upstream should add:** a **generic annotation primitive** on experiments. Not a fixed set of named fields with a fixed vocabulary — upstream should not have to know what a "recommendation pattern" is, or what "toolkit source" means. Instead, upstream exposes a minimal bag-of-strings abstraction that any consumer can populate with whatever structured metadata that consumer cares about.

**The key design principle:** upstream owns *"there is a way to attach structured metadata to an experiment and read it back."* The toolkit (and any future consumer) owns *"here is what we choose to put in that bag."* Upstream never commits to a vocabulary, never defines enums, never has to learn what any particular consumer is doing with the field.

**Concrete proposal — one of the following shapes, whichever upstream prefers:**

- **Option A: key/value annotations map.** A JSON object of string keys to string values. Keys use a namespace convention (`toolkit:pattern`, `toolkit:source`, `seo:variant_type`, etc.) so different consumers coexist without collisions. Stored as `_xb_annotations` post meta (JSON-serialised).
- **Option B: flat label list.** An array of strings, each of the form `"namespace:key=value"` or just `"namespace:tag"`. Stored as `_xb_labels` post meta. Simpler storage, less structure.
- **Option C: WordPress terms on a custom taxonomy.** Reuse WordPress's native taxonomy system. `wp_set_post_terms($block_id, ['toolkit:pattern:headline_match_intent', ...], 'accelerate_labels')`. Most WordPress-native but requires a taxonomy registration.

Option A (key/value map) is the cleanest abstraction and is my recommendation — it maps directly to how most structured-metadata APIs work, it's easy to serialize/deserialize, and it supports both "set a known key" and "discover what keys are on this experiment" lookups. But upstream is free to pick the shape that fits Accelerate's existing patterns.

**Integration with the rest of the surface:**

- `create-ab-test` accepts an optional `annotations` / `labels` input.
- `get-experiment-results` returns the annotations verbatim as part of its output.
- `list-experiments` (Prereq 1) supports filtering by annotation key/value (e.g. "give me all experiments with `toolkit:pattern=headline_match_intent`"). This is where upstream's extensible bag becomes most valuable to consumers — you can query on toolkit-specific keys upstream never had to define.

**What the toolkit will put in the bag (v1.3):**

- `toolkit:pattern` — the toolkit's `pattern_id` value (e.g. `headline_match_intent`). Maps to §9 taxonomy. Must-have.
- `toolkit:source` — which toolkit skill proposed the test (e.g. `accelerate-opportunities`, `accelerate-optimize-landing-page`, `accelerate-test`). Nice-to-have.
- `toolkit:surface` — how the experiment entered the system (e.g. `accelerate_toolkit` vs `wordpress_admin`). Nice-to-have.
- `toolkit:version` — the toolkit version that created the test, for future migrations.

The canonical enum values for `toolkit:pattern` live in the toolkit's §9, not in upstream. When the toolkit adds a new pattern in a future release, upstream does not need to ship a corresponding release — it already stores whatever string the toolkit puts in the bag.

**Why this is strictly better than my earlier "named string fields" proposal:**

- **Upstream never has to agree on a vocabulary.** `toolkit:pattern` is a string key upstream stores verbatim. A future SEO experimentation tool can use `seo:variant_type` without any upstream change.
- **Multiple consumers coexist cleanly.** If another plugin also wants to annotate experiments, it uses its own namespace (`tracking:campaign_id`, `analytics:cohort`) without colliding.
- **Consumer taxonomies evolve independently of upstream release cycle.** The toolkit adds a new pattern → the toolkit ships → upstream is untouched.
- **Filtering still works.** `list-experiments` supports `annotation_key` and `annotation_value` filters, which means any consumer can do "show me experiments where my key has my value" without upstream knowing what the key means.

This turns Prereq 3 from a toolkit-shaped ask ("support our classification needs") into a universal experimentation-metadata primitive that any future learning loop, agent system, or analytics consumer can build on.

**v1.2's workaround for Prereq 3:** when `accelerate-test` creates a test via `create-ab-test`, it prepends a structured marker to the free-text `hypothesis` field — e.g. `[pattern:headline_match_intent] Rewrite the homepage hero to match the pricing search term`. The `accelerate-learn` skill reads the `[pattern:...]` marker first and falls back to keyword matching only if no marker is present. When the upstream annotations primitive lands, the skill reads `annotations['toolkit:pattern']` directly and deprecates the marker parsing. `toolkit:source` and `toolkit:surface` have no v1.2 bridge — they simply don't exist until the upstream annotation bag ships, at which point the toolkit starts populating them.

#### Prereq 4 — Complete lifecycle fields on experiment results

Partially satisfied today. `get-experiment-results` already returns `started_at`, `ended_at`, `goal`, `status`, `has_winner`, `winner_variant_index`, `traffic_percentage`, `confidence_threshold`, and per-variant metrics (`impressions`, `conversions`, `conversion_rate`, `p_value`, `probability_to_beat_control`, `is_winner`). Good enough for v1.2's learning loop.

**Still missing (for future improvements):**

- `created_at` — when the experiment was first created (distinct from `started_at`, which is when traffic started flowing). Enables "time from creation to first run" measurement.
- `status_changed_at` — most-recent state change. Enables recency weighting and "stale test" detection.
- `confidence_at_close` — the Bayesian probability-to-be-best for the winner at the moment the experiment was stopped or auto-closed. Useful for distinguishing "overwhelming win" from "barely significant win".
- `close_reason` — enum: `auto_significance` / `manual_stop` / `declared_winner` / `timed_out` / `paused_indefinitely`. Enables separating clean wins from manually-stopped experiments (which may be biased).

None of these block v1.2. They're documented so the v1.3 runner has a known list of improvements to ask for.

#### Prereq 5 — Webhook or event hooks for experiment state changes

Polling is fine for weekly learning runs, but event-driven would be more efficient and more responsive.

**What upstream should add:**

- A WordPress action hook (e.g. `accelerate_experiment_completed`) fired when an experiment reaches statistical significance or is manually stopped.
- A WordPress action hook (e.g. `accelerate_experiment_winner_declared`) fired when a winner is declared via `stop-experiment` with `action: declare_winner`.
- A webhook mechanism that maps these action hooks to outbound HTTP POSTs with a payload containing `experiment_id`, `subject_post_id`, `block_id`, `status`, `winner_variant_index`, `pattern_id`, and timestamps.

For the toolkit, this would let a GitHub Actions `repository_dispatch` or a webhook endpoint on the user's own infra trigger a learning-loop run within minutes of an experiment concluding, instead of waiting for the weekly cron. Lower priority than prereqs 1–3.

#### Prereq 6 — Dedicated read-only analytics capability

Today, `can_view_analytics()` and `can_create_experiments()` in `../altis-accelerate/inc/abilities/namespace.php:88–101` both resolve to `current_user_can('edit_posts')`. A user granted "analytics access" in practice also has experiment-creation rights, which collapses two roles into one.

**What upstream should add:** a first-class `view_accelerate_analytics` WordPress capability, granted to a new WordPress role (e.g. "Accelerate Analyst") or additively to existing roles. `can_view_analytics()` is updated to check the new capability. `can_create_experiments()` continues to require `edit_posts`.

Impact:

- Agencies running the toolkit for clients can grant read-only analytics access without also granting the ability to create or stop experiments.
- The `accelerate-learn` skill, which is read-only by design, can run under an account that genuinely has no mutation rights — defence-in-depth.
- `docs/authentication.md` in the toolkit gets a proper three-tier story instead of the current two-tier compromise.

This is the most-requested upstream improvement from a product-safety standpoint.

#### Prereq 7 — Learning-friendly summary ability (optional)

Even with prereqs 1–4, the toolkit's learning loop would still have to aggregate raw per-experiment results into per-pattern hit rates. Upstream could ship a pre-aggregated summary ability that does this server-side.

**What upstream should add:** `accelerate/get-experiment-history-summary` ability.

Proposed input schema:

- `date_range` — `since` / `until`
- `group_by` — enum: `pattern_id` / `page` / `source` / `goal` / `none`
- `status_filter` — enum: `completed` / `has_winner` / `all`

Proposed output: an array of groups, each with `count`, `wins`, `losses`, `inconclusive`, `avg_lift_percent`, `last_tested_at`, and the group key (e.g. the `pattern_id` string).

**Why lower priority:** the v1.2 runner can aggregate raw results from `list-experiments` + `get-experiment-results` itself, and does it in a few dozen lines of logic. Moving aggregation upstream is a *performance and convenience* win, not a correctness win. Nice to have; not blocking.

Also, pushing aggregation upstream means upstream has to commit to what counts as a "win", which may not match the toolkit's four-state model from §8.2 (`won` / `lost` / `mixed` / `inconclusive`). Any summary ability should return raw counts and let the caller apply their own status rules.

#### Prereq 8 — Canonical site identity in `get-site-context`

The `site` object returned by `get-site-context` contains `name`, `description`, `url`, `language`, `has_theme_json`, but **no stable site identifier**. The toolkit must derive a slug from `url` today to produce journal filenames like `journal-example-com.json`.

**What upstream should add:** a `slug` (or `site_key`) field on the `site` object. Proposed shape:

- `slug` — lowercased, URL-safe, derived from the WordPress home URL (`home_url()`) with protocol stripped, `www.` stripped, dots replaced with hyphens, port number stripped. For multisite, the blog ID is appended after a separator.
- Stable across runs as long as the site's home URL doesn't change.
- Optionally, a `site_key` field that is truly immutable (a hashed identifier stored in a site option the first time it's requested).

Lower priority than prereqs 1–6. The toolkit can slugify `url` itself in v1.2. Documented here because AR-CODEX raised it and it's a real improvement, just not load-bearing.

#### Non-goals for upstream — what Accelerate should NOT own

Even in the ideal version, the Accelerate plugin should not own the entire learning loop. Explicit non-goals so the upstream surface stays small:

- Upstream should **not** write the toolkit journal file. Journal format, schema version, and file location are toolkit concerns.
- Upstream should **not** decide how downstream skills weight patterns. Consumption rules (minimum sample size, four-state classification, which patterns get weighted up vs ignored) live in the toolkit's skill bodies.
- Upstream should **not** mutate future recommendations automatically based on learned state. All mutations go through the existing confirmation-gated skills in the toolkit.
- Upstream should **not** turn the WordPress plugin into a generic agent runtime. If a toolkit-style learning loop needs to run server-side, it runs as a separate process on separate infrastructure — WordPress hosts data and exposes abilities; it does not host the agent.

Upstream's job is to provide clean experiment history, structured metadata, lifecycle fields, event hooks, proper permissions, and a canonical site identity. The toolkit's job is to interpret that data and present it to the user.

---

## 6. User decisions locked in

Settled during the design session:

1. **Shipping strategy: all-at-once.** v1.2 ships the skill, the GitHub Actions workflow template, the docs, and the ROADMAP update together. Not phased. If any part slips, all of it slips.

2. **Journal storage: local-first with optional git mirror.** Primary storage is `~/.config/accelerate-ai-toolkit/journal-<site-slug>.md` on the user's machine, site-scoped. The optional GitHub Actions workflow mirrors the journal to a user-owned git repo for multi-machine or agency use. The toolkit never stores journals centrally.

3. **Default monitoring: the agent itself.** The marketer asks *"what have you learned about my site lately?"* or runs `/accelerate-learn` to trigger a new learning pass. No GitHub account required for the default path. GitHub Actions and Slack webhooks are opt-in for power users and agencies.

4. **Feedback loop cadence: weekly (at most).** Running the loop more often than that wastes Claude credits with no signal, because experiments don't change state faster than that.

5. **Mutation boundary: the learning loop never mutates experiments.** It reads and writes the journal file only. All mutations stay inside the existing mutation skills, which already have confirmation rules.

---

## 7. Architecture

```
                                 ┌───────────────────────────┐
                                 │   WordPress + Accelerate  │
                                 │   Bayesian A/B results    │
                                 └──────────────┬────────────┘
                                                │ MCP (via @automattic/mcp-wordpress-remote)
                                                ▼
    ┌───────────────────────┐        ┌───────────────────┐
    │  /accelerate-learn    │───────▶│  accelerate-learn │
    │  (slash command or    │        │   workflow skill  │
    │   agent prompt)       │        └─────────┬─────────┘
    └───────────────────────┘                  │
                                               │ reads experiments,
                                               │ classifies patterns,
                                               │ computes hit-rate + lift
                                               ▼
                              ┌──────────────────────────────┐
                              │  ~/.config/accelerate-       │
                              │   ai-toolkit/                │
                              │   journal-<site-slug>.json   │  ← source of truth
                              │   journal-<site-slug>.md     │  ← derived, human-readable
                              └──────────────┬───────────────┘
                                             │ other skills parse the .json,
                                             │ the marketer reads the .md
                    ┌────────────────────────┼─────────────────────┐
                    ▼                        ▼                     ▼
           ┌──────────────────┐    ┌──────────────────┐   ┌──────────────────┐
           │ accelerate-      │    │ accelerate-      │   │ accelerate-      │
           │ opportunities    │    │ test             │   │ review           │
           │ (prioritisation) │    │ (propose tests)  │   │ (check-in)       │
           └──────────────────┘    └──────────────────┘   └──────────────────┘

           Automation (optional, opt-in, user-owned):

           ┌──────────────────────────────────────────┐
           │ .github/workflows/accelerate-learn.yml   │   copied from
           │ (user-owned repo, user-owned secrets)    │   docs/examples/
           │ cron: weekly Sunday night                │
           │ creates PR with journal diff             │
           └──────────────────────────────────────────┘

           v1.3 architectural evolution (not in v1.2):
           Once the upstream generic annotations primitive lands on
           create-ab-test, the classification step becomes a pure
           dictionary lookup and the runner can be a plain Python/Node
           script instead of a Claude agent.
```

---

## 8. Journal format (design contract)

The journal is **two files**, not one:

1. **`journal-<site-slug>.json`** — machine-readable source of truth. The `accelerate-learn` skill writes it. Every other skill parses it. Deterministic schema.
2. **`journal-<site-slug>.md`** — human-readable summary derived from the JSON on every run. The user reads it. No skill parses it. Regenerated from the JSON each time the learning loop runs.

Splitting the journal prevents skills from doing fragile regex parsing of markdown and gives the user a clean readable view they never have to touch.

### 8.1 JSON source of truth — schema

`~/.config/accelerate-ai-toolkit/journal-<site-slug>.json`, `chmod 600`.

```json
{
  "schema_version": 1,
  "site": {
    "slug": "example-com",
    "name": "Example Site",
    "url": "https://example.com"
  },
  "last_updated": "2026-04-12T03:14:00Z",
  "stats": {
    "total_experiments_considered": 18,
    "concluded_with_winner": 11,
    "still_running": 3,
    "dropped_as_too_thin": 4
  },
  "patterns": [
    {
      "pattern_id": "headline_match_intent",
      "display_name": "Rewrite headline to match referrer intent",
      "status": "won",
      "tests_total": 5,
      "tests_won": 4,
      "hit_rate": 0.8,
      "avg_lift_percent": 23.0,
      "last_tested_at": "2026-03-12",
      "last_winning_block": { "id": 142, "title": "Homepage hero" },
      "notes": "Biggest wins on pricing and feature-tour pages. Smaller effect on the homepage."
    },
    {
      "pattern_id": "urgency_copy",
      "display_name": "Add urgency / scarcity copy to CTAs",
      "status": "lost",
      "tests_total": 3,
      "tests_won": 0,
      "hit_rate": 0.0,
      "avg_lift_percent": null,
      "last_tested_at": "2026-02-28",
      "last_winning_block": null,
      "notes": "Three attempts across different pages; none reached significance. Audience may not respond to urgency signals."
    },
    {
      "pattern_id": "hero_image",
      "display_name": "Change hero image",
      "status": "mixed",
      "tests_total": 4,
      "tests_won": 2,
      "hit_rate": 0.5,
      "avg_lift_percent": 6.0,
      "last_tested_at": "2026-03-24",
      "last_winning_block": { "id": 88, "title": "Blog sidebar hero" },
      "notes": "Half win, half lose. Outcome depends on the page — worth testing case by case, not leaning on as a default."
    },
    {
      "pattern_id": "form_fields",
      "display_name": "Change form field count",
      "status": "inconclusive",
      "tests_total": 2,
      "tests_won": 0,
      "hit_rate": null,
      "avg_lift_percent": null,
      "last_tested_at": "2026-04-02",
      "last_winning_block": null,
      "notes": "Not enough data yet."
    }
  ]
}
```

### 8.2 Four status values — the rules

Every pattern has exactly one `status`. The rules are deterministic:

| Status | Rule | Other skills' behaviour |
|---|---|---|
| `inconclusive` | `tests_total < 3` | Ignore. The pattern is invisible to ranking. |
| `won` | `tests_total >= 3` AND `hit_rate >= 0.75` | Weight up. Lean on this pattern explicitly in recommendations. |
| `lost` | `tests_total >= 3` AND `hit_rate <= 0.25` | Demote or skip. Only surface if the user specifically asks. |
| `mixed` | `tests_total >= 3` AND `0.25 < hit_rate < 0.75` | Treat as neutral. Mention in presentations but do not weight the ranking. |

The minimum-sample floor of 3 is load-bearing. It's what keeps a single lucky test from promoting a pattern to "won", and what keeps a single loss from demoting a pattern to "lost". It is not a guess — it's the minimum number of data points that makes "hit rate" a word that means anything.

### 8.3 Derived markdown summary

`~/.config/accelerate-ai-toolkit/journal-<site-slug>.md`, `chmod 600`. Regenerated from the JSON on every run. The user reads this; skills do not parse it.

```markdown
# Accelerate learning journal — Example Site

Last updated: 2026-04-12

Summary: 18 experiments considered, 11 concluded with a winner, 3 still running, 4 dropped as too thin to count.

## How to read this file

Each "pattern" is a kind of change this site has A/B tested. "Hit rate" is the fraction of tests using this pattern that reached statistical significance and won. "Avg lift" is the mean percentage improvement of winning variants.

## Patterns that have won on this site

### Rewrite headline to match referrer intent
- Hit rate: 4/5 (80%)
- Avg lift: +23%
- Last tested: 2026-03-12
- Last winning block: "Homepage hero" (id 142)
- Notes: Biggest wins on pricing and feature-tour pages. Smaller effect on the homepage.

## Patterns that have lost on this site

### Add urgency / scarcity copy to CTAs
- Hit rate: 0/3 (0%)
- Last tested: 2026-02-28
- Notes: Three attempts across different pages; none reached significance. The audience may not respond to urgency signals.

## Mixed results (works sometimes, not a default)

### Change hero image
- Hit rate: 2/4 (50%)
- Avg lift on wins: +6%
- Last tested: 2026-03-24
- Notes: Half win, half lose. Outcome depends on the page — worth testing case by case, not leaning on as a default.

## Inconclusive (not enough data yet)

### Change form field count
- Tests run: 2
- None have reached statistical significance yet. Need at least one more concluded test before I can say anything confident.
- Last tested: 2026-04-02
```

### 8.4 Invariants

- **The JSON is the source of truth.** The markdown is generated from it. If they ever disagree, the JSON wins and the markdown is regenerated.
- Both files are `chmod 600` — same posture as the credentials file.
- Both files are written atomically: write to a temp file with `chmod 600`, then rename over the target.
- The JSON file has a `schema_version` field. Any bump triggers a migration path when `accelerate-learn` runs — document the migration in the skill body, don't silently overwrite.
- Skills that read the JSON tolerate missing optional fields (`avg_lift_percent`, `last_winning_block`, `notes` can all be `null`) but treat missing required fields (`pattern_id`, `status`, `tests_total`, `tests_won`) as a corruption signal that should fail loudly.

---

## 9. Pattern taxonomy

Baked into the `accelerate-learn` skill body. This is the closest thing our loop has to a `program.md` — the list of kinds of things the agent knows how to recognise.

**v1.2 canonical patterns (~15):**

1. Rewrite headline to match referrer intent
2. Rewrite headline for clarity
3. Move CTA above the fold
4. Rewrite CTA copy (action-oriented)
5. Add social proof near CTA
6. Add testimonial near CTA
7. Add urgency / scarcity copy
8. Simplify hero (remove clutter)
9. Change pricing display (default period)
10. Personalise for audience segment (referrer-based)
11. Personalise for audience segment (geo-based)
12. Personalise for audience segment (device-based)
13. Change hero image
14. Change form field count
15. Other / unclassified

Each pattern in the taxonomy has a stable `pattern_id` string (kebab-case with underscores) used as the key in the JSON journal and as the structured marker in experiment hypothesis text:

| Display name | `pattern_id` |
|---|---|
| Rewrite headline to match referrer intent | `headline_match_intent` |
| Rewrite headline for clarity | `headline_clarity` |
| Move CTA above the fold | `cta_above_fold` |
| Rewrite CTA copy (action-oriented) | `cta_copy` |
| Add social proof near CTA | `social_proof` |
| Add testimonial near CTA | `testimonial` |
| Add urgency / scarcity copy | `urgency_copy` |
| Simplify hero (remove clutter) | `simplify_hero` |
| Change pricing display (default period) | `pricing_display` |
| Personalise for audience segment (referrer-based) | `personalize_referrer` |
| Personalise for audience segment (geo-based) | `personalize_geo` |
| Personalise for audience segment (device-based) | `personalize_device` |
| Change hero image | `hero_image` |
| Change form field count | `form_fields` |
| Other / unclassified | `other` |

**Classification rules (v1.2 heuristic with structured-marker bridge):**

1. **Structured marker first.** When `accelerate-test` creates a test via `create-ab-test`, it prepends a marker to the hypothesis: `[pattern:headline_match_intent] Rewrite the homepage hero to match the pricing search term`. When `accelerate-learn` reads the experiment back, it parses the `[pattern:<pattern_id>]` prefix and maps it directly to the taxonomy. Zero ambiguity.

2. **Keyword fallback.** If no marker is present (experiment was created outside the toolkit, or by a pre-marker version of `accelerate-test`), fall back to case-insensitive substring matching against the hypothesis text first, then against the variant titles, then against the variant content. The skill body §10 lists the canonical keywords for each pattern.

3. **Unclassified goes to `other`.** If no marker is present and no keyword matches, the experiment is classified as `other` with a one-line description extracted from the hypothesis. The `other` bucket is still useful — it tells the marketer that some experiments exist outside the taxonomy, and the description lets them see what they were.

**v1.3 evolution:** once the upstream generic annotations primitive lands (see §5.1 Prereq 3), classification collapses to a pure dictionary lookup: read `annotations['toolkit:pattern']` from the experiment results, find the entry in this taxonomy, done. The marker bridge in the hypothesis text becomes deprecated but is still read as a fallback for experiments created before the upstream annotations primitive landed. The taxonomy itself stays toolkit-side — upstream stores whatever string key the toolkit writes without needing to know what it means.

**Extending the taxonomy** is an explicit, code-level decision: patterns are added to the skill body in a future release, never inferred dynamically during a run. This keeps the taxonomy stable across runs — if the set of patterns changed between runs, hit-rate numbers would become incomparable.

---

## 10. The `accelerate-learn` skill (proposed body)

When this skill is eventually written, it should follow this shape.

**Location:** `skills/accelerate-learn/SKILL.md`

**Frontmatter:**

```yaml
---
name: accelerate-learn
description: Use when the user wants the toolkit to update what it has learned about their site, see their learning journal, or refresh self-improving suggestions. Keywords include learn, learning, journal, learnings, what have you learned, track patterns, remember what works, self-improving, tailored suggestions, update learnings, what works on my site, what doesn't work here.
license: MIT
category: learning
parent: accelerate
disable-model-invocation: true
---
```

**Body structure:**

1. **Purpose paragraph.** One sentence: *"You read the site's recent A/B test results, classify each experiment into a canonical suggestion pattern, and update the site's learning journal so every other skill can tailor future recommendations to what has worked here."*

2. **What to fetch** (in parallel where possible):
   - `accelerate/get-site-context` — so the skill knows the site slug for the journal filename
   - `accelerate/list-active-experiments` — despite the name, this returns every `wp_block` post with experiment meta, including stopped and declared-winner ones (see §5 verified facts). Filter the returned set on the `status` field to find concluded experiments alongside running ones. This is the v1.2 bridge until the upstream `list-experiments` ability (§5.1 Prereq 1) ships.
   - For each experiment block, `accelerate/get-experiment-results` with the `block_id`
   - If `list-active-experiments` returns exactly 100 items, warn in the journal that older experiments may be missing (the silent `posts_per_page: 100` ceiling)

3. **Read the existing JSON journal**, if any, at `~/.config/accelerate-ai-toolkit/journal-<site-slug>.json`. Parse it. If the file is missing, start with an empty journal. If the file is present but `schema_version` doesn't match the current version (1 as of v1.2), run the migration path defined in the skill body.

4. **For each experiment** returned by `get-experiment-results`:

   **4a. Classify into a `pattern_id` using the structured-marker bridge from §9:**
   - If the experiment's `hypothesis` field starts with `[pattern:<pattern_id>]`, parse the marker and use that `pattern_id` directly. No ambiguity.
   - Otherwise, fall back to case-insensitive substring matching on the hypothesis text, then the variant titles, then the variant content. Use the canonical keyword list for each pattern (defined alongside the taxonomy in the skill body).
   - If nothing matches, classify as `other` and record a one-line description extracted from the hypothesis.
   - **v1.3 note:** when the upstream generic annotations primitive lands (§5.1 Prereq 3), check `annotations['toolkit:pattern']` first — if present, use that directly and skip the marker parsing entirely. The marker bridge stays as a tertiary fallback for experiments created before the annotations primitive shipped.

   **4b. Determine the experiment outcome:**
   - Skip if `has_winner` is false AND the experiment's status is still `active` (not yet conclusive).
   - If `has_winner` is true and `winner_variant_index > 0`: the tested change **won**. Record as a win for the pattern.
   - If `has_winner` is true and `winner_variant_index == 0`: the control won. The tested change **lost**. Record as a loss for the pattern.
   - If `has_winner` is false but the experiment concluded (`status` is `completed` or `stopped`): the experiment never reached significance. Do not record it as a win or a loss; instead increment a separate `tests_inconclusive` counter for the pattern. It does not affect hit rate.

5. **Merge with the journal state:**
   - For each pattern touched, update `tests_total`, `tests_won`, `hit_rate`, `avg_lift_percent`, and `last_tested_at`.
   - `last_tested_at` comes directly from the `ended_at` field returned by `get-experiment-results` (already present in the ability output as verified ISO 8601 in §5). If `ended_at` is null because the experiment is still running, fall back to the max `last_tested_at` across variants or skip this field entirely.
   - `avg_lift_percent` is computed from the winning variant's `conversion_rate` vs the control's (variant index 0) `conversion_rate`, both already present in the result's `variants` array. Store the mean across all wins for this pattern.
   - Recompute the pattern's `status` using the four-state rule from §8.2 (`inconclusive` if `tests_total < 3`; `won` if `hit_rate >= 0.75` with ≥3 tests; `lost` if `hit_rate <= 0.25` with ≥3 tests; `mixed` otherwise).
   - Update the top-level `stats` block with counts.

6. **Write the updated journal atomically:**
   - Write the JSON to `journal-<site-slug>.json.tmp`, `chmod 600`, rename over `journal-<site-slug>.json`.
   - Regenerate the markdown from the fresh JSON, write to `journal-<site-slug>.md.tmp`, `chmod 600`, rename over `journal-<site-slug>.md`.
   - Both files end up atomically updated; if either rename fails, the previous version is untouched.

7. **Print a short summary to the user.** Plain English, marketer-friendly, no jargon. Example (this is the user-facing output, so banned words are forbidden):

   > Updated your learning journal for `example.com`.
   >
   > - **New winner this week:** "Rewrite headline to match referrer intent" is now winning 4 out of 5 tests on your site with an average +23% lift. I'll lean on this more next time you ask for A/B test ideas.
   > - **New loser this week:** "Add urgency copy to CTAs" has now lost 3 in a row. I'll stop suggesting it unless you ask me to.
   > - **Mixed results:** "Change hero image" is at 2 wins and 2 losses. Works sometimes, not a default — I'll keep mentioning it but won't push it.
   > - **Still inconclusive:** Two experiments haven't reached significance yet. I'll check back on them next time.
   >
   > Want me to show you the full journal, or suggest what to test next based on what we've learned?

**Hard rules for the skill:**

- Never create, modify, or stop experiments. Read-only on the WordPress side.
- Never recommend specific test ideas in the summary — hand off to `accelerate-opportunities` or `accelerate-test`.
- If the site has fewer than 3 concluded experiments per pattern, every pattern stays in `inconclusive`. No `won`/`lost`/`mixed` classification happens until the 3-test floor is crossed. Explain plainly in the summary when this is the case.
- Never invent new pattern names or `pattern_id` values. The taxonomy is fixed in the skill body and `other` is always available as a catch-all.
- Both journal files must always be `chmod 600`.
- Summary output follows the `accelerate` router's tone ban list. Specifically: say "learning journal" not "journal file", never say "JSON", "schema", or "parse", and never show raw `pattern_id` strings to the user — always use the `display_name`.

---

## 11. Edits to other skills

These edits are described for the implementer — they don't change the workflow skills' purpose, only add a journal-consultation step.

**Journal consumption rule (applies to all four skills below):** skills read `journal-<site-slug>.json` (not the markdown). They only weight a pattern when its `status` field is `won`. Patterns in `inconclusive` or `mixed` are **invisible to ranking** — the skill falls back to its generic reasoning for those. Patterns in `lost` are demoted or skipped. When a skill does lean on a `won` pattern, it must **say so out loud** in the user-facing output. *"I'm leaning on the headline-rewrite pattern because it's won 4 of 5 tests on this site"* is load-bearing — it's how the user learns that the toolkit is adapting to their site, and it's how the user can push back if the weighting feels wrong.

### 11.1 `skills/accelerate/SKILL.md` (the router)

Three changes:

- **New row in the "What you can do for the user" table:** *"Update what the toolkit has learned about my site / see my learning journal" → `accelerate-learn`*.
- **New paragraph** after the prioritisation disambiguation: *"Before recommending a test or a personalisation idea, consult the learning journal at `~/.config/accelerate-ai-toolkit/journal-<site-slug>.json` if it exists. Only patterns with `status: won` (≥3 concluded tests and ≥75% hit rate) should influence ranking — weight them up. Patterns with `status: lost` should be demoted or skipped unless the user explicitly asks. Patterns with `status: inconclusive` or `status: mixed` are invisible to ranking; treat them as if the journal said nothing about them. When you lean on a won pattern, say so out loud ('I'm prioritising X because it's won 4/5 tests here'). If the journal is empty or missing, fall back to the generic reasoning rules in this router."*
- **Terminology table:** add "learning journal" and "self-optimising loop" translations so the user sees plain English ("the site's learning journal") and never sees "autoresearch-style loop", "JSON", or "schema".

### 11.2 `skills/accelerate-opportunities/SKILL.md`

Add a new "Rule 0 — consult the learning journal first" at the top of the "How to think" section:

> Before applying the rules below, read the learning journal JSON if one exists at `~/.config/accelerate-ai-toolkit/journal-<site-slug>.json`. Only patterns with `status: won` get a +1 priority bump in your ranking — these are patterns with at least 3 concluded tests and a ≥75% hit rate on this site. Patterns with `status: lost` should not appear in your top 3 unless the user explicitly asks. Patterns with `status: inconclusive` or `status: mixed` do not influence the ranking at all — fall back to the generic rules for those. When you lean on a won pattern, say it out loud: *"I'm leaning on the headline-rewrite pattern because it's won 4 out of 5 tests here"* is far more valuable than *"I suggest rewriting the headline"*.

### 11.3 `skills/accelerate-test/SKILL.md`

Two changes to the Planning workflow:

1. Add one line: *Before proposing hypotheses, read the learning journal JSON at `~/.config/accelerate-ai-toolkit/journal-<site-slug>.json` and bias toward patterns with `status: won`. If a hypothesis you were going to propose maps to a pattern with `status: lost`, replace it with one that hasn't. Ignore `inconclusive` and `mixed` patterns — they don't have enough signal to bias on yet.*

2. Add a Creation-phase line: *When calling `accelerate/create-ab-test`, always prepend a structured marker to the `hypothesis` field naming the pattern this test is exercising — e.g. `[pattern:headline_match_intent] Rewrite the homepage hero to match the pricing search term`. The marker is what lets `accelerate-learn` classify the experiment reliably when it reads the result back. The taxonomy of `pattern_id` values lives in `accelerate-learn`'s SKILL.md and is documented in the ability reference.*

### 11.4 `skills/accelerate-review/SKILL.md`

Add an optional new section after the "What's running" block: **"What you've learned about your site."** Render only if the journal has at least one pattern with `status: won` (a fresh install or a site still gathering data won't have this section — that's correct). Content: pull the top 2 `won` patterns (highest hit rate) and the top 1 `lost` pattern, render as one-line bullets each. Never render `inconclusive` or `mixed` patterns in the review — they're noise at this altitude.

---

## 12. GitHub Actions workflow template

**Where it lives in the toolkit:** `docs/examples/workflow-accelerate-learn.yml`

**Where it lives for the user:** copied by the user into `.github/workflows/accelerate-learn.yml` in **their own git repo** (not the toolkit repo).

Why not `.github/workflows/` in the toolkit repo? Because GitHub Actions auto-runs any `.yml` file under that path for the repo that contains it. If we shipped it there, every pull request against the toolkit would trigger the workflow. Hosting it under `docs/examples/` makes it a copy-paste template instead of a live workflow.

```yaml
# Accelerate AI Toolkit — weekly learning loop
#
# Copy this file into your own repo at .github/workflows/accelerate-learn.yml
# Set the following repo Secrets before enabling:
#   - ANTHROPIC_API_KEY
#   - WP_API_URL           (your WordPress site root, e.g. https://example.com)
#   - WP_API_USERNAME      (your WordPress username)
#   - WP_API_PASSWORD      (your WordPress Application Password)

name: Accelerate — weekly learning loop

on:
  schedule:
    - cron: '0 3 * * 0'   # Every Sunday at 03:00 UTC
  workflow_dispatch: {}

concurrency:
  group: accelerate-learn
  cancel-in-progress: false

jobs:
  learn:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: write
      pull-requests: write

    steps:
      - uses: actions/checkout@v4

      - name: Run Accelerate learning loop
        uses: anthropics/claude-code-action@v1
        env:
          WP_API_URL: ${{ secrets.WP_API_URL }}
          WP_API_USERNAME: ${{ secrets.WP_API_USERNAME }}
          WP_API_PASSWORD: ${{ secrets.WP_API_PASSWORD }}
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_args: "--max-turns 6"
          prompt: |
            Run the accelerate-learn skill to update the learning journal.

            After the skill finishes, commit the updated journal file to a
            new branch named learnings/$(date +%Y-%m-%d) and open a pull
            request against main titled "Learnings update YYYY-MM-DD".

            Do not merge the PR. The site operator will review and merge.

# Optional: Slack notification on completion (uncomment and set SLACK_WEBHOOK).
#      - name: Notify Slack
#        if: always()
#        uses: 8398a7/action-slack@v3
#        with:
#          status: ${{ job.status }}
#          text: "Accelerate learning loop ran — status ${{ job.status }}"
#          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

**Design notes for this workflow:**

- **The local journal is canonical; the git mirror is a replica.** The user's `~/.config/accelerate-ai-toolkit/journal-<site>.json` on their own machine is the source of truth. The scheduled workflow produces a git-mirror version of the same journal in the user's own repo, purely for human review via GitHub's diff view. This is a deliberate constraint: v1.2 does not make GitHub Actions the canonical shared state store. Multi-machine sync and agency fleet management are explicit v2 concerns, designed separately.
- **PR-per-run, not commit-to-main.** Every scheduled run creates a branch and a PR. The marketer (or the agency running the site) reviews the diff before merging. If a run produces garbage, close the PR — no damage.
- **`timeout-minutes: 15` + `--max-turns 6`** are the cost guardrails. Even a pathological run cannot burn more than ~15 minutes of compute or more than 6 Claude turns.
- **`concurrency.cancel-in-progress: false`** prevents a new scheduled run from killing an in-progress one. Weekly cadence should not produce overlap, but this is defensive.
- **Sunday 03:00 UTC** — most site traffic is lowest overnight. Sunday is chosen so Monday-morning coffee readers see a fresh PR. Note: GitHub Actions docs explicitly state that *"Scheduled workflows run on the latest commit on the default branch"* — so the workflow always runs against whatever `main` looks like at fire time, with no risk of a stale branch firing.
- **WordPress credentials are the same Application Password the user already set up via `/accelerate-connect`.** They paste the same values into GitHub repo Secrets. `docs/self-optimising.md` must make this explicit.
- **Secrets are never logged.** GitHub Actions automatically redacts secret values from workflow output.
- **5-minute floor.** The minimum schedule interval for GitHub Actions workflows is 5 minutes. This isn't relevant for our weekly cadence, but is worth documenting so nobody tries to run the learning loop more often than once an hour — the feedback loop on A/B tests doesn't produce new signal faster than that, and running more often just burns Claude credits.

### 12.1 v1.3 architectural evolution — deterministic runner

For v1.2, the workflow runs `accelerate-learn` via `anthropics/claude-code-action@v1` because classification needs LLM reasoning — the fallback keyword-matching path is too loose to be trusted without an LLM's judgement, and the structured-marker bridge from §9 only covers experiments the toolkit itself created.

Once upstream Prereq 1 (list-experiments ability) and Prereq 3 (generic annotations primitive) from §5.1 land, classification collapses to a pure dictionary lookup. At that point the runner could be a small Python or Node script that:

- Calls `list-experiments` (Prereq 1) with filters like `annotation_key=toolkit:pattern`
- For each completed experiment, reads `annotations['toolkit:pattern']` directly from the ability's output
- Recomputes `hit_rate` and status per pattern
- Writes the two-file journal
- Commits it to a branch and opens a PR

No Claude invocation needed. Faster, cheaper, deterministic, and the same workflow shape can run in any CI that can execute a script. This is explicitly **not v1.2 scope** — it's what the architecture grows into once the upstream prerequisites ship. Documented here so the implementation direction is visible.

### 12.2 Alternative runners (researched but not shipped)

For completeness — these came up in the GitHub Actions research and we explicitly chose not to ship templates for them:

| Runner | Why not | When a user might pick it |
|---|---|---|
| [Inngest](https://www.inngest.com/) | Requires developer setup; no clear marketer-facing monitoring | Agencies with existing Inngest infra |
| [Modal](https://modal.com/) | Pay-per-second compute, Python-centric, overkill for a weekly prompt | Needed compute power we don't need |
| [Replicate](https://replicate.com/) | API/webhook-based, oriented toward model inference, not agent loops | Not a fit |
| [Vercel Cron](https://vercel.com/docs/cron-jobs) | Only runs Vercel-hosted functions, not general agents | Users with Vercel projects who want to host the agent there |
| [Cloudflare Workers Cron](https://developers.cloudflare.com/workers/configuration/cron-triggers/) | Short execution limits unsuitable for multi-minute agent runs | Not a fit |
| [GitHub Agentic Workflows](https://github.blog/ai-and-ml/automate-repository-tasks-with-github-agentic-workflows/) | In technical preview as of February 2026; native markdown-based agent workflows on GitHub | Worth revisiting once GA |

The recommendation in `docs/self-optimising.md` is: stick with GitHub Actions if you want automation, because the free tier is ample and the monitoring surface (GitHub web UI or Slack webhook) is well-understood. Other runners are mentioned as alternatives exist, not recommended.

---

## 13. `docs/self-optimising.md` — proposed outline

~250 lines, human-facing guide. Table of contents:

1. **What the loop does.** Plain English, one paragraph.
2. **The journal file.** Where it lives, what it looks like, how to read it.
3. **How to run it manually.** `/accelerate-learn` via the agent. The default path. Zero setup.
4. **How to run it on a schedule.** The GitHub Actions pattern. Explicit about the prerequisites: a GitHub account, a repo (can be private), basic familiarity with GitHub Secrets. Users without those skip this section and stay with the manual path forever.
5. **What it will not do.** Never creates, modifies, or stops experiments. Never sends data off the user's machine unless they opt into git mirroring.
6. **Pattern taxonomy.** The ~15 canonical patterns with a one-sentence example of what each one looks like in a real experiment.
7. **Troubleshooting.** Empty journal, classification confusion, rate-limit errors, git-mirror conflicts.
8. **FAQ.** *"How is this different from Accelerate's built-in recommendations?"* — built-in recs are generic; this is per-site. *"Why can't I just run the skill from inside the agent and skip GitHub?"* — you can, that's the default. *"Does this learn across sites?"* — no, deliberately. *"Can I edit the journal by hand?"* — yes, but the skill may overwrite your notes on the next run if the pattern you edited also gets touched.

---

## 14. `ROADMAP.md` — proposed update

Replace the current v1.2 section with:

```markdown
## v1.2 — Self-optimising skill loop (shipped, heuristic bridge version)

The toolkit learns what works on your specific site and tailors future suggestions accordingly. Inspired by the loop pattern from karpathy/autoresearch, adapted for marketing A/B testing where experiments take days to reach significance instead of minutes.

- **`/accelerate-learn`** — reads your recent experiment results, classifies each by suggestion pattern, writes findings to a per-site learning journal, and teaches the other skills to consult it.
- **Journal** lives as two files on your machine: `~/.config/accelerate-ai-toolkit/journal-<site>.json` (machine-readable source of truth) and `~/.config/accelerate-ai-toolkit/journal-<site>.md` (human-readable summary). Private by default. Never sent anywhere.
- **Four pattern states** — `won`, `lost`, `mixed`, `inconclusive` — with strict rules (minimum 3 concluded tests before a pattern leaves inconclusive; ≥75% hit rate for won; ≤25% for lost; everything else is mixed). Only `won` patterns influence other skills' recommendations.
- **Optional automation** via the GitHub Actions template at `docs/examples/workflow-accelerate-learn.yml`. Runs weekly on a schedule, creates a PR with the updated journal for you to review. Requires a GitHub repo and basic GitHub familiarity.
- **Pattern taxonomy** is baked into the skill — 15 canonical suggestion types. Experiments created via the toolkit are tagged at creation time with a structured `[pattern:<id>]` marker in their hypothesis text so classification is reliable. Experiments created via the WordPress admin UI fall back to keyword matching.

**This is the heuristic bridge version.** Its accuracy is bounded by two upstream gaps in Accelerate itself (see v1.3 below). Once those land, the learning loop becomes deterministic and the runner can drop its LLM dependency for classification.

See `docs/self-optimising.md` for the full guide.
```

Replace the existing autoresearch-related upstream ask (if present) with the eight prerequisites from §5.1. Grouped by blocking vs nice-to-have. Full detail and rationale for each lives in §5.1 — the ROADMAP bullets are one-line summaries.

**Blocking v1.3 (robust learning):**

- **Prereq 1 — `accelerate/list-experiments` ability.** Historical-experiments discovery with `status`, `type`, `date_range`, `post_id`, `subject_post_id`, annotation-key/value filters, and pagination. Thin wrapper around the existing internal `Experiments\Experiment::query()`. PR to `inc/abilities/discovery.php`.
- **Prereq 2 — experiment-id addressable results.** Accept `experiment_id` as an alternative to `block_id` on `accelerate/get-experiment-results`. Today only the most-recent experiment for a block is retrievable. PR to `inc/abilities/execution.php`.
- **Prereq 3 — generic annotations/labels primitive on experiments.** A universal bag-of-strings metadata abstraction (e.g. namespaced key/value map like `{"toolkit:pattern": "headline_match_intent"}`) that any consumer can populate with its own vocabulary. Upstream stores the bag verbatim without needing to know what any key means; upstream never commits to a vocabulary. The toolkit populates `toolkit:pattern` / `toolkit:source` / `toolkit:surface` from its own taxonomy. Other future consumers use their own namespaces. Accepted on `create-ab-test`, returned on `get-experiment-results` and `list-experiments`, filterable in `list-experiments`. PR to `inc/abilities/execution.php`. **This is the right shape specifically because it is not toolkit-shaped** — it's a universal experimentation-metadata primitive that vanilla learning loops, future agent systems, and other tools can all build on.
- **Prereq 6 — dedicated read-only analytics capability.** Split `view_accelerate_analytics` off from `edit_posts`. `can_view_analytics()` checks the new capability; `can_create_experiments()` keeps `edit_posts`. Essential for agencies running the toolkit for clients. PR to `inc/abilities/namespace.php`.

**Nice-to-have (not blocking, v1.3+ polish):**

- **Prereq 4 — complete lifecycle fields** on experiment results. `started_at`, `ended_at`, `goal` already present; add `created_at`, `status_changed_at`, `confidence_at_close`, `close_reason`.
- **Prereq 5 — webhook or event hooks for experiment state changes.** Today the learning loop polls weekly. An action hook (`accelerate_experiment_completed`, `accelerate_experiment_winner_declared`) plus an optional webhook mapping would let the loop run reactively.
- **Prereq 7 — `accelerate/get-experiment-history-summary` ability.** Pre-aggregated grouped summaries over a date range. Performance and convenience win; the v1.2 runner already computes this from raw results.
- **Prereq 8 — canonical site slug** in `get-site-context.site`. Stable per-site identifier for journal filenames without the toolkit having to slugify `url`.

All eight are fully specified in §5.1 of this document, including the current source file references, the existing internal APIs upstream can reuse, and the toolkit-side workarounds where applicable. The upstream surface should stay minimal — see §5.1's "Non-goals for upstream" list for what the plugin should explicitly not own.

---

## 15. `AGENTS.md` — proposed update

Add one row to the directory-layout tree:

```
├── docs/examples/                # Copy-paste templates (workflow YAML, etc.)
```

Add one rule to the "Hard rules" section as rule 12:

> **12. Do not create `.github/workflows/` in this repo.** The toolkit is a plugin, not a CI project. GitHub Actions templates live under `docs/examples/` as copy-paste files the user installs into their own repo. GitHub auto-runs any `.yml` file under `.github/workflows/`, which would make them impossible to ship as opt-in.

---

## 16. Implementation checklist

When this design is approved for execution, these are the concrete tasks, in order:

1. Create `skills/accelerate-learn/SKILL.md` from Section 10 of this doc.
2. Create `commands/accelerate-learn.md` as the slash-command wrapper.
3. Edit `skills/accelerate/SKILL.md` per Section 11.1.
4. Edit `skills/accelerate-opportunities/SKILL.md` per Section 11.2.
5. Edit `skills/accelerate-test/SKILL.md` per Section 11.3.
6. Edit `skills/accelerate-review/SKILL.md` per Section 11.4.
7. Create `docs/examples/workflow-accelerate-learn.yml` from Section 12.
8. Create `docs/self-optimising.md` from Section 13.
9. Edit `ROADMAP.md` per Section 14.
10. Edit `AGENTS.md` per Section 15 (add directory row + hard rule 12).
11. Edit `README.md` — bump skill count 12 → 13, add a one-line mention of the self-optimising loop in the "What's inside" block.

Verification at the end of execution:

- All 7 JSON manifests still parse.
- Every `accelerate/` capability in `accelerate-learn/SKILL.md` exists in `../altis-accelerate/inc/abilities/*.php`.
- The example workflow YAML parses: `python3 -c "import yaml; yaml.safe_load(open('docs/examples/workflow-accelerate-learn.yml'))"`.
- `ls .github/workflows/` returns nothing — the template lives under `docs/examples/`, not here.
- `grep` for the banned-words list on any user-facing skill prose returns nothing new.
- Skill count in README matches the actual number of skill folders under `skills/`.
- The router routes the sample prompt *"what have you learned about my site?"* to `accelerate-learn` during a live session test.

---

## 17. Open questions for execution

Flagged here so the execution session knows what's still ambiguous. Several questions from earlier drafts have been resolved and committed to design decisions in §8 (four-state journal) and §11 (consumption gate) — they no longer appear here.

1. **Exact ability shape for upstream `list-experiments`.** §5.1 Prereq 1 says we need a new or renamed ability with `status` filter, `since`/`until` dates, annotation filters, and pagination. The precise input schema (parameter names, types, defaults) should be agreed with upstream before the PR goes up. This is a separate upstream task, not a v1.2 execution blocker — v1.2 uses the bridge via `list-active-experiments`.

2. **Exact shape of the upstream generic annotations primitive.** §5.1 Prereq 3 proposes three options (key/value map, flat label list, WordPress terms on a custom taxonomy) and recommends Option A. Upstream should pick whichever shape fits Accelerate's existing patterns best — we only care that (a) consumers can write arbitrary namespaced strings, (b) consumers can read them back verbatim, and (c) `list-experiments` can filter on them. The storage meta key (e.g. `_xb_annotations`), the separator convention, and the exact JSON shape are all upstream calls. Upstream task.

3. **Site slug generation rule.** The journal filenames (`journal-<site-slug>.json/.md`) derive from the site hostname via `get-site-context`. The exact slugification (lowercase, replace dots with hyphens, strip `www.`, strip port numbers, strip protocol) must be specified in the skill body when it's written, so the filename is deterministic across runs. Proposal: `https://www.example.com:8080` → `example-com`. Commit during execution.

4. **Secret rotation reminder in `docs/self-optimising.md`.** When the user rotates their WordPress Application Password, the workflow's GitHub Secret needs manual update. This should go in the Troubleshooting section of the self-optimising doc, but the exact wording is an execution-time call.

5. **Multi-site / agency onboarding.** If a user runs the toolkit against three client sites, they get three separate journal files. The skill body and `docs/self-optimising.md` should document this clearly so agencies know what to expect, but the exact presentation ("one journal per site" vs "a list of journals") is a polish decision during execution.

6. **Journal schema version migration path.** The JSON has a `schema_version` field. Today it's 1. When v1.3 bumps it (e.g. to add `pattern_id_source` tracking for marker-vs-upstream-field classification), the skill needs a migration path — read the old schema, rewrite in the new shape, preserve history. This is out of scope for v1.2 execution but should be noted in a comment in the skill body so the first migration isn't a surprise.

---

## 18. Test scenarios

Behaviour-level scenarios the first implementation must handle. Treat these as integration tests for the feature, not unit tests for the skill body. When execution begins, these become the sign-off criteria for "does it work".

### Data-shape scenarios

1. **No completed experiments.** `/accelerate-learn` runs on a fresh site with zero concluded tests. The skill writes an empty journal with `stats.concluded_with_winner = 0`. The user-facing summary explains plainly that the journal needs more runs to produce meaningful learning. Other skills fall back to generic reasoning without complaint.

2. **One or two completed experiments only.** Every pattern is in `inconclusive` state. No pattern influences other skills' recommendations. The summary is cautious: *"I've seen 2 concluded tests so far, but I need at least 3 per pattern before I start drawing conclusions."* Other skills silently ignore the journal.

3. **Multiple experiments with the same pattern, clear winner.** A pattern at 4 wins out of 5 tests. The skill promotes it to `won`. `accelerate-opportunities`, `accelerate-test`, and `accelerate-review` all weight it up on their next run. The weighting is announced in the user-facing output: *"I'm leaning on the headline-rewrite pattern because it's won 4 of 5 tests here."*

4. **Mixed results across the same pattern.** A pattern at 2 wins out of 4 tests (50% hit rate, ≥3 tests). The skill classifies it as `mixed`. The journal's markdown has a "Mixed results (works sometimes, not a default)" section listing it. Other skills do **not** weight it — they treat it as neutral and fall back to generic reasoning. The marketer sees it in the journal summary but no recommendation actively leans on it.

5. **Clear loss.** A pattern at 0 wins out of 3 tests (0% hit rate, ≥3 tests). The skill classifies it as `lost`. Other skills demote or skip it in their recommendations. `accelerate-opportunities` never includes it in the top 3. `accelerate-test` replaces any proposed hypothesis that maps to it with an alternative.

6. **Experiment created outside the toolkit (no `[pattern:...]` marker).** The classification step falls back to keyword matching on the free-text hypothesis + variant titles + content. If nothing matches, the experiment lands in `other`. The summary notes the fallback: *"3 experiments couldn't be matched to a standard pattern — they're recorded in the journal for reference."*

7. **Experiment created via the toolkit with a valid marker.** The classification step reads the `[pattern:headline_match_intent]` prefix from the hypothesis and maps directly. No keyword matching needed. Deterministic.

### Failure-mode scenarios

8. **Corrupted journal JSON on disk.** The skill detects invalid JSON when reading the existing journal. It refuses to write on top of corruption, logs a clear error, and tells the user to delete or restore the file manually. The old journal is not overwritten.

9. **Schema version mismatch.** The skill reads a journal with `schema_version: 0` (or any future version it doesn't understand). It runs the migration path for known upgrades, or if the version is too new, refuses to write and tells the user to upgrade the toolkit.

10. **`list-active-experiments` returns exactly 100 items.** The skill warns the user via the summary and the journal's top-level `stats.warning` field: *"Your site has at least 100 experiments, which is the current upper limit for the historical-experiments bridge. Older experiments may be missing from the learning data. This is tracked as an upstream improvement."* The loop still runs on the 100 it can see.

11. **WordPress connection is down during a scheduled run.** The workflow fails cleanly. No half-written journal. No partial data corruption. The PR simply isn't created, and the next run retries.

12. **Credential failure (401 from the Abilities API).** The skill tells the user plainly that their Application Password is wrong or expired and points them at `/accelerate-connect`. No journal write.

13. **Skill body is run under GitHub Actions and pushes a PR, but the PR never merges.** The local journal on the marketer's machine continues to diverge from the git mirror. This is expected — the local file is the source of truth, the git mirror is a replica. Document this explicitly in `docs/self-optimising.md` so agencies understand.

### Agency / multi-site scenarios

14. **Agency running the toolkit against 3 client sites.** Each site has its own journal file (`journal-site1.json`, `journal-site2.json`, `journal-site3.json`) on the analyst's machine. The skill writes to whichever one matches the currently-configured site. No cross-contamination. Documented in the skill body.

15. **Site hostname changes (e.g. migration from `www.example.com` to `example.com`).** The slugification rule is deterministic (see §17 open question 3), but a hostname change will generate a new slug and leave the old journal file orphaned. The first-run skill for the new hostname detects this — if `journal-<new-slug>.json` doesn't exist AND there's an older journal on disk with the same site name, it offers to migrate.

### Tone / safety scenarios

16. **Marketer can read the output without seeing developer jargon.** No banned words (`ability`, `endpoint`, `API`, `MCP`, `schema`, `parameter`, `JSON`, `tool call`, `WP_API_*`, `pattern_id`) in anything the user reads. Spot-check by running the skill and grepping the output.

17. **The scheduled GitHub Actions run does not leak secrets.** The workflow's output redacts all `${{ secrets.* }}` values. The journal file itself never contains credentials. PR diffs don't contain credentials.

18. **No automated workflow creates, stops, or declares winners on any experiment.** `accelerate-learn` never calls any mutating ability. `create-ab-test`, `stop-experiment`, and friends are only callable from `accelerate-test` / `accelerate-personalize` under their existing confirmation rules. The learning loop is strictly read-only on the WordPress side.

---

## 19. References

### karpathy/autoresearch

- Repo — <https://github.com/karpathy/autoresearch>
- Karpathy's "I packaged up the autoresearch project..." post — <https://x.com/karpathy/status/2030371219518931079>
- Karpathy on collaborative agents — <https://x.com/karpathy/status/2030705271627284816>
- Fortune: "The Karpathy Loop — 700 experiments, 2 days..." — <https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/>
- Data Science Dojo: "Karpathy Autoresearch Explained" — <https://datasciencedojo.com/blog/karpathy-autoresearch-explained/>
- SkyPilot: "Scaling Karpathy's Autoresearch" — <https://blog.skypilot.co/scaling-autoresearch/>
- OSS Insight: "54,000 Stars in 19 Days" — <https://ossinsight.io/blog/autoresearch-overnight-ai-scientist>
- The New Stack: "Karpathy's Autonomous Experiment Loop" — <https://thenewstack.io/karpathy-autonomous-experiment-loop/>

### Autoresearch forks and marketing adaptations

- <https://github.com/uditgoenka/autoresearch>
- <https://github.com/proyecto26/autoresearch-ai-plugin>
- <https://github.com/drivelineresearch/autoresearch-claude-code>
- MindStudio: "Self-Improving A/B Testing Agent for Landing Pages and Ad Copy" — <https://www.mindstudio.ai/blog/self-improving-ab-testing-agent-landing-pages-ad-copy>
- MindStudio: "What Is Karpathy's AutoResearch Pattern and How to Apply It to Marketing" — <https://www.mindstudio.ai/blog/karpathy-autoresearch-pattern-marketing-automation>
- BSWEN: "Can You Use Karpathy's Autoresearch Loop for SEO Testing" — <https://docs.bswen.com/blog/2026-03-29-autoresearch-non-ml-tasks/>

### Anthropic Claude Code Action

- Repository — <https://github.com/anthropics/claude-code-action>
- Marketplace listing — <https://github.com/marketplace/actions/claude-code-action-official>
- Docs — <https://code.claude.com/docs/en/github-actions>

### GitHub Actions references

- GitHub Agentic Workflows (technical preview) — <https://github.blog/ai-and-ml/automate-repository-tasks-with-github-agentic-workflows/>
- Using secrets in GitHub Actions — <https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions>
- Monitoring workflows — <https://docs.github.com/en/actions/how-tos/monitor-workflows>
- Add & Commit action — <https://github.com/marketplace/actions/add-commit>
- git-auto-commit-action — <https://github.com/marketplace/actions/git-auto-commit>
- Elasticsearch Labs: "CI pipelines with agentic AI" — <https://www.elastic.co/search-labs/blog/ci-pipelines-claude-ai-agent>
- Awesome Continuous AI — <https://github.com/githubnext/awesome-continuous-ai>

### Accelerate plugin (source of truth for capability names and permissions)

- `../altis-accelerate/inc/abilities/namespace.php` — permission callbacks (lines 88–112)
- `../altis-accelerate/inc/abilities/discovery.php` — `list-active-experiments` at line 200, plus all read-only analytics capabilities
- `../altis-accelerate/inc/abilities/execution.php` — `get-experiment-results` at line 1296, `create-ab-test`, `stop-experiment`, etc.
- `../altis-accelerate/inc/abilities/query.php` — `query-events` at line 37, `aggregate`, `get-event-schema`, `search-content`
- `../altis-accelerate/.mcp.json` — reference MCP client configuration for a WordPress site running the Abilities API
- `../altis-accelerate/.claude/skills/accelerate.md` — reference skill for Accelerate terminology (synced patterns, audience fields, Bayesian stats context)

### WordPress MCP transport

- WordPress MCP Adapter — <https://github.com/WordPress/mcp-adapter>
- `@automattic/mcp-wordpress-remote` (npm) — <https://www.npmjs.com/package/@automattic/mcp-wordpress-remote>
- `@automattic/mcp-wordpress-remote` (source) — <https://github.com/Automattic/mcp-wordpress-remote>
- WordPress AI team blog (Abilities API + MCP) — <https://make.wordpress.org/ai/>
- WordPress Application Passwords integration guide — <https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/>

### Model Context Protocol

- Overview — <https://modelcontextprotocol.io/>
- Specification — <https://spec.modelcontextprotocol.io/>

### GitHub Actions documentation (quoted verbatim in §5)

- Events that trigger workflows — schedule section — <https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule>
  - Source of the verified facts that scheduled workflows have a 5-minute minimum interval and run on the latest commit of the default branch.

### Internal repo files this design depends on

- `AR-CODEX.md` — sibling design doc authored by Codex. The critique that shaped this revision of AR-CLAUDE.md: proper upstream prerequisites framing, first-class `mixed` and `insufficient-data` journal states, canonical machine-readable file plus human-readable summary, and the two verbatim GitHub Actions facts that informed §5. Read them as a pair for the full picture.
- `skills/accelerate/SKILL.md` — the router this plan edits
- `skills/accelerate-opportunities/SKILL.md` — consumes the journal
- `skills/accelerate-test/SKILL.md` — consumes the journal; also writes `[pattern:...]` markers on new experiments
- `skills/accelerate-review/SKILL.md` — consumes the journal
- `SKILLS-REVIEW.md` — the Shopify/PostHog benchmark that informed the original skill map
- `AGENTS.md` — repo editing rules this design adds to
- `ROADMAP.md` — the v1.2 entry this design replaces

---

## 20. What this document does not do

- It does not create, edit, or delete any skill, command, workflow, or documentation file in the toolkit repo.
- It does not modify `../altis-accelerate/`.
- It does not schedule or run any agent loop.
- It does not commit to any version number, release date, or timeline.
- It does not invent new Accelerate capabilities that do not exist in `../altis-accelerate/inc/abilities/*.php`.
- It does not make cost projections for Claude API usage under automation — the guardrails (`--max-turns 6`, `timeout-minutes: 15`, weekly cadence) are engineered to make this a non-issue, but the specific monthly cost depends on the size of the user's experiment history and is not something we can estimate from the design alone.

When the implementation of this design begins, all of the above become possible. Until then, this file is the complete record.
