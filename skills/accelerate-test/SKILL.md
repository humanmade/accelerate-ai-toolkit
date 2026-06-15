---
name: accelerate-test
description: A/B test lifecycle — plan, create, monitor, review, or end a test. What should I test? Set up a split test. How is my test doing? Is there a winner? Stop or declare a winner. NOT for composing a single on-brand variant without a test (use accelerate-design) or running a multi-round optimization loop (use accelerate-evolve).
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

**The core idea: test concepts, not levers.** A variant is not a tweak to one element — it is a *strategic concept*: a coherent, differently-framed answer to "why should this visitor act?" One arm might argue from the outcome the visitor gets (pain relieved, job done); another from social proof (other people like them already chose this); another from scarcity or a deadline; another from trust and safety (no risk, easy to reverse). Each concept is executed with full visual craft — imagery, color pairing, typography, and CTA treatment all chosen to serve *that* argument, not decoration bolted on afterward.

Why this matters: industry corpus studies show most A/B tests produce no measurable lift, and the few that win are driven by big strategic differences, not element styling. The highest-leverage axis is almost always *motivation and value proposition* — what the visitor is promised and why they should care — not how a button looks. The single most reliable move is reframing a feature into an outcome: not "what this is," but "what you get and the problem it ends." Incremental wording changes are statistically invisible; you cannot detect what a visitor can't perceive.

**The progression ladder.** On a *fresh* block with no test history, round 1 fields radically different concepts — each arm a distinct strategic frame, not a variation on one theme. Only *after* a concept wins do later rounds refine within it: round 2 tightens the winning concept (clustered levers), round 3 isolates single factors inside it. Don't refine a concept you haven't yet established. Don't open with timid variations on a fresh block.

**The escalation ladder (what to do after an *inconclusive* round).** A win triggers the convergence ladder above; an inconclusive round triggers the opposite move — *escalate*, don't repeat. With a binding stopping gate, most rounds will come back inconclusive, and the failure mode to avoid is re-fielding the same *class* of lever round after round and plateauing. Lever classes ascend in structural ambition:

1. **Copy / frame** — headline, body, CTA language. The lightest touch.
2. **Composition** — a redesigned section: layout, imagery, color + typography presets, the order and grouping of elements. The bold-challenger default.
3. **Architecture / goal** — a structurally different section (e.g. single-column inquiry vs. two-column cards), *or* a change to the conversion metric itself toward a deeper-funnel signal when the current goal is saturated.

When a round concludes inconclusive (no concept cleared the gate), the next iteration must climb at least one rung — never re-litigate the same class with reworded copy. **Two consecutive inconclusive rounds at one class means the metric is inelastic to that class on this block; escalate.** Two inconclusive copy rounds → move to composition. Two inconclusive composition rounds → move to architecture/goal. Surface the escalation to the user in one line ("copy framing hasn't moved this block in two rounds — next round redesigns the section's structure"). This is how a multi-iteration sequence on one block keeps gaining rather than spinning at the same tier.

**Architecture changes are not universally good — respect the block's *function*.** Before escalating to the architecture rung, ask what job the block does. A bold reimagining (a stat-anchor hero, a stripped minimal frame) reliably lifts **inspiration / registration** blocks — a hero, a waitlist, a closing banner — where the goal is to raise desire or prompt one action. But the same move can *hurt* a **comparison / decision** block — a pricing-tier section, a feature matrix — where the structure the visitor came to use *is* the comparison. Stripping a two-column tier layout down to a single anchor removes the information the visitor needs to choose; it does not reduce friction. For comparison blocks, reimagine *within* the comparison (reorder tiers, re-weight emphasis, change which option leads), and reach for the metric/goal half of this rung rather than the structural half. Match the architecture move to the block's job, not to what won on a different kind of block.

**The goal-switch guard (binds on the architecture/goal rung).** When an architecture/goal escalation changes the conversion *metric* itself (e.g. `engagement` → `click_any_link`, or click → a deeper-funnel signal), the new metric has no established baseline — the old rounds measured something else. Before claiming any lift on the new metric, re-establish the baseline on it: the first post-switch round's control *is* the new baseline, not a comparison against pre-switch numbers. Treat pre-switch and post-switch rounds as separate series. A metric change must never be reported as a content-driven lift — the numbers moved because you changed what you were counting, not because the variant won.

0. **Consult the learning journal first.** Derive the site key from `get-site-context` using the site key derivation rule in `accelerate-learn`. Read `~/.config/accelerate-ai-toolkit/sites/<key>/journal.json` if it exists. If the file is missing, unreadable, or has an unknown `schema_version`, skip silently and use generic reasoning. If it's valid: bias toward patterns with `status: "won"` when proposing concepts. Demote patterns with `status: "lost"` -- still surface them if the user specifically asks or they're the only viable option, but flag the history: *"This concept has lost [N] of [M] tests on your site, so I'm not leading with it -- but it might work in this specific context."* Ignore `inconclusive` and `mixed` patterns -- not enough signal to bias on. Read each pattern's `compositions_tried` and `notes` so this pass builds on the last — don't re-field a structural recombination that already settled; extend or recombine differently instead. Also read `iteration_counter` from the journal: the next test's number is `iteration_counter + 1`, used to name the test `"#<n> <Block>"` (see the naming convention in Creating). This number also indexes the x-axis of the auto-research progress chart, so it stays stable and global across rounds and blocks. If there's no journal, fall back to the count from `list-experiments` + 1.
1. Call `accelerate/list-active-experiments` — don't propose a new test on a block that already has one running.
2. If the user hasn't named a target, use the findings from `accelerate-review`, `accelerate-diagnose`, or `accelerate-opportunities` to suggest the block with the best impact potential. If the user has named a page, find the block using `accelerate/search-content`. **Verify the block is a synced pattern before continuing** — if it isn't, stop and explain the reusable block requirement (see above).
3. **Gather the evidence each concept will stand on** via `accelerate/get-performance-summary` (`date_range_preset: "7d"`, or `"30d"` for a slower-burn test) and the audience/behavior tools (`get-traffic-breakdown`, `get-engagement-metrics`, `get-audience-fields`). You need two things from this step: (a) the traffic and conversion volume, to gauge whether a test can resolve at all (see step 5); and (b) the raw material for concepts — who is arriving (referrer/device/geo), how they behave on the page, and the language the site already uses to describe itself (headings, body copy, testimonials). Concepts are mined from this, not invented. This is the **STYLE** layer of grounding: the site's colors, typography, and voice.
3b. **Learn the site's STRUCTURE — its compositional vocabulary, not just its style.** Style grounding (step 3) tells you what the site *sounds and looks* like; this step tells you how it *builds sections*. Without it, every variant is a re-skin of the one target block. The full whole-site ingest — global styles + **all** synced patterns + representative pages across types + media — is specified in `docs/brand-pack.md`; use it as the canonical loader and never infer the grammar from a single page. Survey the site's existing synced patterns as a compositional palette:

   - **Reuse the cache first.** If `~/.config/accelerate-ai-toolkit/sites/<key>/palette.json` exists, load it instead of re-scanning. Refresh it only if it's clearly stale or the user asks.
   - **Otherwise survey, then cache.** `accelerate/get-site-context` lists the site's synced patterns (id + title). For each (or a representative sample if there are many), call `accelerate/get-variants` to read its `raw_markup` and `inner_block_types`. Note how the site composes each kind of section — hero, pricing, CTA, testimonial, feature grid — which block types it pairs, and the structural shape it favours. Write the surveyed palette to `palette.json` (atomic write, `chmod 600`, same as the journal) so later passes reuse it.
   - **Compose variants by recombining and extending this real vocabulary**, not by restyling the target block. A concept can be structurally *very different* from the control — a different arrangement of sections drawn from the site's own palette — yet remain unmistakably the same site, anchored to its design DNA. This is what lets a variant escape the single-block ceiling: you are recombining the site's proven building blocks, then extending them, rather than decorating one block.

   Together steps 3 and 3b are the full grounding: STYLE (how it looks and speaks) plus STRUCTURE (how it composes). Concepts in step 4 draw on both.
4. **Frame 2–4 distinct concepts** (how many depends on conversion volume — see step 5). Each concept names: the block, the strategic frame it argues (the motivation it appeals to), the change that expresses it, the expected outcome, and the success metric. **The evidence gate (mandatory):** every concept must cite its grounding before it can run — which audience fact, which on-page behavior, or which piece of the site's own language it answers. A concept that cannot name its evidence does not get proposed. This supersedes intuition-led ideation: "this feels fresher" is not a reason; "62% arrive from a pricing search and the hero never mentions price" is. **Classify each concept against the pattern taxonomy** in `accelerate-learn` to determine its `pattern_id` -- you'll need this when creating the test.
5. **Apply the detectability (MDE) gate — before you commit to a test.** A test that can't resolve is wasted calendar time. Check the fetched volume against these floors:

   - **Per-arm minimums:** no conclusion is trustworthy until each arm has reached **~25 conversions AND ~800+ visitors**. Below that, the numbers lie.
   - **Multi-arm threshold:** only run more than 2 arms if the site is generating roughly **500+ conversion events per month**. More arms split the conversion stream further, so they need proportionally more of it.
   - **Plausible-lift check:** estimate the lift each concept could realistically produce. If a concept's plausible lift is so small it could never clear detection at this traffic level within a reasonable window, it has two fates: make it **bolder** (a stronger strategic frame, a more composed execution) or **don't run it**. A timid concept on thin traffic is a test that never concludes.

   **How many arms.** Arms scale with *conversion volume*, not page views:

   - **Ample conversion volume (≥500 events/month):** prefer **ONE experiment with 3–5 distinct concept arms** over a chain of sequential 2-arm tests. Each sequential test re-pays burn-in and calendar time; one many-armed test amortizes both and searches the concept space in parallel. State the honest constraint: more arms need proportionally more conversions to resolve.
   - **Low conversion volume:** stay at **2 arms** (control + one bold concept). Under-differentiated arms split thin traffic and starve each other of statistical power. Fewer, bolder arms is almost always the right call.

6. **Execute each concept with full visual craft, then check it against `docs/design-standards.md`.** A concept is an *argument staged as an experience* — the imagery, the color pairing, the typography, and the CTA treatment should all serve the frame, not sit on top of it. Score each variant against the differentiation rubric (Message 0–2 + Visual/structural 0–3 + Hypothesis clarity 0–2). Message Score 2 requires a genuinely different strategic frame (a different motivation appealed to), not the same frame reworded. Visual Score 2 is a composed redesign (three or more structural levers staging the concept); **Visual Score 3 is a ground-up *reimagining*** — the section rebuilt from the site's full registered block palette into a different *kind* of section, still unmistakably this site. If the total is below 3/7 or any dimension scores 0, strengthen it. Do not present a variant that fails the rubric. For low-traffic sites (under ~1,000 weekly visitors), only propose Score 2+ variants.

   **Compose from the full palette — don't re-skin the control.** Every block type in the site's registered `blocks` list is available (`core/columns`, `core/group`, `core/cover`, `core/media-text`, `core/buttons`, …), and you may replace the section's structure wholesale. The single biggest cause of timid variants is treating the control's structure as a fixed skeleton and only changing copy/colors on it. Don't. The boldest rounds (a plateaued block, lots of headroom, low traffic, or the architecture rung of the escalation ladder) should reach for Visual Score 3 — recompose, don't re-skin. See the escalation ladder in Planning for *when* to swing big vs. refine.

   **Author the variant as a block tree, then serialize it.** Design the composition first as a structure — which blocks, nested how, with which grounded attributes — then write the markup from that tree. Fill only attributes you can ground (preset slugs, copy you're writing, real media from the site's library/patterns); omit anything you'd be guessing and let the block default. This is how bold composition stays valid; §2 of `design-standards.md` is the safety contract. The recombination engine is the site's own pattern vocabulary surveyed in step 3b — transplant and recombine whole sections, don't invent generic ones.

   Structural levers to stage a concept with, roughly strongest-signal first:
   - Add a `core/button` block with a clear CTA where the control has none
   - Add or swap a `core/image` block (with descriptive alt text — not empty or generic). Source images from the site's own media library — existing block markup reveals attachment URLs you can reuse, and on-brand imagery usually already exists; never hotlink external images
   - Apply a theme `backgroundColor` preset slug on a wrapping group paired with an explicit `textColor` preset (changes the visual weight of the section; never apply a background without setting a contrasting text color)
   - Reorder blocks so the CTA appears above the fold
   - Convert a paragraph to a list
   - Change the heading level or structure
   - Pair typography deliberately: a theme `fontFamily` preset for the heading and a readable body preset, set via preset slugs (never inline `font-family` styles, never more than two families in one section)

   **Commonly underused levers** — these are high-signal and frequently skipped: imagery with descriptive alt text, heading/body font-family preset pairing, and background color preset explicitly paired with a contrasting text color preset. If none of these appear in a composed variant, reconsider before presenting it.

   **The bold-challenger rule (binds on every round):** every test, in **every round**, must field at least one composed challenger — a Visual Score 2 variant per the differentiation rubric in `docs/design-standards.md` (three or more structural levers working together to stage the concept). A lone single-lever challenger is **never permitted as the sole challenger in any round** — not in round 1, and not in refinement rounds. Refining a winning concept (round 2+) means a *fuller composition of that concept* — a richer, more committed staging of the same strategic frame — never degrading to a single-lever tweak (e.g. changing only the CTA button text on an otherwise identical block). A single-lever change is allowed only *alongside* a composed challenger when you are deliberately isolating one factor inside an already-won concept, never as the only thing on offer. This is the front-end counterpart to the **anti-false-negative rule** in Reviewing/ending: a timid challenger cannot teach you whether the concept works, so it must never stand alone. If you are proposing only one variant, it must be a composed concept. Visual Score 2 is the *floor* for a challenger; on a big-swing round — the architecture rung of the escalation ladder, a block that has plateaued across rounds, or low traffic where only bold can resolve — the composed challenger should be a **Visual Score 3 reimagining**, not merely Score 2.

   A single variant moves both copy and structure together — that is the norm for a concept, not an exception: the message *is* the frame and the composition *stages* it. The hypothesis must still name which axis you expect to drive the result. All structural changes must satisfy the slug-first and anti-pattern rules from `docs/design-standards.md`.

Example output:

> **Here's what I'd test on the homepage hero — three different reasons to act:**
>
> The block currently leads with what the product *is* ("Build better websites with WordPress"). Your analytics show 62% of these visitors arrive from Google searches naming a specific problem (slow sites), and your top testimonial talks about speed. So rather than reword the headline, I want to test three distinct *arguments* for why someone should act:
>
> - **Control (current):** "Build better websites with WordPress" — feature framing.
> - **Concept A — Outcome / pain relief:** "Fix your slow WordPress site in one afternoon." Staged with a before/after speed image and a single high-contrast CTA. *(Grounded in: 62% arrive from speed-related searches.)*
> - **Concept B — Social proof:** "Join 12,000 sites that load in under a second," led by your strongest speed testimonial and a logo strip. *(Grounded in: your existing testimonials emphasise speed.)*
> - **Success metric:** clicks on the main CTA (engagement)
> - **Traffic:** evenly split across the three; you have the conversion volume to resolve a 3-arm test.
>
> Want me to create it?

## Creating

Confirm the variant text and the success metric with the user. **Never call `create-ab-test` without explicit confirmation.**

Before showing the confirmation prompt, verify the variant content against the site's brand context file (`~/.config/accelerate-ai-toolkit/sites/<key>/brand.md`). If the file does not exist, generate it from `accelerate/get-site-context` with `blocks: "styled"` (falls back to `include_blocks: true` on older plugin versions). Check that all colors, font sizes, spacing, and font families use preset slugs (not hardcoded values), that all block types are registered on the site, and that no anti-pattern bans from `docs/design-standards.md` are violated. Silently correct any violations — swap a hardcoded hex to the nearest palette slug, swap a raw font size to the nearest scale step. The user should only see brand-consistent variant content in the confirmation prompt.

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
   - `annotations`: merge two keys — `{ "toolkit:pattern": "<pattern_id>", "source": "ai" }`. The `toolkit:pattern` value is the pattern_id you classified in Planning step 4; the `source` value records how the experiment was created. Pick exactly one of these two values:
     - **`"ai"`** — AI-generated, one-shot. You proposed this test and a human reviews it before (or while) it goes live. This is the default for any normal human-in-the-loop session.
     - **`"autopilot"`** — AI-generated **and** part of a continuous, unattended optimization loop, where there is no human in the per-step loop deciding whether each test goes live. Use this only when this skill is invoked by such a loop.

     `autopilot` **implies** `ai` — it is a *superset*, not a sibling: every autopilot experiment is also AI-generated. The difference is purely whether a human reviews each step. Anything that surfaces "AI-generated" provenance should treat both values as AI; the "autopilot" distinction only matters for showing that an autonomous loop is actively running. Never set `source` to anything other than these two values for a test this skill creates.

   **Naming convention.** Names are read on small screens and in narrow lists, so the first ~6–7 characters must carry the meaning. Keep both experiment and variant titles short, consistent, and legible to a non-developer. Do **not** bake provenance into the title text: never prefix a title with `"AI: "` or any "AI"/"autopilot" marker. Provenance is conveyed by the `source` annotation (set below) and rendered as a badge in the UI — putting it in the title duplicates the badge and steals the scannable first characters. Do not derive titles from the block's H1 or any heading; a truncated headline (`"R2 con…"`) is not a name.

   - **Experiment title = a test number + the block name.** Format: `"#<n> <Block>"` — e.g. `"#12 Hero"`, `"#7 Pricing"`, `"#15 Waitlist"`. `#<n>` is the test's number in *this site's* auto-research sequence — the **same number that indexes the x-axis of the progress chart**, so a card ties straight to the chart and tells a non-developer which test they're on. The number leads (it's the at-a-glance code); the block name follows, **spelled out in full**. Derive `n` from the journal's `iteration_counter + 1` (or the count from `list-experiments` + 1 if no journal — see the journal-consult step in Planning). **The code is a number, never an abbreviation:** never abbreviate the block to letters (`"WAIT"`, `"PRIC"`, `"H7"`) — a number needs no key, a letter-cipher does. **Do not write a sentence or the block's H1** as the title (`"Waitlist — join the waitlist"`, `"Trust — safety record"` are wrong — they bury the block name in prose). Just `#<number> <Block>`, nothing else.
   - **Variant title = the concept, spelled out in 1–2 words.** Name each arm by its strategic frame, never `"Variant A/B/C"`, never an H1, and **never an abbreviation** (`"OUT"`, `"SCR"` are wrong — write `"Outcome"`, `"Scarcity"`). Use `"Control"` for the incumbent (variant index 0); name challengers by the motivation they argue — e.g. `"Scarcity"`, `"Outcome"`, `"Social proof"`, `"Safety"`, `"Urgency"`. Short, human, consistent. The test number lives on the experiment, not in every variant — in context a variant reads as `"#12 Hero — Outcome"`. Good: `"Control"`, `"Outcome"`, `"Social proof"`. Bad: `"Variant B"`, `"AI: R2 con…"`, `"OUT"`, a truncated headline.

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
| Outcome | 1,155 | 241 | 20.9% | 82% |

**Current lead:** Outcome, with +27% improvement.
**Statistical confidence:** 82% — not conclusive yet. Rule of thumb: wait until one version is 95%+ likely to win.
**ETA:** at the current rate, you should have a clear result in about a week.
```

If there's already a winner (`has_winner` is true), say so — but apply the stopping gate below before urging the user to declare it. A high probability-to-win on day 3 with 40 visitors per arm is not a result.

### The stopping gate (binding — this is not advisory)

You **MUST NOT** declare a winner, conclude the test, harvest a variant, or report any arm as "winning" / "the winner" / "+X% lift" / "the leader to harvest" **unless both of these hold**:

- **(a) Every arm has crossed the per-arm minimums from Planning** — **~25 conversions AND ~800+ visitors, on every arm**, not just the leader.
- **(b) The leader is at ≥95% probability-to-be-best, sustained across at least 2–3 consecutive checks** — not a number that spiked once and may retract. One reading at 96% is not "sustained."

If either condition is not met, the **only** valid conclusion is **"inconclusive — insufficient data."** The test keeps running, and you report it as not-yet-resolved. There is no third option where you declare a soft or tentative winner.

**A directional reading on thin data is noise, not a result — do not present it as one.** When the gate is not met, you must not frame an observed delta as a finding. Saying *"variant C is at 5.4% vs control's 3.9%, so C is ahead"* on 7–10 conversions per arm is reporting noise as signal. A higher observed rate on a handful of conversions is **not evidence** — it routinely inverts as data accumulates, with the early "leader" ending up behind. Acting on that reading is worse than waiting: you harvest a coin-flip and learn nothing. Below the gate, name the leader's number only inside an explicit "too early to read" framing, never as a conclusion or a recommendation to harvest.

### "Not enough data" is not "the tool is broken"

If a test isn't accumulating conversions fast enough to cross the gate, that is a property of the site's traffic and conversion volume — **not** a fault in Accelerate or the data pipeline. The correct responses are: keep waiting, report the test as still-resolving with an honest ETA, or (next time) field fewer arms so the conversion stream isn't split as thin. The wrong responses are concluding early on the data you have, or telling the user the platform/tracking is faulty because the numbers are small. Do not misattribute your own impatience to the tooling. If you genuinely suspect a tracking break (e.g. zero events across all arms for days on an otherwise busy page), say that as a separate, specific observation — never as a reason to declare a winner.

### Worth-caring-about lift, and the winner's-curse guard

Even once the gate is met, a statistically clean +0.3% is rarely worth the switch — declare when the lift is large enough to matter to the business.

**Treat any observed lift above ~10% as probably-an-error until confirmed.** A very large lift is more often a measurement artifact (tracking error, a traffic anomaly, an early-sample fluke) or plain winner's curse — the arm that happened to look best having been partly lucky — than a genuine miracle. For any durable or hard-to-reverse harvest, **recommend a confirmatory re-test**: re-run the apparent winner against the control in a fresh fixed split, and only apply once it holds up. Do not harvest a >10% lift irreversibly on a single test's say-so.

## Reviewing / ending

1. Call `accelerate/get-experiment-results` to get the current state.
2. If the user wants to declare a winner, confirm **which variant** they want to declare (the current leader is the default but not assumed — ask them). Then call `accelerate/stop-experiment` with `action: "declare_winner"` and `winner_variant_index: <index>`.
3. If the user wants to stop without picking a winner, call `accelerate/stop-experiment` with `action: "stop"`.
4. If the user wants to pause temporarily, `action: "pause"`.
5. If the user wants to resume a paused test, `action: "resume"`.

After any state change, confirm in a single sentence.

### Declaring is not serving — you must harvest the winner

**A winner appearing in `get-experiment-results` is NOT being served to visitors.** Reaching the gate records the winner in the results only; the block keeps serving all variants until you **harvest** it. Harvesting = calling `accelerate/stop-experiment` with `action: "declare_winner"` and the winning `winner_variant_index` — that is the *only* step that collapses the block to the winning content so visitors actually see it. A test that "has a winner" but was never harvested has captured **zero** real improvement, no matter how large the reported lift (this is the gap that makes "we found a winner" quietly untrue in production).

**In autonomous / autopilot operation this is mandatory and easy to miss:** when a round reaches a gate-valid winner that you intend to keep and build the next round on, you **must** call `declare_winner` to harvest it *before* starting the next round. Do not move on having only read the winner from results — the next round would then build on un-harvested, baseline content and the climb never materialises. (The winner's-curse caution still applies: for a reported lift over ~10%, prefer a confirmatory re-test before treating the harvest as durable — but a gate-valid winner you're carrying forward must be harvested, not left declared-only.)

### Recording learnings: losing is the system working

**Set expectations up front.** Even elite testing programs win only roughly 8–20% of their tests. Most concepts lose, and that is not failure — it is how the system works. A test that loses *well* is worth running. Frame results to the user this way so a loss reads as evidence, not a wasted effort.

But a loss only teaches if the concept was bold enough to teach something:

- A **bold concept that loses** is valuable: you've learned that a whole strategic frame doesn't move this audience (record that concept-level learning — see below).
- A **timid concept that loses** teaches nothing: you can't tell whether the frame failed or whether you just didn't express it strongly enough. This is the worst outcome — calendar time spent, nothing learned.

When recording outcomes, **record which *concept* won or lost, not which micro-lever.** The learning is "the social-proof frame beat the outcome frame on this block," not "the green button beat the blue one." Concept-level learnings transfer to future blocks; lever-level ones rarely do. (In the journal, this is what `toolkit:pattern` already captures — each pattern is a concept.)

**Anti-false-negative rule:** the scope of the learning must match the scope of the challenger. A single-lever variant (Visual Score 1) that loses tells you only that *that specific tweak did not move the metric*. It does not tell you whether the underlying concept works on this block. Never record the conclusion as "social proof doesn't work here" or "visual changes don't matter for this section" off the back of a timid variant. Concept- or axis-level conclusions — "the outcome frame is what moves this block" or "structural changes don't help here" — require a composed, clearly-differentiated challenger (Visual Score 2) to have lost cleanly. If the losing variant was incremental, flag this explicitly: *"The variant we tested was a single-lever change — we haven't yet learned whether a bolder version of this concept would move this metric."*

## Monitoring multiple experiments

If the user asks "how are all my tests going", call `accelerate/list-active-experiments` first to get the set, then loop over each with `accelerate/get-experiment-results` and present a single summary table. Flag any that have reached a winning state.

## Rules

- **Never create, stop, pause, resume, or declare a winner without explicit user confirmation.** These are mutations; always show the user exactly what you're about to do.
- Always show variant text in confirmation prompts — don't hide it inside a "create test" summary.
- Check `list-active-experiments` before creating a new test to avoid overlapping experiments on the same block.
- **The stopping gate is binding, not advisory.** Never declare a winner, conclude, harvest, or report any arm as winning / "+X% lift" until **both** hold: per-arm minimums met on **every** arm (~25 conversions AND ~800+ visitors), AND the leader sustained ≥95% probability-to-be-best across 2–3 consecutive checks. Below that, the only valid conclusion is "inconclusive — insufficient data," and the test keeps running. Never present a directional delta on thin data as a result — it is noise and routinely inverts. See the stopping gate in Monitoring.
- **"Not enough data" is never "the tool is broken."** If a test isn't crossing the gate, keep waiting, report it as still-resolving, or field fewer arms next time — never conclude early, never blame the platform or data pipeline for small numbers.
- Treat any observed lift over ~10% as probably-an-error until confirmed — more likely a measurement artifact or winner's curse than a miracle. Recommend a confirmatory re-test before any durable or irreversible harvest.
- **A winner in the results is not served until harvested.** Reaching the gate only records the winner; you must call `stop-experiment` `declare_winner` to collapse the block to it. In autopilot, harvest every gate-valid winner you carry forward *before* the next round — a declared-but-unharvested winner captures zero real improvement. See "Declaring is not serving" in Reviewing/ending.
- Always translate "chance to be best" into a plain-English percentage. Never use the word "Bayesian" unless the user uses it first.
- If the test is on a block the user can't easily identify by name, include the `edit_url` from the response so they can click through to the editor.
- Every proposed variant must be a distinct *concept* — a different strategic answer to "why should this visitor act?" — grounded in cited evidence, and must score 3 or higher on the differentiation rubric (Message + Visual/structural + Hypothesis clarity, each scored 0–2). A concept that can't name its evidence doesn't run. See `docs/design-standards.md` for the full rubric.
- **The bold-challenger rule binds on every round.** Every round — including refinement rounds (round 2+) — must field at least one composed (Visual Score 2) challenger. Refining a winning concept means a fuller composition of that concept, never degrading to a single-lever tweak; a lone single-lever challenger is never the sole challenger in any round. See the bold-challenger rule in Planning and the anti-false-negative rule in Reviewing/ending.
- **After an inconclusive round, escalate the lever class — never repeat it.** Two consecutive inconclusive rounds at one class (copy / composition / architecture-goal) means the metric is inelastic to that class on this block: climb a rung rather than re-fielding reworded copy. See the escalation ladder in Planning.
- **If an escalation changes the conversion metric, re-establish the baseline on the new metric before claiming a lift** — pre-switch and post-switch rounds are separate series; a metric change is never a content-driven lift. See the goal-switch guard in Planning.
- Never propose variant text that uses AI-slop markers: "unlock", "supercharge", "leverage", "empower", "elevate", "streamline", "revolutionize", or other generic power words. Use specific, concrete language grounded in the page's data instead.
