# The brand pack — whole-site design ingest

This document defines how a variant-producing skill learns a site's **full** design grammar before composing anything. It is never shown to the user. `accelerate-design`, `accelerate-evolve`, and `accelerate-test` all load the brand pack first.

**The one rule that matters here: never infer a site's grammar from a single page.** A brand is its global styles *plus* the way it composes sections across the whole site. Reading one page (or one block) yields a shallow grammar, and shallow grammar produces generic variants. The ingest below reads four layers; an ingest that skipped patterns or pages is **insufficient** and must be flagged, not used as if complete.

---

## The four layers

### 1. Global style (theme.json)
Call `accelerate/get-site-context` with `blocks: "styled"` (fall back to `include_blocks: true` on older plugin versions). Capture: the color **palette**, **font sizes**, **font families**, **spacing** scale, the **registered blocks** and their **style variations**, and the global style presets. These are the slugs every composition must reference (slug-first — see `docs/design-standards.md` §1). The human-readable prose form is the existing `brand.md` (template in `design-standards.md` §6).

### 2. Structure vocabulary (all synced patterns)
`get-site-context` lists the site's synced patterns. Read **every** one (or a representative spread only if there are very many) via `accelerate/get-variants` → `raw_markup` + `inner_block_types`. For each, note the **kind** of section (hero, pricing, CTA, testimonial, feature grid, …), which block types it pairs, and the structural shape it favours. This is the site's compositional vocabulary — the building blocks a bold variant recombines and extends, rather than re-skinning one block.

### 3. Representative pages (across types)
Patterns alone miss how *real pages* assemble sections. Auto-select a spread:
- **Top-traffic pages** via `accelerate/get-top-content`.
- **One per template / post-type** via `accelerate/search-content` (home, a landing page, a post, a key conversion page).

Read each one's section structure. This is the layer that stops the grammar collapsing to a single page. Pick by coverage, not convenience.

### 4. Media (real assets)
Index the image URLs/IDs that already appear in the pattern and page markup. On-brand imagery almost always already exists on the site — compositions reuse these real assets. **Never hotlink external images** and never invent attachment IDs (`design-standards.md` §2).

---

## Cache

Write a machine-readable superset to `~/.config/accelerate-ai-toolkit/sites/<key>/brandpack.json` (site key from the canonical rule in `accelerate-learn`; atomic temp-then-rename, `chmod 600` — same posture as the journal). Keep the human `brand.md` (style/voice prose) alongside it. **Reuse the cache first**; refresh only when it is older than 7 days or the user asks. Shape:

```json
{
  "schema_version": 1,
  "site": { "key": "<site key>", "name": "...", "theme": "...", "url": "..." },
  "generated": "<ISO 8601 UTC>",
  "global": {
    "palette": [ { "slug": "primary", "hex": "#…", "name": "Primary" } ],
    "font_sizes": [ { "slug": "large", "size": "1.75rem" } ],
    "font_families": [ { "slug": "heading", "name": "…" } ],
    "spacing": [ { "slug": "50", "size": "1.5rem" } ],
    "blocks": [ { "type": "core/button", "styles": ["fill", "outline"] } ]
  },
  "patterns": [
    { "id": 0, "title": "Hero", "kind": "hero", "inner_block_types": ["core/cover", "core/heading", "core/buttons"], "summary": "full-bleed cover + headline + single CTA" }
  ],
  "pages": [
    { "id": 0, "type": "page", "template": "front-page", "section_shape": "hero → logos → feature grid → CTA banner" }
  ],
  "media": [
    { "url": "https://…/hero.webp", "id": 0, "alt": "…", "source": "pattern:Hero" }
  ]
}
```

---

## Sufficiency

Treat the ingest as complete only when it covered **global styles + the pattern library + ≥1 representative page per type + the media index**. If a layer is genuinely empty (a site with no synced patterns, thin content), proceed with what exists but **flag the reduced grammar** in your reasoning — do not fabricate a structure the site doesn't have, and do not silently treat a one-page read as the whole brand.

Confirm exact ability names against `docs/ability-reference.md` and `../altis-accelerate/inc/abilities/*.php` before relying on any of them.
