---
name: accelerate-design
description: Design a new on-brand version of a block or a fresh section — "make me a variant of the hero", "design a new pricing section", "compose an on-brand version", "give me a bolder hero". Produces ready-to-use content; offers to put it in a test but never forces one. NOT for running or tracking an A/B test (use accelerate-test) or a multi-round optimization loop (use accelerate-evolve).
license: MIT
category: design
parent: accelerate
---

# Accelerate — Design an on-brand variant or section

You author a brand-fitting version of a block, or a brand-new section, on demand. This is **test-optional**: you produce the content and *offer* to set up an A/B test, but creating a test is a separate, confirmed step.

**Route elsewhere when:** the user wants to set up / monitor / end one A/B test → `accelerate-test`. The user wants to improve a block over multiple rounds, automatically → `accelerate-evolve`. This skill is the single-shot "make me a version" primitive both of those build on.

## Flow

1. **Load the brand pack.** Follow `docs/brand-pack.md` — the *whole-site* grammar (global styles + all synced patterns + representative pages + media), not one page. Reuse the cached pack if it's fresh.
2. **Take the brief.** Which block or section, and what the user wants it to do (or "a new <kind> section"). If targeting an existing block, read its current content first: `accelerate/get-variants` if it already has variants; otherwise WP-CLI (`wp post get <id> --field=content`) or ask the user to paste it. Do not reconstruct it from memory.
3. **Compose from the site's own vocabulary.** Recombine and extend the brand pack's structures — don't re-skin the control. Aim for a composed redesign (Visual Score 2); reach for a ground-up reimagining (Visual Score 3) on a bold ask. Build it as a block tree, then serialize. Reference design tokens by preset slug only; reuse real media from the site; never invent facts, numbers, or attachment IDs.
4. **Validate silently against `docs/design-standards.md`** — slug-first (§1), markup validity and round-trip (§2), anti-pattern bans (§3), differentiation rubric ≥3/7 with no zeros (§4), no AI-slop copy (§5). Rework anything that fails before showing it. The user only ever sees the passing version.
5. **Present it, then offer the test.** Show what it is, the *concept* it argues, and the real fact it's grounded in. Then offer the next step — set it up as an A/B test (hand to `accelerate-test`), or just hand back the content to use as-is. Never create a test without explicit confirmation.

## Presenting

Lead with the concept, not the markup. Example:

> **Here's a bolder take on your hero — an outcome-led version.**
>
> Your current hero leads with what the product *is*. 62% of these visitors arrive from searches about slow sites, so this version argues the outcome instead — *"Fix your slow site in one afternoon"* — staged as a full-bleed section with one high-contrast call-to-action, using your own heading font and brand colours. *(Grounded in: 62% of hero traffic arrives from speed-related searches.)*
>
> Want me to set this up as an A/B test against your current hero, or just hand you the content to drop in?

Show the variant's copy in the presentation. Keep the structure description in plain English — never paste raw block markup at the user or name a capability.

## Rules

- **Whole-site grammar, never one page.** Always load the brand pack (`docs/brand-pack.md`) before composing.
- **Compose, don't re-skin.** Recombine the site's own sections; a real version is a different experience, not the control with new words. Apply the bold-by-default doctrine in `docs/design-standards.md` §9.
- **Slug-first, real media, no invented facts.** Every token is a preset slug; every image already exists on the site; placeholder copy where you'd otherwise guess a number.
- **Test-optional.** Produce and offer. Never call create-ab-test (a mutation) without explicit confirmation — hand to `accelerate-test` once the user opts in.
- **No AI-slop copy** (`design-standards.md` §5) and no developer jargon in anything the user reads.
