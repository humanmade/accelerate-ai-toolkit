# Upstream Accelerate changes for Autoresearch compatibility

> Draft issue for `humanmade/accelerate` — proposing a small set of generic primitives that would make Accelerate the first WordPress plugin to cleanly support autoresearch-style self-learning loops, for any AI agent or tool that wants to use them.

---

## Summary

Close three small schema gaps and Accelerate becomes the first plugin in WordPress's [~40%-of-the-web footprint](https://w3techs.com/technologies/overview/content_management) capable of hosting [Karpathy-style autonomous learning loops](https://github.com/karpathy/autoresearch) — the pattern that [ran hundreds of experiments a night](https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/) in other domains and is about to hit marketing optimisation.

Accelerate is very close to supporting this today. [The Abilities API](https://make.wordpress.org/ai/) already exposes structured experiment data to AI agents, and the Bayesian statistics engine already produces the measurable outcomes a learning loop needs. Three small additions to the upstream surface — a historical-experiments discovery ability, stable experiment-ID addressable results, and a generic annotations primitive on experiments — would turn Accelerate into the reference implementation for autonomous marketing optimisation in WordPress.

This issue proposes those changes as **universal experimentation primitives**, not bespoke integrations. Any self-learning loop, agent, or analytics consumer can build on them. Accelerate never commits to knowing what "autoresearch" is; it just ships clean data and a clean contract, and the ecosystem does the rest.

---

## Background: what a self-learning loop actually is

The [autoresearch project](https://github.com/karpathy/autoresearch) is a ~630-line Python repo that embodies one idea: give an agent a fixed measurable outcome, a safe iteration surface, and a keep-or-discard rule, and it will iterate autonomously. In Karpathy's version, the agent mutates `train.py`, runs a 5-minute training job, checks `val_bpb`, commits if better, `git reset --hard` if worse. An overnight run produces ~100 experiments and stacks real additive improvements.

The loop is domain-agnostic:

1. Observe the current state
2. Hypothesise a change
3. Apply it safely and reversibly
4. Measure against a fixed metric
5. Keep if better, discard if worse
6. Repeat

For LLM training the cycle takes 5 minutes. For marketing A/B testing the cycle takes 7–14 days — the time a Bayesian test needs to reach significance on typical site traffic. Throughput drops from 100/night to about 4/month, but each experiment is a real test on real visitors with real conversion consequences, so the *value per experiment* is dramatically higher.

### What this looks like in a WordPress context

A site owner lets an agent observe their Accelerate experiment history weekly. The agent notices that *"rewrite the hero headline to match search intent"* has won 4 of 5 A/B tests on this site with an average +23% lift, while *"add urgency copy to CTAs"* has lost 3 in a row. Next time the owner asks for test ideas, the agent prioritises headline rewrites on high-traffic pages and steers away from urgency copy — not because a playbook says so, but because *this site's audience* has shown what works. Over months, recommendations become tailored to the site's real behaviour. The agent never mutates anything without confirmation; it just gets dramatically better at knowing what to propose.

**The whole thing hinges on the agent being able to read back the site's experiment history cleanly.** Accelerate almost supports this today; this issue closes the gap.

### What counts as an experiment in Accelerate

Accelerate's unit of experimentation is the **global block** — a `wp_block` post (WordPress core calls these Synced Patterns) that appears across multiple pages. When a site owner runs an A/B test or attaches a personalization rule, it targets a specific global block, and every page that renders that block inherits the test.

This is unusual in the A/B testing space. Most tools test arbitrary CSS selectors; Accelerate tests structured content. That's why a learning loop reading Accelerate's experiment history is useful — the `block_id` is a stable, queryable handle to *which piece of content was tested*, and "headline rewrite on hero blocks" is a meaningful summary because "hero block" is a real named object.

Every ability in this proposal ultimately points at a global block via `block_id` or `subject_post_id`. A/B tests, personalization rules, and broadcasts all live on global blocks, so the proposed primitives apply to all three uniformly at the data layer — even though only A/B tests have the Bayesian winner model this proposal's outcome interpretation relies on.

### Why Accelerate is uniquely positioned

1. **Real measurable outcomes.** Bayesian A/B tests with `has_winner` and per-variant `probability_to_be_best`. No need to invent a significance layer — consume one that exists.
2. **Structured experiment data, not raw event logs.** Experiments are first-class objects with a known lifecycle. Learning loops read outcomes directly instead of reconstructing them.
3. **Already exposed to AI agents.** [The WordPress Abilities API](https://make.wordpress.org/ai/) and [WordPress MCP Adapter](https://github.com/WordPress/mcp-adapter) solve the transport layer. This issue closes schema-level gaps, not a new integration.

Most analytics products would have to rebuild half their data model to support autoresearch-style loops. Accelerate needs three changes.

---

## What a self-learning loop needs from an experiment platform

Regardless of whether the consumer is Karpathy's autoresearch, a weekly-learning script, or a future agent framework:

- **Historical experiments discovery** — every experiment the site has ever run, filterable by date range, status, type, and metadata. Not just the active ones, not just the most recent per block, with pagination.
- **Stable experiment identity** — every experiment has a stable ID that survives restarts and block mutations. Lookups by ID are deterministic, no "most recent completed" fallback.
- **Structured metadata on experiments** — a way to attach arbitrary machine-readable context at creation time and read it back later without parsing free text. Critically, the platform *should not need to know what the consumer's vocabulary means*. It just stores strings.
- **Clean lifecycle data** — when was the test created, started, ended; what was the status at each transition; what was the confidence when it closed; why did it close.
- **Read-only access** — a learning loop is strictly observational. It should run under a capability that grants read access *without* granting experiment-creation rights.
- **Event or webhook hooks** — ideally the platform fires events when experiments conclude, so consumers react in near-real-time rather than polling.

**Scope note for this proposal.** Accelerate tracks three distinct experiment-shaped objects — A/B tests, personalization rules, and broadcasts. The proposed primitives (discovery, experiment-ID lookup, annotations, read-only capability, lifecycle fields) apply to all three uniformly at the data level. *Outcome interpretation* is scoped to A/B tests, which have a clean Bayesian winner model. Personalization rules don't "win" — they serve different content to a segment, and learning from them is a distinct problem out of scope here. Broadcasts are deployments rather than experiments and have no winner model at all. Consumers that later want to learn from personalization or track broadcast outcomes benefit from the same primitives, but that work is not part of this proposal's acceptance criteria.

---

## What Accelerate already provides

Verified against the current source tree on `main`:

- [`accelerate/get-experiment-results`](https://github.com/humanmade/accelerate/blob/main/inc/abilities/execution.php) returns a rich payload: `started_at`, `ended_at`, `goal`, `status`, `has_winner`, `winner_variant_index`, `traffic_percentage`, `confidence_threshold`, per-variant metrics (`impressions`, `conversions`, `conversion_rate`, `p_value`, `probability_to_beat_control`), `recommendation`, `edit_url`. Most of what a learning loop needs is already there.
- [`accelerate/list-active-experiments`](https://github.com/humanmade/accelerate/blob/main/inc/abilities/discovery.php) happens to return historical experiments too (because `stop-experiment` doesn't clear the `_xb_abtest` / `_xb_personalization` meta). Capped at `posts_per_page: 100`, no date filter, no pagination, misleading name.
- The internal `Experiments\Experiment::query()` method supports `subject_post_id`, `test_id`, `status`, `per_page`, `order_by`. A proper `list-experiments` ability is a thin wrapper, not a new storage layer.
- `accelerate/create-ab-test` stores a free-text `hypothesis` field — the closest thing to a tag today, but unstructured and unqueryable.
- `can_view_analytics()` and `can_create_experiments()` in [`inc/abilities/namespace.php`](https://github.com/humanmade/accelerate/blob/main/inc/abilities/namespace.php) both resolve to `current_user_can('edit_posts')`. No way to express "read-only analytics viewer".
- `accelerate/get-site-context.site` returns `name`, `description`, `url`, `language`, `has_theme_json` — no stable site slug.

---

## Proposed changes

Grouped by priority. The first four are the blocking set; the rest are ergonomic polish that can land later.

### Blocking set

#### 1. `accelerate/list-experiments` ability

Proper historical-experiments discovery. Thin wrapper around the existing `Experiments\Experiment::query()` — model code exists, this is new ability registration.

**Input:**

```json
{
  "status": "active | completed | paused | all",
  "type": "abtest | personalization | all",
  "date_range": { "since": "2026-01-01T00:00:00Z", "until": "2026-04-01T00:00:00Z" },
  "post_id": 142,
  "subject_post_id": 142,
  "annotation_key": "recommendation:pattern",
  "annotation_value": "headline_match_intent",
  "offset": 0,
  "limit": 50
}
```

All fields optional. `annotation_key` / `annotation_value` filter via the primitive in #3 below — any consumer queries its own namespace without upstream knowing what the keys mean.

**Output per item:**

```json
{
  "experiment_id": 1042,
  "block_id": 142,
  "subject_post_id": 142,
  "type": "abtest",
  "status": "completed",
  "started_at": "2026-03-10T09:00:00Z",
  "ended_at": "2026-03-24T14:30:00Z",
  "goal": "engagement",
  "has_winner": true,
  "winner_variant_index": 1,
  "annotations": {
    "recommendation:pattern": "headline_match_intent",
    "recommendation:source": "some-tool",
    "created:surface": "api"
  }
}
```

Full per-variant metrics remain fetched via `get-experiment-results` — discovery returns a summary, not full detail, to keep responses small. **Estimated lift: small.**

#### 2. Experiment-ID addressable results on `get-experiment-results`

Today `get-experiment-results` takes only `block_id` and silently falls back to "the most recent completed experiment for this block" when no active one is running. When a block has had multiple experiments over time, only the latest is retrievable.

**Proposed change:** accept `experiment_id` as an alternative to `block_id`. Exactly one must be provided. Keep the `block_id` path as a convenience for "show me the current test on this block".

```json
{ "experiment_id": 1042 }
```

A learning loop walking a site's history needs every historical experiment, not just the latest per block. **Estimated lift: very small.** The model already supports fetching by row ID.

#### 3. Generic annotations primitive on experiments

The most important change and the one that turns Accelerate into a universal substrate rather than an integration point tuned to one consumer.

**The problem:** today, the only way to attach structured context to an experiment is the free-text `hypothesis` field. A consumer that wants to remember "this test came from pattern X, proposed by tool Y, in context Z" has nowhere to put it in a machine-readable way.

**The wrong fix:** add a fixed set of named fields like `recommendation_pattern`, `recommendation_source` with predefined enums. That locks upstream into one consumer's vocabulary. The learning loop that needs `headline_match_intent` today is not the same as the SEO tool that will need `meta_description_swap` tomorrow, or the campaign plugin that will need `utm_campaign_id` the day after. Upstream should not ship a new release every time a consumer invents a new tag.

**The right fix:** expose a generic key/value annotations primitive that any consumer populates with arbitrary structured metadata, using a namespace convention. Upstream stores the bag verbatim without needing to know what any key means.

**Proposed shape — pick one:**

- **Option A (recommended): key/value annotations map** stored as `_xb_annotations` post meta (JSON-serialised). Closest to [Kubernetes labels and annotations](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/) / [GitHub repository topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics) conventions. Easy to serialise, easy to query, fast to write.

  ```json
  {
    "recommendation:pattern": "headline_match_intent",
    "recommendation:source": "some-learning-tool",
    "created:surface": "api",
    "created:version": "1.3.0"
  }
  ```

- **Option B: flat label list.** Array of `"namespace:key=value"` strings stored as `_xb_labels` post meta. Simpler, less structured.
- **Option C: WordPress custom taxonomy terms.** Most WordPress-native but taxonomy overhead for what is really just labels.

Option A is my recommendation; B and C are listed if A conflicts with existing Accelerate patterns.

**Integration:**

- `accelerate/create-ab-test` and `accelerate/create-personalization-rule` both accept an optional `annotations` input. The bag attaches to the underlying `wp_block` post, so A/B tests and personalization rules carry annotations the same way.
- `accelerate/get-experiment-results` returns `annotations` verbatim.
- `accelerate/list-experiments` (from #1) supports `annotation_key` and `annotation_value` filtering.

**The key design principle:**

> Accelerate owns *"there is a way to attach structured metadata to an experiment and read it back."* The consumer owns *"here is what we choose to put in that bag."* Accelerate never commits to a vocabulary, never defines enums, never has to learn what any particular consumer is doing with the field.

**Why this is universal, not bespoke:**

- **Upstream never agrees on a vocabulary.** A future SEO tool uses `seo:variant_type` without any upstream change.
- **Multiple consumers coexist cleanly.** Different namespaces, no collisions.
- **Filtering still works.** `annotation_key` + `annotation_value` let any consumer query its own keys without upstream providing a query method per consumer.

**Estimated lift: small.** New post meta key, new input field on two abilities, new output field on two abilities, new filter clause in `list-experiments`.

#### 4. Dedicated read-only analytics capability

Today `can_view_analytics()` and `can_create_experiments()` both resolve to `current_user_can('edit_posts')`. A user granted analytics access in practice also has experiment creation rights.

**Proposed change:** add a first-class `view_accelerate_analytics` capability, granted additively or via a new role. Update `can_view_analytics()` to check it. `can_create_experiments()` keeps `edit_posts`.

Agencies running learning loops for clients can grant read-only analytics access without also granting experiment-creation rights. Scheduled learning jobs run under accounts that genuinely have no mutation capability — defence in depth. Most-requested product-safety improvement from consumers building on Accelerate.

### Nice-to-have (follow-up)

#### 5. Complete lifecycle fields on experiment results

Partially satisfied today (`started_at`, `ended_at`, `goal`, `status` already present). Still missing: `created_at` (distinct from `started_at`), `status_changed_at` for recency weighting, `confidence_at_close` to distinguish overwhelming wins from barely-significant ones, and `close_reason` enum (`auto_significance` / `manual_stop` / `declared_winner` / `timed_out` / `paused_indefinitely`). None block the primary use case.

#### 6. Event/webhook hooks for experiment state changes

WordPress action hooks `accelerate_experiment_completed` (on significance or manual stop) and `accelerate_experiment_winner_declared` (on explicit winner declaration). Payload includes `experiment_id`, `block_id`, `status`, `winner_variant_index`, `annotations`, timestamps. Optional outbound webhook mapping for CI or external consumers. Lets consumers react in near-real-time instead of polling.

#### 7. `accelerate/get-experiment-history-summary` ability

Pre-aggregated summary over a date range, grouped by `annotation:<key>`, page, source, or goal. Returns counts, wins, losses, inconclusive, average lift. Performance win, not correctness win — consumers can compute this themselves from raw results. Lower priority. If implemented, return raw counts and let callers apply their own status rules — upstream should not enforce a four-state classification or any specific threshold.

#### 8. Canonical site slug in `get-site-context`

Add `slug` (and optionally `site_key`) to the `site` object. Stable per-site identifier for consumers that cache state locally.

---

## Explicit non-goals for Accelerate

To preserve clean separation of concerns, Accelerate should **not**:

- Write the consumer's journal, state file, cache, or database. State is the consumer's.
- Decide how consumers weight patterns, classify wins, or tier recommendations.
- Mutate future recommendations based on learned state. Mutations stay behind human-in-the-loop confirmation in whatever surface the consumer provides.
- Define a fixed vocabulary for the annotations primitive. Keys are arbitrary strings.
- Become a generic agent runtime. Experiment data and abilities — nothing more.
- Implement any autoresearch-specific endpoint. No route named `/autoresearch`, no ability called `autoresearch-run`, no dependency on any specific AI framework. Accelerate becomes the substrate for *any* self-learning loop, not one specific tool.

Accelerate provides experiment history, metadata, lifecycle, events, and permissions. Consumers provide interpretation, logic, and user experience.

---

## Suggested implementation plan

**Ship as a single PR with four logical commits for reviewability.** One PR keeps the change reviewable as a whole — the substrate is small enough that splitting into multiple PRs adds coordination overhead without meaningful isolation. Commits let reviewers follow the pieces in logical order.

- [ ] **Commit 1 — Generic annotations primitive (#3).** Adds `_xb_annotations` post meta, the new input field on `create-ab-test` and `create-personalization-rule`, and the new output field on `get-experiment-results`. Unblocks meaningful structured metadata for any consumer. *File: [`inc/abilities/execution.php`](https://github.com/humanmade/accelerate/blob/main/inc/abilities/execution.php).*

- [ ] **Commit 2 — Experiment-ID addressable results (#2).** Adds `experiment_id` as an alternative input on `accelerate/get-experiment-results`. Unlocks historical-experiment lookups without the "most recent per block" ambiguity. *File: [`inc/abilities/execution.php`](https://github.com/humanmade/accelerate/blob/main/inc/abilities/execution.php).*

- [ ] **Commit 3 — `accelerate/list-experiments` ability (#1).** New ability registration, thin wrapper around `Experiments\Experiment::query()`. Adds status, date-range, post-id, subject-post-id, annotation filters, and pagination. *File: [`inc/abilities/discovery.php`](https://github.com/humanmade/accelerate/blob/main/inc/abilities/discovery.php).*

- [ ] **Commit 4 — Read-only analytics capability (#4).** New WordPress capability, updated `can_view_analytics()` callback, docs update. *File: [`inc/abilities/namespace.php`](https://github.com/humanmade/accelerate/blob/main/inc/abilities/namespace.php).*

Once this PR lands, autoresearch-style loops are fully supported: any consumer can discover experiments, fetch results by stable ID, attach and read back structured metadata, and run under a genuinely read-only account.

**Follow-up issue and PR for the ergonomic items** (#5 lifecycle fields, #6 event hooks, #7 summary ability, #8 canonical site slug). These are independent improvements that can ship after the blocking set lands, in whatever order suits the team.

**Rollout and backwards compatibility.** `list-active-experiments` should stay as a permanent alias for `list-experiments` with `status: active` pre-applied. No deprecation timeline, no breaking change. Any existing MCP client calling it today continues working without modification. The new ability is additive; the capability addition for `view_accelerate_analytics` is additive too. Nothing in this PR removes or renames an existing surface.

Rough complexity estimate: **each of the four commits is a few hours to a day of work.** The substrate exists; most of this is surface-area extension of existing abilities. Commit 1 (annotations) is the most design-sensitive because it sets a precedent for how Accelerate handles generic extensible metadata, but the code itself is small.

---

## Testing

The PR should ship with test coverage for each commit. Accelerate already uses PHPUnit — see [`tests/phpunit/`](https://github.com/humanmade/accelerate/tree/main/tests/phpunit) for existing patterns. Minimum expected coverage:

- **Annotations round-trip.** Create an experiment with `annotations: {"foo:bar": "baz"}`, read it back via `get-experiment-results`, verify the bag is preserved verbatim. Same test for personalization rules via `create-personalization-rule`.
- **`list-experiments` filter semantics.** Status filter, date-range filter, `annotation_key` + `annotation_value` filter (including namespace-scoped keys), pagination correctness at the 100-item boundary and above.
- **`get-experiment-results` by experiment_id vs block_id.** Including the "multiple historical experiments on the same block" case — verify that `experiment_id` returns the right historical row and `block_id` still falls back to the most recent for backwards compatibility.
- **Read-only capability enforcement.** A user granted `view_accelerate_analytics` but not `edit_posts` can call read abilities (`list-experiments`, `get-experiment-results`, `get-site-context`) and is blocked from mutate abilities (`create-ab-test`, `stop-experiment`, `create-personalization-rule`, `broadcast-content`). A user with `edit_posts` but not `view_accelerate_analytics` continues to have full access via the fallback logic.
- **Integration: full annotation lifecycle.** Create → list (filtered by annotation) → get (by experiment_id) → stop → list (with `status: completed`) → verify annotations remain consistent across all four surfaces.

---

## Acceptance criteria for the blocking set

The proposal ships when:

- [ ] A consumer can call `list-experiments` with a date range and get every completed experiment from that range, paginated, filterable by annotation key/value, without hitting the current 100-item silent ceiling.
- [ ] A consumer can call `get-experiment-results` with an `experiment_id` and get results for any historical experiment, not just the most recent one per block.
- [ ] A consumer can call `create-ab-test` (and `create-personalization-rule`) with `annotations: { "consumer:key": "value" }` and read those annotations back verbatim via `get-experiment-results` and `list-experiments`.
- [ ] A consumer can filter `list-experiments` with `annotation_key=consumer:key&annotation_value=value` and get only matching experiments.
- [ ] Upstream documentation confirms that annotation keys and values are arbitrary strings and upstream will not enforce a vocabulary.
- [ ] A WordPress user with `view_accelerate_analytics` but without `edit_posts` can call read abilities but cannot call mutate abilities.

Pass those six criteria and Accelerate is ready for autoresearch-style self-learning loops. Any consumer — AI agent, scheduled CI job, marketing automation tool, analytics exporter — can plug into the same primitives.

---

## Open questions for the Accelerate team

1. **Annotations storage shape — A, B, or C?** Option A (JSON key/value map in `_xb_annotations` meta) is my recommendation; existing conventions may argue for B or C. Team call.
2. **Backwards compatibility for `list-active-experiments`.** Proposal: permanent alias with `status: active` pre-applied. Team may prefer a deprecation timeline.
3. **Permission model for `view_accelerate_analytics`.** Additive capability granted to existing roles, a brand-new "Accelerate Analyst" role, or both? Product-design call.
4. **Annotation key namespace validation.** Enforce a `namespace:key` format, or store anything verbatim? I lean toward no validation — let consumers self-police.
5. **Event hook firing semantics.** `accelerate_experiment_completed` on auto-close only, or also on manual stop? I'd suggest firing on both with `close_reason` distinguishing them.

---

## Prior art and related reading

- [Andrej Karpathy's autoresearch repo](https://github.com/karpathy/autoresearch) — the original pattern, for ML training experiments.
- [Fortune on "The Karpathy Loop"](https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/) — broad context on why the pattern is getting attention.
- [WordPress AI team blog](https://make.wordpress.org/ai/) — background on the Abilities API.
- [WordPress MCP Adapter](https://github.com/WordPress/mcp-adapter) — transport layer between Abilities and MCP clients.
- [Model Context Protocol specification](https://spec.modelcontextprotocol.io/) — the protocol consumers use to talk to Accelerate abilities.
- [Kubernetes labels and annotations](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/) — industry-standard model for the generic annotations primitive proposed in #3.
- [GitHub repository topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics) — another example of free-form user-defined metadata on a platform object.

---

## Closing thought

Accelerate is already the most thoughtful A/B testing plugin in the WordPress ecosystem. It has the Bayesian engine, the structured experiment model, and the Abilities API exposure most other plugins are still catching up on. This proposal closes a small schema-level gap that turns Accelerate from *"the best WordPress A/B testing plugin"* into *"the best substrate for any self-learning loop, agent, or autonomous marketing tool that wants to read a WordPress site's experiment history and learn from it."*

Total surface-area change is modest — one PR with four commits for the blocking set, a follow-up for polish. The ecosystem leverage is large. Happy to discuss, adjust the schema shapes, or contribute PRs for any items the team prefers to receive externally.
