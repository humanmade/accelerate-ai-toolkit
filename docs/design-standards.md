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

**Use Block Runner for the actual editor-validity verdict whenever it is available.** The required `validate` → `fix` → `validate` pre-flight, including its repair, withholding, and fail-open rules, lives in `docs/block-runner.md`. The tables below are still essential authoring guidance and are the manual fallback when that optional tool is unavailable; they are not a substitute for a successful headless-Gutenberg validation.

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
- **Round-trip check before you ship it.** When Block Runner is available, its required pre-flight (`validate` → `fix` → `validate`) is the round-trip check — do not replace it by eyeballing this table. If the tool is unavailable, manually check that the block delimiters, attribute JSON, and nesting parse and re-serialize cleanly, then disclose the fallback as `docs/block-runner.md` requires.
- **Prefer forgiving primitives for full-bleed / visual sections.** Hand-authored `wp:cover` is the most mismatch-prone block — build the same look from `wp:group` + `wp:image` + `wp:heading` + `wp:paragraph` + `wp:buttons` styled in CSS. This and the editor/alignment/width gotchas that govern whole sections are in **§15**.

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

### The detector tells — generation must pre-clear these

Generation must pre-clear the list below: **these are exactly what `impeccable detect` flags** (~44 deterministic detector rules). A variant that trips one is generic-AI design by definition — rework it before presenting. Each tell, and the block-level shape it takes in WordPress:

| Tell (`impeccable detect` rule) | What it looks like in block markup | Pre-clear by |
|---|---|---|
| `gradient-text` | `{"gradient":"…"}` on a heading/paragraph | Solid `{"textColor":"<slug>"}` |
| `side-stripe` | one-sided thick colored `border` on group/column/callout | Background slug, full border preset, or no indicator |
| `identical-card-grids` | same-size icon+heading+text columns repeated, no variation | Varied spans/sizes, mixed non-card content (see archetype library §10) |
| `repeated-section-kickers` | a tiny uppercase tracked eyebrow above **every** section | **One** named kicker is voice; an eyebrow on every section is AI grammar — drop the repetition |
| `numbered-section-markers` | `01· / 02· / 03·` on every section | Numbers earn their place only inside a real ordered sequence; never as default scaffold |
| `icon-tile-stack` | a large rounded-corner icon tile above every heading | Lead with type/space hierarchy, not a decorative tile per section |
| `gray-on-color` | gray text on a colored background (washed out) | A darker shade of the same hue, or an alpha of the text color — never neutral gray on color |
| `monotonous-spacing` | padding = gap = margin everywhere, no rhythm | Tight grouping for related, generous gaps between sections (see §12) |
| `glassmorphism` | decorative blur/glass card surfaces | Solid background slugs; reserve depth for real elevation |
| `hero-metric` | big number + small label + gradient accent (SaaS cliché) | Earn a stat only where proof *is* the argument (stat-band archetype, §10) — never as hero decoration |
| `stat-rail` | a repeated 3–4 cell big-number / tiny-mono-label rail bolted under a hero headline (often with a dead empty cell, gray-on-color labels) | A stat belongs in a hero only *integrated* — inline, one hero figure, or a real asymmetric layout — never a repeated N-up cell grid (§10 stat-anchored) |
| `unstyled-form-control` | a `wp:html` raw native `<input>`/`<button>` — white box, default border, system-font button, no theme tokens | Emit themed form controls: aphelion field styling (token bg/border/radius, `body` font, themed submit via the CTA primitive) — never a bare native control (§10 final-banner) |
| `accent-ground` | a full-bleed section on an accent-color background (accent used as a page ground, not a reserved highlight) | Accent stays ≤10% per 60-30-10 (§12); ground sections in neutral/contrast surfaces, reserve accent for the CTA / primary |
| `ghost-text` | same-hue low-opacity text laid over its own ground as decoration (e.g. orange-on-orange at low alpha) | Decorative text must clear 4.5:1 — a real contrasting slug, never a low-opacity same-hue ghost layer |
| `generic-fonts` | Inter/Roboto/Arial/Open Sans/system fonts | Use the site's registered display/body families (§13) |

**Voice vs grammar (the load-bearing distinction).** One deliberately-named kicker, or one genuine numbered sequence where order is the point, is **voice** — keep it. The *same* device mechanically repeated on every section is **AI grammar** — ban it. The test is whether the device is load-bearing for *this* section's argument, or just scaffolding pasted everywhere.

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

### AI-slop microcopy tells (every interface string, not just headlines)

The slop test extends past marketing copy to every functional string a variant introduces. Each below is a named tell `impeccable` looks for in UX copy — name the action, state the fix, welcome the visitor:

- **Buttons / CTAs**: "OK / Submit / Yes / No / Click here" → name the action — "Create account", "Download PDF", "See pricing".
- **Errors**: "Invalid input" / "Something went wrong" → state the problem **and** the fix — "Enter a valid email, e.g. name@site.com".
- **Empty states**: "No items" / "Nothing here" → the next action plus a welcome — "No tests yet — start your first A/B test".
- **Loaders**: never the cliché whimsy loaders (`ai-loading-copy`): "Herding pixels", "Teaching robots to dance", "Consulting the magic 8-ball", "Counting backwards from infinity". A plain "Loading…" beats forced personality.
- **Redundancy**: a header that restates the intro, the same concept re-explained two ways. Say it once, well — redundant restating is a slop tell in itself.

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
3. Run the Block Runner pre-flight (`docs/block-runner.md`) for every generated or changed markup candidate. If it is unavailable, use the §2 required-class, class-order, and style-order checks as the disclosed fallback.
4. Pick the archetype that fits the argument (§10), then score the variant against the differentiation rubric (§4).
5. Check brand consistency — slug-first principle (§1); on the aphelion stack apply the aphelion binding (§13).
6. Check anti-pattern bans **and pre-clear the detector tells** (§3).
7. Check the polish thresholds — type scale, measure, spacing rhythm, color weight, contrast, motion (§12).
8. Scan copy for AI-slop markers, including microcopy tells (§5).
9. **For a round of >1 arm, run the per-round diversity gate** (§11) over the whole set before presenting any of them.
10. **Revise silently** if anything fails — the user only ever sees the passing version.

The marketer never sees a routine "quality check failed" message. They just see better variants with bolder hypotheses that match their site's visual language. The exception is the required disclosure when automated markup validation is unavailable or misconfigured; use the wording in `docs/block-runner.md` rather than pretending the headless check ran.

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

---

## 10. The archetype library — structurally distinct section kinds

§9 fields one incumbent + bold challengers; this is **what makes a challenger structurally bold** rather than a micro-variation. The single most common generation failure is fielding five arms that share a block skeleton and differ only in words — copy-only swaps that the differentiation rubric (§4) scores 0 on Visual/structural. The cure is to draw each arm from a **different archetype**: a different *kind* of section, not a restyle of the same one.

**Structure must FIT the argument.** Pick the archetype the *message* needs, never the most decorative one: a **process** → ordered sequence/timeline; **proof** → stat-band; **objections** → FAQ; **capabilities** → grid; **story** → editorial; **a single bold claim** → centered statement. The archetype encodes the argument's shape, so two archetypes that argue differently *read* differently even before the copy lands. The site's own brand pack (`docs/brand-pack.md`) is always the first source — prefer a real harvested fragment of the chosen archetype; author a fresh one only once the site's vocabulary of that kind is spent.

Per category, here are 5–6 **structurally distinct** archetypes (different block skeletons, not restyles). A round picks ≥4 distinct ones (§11):

### Hero
- **full-bleed-image-overlay** — `core/cover` with media + headline + CTA overlaid; image carries the mood. Copy over a photographic/gradient plate **requires a scrim/overlay or placement on a dark region** — never the theme's default gray body on a variable-luminance image (`gray-on-color`, §3/§12).
- **split-asymmetric-70-30** — `core/columns` 70/30 (or 30/70); copy stack on one side, single supporting visual on the other.
- **centered-statement-minimal** — one large `core/heading`, one line of body, one CTA; space does the work, no imagery.
- **stat-anchored** — headline paired with a **single integrated** proof stat (`core/group` headline + one hero figure inline), arguing from evidence. **Not** a serif statement bolted to a repeated 3–4 cell big-number rail (`stat-rail`, §3) — that's the SaaS cliché, scores template-grade on craft. If a hero must carry more than one readout, it is a *deliberate compositional element* (a framed panel, a 2-up, or an inline spec strip — **cap ~2–3 rows**), never an open-ended vertical label→value dump (reads as inventory, scores `monotonous-spacing`). Stat labels must clear 4.5:1 contrast; never a grid with a dead empty cell.
- **typographic-display-scale** — oversized display headline (extreme scale jump) as the whole composition; type *is* the hero.
- **product-in-context** — `core/media-text` showing the product/screenshot beside a benefit-led claim.

### Pricing
- **tiered-cards-comparison** — `core/columns` of 2–3 plan cards, one marked recommended (the *only* place identical-ish cards are earned — vary the highlighted tier).
- **single-plan-focus** — one plan, big price, benefit list, one CTA; no comparison clutter.
- **value-anchored-feature-table** — `core/table`/columns mapping features to tiers; argues on inclusion, not price.
- **toggle-framed** (monthly/annual) — pricing staged around a choice, savings made explicit.
- **outcome-led-no-table** — lead with what the visitor gets at each level; price stated plainly, table de-emphasized.
- **enterprise-contact-split** — self-serve tier(s) beside a "talk to us" panel for the high-touch path.

### Trust / social-proof
- **logo-wall** — `core/columns`/gallery of customer/partner marks; breadth as proof.
- **stat-band** — a row of 2–4 headline metrics (`core/columns`), each one number + short label; magnitude as proof.
- **named-quote-strip** — a single strong `core/quote` with attribution; depth over breadth.
- **rating-badges-row** — review scores / awards / certifications as a horizontal band.
- **case-study-teaser** — one customer result staged as a mini before/after with a link out.
- **press-mentions** — "as seen in" publication marks; third-party authority.

### Experience / capability
- **media-text-alternating** — `core/media-text` rows that alternate sides down the page; each pairs one capability with one visual.
- **horizontal-step-sequence** — `core/columns` of ordered steps (numbered *here* legitimately — order is the point).
- **vertical-timeline** — stacked sequence with progression cues; for a journey/process over time.
- **two-column-deep-dive** — one capability explained richly in a 50/50 split (copy + supporting visual), not a grid of many.
- **tabbed-or-sectioned-showcase** — distinct capability areas as separate full-width sections, each self-contained.
- **interactive-demo-callout** — a single capability framed around a live example/screenshot + CTA to try it.

### Testimonial
- **single-hero-quote** — one large `core/quote`, oversized, full attention; the strongest line.
- **three-up-quote-grid** — `core/columns` of three short quotes (vary length/emphasis — not identical cards).
- **quote-with-portrait** — `core/media-text`: portrait beside the quote and named attribution.
- **carousel-strip** (if registered) — a row of quotes the visitor scans.
- **video-testimonial-feature** — a single embedded testimonial as the centerpiece.
- **result-led-quote** — quote framed by the concrete outcome it produced (number + words together).

### FAQ
- **accordion-list** — collapsible Q&A (`core/details`); compact, scannable.
- **two-column-qa** — questions laid out as a 2-column grid for breadth at a glance.
- **objection-grouped** — questions clustered by objection theme (price / trust / fit), each cluster a section.
- **inline-prose-faq** — Q&A as flowing headed prose, not an accordion; editorial register.
- **search-or-categorized** — categorized FAQ with a lead-in for larger question sets.

### Final-banner / CTA
- **full-bleed-color-band** — `core/group` full-width on a **contrast** background (never a full-bleed *accent* ground — `accent-ground`, §3), one headline + one CTA.
- **split-image-cta** — `core/media-text`: closing visual beside the final ask.
- **centered-minimal-cta** — one line + one button on a quiet background; maximum focus.
- **email-capture-form** — a direct capture field + submit (highest conversion-affordance, TI-6). **The form is the conversion mechanism — it must be the best-crafted element, not the worst.** Style it with the site's tokens (field bg/border/radius slugs, `body` font, submit via the CTA button primitive); **never** a bare `wp:html` native `<input>`/`<button>` (`unstyled-form-control`, §3).
- **stacked-reassurance-cta** — CTA plus a short trust line (guarantee / "no card required") beneath.
- **two-path-cta** — primary action + a secondary path (`is-style-outline`) for the not-ready visitor.
- **stat-reinforced-cta** — the closing ask anchored by one last proof number.

### Features / capability-grid
- **icon-feature-grid** — `core/columns` of feature cards (vary spans/lengths — never identical-card-grid §3).
- **alternating-feature-rows** — `core/media-text` rows, one feature per row, sides alternating.
- **bento-mixed-spans** — a grid of deliberately *unequal* tiles (one large + several small) — breaks card monotony.
- **comparison-vs-grid** — features framed as us-vs-alternative columns.
- **categorized-feature-sections** — features grouped under themed sub-headings, each its own block.
- **single-flagship-feature** — one capability given a full section instead of a grid; depth over enumeration.

### Stats / metrics-band
- **horizontal-number-row** — `core/columns` of 3–4 big numbers + short labels.
- **single-hero-metric-in-context** — one dominant number framed with the sentence that gives it meaning (earns the number — not the SaaS `hero-metric` cliché).
- **comparison-stat-pair** — before/after or us/them as two contrasted figures.
- **annotated-stat-with-source** — a metric paired with its source/attribution for credibility.
- **progress-or-milestone-band** — cumulative figures ("X served to date") as a milestone strip.
- **stat-plus-supporting-quote** — one number reinforced by a one-line quote that humanizes it.

---

## 11. Per-round diversity gate (pre-flight)

Before a round ships — **after** drafting all arms, **before** presenting them or calling `create-ab-test` — assert structural diversity. This promotes the thunderdome `_run_validate.py` structural-diversity check *into* generation, so a copy-only round never gets fielded in the first place.

**The gate (a round of N≥3 arms, control excluded):**

1. Tag each arm with its archetype (§10) and its block skeleton — the ordered list of its top-level block types (e.g. `cover → columns → buttons`).
2. **Assert ≥4 distinct archetypes / skeletons across the arms** (for a 5-arm round). For smaller rounds, *every* challenger must use a different skeleton from the incumbent and from each other — no two arms may share a skeleton.
3. If two arms collapse to the same skeleton (same block types in the same order, differing only in copy/tokens), **the round fails the gate** — regenerate the duplicate from an unused archetype before shipping.

A round that passes the gate is structurally diverse by construction; a round that can't pass it is the copy-only failure §10 exists to prevent. Treat this gate as binding, the same way §2 (validity) and §4 (per-variant differentiation) are binding — it operates on the *set*, where they operate on each arm.

---

## 12. Polish thresholds (craft floor)

Differentiation (§4) makes a variant *bold*; these thresholds make it *crafted*. They are the committed numbers a composed variant must hit — reference values, applied via the site's preset slugs (§1), never hardcoded. (Where the site lacks a matching preset, this is direction for *which* registered slug to reach for, not a license to hardcode.)

- **Type scale**: one committed modular ratio — **1.25** (major third), **1.333** (fourth), or **1.5** (fifth). Don't mix ratios within a variant. **Body ≥16px.** Display copy gets a letter-spacing floor (≈ −0.04em on large headings).
- **Headline measure**: cap line length at **65–75ch**; body over 75ch is a slop tell. Lean on `text-wrap: balance` on h1–h3 where the site exposes it (and the display-break rules in §5).
- **Spacing — rhythm, not uniformity**: 4pt base (4/8/12/16/24/32/48/64/96). **Tight grouping (8–12px) for related elements, generous (48–96px) between sections.** Equal spacing everywhere is the `monotonous-spacing` tell. Prefer `gap`/spacing presets over ad-hoc margins.
- **Color — 60-30-10 weight**: ~60% neutral surface, 30% secondary, **10% accent reserved for the CTA / primary / current state**. Don't spread the accent across decoration, and **never use the accent as a full-bleed section ground** (`accent-ground`, §3) — it blows the 10% budget and reads off-brand. Body contrast **≥4.5:1**, large/UI text **≥3:1** — never gray-on-color (use a darker shade of the hue or an alpha), and **never same-hue low-opacity "ghost" text** as decoration (`ghost-text`, §3). Copy over a photographic/gradient plate needs a scrim/overlay or a dark region — not the default gray on variable luminance.
- **Motion**: 100–150ms feedback, 200–300ms state, 300–500ms layout; easing **ease-out** (quart/quint/expo). **Never bounce/elastic** (the `bounce-easing` tell). Every animation needs a `prefers-reduced-motion` path; cap a stagger at ~500ms total.
- **Light-on-dark surfaces** (e.g. dark-themed sites): bump line-height **+0.05–0.1** and optionally step the weight up one notch — light type on dark reads thinner.

---

## 13. Aphelion binding (when composing on the aphelion / dark-brand stack)

When the target site is the aphelion stack (the internal dark-theme brand), these constraints are **hard** and override any generic default above. They are the same slug-first / ground-every-attribute discipline (§1, §2), pinned to this brand's real tokens:

- **Palette — preset slugs only.** `base · base-2 · panel · contrast · contrast-2 · contrast-3 · contrast-4 · accent · blue · champagne · status`. **There is no `accent-3`** — it renders invisible; remap any such reference to `base-2`. Never hardcode hex/px — always the slug.
- **Fonts — three only**: `display` (Instrument Serif), `body` (Geist), `mono`. `{"fontFamily":"heading"}` is **invalid** on this site — use `display`.
- **Images — approved IDs only**: 724 (interior) · 725–730 (nebula) · 731–745 (obscure) · 746–747 (viewport). **Never NASA placeholder images** (IDs 371-class, all 404) and never invent attachment IDs — omit the image and let the block default rather than guess (§2).
- **Registered styles**: check-list `is-style-checkmark-list`; eyebrow `( parenthetical )`; plate `[ bracketed ]` — use the site's real style slugs, not invented classNames.
- **Light-on-dark**: this is a dark surface — apply the §12 light-on-dark rule (line-height bump, weight step).
- **Mirror the control's grammar to compose, not to copy.** Fetch the real block first (it's the control); learn its class/attribute shape, then compose your *new* archetype (§10) from the site's full registered palette — a wholly different composition of individually-valid blocks is wholly valid (§2).

---

## 14. Cross-round escalation — the axis ladder and elite crossover (the evolve climb)

§9 composes a *single* round; this governs how the **sequence** escalates when a round stops improving. It is the spine of `accelerate-evolve`. Validated on a 12-category, 8-round simulation: structural recomposition climbs for ~3–5 rounds then **plateaus**, and the only moves that broke a settled plateau were changes of **argument axis**, not new layouts.

### The axis ladder
A challenger can differ from the incumbent on more than structure. When new *structures* stop beating the incumbent, escalate the **lever**, in order — each is a fresh search basin, not a restyle of the last:

1. **Structure** — the §10 archetype. Exhaust the site's real structural vocabulary first.
2. **Message frame** — reframe the *argument*: magnitude→scarcity, feature→outcome, risk→risk-reversal, loss-aversion, identity, comparison-to-alternative.
3. **Conversion mechanism** — change the action itself: passive CTA → focused CTA → email-capture form (§10 CTA, TI-6).
4. **Imagery** — a different hero image / full-bleed treatment can move outcome on visual draw alone.

Recomposition explores one basin; an axis-change jumps basins. Report the escalation plainly: *"structure hasn't moved this in two rounds — next round changes the message frame, not the layout."*

### Elite crossover when the vocabulary is spent
§9 authors a new section once the site's vocabulary is exhausted. Author it by **crossing the winning traits of the round's top performers**, not by inventing unrelated novelty:

- **Select ≥2 parents** — the top cluster of arms (those within the gate's resolution of the leader). **Widen** the parent pool when scores bunch (no clear winner); **narrow** to the top 2 when one arm clearly leads.
- **Cross their winning traits** into the new section (the winning structure × a winning message frame × the winning image), never a re-skin of a single parent.
- **Anneal boldness up** each round the incumbent holds — modest recombination first, then bolder trait-fusions and structural leaps.
- *Validated:* breeding new sections from ≥2 elite parents beat injecting unrelated novelty — it broke a plateau the random approach could not.

### Promote winners into the brand pack
When a crossed-from-scratch section wins cleanly under the gate, fold it back into the site's vocabulary (the brand pack / pattern library) so future rounds compose from a richer set — extinction of the loser, speciation of the winner. **The vocabulary grows with every climb.**

### Convergence — when to stop
Evolution plateaus fast (typically by round 3–6 on a fixed offer/fact set). Stop after **K consecutive rounds with no gate-valid improvement** over the incumbent — not a fixed round count — and don't grind rounds that only re-stage settled arguments. When the axis ladder is exhausted and crossover has stopped clearing the gate, say plainly the block has plateaued, name the current best, and note that the remaining headroom is in the **offer/substrate** (new facts, proof, imagery), not in recomposition.

---

## 15. Rendering & editability — beyond per-block validity

§2 keeps each block valid *in isolation*. This keeps a whole **section or page** rendering correctly on **both** surfaces — the editor canvas *and* the front end — which are different and can disagree. A composition can pass §2 and still render wrong; verify both, at a wide viewport. Two of these rules are variant-markup choices; the rest are **theme-side** requirements — if you don't own the theme, author to them and **flag them** to whoever does. (Validated building a full aphelion landing page, 2026-06.)

### Prefer forgiving primitives (variant-side)
- Hand-authoring `wp:cover` reliably trips "invalid content / Attempt recovery": its `is-position-*` (content position), `has-background-dim-N`, and gradient-`<span>` markup are easy to mismatch. **Build the same look from forgiving primitives** — `wp:group` + `wp:image` + `wp:heading` + `wp:paragraph` + `wp:buttons` — and do the background image / scrim / overlay in **CSS keyed to classes**. (Cover is still a valid block per §2; it's just mismatch-prone to author by hand.)
- Fewer attributes = smaller mismatch surface: prefer a CSS class over per-block `textColor` / `fontFamily` / `fontSize` / `style` whenever a class can carry it.

### The editor must be able to see the CSS (theme-side)
When the design lives in CSS rather than block attributes, the editor canvas shows **bare structure** unless the theme loads that CSS into the editor with `add_editor_style()`. Front-end `wp_enqueue_style` (on `wp_enqueue_scripts`) does **not** reach the editor iframe. Without this, CSS-driven sections are un-WYSIWYG and effectively uneditable — flag it when handing a CSS-driven section to a theme you don't control.

### Full / wide alignment — all three, or it silently collapses (mixed)
A full-bleed band needs **every** one of these; miss one and the section quietly renders at `contentSize`:
1. **Inline real blocks, not `wp:pattern` references** — the editor strips child `align` when it expands a pattern ref. *(variant-side)*
2. **Mark the band `align:"full"`.** *(variant-side)*
3. **The content root must be a *constrained* layout** — *flow* layouts don't support child alignment, so Gutenberg drops it. In a page template: `wp:post-content {"layout":{"type":"constrained"}}` inside a **flow** `<main>`. Do **not** nest two constrained layers — `align:full` breaks out of post-content but stays trapped at the main's `contentSize` on the front end. *(theme-side)*

### Content width (theme-side)
- Full-bleed bands span the viewport, but their **inner** content is capped by `theme.json` `settings.layout.contentSize`. A 620–720px reading measure is far too narrow for multi-column marketing sections — they huddle in the centre with dead margins. **~1100–1280px is typical;** set it deliberately, not by inheritance.
- Cap the **title element's** measure, not a wrapper `<div>` — a `max-width` in `ch` on a small-font wrapper computes tiny (~the base font, not the heading). To make a child align to the content column exactly, use `max-width: var(--wp--style--global--content-size)`, never a hardcoded narrower value.

### Full-bleed images (variant-side)
- A `wp:image` `<figure>` inherits the content-width cap **even when absolutely positioned** — force `width:100% !important; max-width:none !important` to fill a full-bleed container.
- Images may be `loading="lazy"` (won't paint until scrolled into view) and carry an auto-generated `srcset`; confirm the resized variant URLs actually resolve before treating a blank image as "broken."

### First-column parity — the block-gap leak (mixed)
The classic symptom: in a multi-column row (stat band, card pair, timeline, feature grid) **column 1 sits at a different height / offset** than cols 2..n. Two causes, both about the first child being special-cased:
- **WordPress block-gap leak (most common).** WP implements block spacing as `margin-block-start` on every child **except the first** (`> :where(:not(:first-child)) { margin-block-start: var(--wp--style--block-gap) }`). When a container is `is-layout-flow`/constrained but you restyle it as CSS **grid or flex**, those sibling top-margins leak onto the items and push cols 2..n down — leaving col 1 high (a ~19px offset on default gap). **Fix:** declare the container `"layout":{"type":"flex"}` (or `grid`) in the block JSON so WP stops emitting flow margins, **or** zero it in CSS on the children — `.row > * { margin-block-start: 0 }` — and use a real `gap`.
- **Asymmetric dividers / padding.** `border-left` + `padding-left` per cell with only `:first-child{ border-left:0 }` leaves col 1 padded-but-divider-less, so its content doesn't line up with the content column. Keep per-cell padding symmetric and **zero the first cell's leading padding** so col 1 sits flush with the column edge (dividers then separate cols 2..n).

Verify by measuring, not eyeballing: every column's content should share one left edge and one top baseline.
