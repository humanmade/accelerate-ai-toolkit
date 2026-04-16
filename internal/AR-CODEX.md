# AR-CODEX

## Autoresearch Review and Integration Plan

### Summary

Treat `karpathy/autoresearch` as a design reference, not a dependency or embedded subsystem. The useful idea is the closed loop of suggestion -> measurable result -> updated future behavior. The wrong move would be to vendor the project, expose "autoresearch" to marketers, or depend on an always-on agent runtime.

The best fit for this repo is a toolkit-native learning loop with three layers:

- a marketer-safe, mostly hidden product surface in this repo
- a deterministic learning runner that can be invoked manually or on a schedule
- optional automation examples, with GitHub Actions as the first blessed scheduler

The default monitoring path should still be the agent itself. GitHub automation is optional, not the primary user experience.

Because the current Accelerate surface lacks robust experiment history and structured recommendation tags, the roadmap should be revised to make upstream data-model support a prerequisite for correctness-first learning.

### Key Changes

#### 1. Reframe the roadmap item

Replace the current "Inspired by autoresearch" wording with a clearer positioning:

- `autoresearch` is inspiration for the loop pattern only
- the shipped feature is called something like `Learning from experiments` or `site learning loop`
- the user-facing promise is: "the toolkit gets better at recommending what works on your site"
- avoid implying long-running autonomous agents or self-modifying prompts/skills

Update the roadmap to split the current single item into:

- `Manual learning review, analyst-only`
- `Upstream prerequisites`
- `Optional scheduled automation`
- `Future: closed-loop learning influence on recommendations`

#### 2. Keep the capability in this repo/package, but not as a normal front-door feature

Recommended product shape:

- keep the concept native to the toolkit
- do not make it a separate public project or external service
- do not market it in the main README examples yet
- expose it first as an advanced/analyst workflow, not a default marketer skill

Recommended first surfaces:

- an advanced skill or command such as `/accelerate-learn`
- optionally a read-only status surface such as `/accelerate-learn-status`
- output in marketer language: what patterns have worked, what has not, how confident we are, and what to test next
- the default monitoring path is the agent itself: "what have you learned about my site lately?" or `/accelerate-learn`
- no GitHub account should be required for the default path

Do not expose the term `autoresearch` to end users. Keep that as an internal reference in roadmap/design docs only.

#### 3. Make upstream Accelerate support explicit

A robust first version cannot rely on free-text hypothesis parsing alone. The current toolkit has `list-active-experiments` and `get-experiment-results`, but no clean historical discovery surface and no structured metadata for recommendation pattern grouping.

Move these into explicit upstream prerequisites:

- a read capability for completed/historical experiments over a date range
- stable result access for completed experiments without already knowing block IDs
- structured experiment metadata for the originating recommendation pattern
  - examples: `headline_match_intent`, `move_cta_above_fold`, `add_social_proof`, `personalize_by_source`
- optional timestamps/status fields that support learning windows and recency weighting

Without these, any first cut is heuristic and should not be framed as reliable learning.

#### 4. Separate learning computation from skill behavior

The learning loop should not directly rewrite skills or prompts.

Instead:

- runner computes learned pattern summaries from experiment outcomes
- runner writes a canonical structured learned-state file plus an optional marketer-readable summary
- skills consult the structured learned-state as advisory context only
- skills still use current site data and current safety rules
- learned patterns can raise or lower recommendation priority, but never auto-create tests or mutations

Recommended learned-state contract:

- canonical machine-readable file as the source of truth
- optional marketer-readable markdown summary generated from the same data
- per-site storage
- includes pattern, sample size, win rate, average lift, last updated, confidence bucket, and status
- includes `insufficient data` and `mixed results` states explicitly
- downstream skills consume the structured file; the markdown summary is for humans

#### 5. Default to manual review first; bless GitHub Actions as the first automation path

The first trustworthy user experience should be:

- advanced/manual invocation by an analyst or power user
- marketer-readable output
- no background unattended policy changes

Then add optional scheduling with GitHub Actions as the documented example path.

GitHub Actions is the first documented automation story because it is transparent, user-owned, and easy to audit. For Codex specifically, it should be treated as the first scheduler we document, not the only long-term automation path.

Why GitHub Actions is a good first automation story:

- official support for scheduled workflows via `on.schedule` cron
- runs on the latest commit on the default branch
- shortest schedule interval is every 5 minutes
- encrypted secrets are available for credentials
- `workflow_dispatch` gives a manual trigger alongside cron

Sources:

- GitHub Actions workflow syntax: <https://docs.github.com/actions/reference/workflows-and-actions/workflow-syntax>
- GitHub Actions secrets: <https://docs.github.com/actions/security-guides/encrypted-secrets>
- GitHub Actions workflow placement and triggers: <https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions>
- Codex overview: <https://openai.com/codex/>
- Codex in ChatGPT: <https://help.openai.com/en/articles/11369540-codex-in-chatgpt>

Recommended automation posture:

- weekly cadence by default, not per-experiment or high-frequency
- scheduled runner generates a learning summary and a structured output file
- expose results through job summary and artifact first
- optional issue/comment reporting later
- do not rely on Actions logs as the primary marketer interface
- do not rely on running Claude Code or Codex interactively inside Actions as the core mechanism
- if the toolkit ships a workflow example, place it under a `docs/examples/`-style copy-paste path, not `.github/workflows/` in this repo
- leave room for future Codex-native cloud/background automation once package boundaries and trust/safety controls are designed

#### 6. Keep marketer accessibility high even in advanced mode

Even though the feature starts analyst-only, the outputs should be marketer-native.

Presentation rules:

- say `what we've learned from recent tests`, not `autoresearch`
- show 3-5 clear lessons maximum
- always show sample size and confidence caveats
- separate:
  - patterns that seem to work here
  - patterns that are inconclusive
  - patterns that have repeatedly lost
- end with concrete next actions, not abstract model talk

Recommended default framing:

- `Based on your last N completed tests...`
- `Patterns that look promising on this site...`
- `Patterns I would stop repeating for now...`
- `What I'd test next...`

### Implementation Changes

#### Repo and documentation changes

Revise `ROADMAP.md` so the learning-loop section states:

- it is inspired by `karpathy/autoresearch`, but not a direct integration
- robust learning depends on upstream experiment-history and metadata support
- first shipped form is manual and analyst-oriented
- the default monitoring path is the agent itself
- GitHub Actions is the first documented automation example
- automatic recommendation adaptation is advisory, not autonomous mutation
- future Codex-native background automation is possible but not part of the first cut

Add a dedicated design doc, e.g. `docs/learning-loop.md`, that defines:

- product wording
- upstream prerequisites
- learned-state contract
- manual flow
- scheduled flow
- monitoring outputs
- trust/safety boundaries

#### Public interfaces and capabilities

If implemented, the first public surfaces should be minimal:

- `/accelerate-learn`
- optional `/accelerate-learn-status`

Upstream/public capability additions needed before robust rollout:

- list completed experiments
- fetch completed experiment result summaries reliably
- attach/read structured recommendation-pattern metadata on experiments

Do not add a general `run forever` or `self-optimize` command.

#### Learned-state contract

The first implementation should treat learned state as a structured per-site artifact, not free-form markdown memory.

- structured file is the source of truth
- optional markdown report is generated for humans
- other skills read the structured file, not brittle prose
- storage remains local-first and site-scoped by default

#### Automation model

Document GitHub Actions as an example scheduler, not the storage backbone of the product.

First automation flow:

- scheduled workflow plus `workflow_dispatch`
- credentials from encrypted secrets
- runner queries completed experiment results
- runner computes learned pattern summary
- workflow publishes:
  - job summary
  - downloadable artifact
  - optional markdown report

Do not make GitHub Actions the canonical shared learned-state store in v1. Use it to produce reports first. Shared learned-state sync can come later once storage is explicitly designed.

If the repo ships a workflow example, keep it as documentation or template material under a non-live path such as `docs/examples/`. Do not ship it as an active workflow in this repo’s `.github/workflows/` directory.

Leave room for a later Codex-native cloud/background automation path, but do not design the first cut around it.

### Test Cases and Scenarios

- Manual user path: a marketer asks "what have you learned about my site lately?" and gets a readable summary with no GitHub dependency.
- No completed experiments: `/accelerate-learn` says there is not enough data yet and explains what to wait for.
- One or two completed experiments only: output is cautious and does not claim learned patterns.
- Multiple experiments with the same structured pattern: report shows hit rate, average lift, and confidence bucket.
- Mixed results across the same pattern: report says inconclusive rather than forcing a recommendation.
- Existing skills consult learned context from the structured learned-state store but still respect current traffic and recency data.
- Markdown summary is generated from the structured learned-state file rather than acting as the source of truth.
- Scheduled GitHub Actions run succeeds using secrets and produces a readable summary without exposing credentials.
- Any shipped GitHub Actions example lives under a docs/template path and not this repo’s `.github/workflows/`.
- A marketer can understand the report without seeing `autoresearch`, `schema`, or internal system language.
- The design still permits a later Codex-native background automation path without forcing a redesign of the learning contract.
- No automated workflow is allowed to create tests, declare winners, or mutate site state without an explicit human-triggered path.

### Assumptions and Defaults

- Defaulting to toolkit-native capability plus optional runner, not a separate product.
- Defaulting to analyst-only advanced entry for the first shipped version.
- Defaulting to the agent itself as the normal monitoring surface.
- Defaulting to correctness first, which means upstream Accelerate support is required before claiming robust learning.
- Defaulting to a structured learned-state file as the canonical source of truth, with markdown summaries layered on top.
- Defaulting to GitHub Actions as the first documented automation example, but not as the canonical source of truth for learned state and not as the only conceivable long-term automation path.
- Treating `karpathy/autoresearch` as conceptual inspiration only: <https://github.com/karpathy/autoresearch>

### Ideal upstream changes in `/altis-accelerate`

In an ideal world, the learning loop would not need to infer history from generic analytics or reconstruct intent from free text. `altis-accelerate` should expose a small set of first-class learning-friendly primitives so the toolkit can stay strict, deterministic, and read-only.

#### 1. First-class historical experiments surface

Today, `accelerate/list-active-experiments` is explicitly active-only, and `accelerate/get-experiment-results` requires a `block_id` and then finds the active or most recent completed experiment for that block. That is not enough for robust learning across time.

Ideal upstream addition:

- `accelerate/list-experiments`
- filters for `status`, `type`, `date_range`, `post_id`, `subject_post_id`, and pagination
- returns active and completed experiments
- includes stable identifiers, subject block/post, started/ended timestamps, current status, and winner summary

This should be the primary discovery surface for learning runs.

#### 2. Experiment results by experiment ID, not just block ID

The toolkit should not have to discover the latest completed experiment for a block indirectly.

Ideal upstream change:

- make experiment IDs first-class in the public surface
- allow `accelerate/get-experiment-results` by `experiment_id`
- preserve `block_id` lookup as a convenience path, but not the only path

That removes ambiguity when a block has multiple experiments over time.

#### 3. Structured recommendation metadata on experiments

This is the most important missing piece.

If the toolkit recommends "rewrite headline to match referrer intent" and the user creates a test, the experiment should carry structured metadata describing that recommendation pattern. Without this, learning has to guess from hypothesis prose.

Ideal upstream addition:

- machine-readable experiment metadata fields
- recommended minimum fields:
  - `recommendation_pattern`
  - `recommendation_source`
  - `recommendation_context`
  - `created_by_surface`
- examples of `recommendation_pattern`:
  - `headline_match_intent`
  - `move_cta_above_fold`
  - `add_social_proof`
  - `personalize_by_source`

This metadata should be readable later without parsing markdown, HTML, or natural-language hypothesis strings.

#### 4. Lifecycle timestamps and outcome fields that are stable and queryable

For learning, we need more than "winner or not." We need clean lifecycle context.

Ideal upstream result fields:

- `created_at`
- `started_at`
- `ended_at`
- `status_changed_at`
- `winner_variant_index`
- `has_winner`
- `confidence_at_close`
- `close_reason`
- `goal`
- normalized outcome metrics per variant

This supports recency weighting, learning windows, and clean reporting.

#### 5. Event or webhook hooks for experiment state changes

Polling weekly is acceptable, but ideal upstream support would make the system more efficient and easier to automate.

Ideal upstream addition:

- hook or webhook when an experiment is completed
- hook or webhook when a winner is declared manually
- payload includes experiment ID, subject block/post, status, winner, and timestamps

That would let external runners react to meaningful changes instead of waking up and often finding nothing new.

#### 6. Read-only permissions that are actually read-only

The learning loop is read-only. In the current `namespace.php`, `can_view_analytics()` and `can_create_experiments()` both resolve to `edit_posts`, which collapses viewing and creation into the same capability tier.

Ideal upstream change:

- a true analytics-read capability distinct from experiment creation
- learning/history/result abilities should sit on the read tier
- mutation abilities stay on create/manage tiers

That makes analyst-only and automation use safer and easier to justify.

#### 7. A learning-friendly summary ability

Even with better primitives, the toolkit should not have to rebuild every learning view from raw rows.

Ideal upstream addition:

- `accelerate/get-experiment-history-summary`
- grouped summaries over a date range
- optional grouping by recommendation pattern, page, source, or goal
- returns counts, wins, losses, inconclusive runs, and average lift

This would not replace raw results, but it would drastically simplify the learning runner.

#### 8. Canonical site identity for local storage and multi-site workflows

The toolkit can derive a file name today, but an ideal upstream surface would expose a stable identity for per-site learned-state.

Ideal upstream addition:

- canonical site slug or site key in `get-site-context`
- stable enough for filenames, multi-site agency usage, and mirrored automation outputs

This is lower priority than experiment history and metadata, but it makes the system cleaner.

#### 9. What upstream should not own

Even in the ideal version, `altis-accelerate` should not own the entire learning loop.

It should not:

- write the toolkit journal itself
- decide how downstream skills weight patterns
- mutate future recommendations automatically
- turn the WordPress plugin into a generic agent runtime

Upstream should provide clean experiment history, metadata, and events. The toolkit should own the learning interpretation and the user-facing experience.
