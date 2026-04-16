---
name: accelerate-learn
description: Update what the toolkit has learned about your site from A/B test results. Run periodically to improve future recommendations.
license: MIT
category: learning
parent: accelerate
disable-model-invocation: true
---

# Accelerate -- Update your site's learning journal

You read the site's completed A/B test results, classify each experiment into a canonical suggestion pattern, and update the site's learning journal so every other skill can tailor future recommendations to what has worked here.

**This skill is read-only on WordPress.** You never create, modify, or stop experiments. You write two local files only.

## Step 1 -- Fetch site context

Call `accelerate/get-site-context` with `include_blocks: false`. You need `site.url` to derive the site slug for the journal filename.

### Site slug derivation rule

This is the canonical rule. No other skill implements its own version.

1. Take `site.url` (e.g. `https://www.example.com:8080`)
2. Strip the protocol (`https://`)
3. Strip `www.` prefix
4. Strip the port number (`:8080`)
5. Strip any trailing slash
6. Replace dots with hyphens
7. Lowercase the result

Example: `https://www.example.com:8080` -> `example-com`

The journal files live at:
- `~/.config/accelerate-ai-toolkit/journal-<site-slug>.json`
- `~/.config/accelerate-ai-toolkit/journal-<site-slug>.md`

## Step 2 -- List completed experiments

Call `accelerate/list-experiments` with:

```
status: "completed"
type: "all"
per_page: 100
page: 1
```

If the response's `total` exceeds 100, paginate: increment `page` and repeat until all experiments are fetched.

Collect the full list of completed experiments. Each item includes `experiment_id`, `block_id`, `has_winner`, `winner_variant_index`, `annotations`, `started_at`, `ended_at`.

## Step 3 -- Get detailed results

For each experiment from step 2, call `accelerate/get-experiment-results` with `experiment_id` (not `block_id`). This returns the full variant metrics: `impressions`, `conversions`, `conversion_rate`, `probability_to_beat_control`, `is_winner` per variant.

## Step 4 -- Read the existing journal

Read `~/.config/accelerate-ai-toolkit/journal-<site-slug>.json` if it exists.

- **File missing:** Start with an empty journal structure.
- **Invalid JSON / parse error:** Do not overwrite. Stop and tell the user: *"Your learning journal appears to be corrupted. You can delete it and I'll rebuild from scratch, or restore it from a backup."* Do not proceed.
- **`schema_version` is not `1`:** Stop and tell the user: *"Your learning journal was created by a newer version of the toolkit. Please update the toolkit to read it."* Do not proceed.
- **Valid:** Parse and continue.

## Step 5 -- Classify each experiment

For each experiment:

### 5a. Determine the pattern

Read `annotations['toolkit:pattern']` from the experiment's annotations object.

- If present and matches a pattern_id in the taxonomy below: use that pattern.
- If present but not in the taxonomy: classify as `other` and record the annotation value in the pattern's notes.
- If `annotations` is missing or doesn't contain `toolkit:pattern`: classify as `other`.

No keyword fallback. No hypothesis text parsing. Classification is a pure dictionary lookup.

### 5b. Determine the outcome

| Condition | Result |
|-----------|--------|
| `has_winner: true` AND `winner_variant_index > 0` | **Win** -- the tested change beat the control |
| `has_winner: true` AND `winner_variant_index == 0` | **Loss** -- the control won |
| `has_winner: false` (experiment concluded without significance) | **Inconclusive** -- does not count as win or loss |

### 5c. Compute lift for wins

For wins: lift = `((winner_conversion_rate - control_conversion_rate) / control_conversion_rate) * 100`. The control is always variant index 0. Store as a percentage.

## Step 6 -- Merge into journal state

For each pattern that has at least one experiment:

1. Update `tests_won`, `tests_lost`, `tests_inconclusive`
2. `tests_total = tests_won + tests_lost + tests_inconclusive`
3. `hit_rate = tests_won / (tests_won + tests_lost)` -- excludes inconclusive. If `tests_won + tests_lost == 0`, hit_rate is `null`.
4. `avg_lift_percent` = mean of all winning lifts for this pattern. `null` if no wins.
5. `last_tested_at` = most recent `ended_at` across all experiments for this pattern.
6. Apply the four-state classification:

| Status | Rule |
|--------|------|
| `inconclusive` | `tests_won + tests_lost < 3` |
| `won` | `tests_won + tests_lost >= 3` AND `hit_rate >= 0.75` |
| `lost` | `tests_won + tests_lost >= 3` AND `hit_rate <= 0.25` |
| `mixed` | `tests_won + tests_lost >= 3` AND `0.25 < hit_rate < 0.75` |

The minimum threshold of 3 decisive tests (wins + losses, not counting inconclusive) is load-bearing. Do not lower it.

## Step 7 -- Write the journal atomically

Write the JSON source of truth:

```bash
# Write to temp file first, then atomic rename
python3 -c "
import json, os, sys
data = json.loads(sys.argv[1])
path = os.path.expanduser(sys.argv[2])
tmp = path + '.tmp'
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(tmp, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
os.chmod(tmp, 0o600)
os.rename(tmp, path)
" '<journal_json>' '~/.config/accelerate-ai-toolkit/journal-<site-slug>.json'
```

Then generate and write the markdown summary from the JSON (same atomic pattern).

### JSON schema

```json
{
  "schema_version": 1,
  "site": {
    "slug": "<site-slug>",
    "name": "<from get-site-context>",
    "url": "<from get-site-context>"
  },
  "last_updated": "<ISO 8601 timestamp>",
  "stats": {
    "total_experiments_considered": 0,
    "concluded_with_winner": 0,
    "concluded_without_winner": 0,
    "patterns_with_signal": 0
  },
  "patterns": [
    {
      "pattern_id": "<from taxonomy>",
      "display_name": "<from taxonomy>",
      "status": "won|lost|mixed|inconclusive",
      "tests_total": 0,
      "tests_won": 0,
      "tests_lost": 0,
      "tests_inconclusive": 0,
      "hit_rate": null,
      "avg_lift_percent": null,
      "last_tested_at": null,
      "last_winning_block": null,
      "notes": null
    }
  ]
}
```

### Markdown format

Regenerated from the JSON on every run. The user reads this; no skill parses it.

```markdown
# Learning journal -- [Site Name]

Last updated: [date]

Summary: [X] experiments analysed, [Y] with a clear winner, [Z] inconclusive.

## Patterns that win on your site

### [Display name]
- Won [N] of [M] tests ([hit_rate]%)
- Average improvement: +[lift]%
- Last tested: [date]

## Patterns that haven't worked here

### [Display name]
- Won [N] of [M] tests ([hit_rate]%)
- Last tested: [date]
- [advisory note -- this is site-specific, not a universal rule]

## Mixed results

### [Display name]
- Won [N] of [M] tests
- Works sometimes, not a default

## Not enough data yet

### [Display name]
- [N] tests so far, need at least 3 decisive results before drawing conclusions
```

## Step 8 -- Print summary to user

Short, marketer-friendly. Follow the output style guide (`docs/output-style.md`). Example:

> **Learning journal updated** for [site name].
>
> 🔴 **New this week:** "Rewrite headline to match what visitors searched for" has now won 4 of 5 tests with an average +23% improvement. I'll lean on this when suggesting A/B tests.
>
> 🟡 **Still building evidence:** "Move the main button higher on the page" has 2 wins out of 3 -- one more test and I'll have a clearer picture.
>
> 🟢 **Not working here:** "Add urgency language to buttons" has lost all 3 tests. I'll stop leading with it unless you ask.
>
> *"Want me to suggest what to test next based on what we've learned?"*

**Hard rules for this output:**
- Never show `pattern_id` values. Always use `display_name`.
- Never say "journal file", "JSON", "schema", "parse", or "pattern taxonomy".
- Never recommend specific test ideas -- hand off to `accelerate-opportunities` or `accelerate-test`.
- If no patterns have enough data yet, say so plainly and encourage patience.

---

## Pattern taxonomy

These are the 15 canonical suggestion patterns. The `pattern_id` is the machine key; the `display_name` is what the user sees.

| `pattern_id` | `display_name` |
|---|---|
| `headline_match_intent` | Rewrite headline to match what visitors searched for |
| `headline_clarity` | Rewrite headline for clarity |
| `cta_above_fold` | Move the main call-to-action higher on the page |
| `cta_copy` | Rewrite button or link text to be more specific |
| `social_proof` | Add social proof near the call-to-action |
| `testimonial` | Add a customer testimonial near the call-to-action |
| `urgency_copy` | Add urgency or scarcity language |
| `simplify_hero` | Simplify the hero section (remove clutter) |
| `pricing_display` | Change how pricing is shown (default period, anchoring) |
| `personalize_referrer` | Personalise content by traffic source |
| `personalize_geo` | Personalise content by visitor location |
| `personalize_device` | Personalise content by device type |
| `hero_image` | Change the hero image |
| `form_fields` | Change form field count or layout |
| `other` | Other / unclassified |

**This taxonomy is fixed.** Do not invent new pattern_ids during a run. If an experiment doesn't match a known pattern, it goes to `other`. The taxonomy grows only in toolkit releases.

---

## Rules

- **Never create, modify, or stop experiments.** This skill is read-only on WordPress.
- **Never recommend specific test ideas in the summary.** Hand off to other skills.
- **Never overwrite a corrupted journal.** Surface the error and let the user decide.
- **Both journal files are `chmod 600`.** Same security posture as credentials.
- **Write atomically.** Temp file + rename. Never write directly to the target path.
- **Minimum 3 decisive tests before classification.** The `inconclusive` floor is non-negotiable.
