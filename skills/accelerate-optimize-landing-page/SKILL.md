---
name: accelerate-optimize-landing-page
description: Use when the user wants to optimise a landing page, improve a landing page, make a landing page convert better, or asks "what should I do about my landing page". Keywords include optimise, optimize, improve, landing page, entry page, homepage, convert better, conversion rate, first impression.
license: MIT
category: optimization
parent: accelerate
---

# Accelerate — Optimise a landing page

You are helping a marketer improve a specific landing page. The goal is to produce 2–3 prioritised, testable recommendations grounded in that page's actual data.

## Understand which page

If the user names a page, use `accelerate/search-content` to find it.

If they don't name one, call `accelerate/get-landing-pages` first. Show them the top 5 landing pages with entries, bounce rate, and conversion rate, and ask which one they want to work on. (Or pick the one with the best effort-to-impact ratio — high entries, high bounce, low conversion — and say "I'd suggest starting with X; shall we?")

## What to fetch once you know the page

In parallel:

1. `accelerate/get-post-performance` with the `post_id` — baseline numbers.
2. `accelerate/get-engagement-metrics` with `entity_type: "post"` and the `post_id` — bounce rate, time on page, scroll depth.
3. `accelerate/get-traffic-breakdown` with `dimension: "referrer"` — where visitors come from.
4. `accelerate/get-source-breakdown` with `group_by: "medium"` — organic vs paid vs social breakdown.
5. `accelerate/get-audience-fields` — so you know what targeting signals are available if you end up suggesting personalisation.

Optionally, if the user wants to understand intent: `accelerate/get-utm-performance` with `group_by: "campaign"` if the page receives paid traffic.

## How to think about the result

Apply the patterns from the `accelerate` router's audience signal priority (referrer > geo > behaviour > device) and traffic-level awareness (big changes for low traffic, small tests for high traffic).

Look at each layer of the page:

1. **Above the fold** — does the headline match what the visitor was searching for / what the link that brought them here promised? This is the single biggest lever on bounce rate.
2. **Value proposition** — is there a clear "what this is and why you should care" within 5 seconds of reading?
3. **Primary CTA** — is it visible without scrolling? Is the copy action-oriented? Does it match the page's success metric?
4. **Social proof** — if the page asks for commitment (signup, purchase, form fill), is there a testimonial, logo wall, or review near the CTA?
5. **Scroll depth** — if scroll p100 is high but bounce is also high, the content is being consumed but not converting. The problem is the CTA, not the content.

## How to present it

```
## Optimising [Page Title]

The page gets **X entries a week**, with **Y% of visitors bouncing** and **Z% converting**. Most traffic comes from [top source].

Here's what I'd try, in order of impact:

### 🔴 HIGH — Align the headline to search intent

**What:** Rewrite the hero headline to match "...".
**Where:** Hero section, first line of copy.
**Why:** 52% of visitors land here from Google, searching for "...". The current headline says "...", which doesn't promise that. They bounce.
**How to measure:** bounce rate on this page, targeting ~60%.
**Confidence:** high. This is the textbook fix when traffic is Google-heavy.

### 🟡 MEDIUM — Move the CTA above the fold

**What:** Put the "Start free trial" button inside the hero, not after the features section.
**Where:** Hero section, under the headline.
**Why:** scroll p50 is only 40%, meaning half your visitors never scroll past the top. They never see the CTA at all.
**How to measure:** click-through on the CTA button.

### 🟢 LOW — Add a testimonial near the CTA

**What:** Add one short customer quote right above the button.
**Where:** Hero CTA area.
**Why:** this is a pricing page and there's no social proof visible before the button.
**How to measure:** click-through on the CTA button.
```

## Offer to run it as an A/B test

After presenting the recommendations, ask:

> "Want me to set up an A/B test for the first one? I can create a new version with a rewritten headline, split traffic 50/50, and we can check back in a week or two to see which one wins."

**Before offering a test, check whether the target section is a reusable block.** If the recommendation targets inline page content (not a `wp_block` synced pattern), say so upfront: *"To test this, the section would need to be converted into a reusable block first — this keeps the test contained so nothing else on the page changes. You can do this in the editor: select the content, click the three-dot menu, choose 'Create pattern'."* Do not offer to create the test until the block exists.

If they say yes and the target is a reusable block, hand off to `accelerate-test` with the specific recommendation as the hypothesis. Do NOT call `create-ab-test` without confirming the exact variant text with the user first. The `accelerate-test` skill handles backup, creation, and verification — follow its full Creating flow.

When constructing the recommendation as a potential variant, apply the design standards from `docs/design-standards.md`. The recommendation must be bold enough to pass the differentiation rubric — a specific new angle grounded in the fetched data, not a minor rewording. Variant block markup must use preset slugs for all design tokens (colors, font sizes, spacing), never hardcoded values. Check the proposed copy against the AI-slop word list before presenting.

## Rules

- 2–3 recommendations maximum. Never 5, never 10.
- Always grounded in real fetched numbers. If you didn't fetch it, don't claim it.
- If the page has under ~100 entries in the window you fetched, tell the user it's hard to recommend confidently on small data and offer to use a longer window.
- Don't suggest changes to page speed, SEO meta tags, or infrastructure — those aren't things Accelerate can test.
- If the engagement metrics are great and bounce is low, say so: *"This page is already healthy — I don't see an obvious win here. Want me to look at a different page?"*
