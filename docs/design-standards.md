# Design standards for variant proposals

This document teaches the model to propose better A/B test variants. It is never shown to the user. Skills that propose variant content — `accelerate-design`, `accelerate-test`, `accelerate-evolve`, `accelerate-optimize-landing-page`, `accelerate-diagnose` — reference it internally before presenting a variant for confirmation.

Inspired by [Impeccable](https://github.com/pbakaus/impeccable), adapted for WordPress block-level reality.

---

## 1. The slug-first principle

This is the single most important guardrail. WordPress block markup supports two ways to reference design tokens (colors, font sizes, spacing, font families):

| Approach | Example | Brand-safe? |
|---|---|---|
| **By preset slug** | `{"backgroundColor":"primary"}` | **Yes** — references the site's theme.json palette |
| **By raw value** | `{"style":{"color":{"background":"#0073aa"}}}` | **No** — hardcoded, may drift from brand |

**Rule: always use preset slug references. Never hardcode raw values.**

When the model constructs variant block markup, every design token must reference a slug from the site's brand context file (`~/.config/accelerate-ai-toolkit/sites/<key>/brand.md`). If that file does not exist yet, call `accelerate/get-site-context` with `include_blocks: true` and generate it before proposing a variant.

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

## 2. Block markup validity

**Invalid markup causes "Block contains unexpected or invalid content" errors in the editor.** WordPress validates each saved block's HTML against the expected output of *that block type's* `save()` function — block by block, against the block's own type, **never against the control or any other variant**. A *missing* generated class or a mismatched tag/attribute triggers a failure. This is not cosmetic — it breaks the editing experience for enterprise users. The way to stay valid is for each block to be well-formed for its own type; it is **not** to keep the variant's structure close to the control. A wholly different composition of individually-valid blocks is wholly valid.

### Required CSS classes from block attributes

WordPress auto-generates CSS classes from block JSON attributes. The HTML element **must** include every class that WordPress would produce. Omitting any of these causes a validation mismatch.

| Block attribute | Generated classes (on the HTML element) |
|---|---|
| `"backgroundColor":"<slug>"` | `has-<slug>-background-color has-background` |
| `"textColor":"<slug>"` | `has-<slug>-color has-text-color` |
| `"style":{"elements":{"link":{"color":{"text":"..."}}}}` | `has-link-color` |
| `"fontSize":"<slug>"` (preset) | `has-<slug>-font-size` |
| `"style":{"typography":{"fontSize":"..."}}` (custom) | `has-custom-font-size` |
| `"fontFamily":"<slug>"` | `has-<slug>-font-family` |
| `"gradient":"<slug>"` | `has-<slug>-gradient-background has-background` |

> Source: WordPress style engine (`wp_style_engine_get_styles` with `convert_vars_to_classnames`). See [Gutenberg style engine docs](https://github.com/wordpress/gutenberg/blob/trunk/packages/style-engine/docs/using-the-style-engine-with-block-supports.md).

### Class presence, not class order

**What matters is that every generated class is present — not the order they appear in.** WordPress's validator compares the class list as a *set* (whitespace-split, order-agnostic), so `"wp-block-button__link has-background"` and `"has-background wp-block-button__link"` validate identically. Do **not** spend effort matching a specific class order; spend it on including every class the block's attributes generate (see the table above). Omitting a generated class fails; reordering does not. (The conventional order below is fine to follow for readability, but it is not a validation requirement.)

- `core/button` `<a>`: `wp-block-button__link`, color classes, font classes, `wp-element-button`.
- `core/group` / `core/heading` / `core/paragraph`: `wp-block-<type>`, alignment, color, font classes.

### Inline style attribute rules

When a block uses custom (non-preset) values via the `style` attribute:

- **Property order must match WordPress serialization:** `padding-top`, `padding-right`, `padding-bottom`, `padding-left`, then `font-size`, then `font-weight`.
- The `href` attribute must come before `style` on link elements.
- Never mix preset slugs and inline styles for the same token type. If you use `"fontSize":"medium"` (preset), do not also set `style.typography.fontSize`.

### Composing safely (so boldness stays valid)

The whole point of these rules is to make ambition *safe*: a Score-3 recomposition (§4) is only worth proposing if it renders cleanly. These are constraints on *how* you build, never on *how boldly*.

- **Compose from the full registered palette.** Every block type in the site's registered `blocks` list (from `get-site-context`) is fair game — `core/columns`, `core/group`, `core/cover`, `core/media-text`, `core/buttons`, etc. — and you may replace the section's structure wholesale. You are not limited to the control's block types.
- **Learn conventions to enable ambition, not to copy the safe thing.** When unsure what classes or markup a block type expects, read a real example on this site (`get-variants` → `raw_markup`, or the site's synced patterns) to learn its exact class/attribute shape — then use that knowledge to compose your *new* structure validly. The goal of reading existing markup is fluency in the site's block grammar, not mirroring one block.
- **Ground every attribute; never invent values.** Fill only attributes you can ground in something real: registered preset slugs (§1), copy you are writing, and media that actually exists on the site (existing markup and synced patterns reveal real attachment URLs/IDs you can reuse). If you cannot ground an attribute — an image you don't have, an ID you'd be guessing, a coordinate — **omit it and let the block use its registered default.** An empty-but-valid block beats a block with an invented value. (Slug-first, §1, is the same principle for tokens.)
- **Never fabricate factual content.** Do not invent numbers, costs, statistics, donation amounts, or operational claims. Use clearly generic placeholder text the site owner can replace. Fabricating figures for a charity or enterprise site is a trust-destroying error.
- **Round-trip check before you ship it.** A reliable validity test for any composition: it must parse and re-serialize cleanly (the block delimiters, attribute JSON, and nesting are well-formed). If you've composed something rich, sanity-check the markup structure rather than assume it.

---

## 3. Anti-pattern bans

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

## 4. The differentiation rubric

**A variant that is not different enough to notice is not different enough to win.** If a visitor would need to read both versions side-by-side to spot the change, the change is too small to produce statistical significance in reasonable time.

These two dimensions describe one coherent system: **the concept is what we argue; the composition is how we stage it.** Message measures whether the variant makes a genuinely different *case* for why the visitor should act; Visual/structural measures whether the page is *staged* to make that case land. A winner usually needs both — a new argument, told through a new experience. Score the proposed variant against the control on all three dimensions (0–2 each):

### Message change (concept distance)

This measures the *strategic distance* between the variant's argument and the control's. The question is not "are the words different?" but "is the variant appealing to a different motivation?" — outcome / pain relief vs social proof vs scarcity vs trust/safety are different concepts; the same concept reworded is not.

| Score | Description | Example |
|---|---|---|
| **0 — fail** | Synonym swap. Same promise, different words. | "Build better websites" → "Create superior websites" |
| **1 — weak** | Same strategic frame, reworded. Same motivation appealed to, different phrasing or emphasis. | "Build better websites" → "Better websites, faster" (still a generic capability claim) |
| **2 — strong** | A genuinely different strategic frame — a different motivation appealed to. A new value proposition, not a new wording of the old one. | "Build better websites" (feature framing) → "Fix your slow site in one afternoon" (outcome / pain-relief framing). Or → "Join 12,000 teams who ship faster" (social-proof framing). |

The highest-leverage Score-2 move is reframing a *feature* into an *outcome*: not what the thing is, but what the visitor gets and the problem it ends.

### Visual / structural change (concept staging)

This measures whether the page is *staged* to make the concept land. A concept argued in plain text on an unchanged layout is under-staged; a concept whose imagery, color, type, and CTA all serve the argument is fully staged.

| Score | Description | Example |
|---|---|---|
| **0 — fail** | Identical block structure, only text content changed. | Heading text swapped, everything else the same |
| **1 — weak** | A single structural lever pulled. | A list added, a CTA moved, a background color applied — one isolated change |
| **2 — strong** | A composed redesign that stages the concept: three or more structural levers working together as one coherent experience, all serving the argument. | For an outcome concept: a before/after image (with descriptive alt text) + a background color preset paired with an explicit text color + a deliberate heading/body font-family preset pairing + a single high-contrast CTA. One lever is a tweak; a composition is a different experience that *embodies* the frame. |
| **3 — reimagined** | A **ground-up recomposition**: the section is rebuilt as a distinctly different *kind* of section — composed from the site's full registered block palette and its own pattern vocabulary — not the control restructured. Judged by **coherence and fit, not lever count**: it must read unmistakably as this site (its tokens, its voice, its patterns) and argue one clear concept, while being a section the control simply does not contain. | An outcome concept restaged as a `core/cover` with a full-bleed media-library image, then a `core/columns` pairing a benefit-led heading with a single proof stat, closing on one high-contrast CTA — a section the control never had. *(Illustrative, not a template — the right recomposition is whatever stages this concept on this site.)* |

> **Why composition matters:** a single-lever variant produces an effect too small to detect on typical traffic volumes, and it leaves the concept under-staged — the argument is made but not felt. Composed variants create a meaningfully different experience, which is what a clear winner requires.
>
> **When to reach for Score 3 (reimagined).** Score 2 is the floor for a real challenger; Score 3 is the gear for a **big swing**, and you should take it when the situation rewards drastic change: a block that has **plateaued** across rounds (copy/composition haven't moved it — see the escalation ladder in `accelerate-test`), a block with lots of **headroom**, **low traffic** (where only a bold difference can ever resolve), or the **architecture rung** of an escalation. Don't force it when *refining* an already-won concept — that's when you tighten, not reinvent. The point is that "drastic, ground-up, but still unmistakably this site" is a **rewarded** outcome, not a risky deviation: the rubric explicitly has a top gear for it.
>
> A Score-3 recomposition is still bound by the slug-first principle (§1) and the anti-pattern bans (§3). Those constrain *how* you compose (on-brand tokens, no generic-AI markers) — never *how boldly*. Validity and brand-fidelity are the floor; ambition is free above it.

### Hypothesis clarity

| Score | Description | Example |
|---|---|---|
| **0 — fail** | No hypothesis or purely generic. | "Let's try a different headline" |
| **1 — weak** | Vague directional hypothesis. | "A shorter headline might work better" |
| **2 — strong** | Specific, data-grounded prediction. | "52% of visitors arrive from Google pricing searches; the current headline doesn't mention pricing. Leading with pricing should reduce bounce." |

### Passing threshold

- **Total score must be 3 or higher** (out of 7 — Message 0–2, Visual/structural 0–3, Hypothesis 0–2).
- **No zeros on any single dimension.** A variant that scores 0 on any dimension must be reworked regardless of total score.
- If the variant does not pass, strengthen it before presenting to the user — change the value proposition, add structural variation, or sharpen the hypothesis with data from the fetched analytics.

> **CRO note:** Strong tests aim for Score 2 on **both** Message and Visual/structural — a distinct concept (Message 2), fully staged (Visual 2). The two are one move: a new argument told through a new experience. Either can be the conversion driver, and you rarely know in advance which — a concept argued but not staged, or a redesign with no new argument behind it, each leaves half the lever untested. When time or traffic constrains you to one variant, prefer the combination that scores highest across both dimensions, and never let a Score-2 composition stand on a Score-1 (reworded) message — that is a redesign with nothing new to say.

### Traffic-aware override

This connects to the router's existing traffic-level awareness (principle §2):

- **Low traffic** (under ~1,000 weekly visitors): Only propose Score 2 variants. Small differences will never reach significance on thin traffic. Say to the user: "With your traffic level, we need to test something bold to get a clear answer."
- **Medium traffic** (1,000–10,000): Score 1 variants are viable. Standard rubric applies.
- **High traffic** (10,000+): Score 1 variants become practical for incremental tests. Still lead with higher-impact ideas first.

---

## 5. Copy quality rules

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

### Display-text line breaks (headlines, heroes, posters)

A display headline is not a sentence — it's a **stack of visual phrases**. How it breaks across lines is part of the design, and a bad break reads as amateur even when the words are right. When you write a headline that will wrap (hero, banner, pull quote, any large type), make the break carry meaning. For prominent display copy these are close to hard rules:

- **Break by meaning, keep phrases together.** "Grow your / business faster", never "Grow your business / faster". Write the phrasing so the natural break falls between phrases.
- **No widows / runts.** Never strand a single short word alone on the last line. If the phrasing produces one, **rewrite the line** — that's usually the cleanest fix, not resizing.
- **Never end a prominent line on a weak word** — `the, and, of, for, to, with`, etc. — and **never split a compound** (`AI-powered`, `New York`, `higher education`). These dangle or misread.
- **Balance the lines.** Avoid one long line over one tiny line; aim for an even rag. (In CSS-controlled contexts, `text-wrap: balance` does this automatically — but the phrasing still has to support it.)
- **Fewer sizes and weights.** Display hierarchy gets worse with more of them; keep it clean. All-caps usually wants slight extra tracking; lowercase does not.
- **The read-it-out-loud test.** If you'd naturally pause at the line break when speaking the headline, it works. If the break makes you trip, it'll look wrong too — rewrite it.

Good break patterns: *modifier / main idea* ("Smarter content / for modern teams"), *setup / payoff* ("Build less / launch more"), *noun phrase / qualifier* ("Enterprise WordPress / without the bottlenecks").

---

## 6. Brand context file format

The brand context file lives at `~/.config/accelerate-ai-toolkit/sites/<key>/brand.md`. It is generated from `accelerate/get-site-context` (with `include_blocks: true`) and maps the site's design tokens to the block attribute slugs the model should use.

### Site key derivation

The site key is derived by the canonical rule in `accelerate-learn` (`<site-name-slug>-<theme-slug>-<url-hash>`, gracefully omitting the theme segment when the plugin doesn't expose it). Do not implement a separate derivation here — use that rule so all per-site files share one key.

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

## 7. When to apply these standards

These standards activate at exactly one point: **between the model drafting a variant and the model presenting it to the user for confirmation.**

```
Fetch data → Reason about what to test → Draft variant → [DESIGN CHECK] → Present to user → Confirm → create-ab-test
                                                              ↑
                                                     invisible to user
```

The design check is an internal reasoning step:

1. Read this document (`docs/design-standards.md`).
2. Read the brand context file (or generate it via `get-site-context` if it does not exist).
3. Validate block markup correctness — required classes, class order, style attribute order (§2).
4. Score the variant against the differentiation rubric (§4).
5. Check brand consistency — slug-first principle (§1).
6. Check anti-pattern bans (§3).
7. Scan copy for AI-slop markers (§5).
8. **Revise silently** if anything fails — the user only ever sees the passing version.

The marketer never sees a "quality check failed" message. They just see better variants with bolder hypotheses that match their site's visual language.

---

## 8. Relationship to the learning journal (v1.2)

These design standards are the **generic quality floor**. When the v1.2 learning journal ships, it becomes the **site-specific layer on top**:

- If the journal shows a pattern has consistently won on this site → prefer it over generic recommendations.
- If the journal shows a pattern has consistently lost on this site → do not propose it, even if the generic standards would allow it.
- The journal overrides these standards for that specific site. These standards apply when the journal has no opinion.

---

## 9. Bold-by-default round composition

The rubric above governs a *single* variant. This governs how a **round** is composed — what set of arms you field at once. It applies whenever you field more than a control + one arm, and it is the spine of `accelerate-evolve`.

**One incumbent, the rest are swings.** A round carries exactly one incumbent — the current control (on a multi-round block, the harvested champion) — as the benchmark to beat. Every *other* arm is a bold challenger: a genuinely different **structure** drawn from the site's own vocabulary (the brand pack, `docs/brand-pack.md`), not a re-skin of the control. Do not spend arms re-testing the winner with timid tweaks; the winner rides as control while the challengers explore.

**Novelty-first.** Pull each challenger's structure from a kind of section the site has that you *haven't tried yet* on this block — recombine and extend it (Visual Score 2–3). Only once the site's vocabulary is genuinely spent do you author a new section from what's winning (`accelerate-design`). Never re-field the same structure with reworded copy.

**The arm budget is the grid.** How many challengers you field is set by traffic/conversion volume, not ambition — see the arm-count rule in `accelerate-test` (Planning step 5) and the router's traffic-level awareness. Low volume → control + **one** bold challenger. Ample volume (≥500 conv/month) → 3–5 distinct challengers in one test. The bold-by-default shape scales to whatever budget the site supports; it never collapses to a lone timid arm (the bold-challenger rule still binds every round).

**Cull on a clean loss, then escalate.** A composed (Visual Score 2+) concept that loses cleanly under the stopping gate is retired — don't re-field it; climb the escalation ladder (`accelerate-test`). A *timid* loss teaches nothing (anti-false-negative rule) and is not grounds to retire a concept.

**Integrity.** Never declare a winner, harvest, or cull on thin data — the binding stopping gate in `accelerate-test` is the only authority on "what won." Bold on composition; honest on results.
