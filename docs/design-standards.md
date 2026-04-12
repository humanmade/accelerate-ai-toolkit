# Design standards for variant proposals

This document teaches the model to propose better A/B test variants. It is never shown to the user. Skills that propose variant content — `accelerate-test`, `accelerate-optimize-landing-page`, `accelerate-diagnose` — reference it internally before presenting a variant for confirmation.

Inspired by [Impeccable](https://github.com/pbakaus/impeccable), adapted for WordPress block-level reality.

---

## 1. The slug-first principle

This is the single most important guardrail. WordPress block markup supports two ways to reference design tokens (colors, font sizes, spacing, font families):

| Approach | Example | Brand-safe? |
|---|---|---|
| **By preset slug** | `{"backgroundColor":"primary"}` | **Yes** — references the site's theme.json palette |
| **By raw value** | `{"style":{"color":{"background":"#0073aa"}}}` | **No** — hardcoded, may drift from brand |

**Rule: always use preset slug references. Never hardcode raw values.**

When the model constructs variant block markup, every design token must reference a slug from the site's brand context file (`~/.config/accelerate-ai-toolkit/brand-<site-slug>.md`). If that file does not exist yet, call `accelerate/get-site-context` with `include_blocks: true` and generate it before proposing a variant.

### Correct vs incorrect patterns

| Token type | Correct (slug-based) | Wrong (hardcoded) |
|---|---|---|
| Background color | `{"backgroundColor":"primary"}` | `{"style":{"color":{"background":"#0073aa"}}}` |
| Text color | `{"textColor":"contrast"}` | `{"style":{"color":{"text":"#333333"}}}` |
| Font size | `{"fontSize":"large"}` | `{"style":{"typography":{"fontSize":"2rem"}}}` |
| Spacing/padding | `"var:preset\|spacing\|50"` | `"20px"` or `"1.5rem"` |
| Font family | `{"fontFamily":"heading"}` | `{"style":{"typography":{"fontFamily":"Georgia"}}}` |

### Additional brand rules

- **Block types** must exist in the site's registered `blocks` array from `get-site-context`. Never introduce a block type the site does not support.
- **Block style variations** (e.g., `is-style-outline` for buttons) must be registered for that block type. Do not invent custom className styling.
- If the site's palette does not include a color you need, tell the user ("Your palette doesn't have a warm accent — want me to use your closest option, or should you add one in the theme?") rather than hardcoding a hex value.

---

## 2. Anti-pattern bans

These are block-level patterns the model must never produce in variant content. Each is a known marker of generic AI-generated design.

| Ban | Block attribute pattern to avoid | What to do instead |
|---|---|---|
| **Side-stripe borders** | `{"style":{"border":{"left":{"width":"4px","color":"..."}}}}` or similar one-sided thick borders on group/column blocks | Use `{"backgroundColor":"<slug>"}` for emphasis, a full border from theme presets, or no indicator at all |
| **Gradient text** | `{"gradient":"..."}` applied to heading or paragraph blocks | Use `{"textColor":"<slug>"}` — a solid color from the site palette |
| **Nested bordered groups** | A `wp:group` block with border styling inside another `wp:group` block with border styling | One level of visual containment maximum. If you need hierarchy, use background color or spacing, not nested borders |
| **Every button primary** | Multiple `wp:button` blocks all using `{"className":"is-style-fill"}` or the default filled style | Only one button should be primary (fill). Others should use `is-style-outline` or the site's alternative registered button style |
| **Hardcoded shadows** | `{"style":{"shadow":"..."}}` with raw CSS shadow values | Use theme shadow presets if the site defines them. Otherwise, omit shadows entirely |
| **Identical column content** | Every column in a `wp:columns` block using the exact same block structure (icon + heading + paragraph, repeated identically) | Vary the content structure and length across columns. Not every column needs the same template |
| **Decorative-only blocks** | Adding `wp:separator`, `wp:spacer`, or empty `wp:group` blocks purely for visual padding | Use the spacing scale (`var:preset\|spacing\|<slug>`) on the surrounding blocks instead |

---

## 3. The differentiation rubric

**A variant that is not different enough to notice is not different enough to win.** If a visitor would need to read both versions side-by-side to spot the change, the change is too small to produce statistical significance in reasonable time.

Score the proposed variant against the control on three dimensions (0–2 each):

### Message change

| Score | Description | Example |
|---|---|---|
| **0 — fail** | Synonym swap. Same promise, different words. | "Build better websites" → "Create superior websites" |
| **1 — weak** | Emphasis shift. Same message, different framing. | "Build better websites" → "Better websites, faster" |
| **2 — strong** | New promise or new angle. Different value proposition entirely. | "Build better websites" → "Fix your slow site in one afternoon" |

### Visual / structural change

| Score | Description | Example |
|---|---|---|
| **0 — fail** | Identical block structure, only text content changed. | Heading text swapped, everything else the same |
| **1 — weak** | Minor structural addition. | A subheading block added, a word bolded, a list item added |
| **2 — strong** | Visible layout change a visitor would notice at a glance. | CTA moved above the fold, image added/removed, section reordered, new block type introduced |

### Hypothesis clarity

| Score | Description | Example |
|---|---|---|
| **0 — fail** | No hypothesis or purely generic. | "Let's try a different headline" |
| **1 — weak** | Vague directional hypothesis. | "A shorter headline might work better" |
| **2 — strong** | Specific, data-grounded prediction. | "52% of visitors arrive from Google pricing searches; the current headline doesn't mention pricing. Leading with pricing should reduce bounce." |

### Passing threshold

- **Total score must be 3 or higher** (out of 6).
- **No zeros on any single dimension.** A variant that scores 0 on any dimension must be reworked regardless of total score.
- If the variant does not pass, strengthen it before presenting to the user — change the value proposition, add structural variation, or sharpen the hypothesis with data from the fetched analytics.

### Traffic-aware override

This connects to the router's existing traffic-level awareness (principle §2):

- **Low traffic** (under ~1,000 weekly visitors): Only propose Score 2 variants. Small differences will never reach significance on thin traffic. Say to the user: "With your traffic level, we need to test something bold to get a clear answer."
- **Medium traffic** (1,000–10,000): Score 1 variants are viable. Standard rubric applies.
- **High traffic** (10,000+): Score 1 variants become practical for incremental tests. Still lead with higher-impact ideas first.

---

## 4. Copy quality rules

### AI-slop word bans

Never use these words in variant copy. They are the top markers of AI-generated marketing text:

> unlock, supercharge, leverage, empower, elevate, streamline, revolutionize, game-changing, cutting-edge, seamless, next-level, harness, transform, reimagine

Replace with specific, concrete language grounded in the page's data. "Start your free trial" beats "Unlock your potential." "See pricing for teams" beats "Elevate your workflow."

### The AI slop test

After drafting variant copy, apply this test:

**"If a marketer would look at the variant and think 'this is clearly just an AI rewording', the variant needs more work. A good variant makes the marketer think 'oh, that's a different angle.'"**

### Copy principles for variants

- **Specific beats generic.** "Fix your slow WordPress site" is better than "Improve your web presence."
- **Name the visitor's problem.** The data from `get-traffic-breakdown` and `get-engagement-metrics` tells you who's arriving and what they're looking for. Use that in the copy.
- **Match the referrer's promise.** If 60% of traffic comes from a Google search for "free trial", the hero should mention "free trial" — not a generic value proposition.
- **One CTA per section.** If the variant introduces a new call-to-action, don't scatter three more around it.
- **Plain language over jargon.** The site's visitors are real people. Write like you're talking to them, not writing ad copy for an awards submission.

---

## 5. Brand context file format

The brand context file lives at `~/.config/accelerate-ai-toolkit/brand-<site-slug>.md`. It is generated from `accelerate/get-site-context` (with `include_blocks: true`) and maps the site's design tokens to the block attribute slugs the model should use.

### Site slug derivation

Lowercase the hostname, replace dots with hyphens, strip `www.`, strip port numbers.
Example: `https://www.example.com:8080` → `example-com`

### File template

```markdown
# Brand context for [site name]

Generated: [date]
Source: [site URL]

## Color palette

Use these slugs in block attributes — never hardcode hex values.

| Slug | Name | Hex | Use as |
|---|---|---|---|
| primary | Primary | #0073aa | `{"backgroundColor":"primary"}` or `{"textColor":"primary"}` |
| contrast | Contrast | #1d2327 | `{"textColor":"contrast"}` |
| base | Base | #ffffff | `{"backgroundColor":"base"}` |

## Font sizes

| Slug | Name | Size | Use as |
|---|---|---|---|
| small | Small | 0.875rem | `{"fontSize":"small"}` |
| medium | Medium | 1.125rem | `{"fontSize":"medium"}` |
| large | Large | 1.75rem | `{"fontSize":"large"}` |

## Font families

| Slug | Name | Use as |
|---|---|---|
| heading | Heading | `{"fontFamily":"heading"}` |
| body | Body | `{"fontFamily":"body"}` |

## Spacing presets

| Slug | Size | Use as |
|---|---|---|
| 40 | 1rem | `"var:preset\|spacing\|40"` |
| 50 | 1.5rem | `"var:preset\|spacing\|50"` |
| 60 | 2rem | `"var:preset\|spacing\|60"` |

## Available blocks and style variations

| Block | Registered styles |
|---|---|
| core/button | fill, outline |
| core/image | rounded, default |
| core/quote | default, plain |
```

### Lifecycle

- **Created automatically** the first time a variant-producing skill runs and no brand file exists for this site.
- **Regenerated** if the file is older than 7 days, or when the user asks to "refresh my brand context."
- **Permissions:** `chmod 600`, same as credential and journal files.

---

## 6. When to apply these standards

These standards activate at exactly one point: **between the model drafting a variant and the model presenting it to the user for confirmation.**

```
Fetch data → Reason about what to test → Draft variant → [DESIGN CHECK] → Present to user → Confirm → create-ab-test
                                                              ↑
                                                     invisible to user
```

The design check is an internal reasoning step:

1. Read this document (`docs/design-standards.md`).
2. Read the brand context file (or generate it via `get-site-context` if it does not exist).
3. Score the variant against the differentiation rubric (§3).
4. Check brand consistency — slug-first principle (§1).
5. Check anti-pattern bans (§2).
6. Scan copy for AI-slop markers (§4).
7. **Revise silently** if anything fails — the user only ever sees the passing version.

The marketer never sees a "quality check failed" message. They just see better variants with bolder hypotheses that match their site's visual language.

---

## 7. Relationship to the learning journal (v1.2)

These design standards are the **generic quality floor**. When the v1.2 learning journal ships, it becomes the **site-specific layer on top**:

- If the journal shows a pattern has consistently won on this site → prefer it over generic recommendations.
- If the journal shows a pattern has consistently lost on this site → do not propose it, even if the generic standards would allow it.
- The journal overrides these standards for that specific site. These standards apply when the journal has no opinion.
