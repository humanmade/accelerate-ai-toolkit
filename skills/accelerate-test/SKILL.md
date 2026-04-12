---
name: accelerate-test
description: Use when the user wants to plan, create, monitor, review, or end an A/B test. Keywords include A/B test, split test, experiment, variant, test idea, what to test, create a test, running tests, test results, declare winner, stop test, pause test.
license: MIT
category: experimentation
parent: accelerate
disable-model-invocation: true
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

## Planning

1. Call `accelerate/list-active-experiments` — don't propose a new test on a block that already has one running.
2. If the user hasn't named a target, use the findings from `accelerate-review`, `accelerate-diagnose`, or `accelerate-opportunities` to suggest the block with the best impact potential. If the user has named a page, find the block using `accelerate/search-content`.
3. Check site traffic volume via `accelerate/get-performance-summary` (`7d` or `30d` depending on how fast the user wants results) so you can gauge whether the test can reach significance.
4. Propose 1–2 clear hypotheses in plain English. Each hypothesis names: the block, the change, the expected outcome, and the success metric.
5. Before presenting the hypothesis, apply the design standards from `docs/design-standards.md`. Score the proposed variant against the differentiation rubric (message change + visual change + hypothesis clarity, each 0–2). If the total is below 3/6 or any dimension scores 0, strengthen the variant — change the value proposition, add structural variation, or sharpen the hypothesis with data from the fetched analytics. Do not present a variant that fails the rubric. For low-traffic sites (under ~1,000 weekly visitors), only propose Score 2 variants.

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

Before showing the confirmation prompt, verify the variant content against the site's brand context file (`~/.config/accelerate-ai-toolkit/brand-<site-slug>.md`). If the file does not exist, generate it from `accelerate/get-site-context` with `include_blocks: true`. Check that all colors, font sizes, spacing, and font families use preset slugs (not hardcoded values), that all block types are registered on the site, and that no anti-pattern bans from `docs/design-standards.md` are violated. Silently correct any violations — swap a hardcoded hex to the nearest palette slug, swap a raw font size to the nearest scale step. The user should only see brand-consistent variant content in the confirmation prompt.

Once confirmed:

1. Call `accelerate/create-ab-test` with:
   - `block_id`: the synced pattern / reusable block ID that holds the content to test
   - `hypothesis`: the plain-English hypothesis you agreed on
   - `goal`: `engagement`, `click_any_link`, or `submit_form` based on what the user cares about
   - `variants`: an array of `{ title, content }` pairs. The first variant should be the control (current content); the user may need to provide the raw block markup for the variant content, or you can use plain text/HTML which Accelerate accepts
   - `traffic_percentage`: default to `100` unless the user asks for a gradual rollout

2. When the call succeeds, confirm to the user in one sentence: *"Done. The test is live on the homepage hero."*
3. Tell them roughly when to check back. For sites with 1000+ weekly visitors, 1–2 weeks. For lower traffic, 2–4 weeks.

If the target block doesn't exist yet as a synced pattern / reusable block, explain that gently: "This element needs to be turned into a reusable block first — the Accelerate team uses these as the unit of testing. You'll need to do that step in the WordPress editor."

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
