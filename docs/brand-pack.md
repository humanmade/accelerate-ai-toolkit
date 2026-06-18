# The brand pack — whole-site design ingest

This document defines how a variant-producing skill learns a site's **full** design grammar before composing anything. It is never shown to the user. `accelerate-design`, `accelerate-evolve`, and `accelerate-test` all load the brand pack first.

**The three rules that matter here:**

1. **Never infer a site's grammar from a single page.** A brand is its global styles *plus* the way it composes sections across the whole site. Reading one page (or one block) yields a shallow grammar, and shallow grammar produces generic variants.
2. **For *structure*, real in-use markup is the source of truth — not summaries, and not whatever happens to be registered.** A one-line description of a section ("full-bleed cover + headline + CTA") cannot be recomposed; only its real block markup can. A synced pattern or theme pattern that appears on **no live page** is suspect — legacy, demo leftover, or deprecated — not authoritative brand grammar. **For structure: what's published and used is the source of truth; the registry is a list of candidates.**
3. **For *tokens*, the theme is the source of truth — validate, don't copy blindly.** The palette / typography / spacing from `get-site-context` (theme.json) is the authority for which slugs are *valid*. A slug that appears in live markup but is **absent from that palette is a red flag** — very likely a legacy or broken token that renders invisibly (a silent drop), not a slug to reuse. Remap it to the nearest valid palette slug; never propagate an unlisted slug into a variant. (Structure → trust live usage. Tokens → trust the theme.)

The ingest below builds a **usage-grounded structure library**: real, in-use section fragments (with their semantic classes and preset slugs intact), harvested primarily from published pages and *confirmed* against registered patterns. An ingest that captured only summaries, or only synced patterns, is **insufficient** and must be flagged — not used as if complete.

---

## The layers

### 1. Global style (theme.json)
Call `accelerate/get-site-context` with `blocks: "styled"` (fall back to `include_blocks: true` on older plugin versions). Capture: the color **palette**, **font sizes**, **font families**, **spacing** scale, the **registered blocks** and their **style variations**, and the global style presets. These are the slugs every composition must reference (slug-first — see `docs/design-standards.md` §1), **and this palette is the authority for which slugs are valid** (rule 3): if harvested markup uses a slug not listed here, treat it as suspect and remap, don't reuse it. For CSS properties the theme exposes **no preset for** (e.g. a one-off `letter-spacing` or `border-radius` that has no slug scale), copying the site's own real value from a harvested fragment is acceptable and on-brand — slug-first applies to properties that *have* a preset, not to every value. The human-readable prose form is the existing `brand.md` (template in `design-standards.md` §6).

### 2. Structure library — usage-grounded, page-harvest first
The site's compositional vocabulary is the set of **real section fragments it actually uses**. Build it from the widest live surface, in this order of trust:

**2a. Harvest published pages (primary).** Select a broad spread of real pages — **top-traffic** via `accelerate/get-top-content`, **landing pages** via `accelerate/get-landing-pages`, and **one per template / post-type** via `accelerate/search-content` (home, a landing page, a post, a key conversion page). For each, read the **raw block markup** via `accelerate/get-content` (by `id` or `url` — works on any post or page, not just synced blocks). **Resolve synced-pattern references:** a page built from synced patterns stores only references (`<!-- wp:block {"ref":N} /-->`), not inline markup — for each, fetch post `N` via `get-content` to recover the real section markup (this is also what proves those sections are live). Decompose each page into its **section-level fragments**: the real block subtrees, preserving whatever semantic classes and preset-slug tokens the theme uses, verbatim — judge a fragment by its **structure** (the composition it expresses), never by a particular class prefix. Note each fragment's **kind** (hero, pricing, CTA, testimonial, feature grid, sequence, stat band, FAQ, …), the block types it pairs, and **which pages it appears on** (its usage). Pick pages by coverage and traffic, not convenience — this is both the widest source of grammar *and* the evidence of what is genuinely live.

**2b. Confirm against registered patterns (candidates only).** `get-site-context` lists the site's synced patterns (`wp_block` posts); read each via `accelerate/get-variants` → `raw_markup` + `inner_block_types`. Treat these as **candidate** vocabulary, **confirmed by page usage from 2a**:
- **Exclude A/B-test / personalization blocks** (these are experiment artifacts, not brand grammar — match the same `wp_block` posts the experiment tooling created, never the canonical sections).
- **Nested experiment arms:** a canonical synced pattern may itself contain inline variant arms (`wp:altis/variant`). Treat the **control / first arm as the canonical fragment** and ignore the other arms — they are experiment state, not separate vocabulary.
- **A pattern that appears on no harvested page is flagged, not fed to the composer** — keep it as a low-confidence candidate, never as authoritative grammar.
- Theme-registered patterns (PHP `register_block_pattern`) are not directly readable via an ability; they enter the library only where a real page instantiates them (2a) — which is exactly the usage filter we want.

The result is a library of real fragments, each tagged with kind + usage + confidence. This is what a bold variant **recombines and extends** — never a re-skin of one control block, never a paraphrase of a summary.

### 3. Media (real assets)
Index the image URLs/IDs that already appear in the harvested fragments and pages (`accelerate/get-media` lists the library; the fragments show what's actually placed). On-brand imagery almost always already exists on the site — compositions reuse these real assets. **Never hotlink external images** and never invent attachment IDs (`design-standards.md` §2).

---

## Cache

Write a machine-readable superset to `~/.config/accelerate-ai-toolkit/sites/<key>/brandpack.json` (site key from the canonical rule in `accelerate-learn`; atomic temp-then-rename, `chmod 600` — same posture as the journal). Keep the human `brand.md` (style/voice prose) alongside it. **Reuse the cache first if it exists**; refresh when it is older than 7 days or the user asks. **If no cache exists (no writer is wired up yet), ingest fresh from the layers above — do not block on a missing cache**; the cache is an optimisation, not a prerequisite. Shape:

```json
{
  "schema_version": 2,
  "site": { "key": "<site key>", "name": "...", "theme": "...", "url": "..." },
  "generated": "<ISO 8601 UTC>",
  "global": {
    "palette": [ { "slug": "primary", "hex": "#…", "name": "Primary" } ],
    "font_sizes": [ { "slug": "large", "size": "1.75rem" } ],
    "font_families": [ { "slug": "heading", "name": "…" } ],
    "spacing": [ { "slug": "50", "size": "1.5rem" } ],
    "blocks": [ { "type": "core/button", "styles": ["fill", "outline"] } ]
  },
  "fragments": [
    {
      "id": "hero-1",
      "kind": "hero",
      "source": "page:12",
      "seen_on_pages": [12, 40],
      "usage_count": 2,
      "confidence": "high",
      "inner_block_types": ["core/cover", "core/heading", "core/buttons"],
      "preset_slugs": ["base", "accent", "display", "60"],
      "markup_skeleton": "<!-- wp:cover {…} --> … the real block markup, with the theme's own classes + preset-slug tokens … <!-- /wp:cover -->"
    }
  ],
  "pages": [
    { "id": 12, "type": "page", "template": "front-page", "section_kinds": ["hero", "stat-band", "faq", "cta"] }
  ],
  "media": [
    { "url": "https://…/hero.webp", "id": 0, "alt": "…", "source": "fragment:hero-1" }
  ]
}
```

`fragments[]` is the load-bearing addition: each carries the **real `markup_skeleton`** (not a summary), its **preset slugs**, and its **usage/confidence**. The composer recombines these. `confidence` is `high` when a fragment is used on ≥1 real page, `low` when it is a registered-but-unused candidate.

---

## Sufficiency

Treat the ingest as complete only when it covered **global styles + a usage-grounded structure library (≥1 real page per template, fragments extracted with real markup) + the media index**.

- **Escalate, don't degrade.** If the usage-confirmed surface is thin (few fragments, little coverage), **harvest more pages / widen the sweep** before composing — do not silently fall back to paraphrased summaries or to a one-page read.
- **Cold-start fallback.** A brand-new site with little published content has little usage to confirm against. There, fall back to registered patterns but mark the whole vocabulary **low-confidence** in your reasoning — never assert that an unused pattern is the live grammar, and never fabricate a structure the site doesn't have.

Confirm exact ability names against `docs/ability-reference.md` and `../altis-accelerate/inc/abilities/*.php` before relying on any of them.
