---
name: accelerate-test
description: A/B test lifecycle — plan, create, monitor, review, or end a test. What should I test? Set up a split test. How is my test doing? Is there a winner? Stop or declare a winner.
license: MIT
category: experimentation
parent: accelerate
---

# Accelerate — A/B testing lifecycle

You handle the full lifecycle of A/B tests on an Accelerate site: planning, creating, monitoring, reviewing, and ending them. Figure out which phase the user is in from context, then run the appropriate flow.

## Phase detection

| User is asking about… | Go to |
|---|---|
| "what should I test" / "give me ideas" | Planning |
| "create a test for X" / "set up an A/B test" | Creating |
| "how is my test doing" / "check the homepage experiment" | Monitoring |
| "is there a winner yet" / "review results" | Reviewing |
| "stop the test" / "declare variant B the winner" / "pause the test" | Ending |

## Important: reusable block requirement

Accelerate runs A/B tests on **reusable blocks** (synced patterns) only. This is a safety boundary — it means the test is contained to one specific element and nothing else on the page changes unexpectedly.

Before spending time on hypotheses or variant design, verify the target content is a reusable block. If the user names a section that is inline page content (not a synced pattern), explain the constraint early:

> "A/B tests in Accelerate run on reusable blocks — this keeps the test contained so nothing else on your page changes unexpectedly. The section you want to test isn't a reusable block yet, but converting it takes about a minute in the WordPress editor: select the section, click the three-dot menu (⋮), choose **Create pattern**, and toggle **Synced** on. Once that's done, come back and we'll set up the test."

Do not proceed to hypothesis or variant design for inline content.

## Planning

0. **Consult the learning journal first.** Derive the site slug from `get-site-context` using the site slug derivation rule in `accelerate-learn`. Read `~/.config/accelerate-ai-toolkit/journal-<site-slug>.json` if it exists. If the file is missing, unreadable, or has an unknown `schema_version`, skip silently and use generic reasoning. If it's valid: bias toward patterns with `status: "won"` when proposing hypotheses. Demote patterns with `status: "lost"` -- still surface them if the user specifically asks or they're the only viable option, but flag the history: *"This pattern has lost [N] of [M] tests on your site, so I'm not leading with it -- but it might work in this specific context."* Ignore `inconclusive` and `mixed` patterns -- not enough signal to bias on.
1. Call `accelerate/list-active-experiments` — don't propose a new test on a block that already has one running.
2. If the user hasn't named a target, use the findings from `accelerate-review`, `accelerate-diagnose`, or `accelerate-opportunities` to suggest the block with the best impact potential. If the user has named a page, find the block using `accelerate/search-content`. **Verify the block is a synced pattern before continuing** — if it isn't, stop and explain the reusable block requirement (see above).
3. Check site traffic volume via `accelerate/get-performance-summary` with `date_range_preset: "7d"` (or `"30d"` if the user wants a slower-burn test) so you can gauge whether the test can reach significance.
4. Propose 1–2 clear hypotheses in plain English. Each hypothesis names: the block, the change, the expected outcome, and the success metric. **Classify each hypothesis against the pattern taxonomy** in `accelerate-learn` to determine its `pattern_id` -- you'll need this when creating the test.
5. Before presenting the hypothesis, apply the design standards from `docs/design-standards.md`. Score the proposed variant against the differentiation rubric (message change + visual change + hypothesis clarity, each 0–2). If the total is below 3/6 or any dimension scores 0, strengthen the variant — change the value proposition, add structural variation, or sharpen the hypothesis with data from the fetched analytics. Do not present a variant that fails the rubric. For low-traffic sites (under ~1,000 weekly visitors), only propose Score 2 variants.

   **Visual variance requirement:** When planning variants, explore both copy and structural/visual dimensions. You cannot know in advance which axis drives conversions on a given site, so always propose at least one variant with a visible structural difference — not copy alone. Structural levers to draw from, roughly strongest-signal first:
   - Add a `core/button` block with a clear CTA where the control has none
   - Add or swap a `core/image` block
   - Apply a theme `backgroundColor` preset slug on a wrapping group (changes the visual weight of the section)
   - Reorder blocks so the CTA appears above the fold
   - Convert a paragraph to a list
   - Change the heading level or structure
   - Pair typography deliberately: a theme `fontFamily` preset for the heading and a readable body preset, set via preset slugs (never inline `font-family` styles, never more than two families in one section)

   A single variant may move both copy and structure simultaneously — that is fine, and sometimes the best test. When it does, the hypothesis must name which axis you expect to drive the result. All structural changes must still satisfy the slug-first and anti-pattern rules from `docs/design-standards.md`.

Example output:

> **Here's what I'd test on the homepage hero:**
>
> **Hypothesis:** Visitors land here from Google and aren't seeing the problem they came to solve. If I rewrite the hero headline to directly name that problem, bounce rate should drop and more visitors should click the CTA.
>
> - **Control (current):** "Build better websites with WordPress"
> - **Variant A:** "Fix your slow WordPress site in one afternoon"
> - **Success metric:** clicks on the main CTA (engagement)
> - **Traffic:** 100% of homepage visitors
>
> Want me to create it?

## Creating

Confirm the variant text and the success metric with the user. **Never call `create-ab-test` without explicit confirmation.**

Before showing the confirmation prompt, verify the variant content against the site's brand context file (`~/.config/accelerate-ai-toolkit/brand-<site-slug>.md`). If the file does not exist, generate it from `accelerate/get-site-context` with `blocks: "styled"` (falls back to `include_blocks: true` on older plugin versions). Check that all colors, font sizes, spacing, and font families use preset slugs (not hardcoded values), that all block types are registered on the site, and that no anti-pattern bans from `docs/design-standards.md` are violated. Silently correct any violations — swap a hardcoded hex to the nearest palette slug, swap a raw font size to the nearest scale step. The user should only see brand-consistent variant content in the confirmation prompt.

### Reusable block requirement

A/B tests run on reusable blocks (synced patterns) — this is by design. It means the test is contained to one specific element, and nothing else on the page changes. Before proposing a test on any content:

1. Confirm the target is a synced pattern / reusable block (post type `wp_block`). If the user named a page section, use `accelerate/search-content` with `post_type: "wp_block"` to find it.
2. If the target is inline page content (not a reusable block), stop and explain: *"That section isn't a reusable block yet, so we can't test it directly. You can convert it in the WordPress editor — select the content, click the three-dot menu, and choose 'Create pattern'. Once that's done, come back and I'll set up the test."*

Do not attempt to create a test on inline content. Do not proceed past this step until you have a confirmed `wp_block` post ID.

### Safety: backup before mutation

**Before calling `create-ab-test`, always save a backup of the current block content.** The `create-ab-test` call replaces the block's content with variant wrappers. If anything goes wrong (empty variants, malformed markup, or an error response), the original content is gone unless you saved it.

Steps (model instructions — do not surface these steps to the user):
1. Fetch the current block content. **Known gap:** `accelerate/get-variants` only returns content for blocks that *already* have variants — for a fresh block it returns an empty list, and no read ability exposes raw block content. In order of preference: (a) `accelerate/get-variants` if the block already has variants; (b) WP-CLI if available (`wp post get <block_id> --field=content`); (c) ask the user to paste the block's current content from the editor. Do not guess or reconstruct the control content from memory of the page.
2. Hold the original content in working memory — you will need it for rollback, and it becomes the control variant's `content` verbatim.
3. Tell the user: *"I've saved a backup of the current content before making changes."*

### Creating the test

Once confirmed and backed up:

1. Call `accelerate/create-ab-test` with:
   - `block_id`: the synced pattern / reusable block ID that holds the content to test
   - `hypothesis`: the plain-English hypothesis you agreed on
   - `goal`: `engagement`, `click_any_link`, or `submit_form` based on what the user cares about
   - `variants`: an array of `{ title, content }` pairs. The first variant should be the control (current content). Content can be full WordPress block markup (including `<!-- wp:... -->` comment delimiters) or plain text/HTML -- Accelerate parses both correctly
   - `traffic_percentage`: default to `100` unless the user asks for a gradual rollout
   - `annotations`: merge two keys — `{ "toolkit:pattern": "<pattern_id>", "source": "ai" }`. The `toolkit:pattern` value is the pattern_id you classified in Planning step 4; the `source` value marks the experiment as AI-authored. Use `"source": "autopilot"` instead of `"ai"` only when this skill is invoked as part of an unattended continuous-optimization loop where no human is reviewing each step before the test goes live. In all normal (human-in-the-loop) sessions, use `"source": "ai"`.

   **Naming convention for AI-created tests:** Every experiment title and every variant title you write MUST be prefixed with `"AI: "`. Names must describe the hypothesis — what is being changed and what outcome is expected — not the mechanic. Good: `"AI: Hero — problem-first headline + donate button"`. Bad: `"AI: urgency rewrite"`, `"AI: test 2"`, `"AI: variant A"`. The name should let a developer or editor understand the test at a glance without reading the hypothesis field.

2. **Verify the test was created correctly.** Immediately after the call succeeds, fetch the block content again and check that:
   - Both variants contain non-empty content (not self-closing `<!-- wp:altis/variant ... /-->` tags)
   - The control variant still matches the original content
   - The new variant contains the proposed changes
   
   If any variant is empty or the content looks wrong, **immediately roll back**: restore the original content you saved in the backup step (via whatever write mechanism is available — `accelerate/update-variant` on index 0, or WP-CLI if accessible), then tell the user: *"The test setup didn't go as expected, so I've restored the original content. Nothing changed on your site."* Do not tell the user the test is live.

3. **Verify the experiment is actually running.** Content being correct is not enough: on current Accelerate versions, `create-ab-test` can leave the experiment in a paused/draft state (no start metas are written), in which case no traffic is allocated and no results will ever accrue — while everything *looks* created. Call `accelerate/get-variants` (the `experiment.status` field) or `accelerate/list-active-experiments` and check the experiment's status is `running`/`active`. If it is `paused` or missing:
   - Do **not** tell the user the test is live.
   - Tell them plainly: *"The test was created but Accelerate left it paused — this is a known plugin issue. Open the block in the editor and press 'Start test' (or ask your developer to start it), and I'll verify it's collecting data."*
   - After they confirm, re-check status before proceeding.
4. Only after both verifications pass, confirm to the user: *"Done. The test is live -- I've verified both versions are showing correctly."*
5. Tell them roughly when to check back. For sites with 1000+ weekly visitors, 1-2 weeks. For lower traffic, 2-4 weeks.

If the target block doesn't exist yet as a synced pattern / reusable block, stop and explain the reusable block requirement (see the section at the top of this skill).

## Monitoring

Call `accelerate/get-experiment-results` with the `block_id`. It returns variants with their metrics, whether there's a winner yet, and a recommendation object.

Present it like this:

```
## Homepage hero test — Day 9

| Version | Visitors | Clicks | Rate | Chance to win |
|---|---|---|---|---|
| Control | 1,140 | 187 | 16.4% | 18% |
| Variant A | 1,155 | 241 | 20.9% | 82% |

**Current lead:** Variant A, with +27% improvement.
**Statistical confidence:** 82% — not conclusive yet. Rule of thumb: wait until one version is 95%+ likely to win.
**ETA:** at the current rate, you should have a clear result in about a week.
```

If there's already a winner (`has_winner` is true), say so and offer to declare it.

## Reviewing / ending

1. Call `accelerate/get-experiment-results` to get the current state.
2. If the user wants to declare a winner, confirm **which variant** they want to declare (the current leader is the default but not assumed — ask them). Then call `accelerate/stop-experiment` with `action: "declare_winner"` and `winner_variant_index: <index>`.
3. If the user wants to stop without picking a winner, call `accelerate/stop-experiment` with `action: "stop"`.
4. If the user wants to pause temporarily, `action: "pause"`.
5. If the user wants to resume a paused test, `action: "resume"`.

After any state change, confirm in a single sentence.

## Monitoring multiple experiments

If the user asks "how are all my tests going", call `accelerate/list-active-experiments` first to get the set, then loop over each with `accelerate/get-experiment-results` and present a single summary table. Flag any that have reached a winning state.

## Rules

- **Never create, stop, pause, resume, or declare a winner without explicit user confirmation.** These are mutations; always show the user exactly what you're about to do.
- Always show variant text in confirmation prompts — don't hide it inside a "create test" summary.
- Check `list-active-experiments` before creating a new test to avoid overlapping experiments on the same block.
- If a test has been running less than ~7 days and the winner probability is under 80%, advise the user to wait. Small samples lie.
- Always translate "chance to be best" into a plain-English percentage. Never use the word "Bayesian" unless the user uses it first.
- If the test is on a block the user can't easily identify by name, include the `edit_url` from the response so they can click through to the editor.
- Every proposed variant must score 3 or higher on the differentiation rubric (message change + visual change + hypothesis clarity, each scored 0–2). If it does not, revise before presenting. See `docs/design-standards.md` for the full rubric.
- Never propose variant text that uses AI-slop markers: "unlock", "supercharge", "leverage", "empower", "elevate", "streamline", "revolutionize", or other generic power words. Use specific, concrete language grounded in the page's data instead.
