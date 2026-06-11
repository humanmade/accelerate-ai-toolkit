# Live audit — humanmade.com, 2026-06-11

Site: humanmade.com running Accelerate **4.1.3** (local code is newer; 4.2.x fixes not yet deployed).
Method: 6 parallel subagents — 4 ability-domain matrices (every read ability exercised live; mutation abilities schema-inspected only), 2 skill walkthroughs (12 user-facing skills). Latencies are approximate wall-clock including harness overhead.

## Coverage

39 abilities in local code; 38 MCP-public live (+ `broadcast-content` registered but MCP-gated — appears in discovery yet uncallable). All 39 have a row below or in the agent matrices. All 12 user-facing skills walked through.

## Ability matrix (condensed)

| Ability | Status live | date_range presets | Custom start/end | Bogus `days:30` | ~Tokens | Notes |
|---|---|---|---|---|---|---|
| get-performance-summary | OK | honoured (`date_range_preset`) | **CRASHES** on long spans — ClickHouse `Incompatible types of WITH FILL expression values` (err 475) | silent | 340–960 | phantom zero-rows interleaved in time series (WITH FILL artifact) |
| get-top-content | OK | honoured | honoured | silent | ~470 | |
| get-post-performance | OK | honoured | honoured | silent | ~140 | `visitors` always 0 (single-post path never populates it) |
| get-content-diff | OK | n/a (`current_period`) | honoured | n/a | ~30 | requires `post_ids` (array) + `current_period` — skills document it wrong |
| get-traffic-breakdown | **BROKEN** | **ignored** | **ignored** — byte-identical output for 7d/32d/bogus | silent | ~93 | delegates to cached `Audiences\get_field_data()`, no time scope |
| get-taxonomy-performance | **BROKEN live** | — | — | — | err | ClickHouse `Array does not start with '[' character` (err 130); array-include path unsupported on 4.1.3 — verify current code |
| get-site-context | OK | n/a | n/a | n/a | **1,645 / 5,444** (blocks) | 88-block registry dump; no-blocks form already heavy (28 colors + 18 gradients) |
| get-audience-fields | OK | n/a (fixed 7d window) | n/a | silent | **~7,500** | Country field: ~250 entries, 230+ zero-count (>92% noise, ~2,300 wasted tokens) |
| get-audience-segments | OK | n/a | n/a | n/a | ~120 | all 6 audiences return `rules: []`; `include_estimates` silently no-ops |
| list-experiments / list-active-experiments | OK | filter is on `start_time` (reads as "active during" — misleading) | — | silent | ~780 | 66 experiments, real data |
| get-engagement-metrics | OK | honoured | honoured | silent | ~250 | **param trap:** requires `entity_id`; sibling abilities use `post_id` — guaranteed agent error. scroll_depth + avg_time always 0; `exit_pages` always [] |
| get-author-performance / get-author-content | OK | honoured | honoured | silent | 700 / **3,500** | `visitors` always 0; author-content default limit 50 is heavy |
| get-attribution-comparison / get-source-breakdown / get-utm-performance | OK | honoured | honoured | silent | 30–50 | all return **empty data** on this site every window — needs server-side investigation (traffic-breakdown shows referrers, so data exists) |
| get-landing-pages | **BROKEN live** | — | — | — | err | known `Cannot parse uuid` (`session_id != ''`); fixed in 4.2.0, site on 4.1.3 |
| query-events / aggregate / get-event-schema / search-content | OK | accepted (0-row results — unverifiable) | accepted | silent | ~16 | zero events returned — possible blog_id/table scope mismatch worth checking |
| get-trending-content / get-concurrent-visitors | OK | n/a (window param) | n/a | silent | 20–70 | healthy, sub-100ms |
| export-events / get-export-status | OK | n/a | n/a | silent | ~100 | `total_events` always 0 (Export namespace gap on 4.1.3) |
| get-variants / get-experiment-results | OK | n/a | n/a | n/a | ~175 | experiment 35 (completed) returns `variants: []` — monitoring templates would render blank |

**Latency:** healthy throughout — ~30–900 ms per call; ClickHouse itself ~15–850 ms. Slowness in sessions comes from call count × payload tokens, not per-call server time.

## Mutation-ability schema inspection (not executed)

- **No ability sets `additionalProperties: false`** — every unknown param is silently swallowed toolkit-wide (confirmed live on 14 read abilities).
- `create-ab-test` is silently destructive (overwrites existing variants/personalization on the block) and not flagged `destructive: true`; only `remove-variant` and `stop-experiment` carry the flag.
- `stop-experiment`: `winner_variant_index` described as required for `declare_winner` but schema-optional (runtime error instead of validation).
- `update-audience.rules` is a bare `type: object` (no sub-schema), unlike `create-audience`.
- `create-audience` rule `operator` is un-enum'd free string — invalid operators fail silently at evaluation time.
- Goal enum (`engagement`/`click_any_link`/`submit_form`) has no descriptions.
- Annotations write-shape (object) vs read-back (`annotations: []` array) mismatch — likely PHP empty-assoc-array JSON serialization.

## Skill walkthroughs — verdicts

| Skill | Errors hit | Worst issue |
|---|---|---|
| opportunities | get-landing-pages | source-breakdown empty silently guts Rules 3–4 |
| review | — | "same date range" instruction with no param name given |
| diagnose | **get-content-diff ×4** | SKILL.md documents wrong shape (`post_id` vs required `post_ids` + `current_period`) — feature unusable as written |
| optimize-landing-page | get-engagement-metrics | SKILL.md says pass `post_id`; ability requires `entity_id` — always fails |
| realtime | — | clean |
| campaigns | get-landing-pages | date param name undocumented; empty sources = blank default view |
| router | — | references non-existent `accelerate-connect` file path nuance; terminology fine |
| test | — | tells model `date_range: "30d"` (string) — hard validation error; WP-CLI commands surfaced in user-visible backup prose |
| personalize | — | documents non-existent field `endpoint.Attributes.referer` (live name: `attributes.referer`); `include_estimates` column always empty |
| content-plan | get-taxonomy-performance | string presets again; `underserved_score` unverifiable |
| learn | — | precise; `get-site-context` fat-fetch for one URL field |
| abilities-reference | — | conflates `date_range_preset` (summary only) with nested `date_range` everywhere; permission tier names inconsistent with router |

## Findings → actions

| # | Finding | Tag |
|---|---|---|
| 1 | get-traffic-breakdown ignores date_range; cached unscoped data | fix-server (Phase 2, in progress) |
| 2 | get-performance-summary WITH FILL crash on custom ISO spans + phantom zero-rows | fix-server |
| 3 | get-taxonomy-performance ClickHouse array error | fix-server (verify on current code; add test) |
| 4 | get-engagement-metrics `entity_id`/`post_id` inconsistency | fix-server (accept alias) + fix-skill |
| 5 | No additionalProperties anywhere; bogus params silent | fix-server |
| 6 | get-audience-fields zero-count bloat (~7.5k tokens) | fix-server |
| 7 | get-site-context block dump (5.4k tokens) + heavy default | fix-server |
| 8 | `visitors` always 0 (post-performance, author abilities) | fix-server (investigate; may be API gap) |
| 9 | source-breakdown/utm/attribution empty while referrer data exists | fix-server (investigate) |
| 10 | broadcast-content in discovery but MCP-gated | fix-server (filter discovery) |
| 11 | get-experiment-results `variants: []` for completed tests | fix-server (investigate) |
| 12 | annotations object/array serialization mismatch | fix-server (force object) |
| 13 | mutation schema gaps (destructive flags, enums, oneOf) | fix-server (cheap subset) |
| 14 | skills instruct wrong shapes (content-diff, engagement, string presets) | fix-skill |
| 15 | date_range shape undocumented everywhere; reference conflates mechanisms | fix-docs |
| 16 | jargon leaks (wp_block, WP-CLI in user prose, raw param names in quoted text) | fix-skill |
| 17 | personalize documents non-existent field name | fix-skill |
| 18 | list-experiments date filter semantics ("started in" not "active during") | fix-docs |
| 19 | permission tier naming inconsistency (router vs reference) | fix-docs |
| 20 | scroll_depth / avg_time / exit_pages all zero | investigate-tracker (likely 4.1.3 event schema skew; re-test after site upgrade) |
| 21 | zero events via query-events/aggregate (blog_id scope?) | investigate (re-test after upgrade) |
| 22 | get-performance-summary phantom zero-rows pollute trends | fix-server (same WITH FILL work as #2) |
| 23 | `accelerate-learn` frontmatter `disable-model-invocation: true` undocumented | verify-intentional |

Items 20–21 are deferred pending the humanmade.com 4.1.3 → 4.2.2 upgrade (handled separately); re-run this audit after deploy.
