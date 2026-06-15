---
name: accelerate-evolve
description: Improve a block over multiple rounds — "keep improving my hero", "run an optimization loop on the homepage", "autopilot the waitlist block", "evolve this section until it stops getting better". Each round fields bold new challengers, tests them, harvests the winner, and builds the next round on it. NOT for a single A/B test (use accelerate-test) or a one-off variant (use accelerate-design).
license: MIT
category: experimentation
parent: accelerate
---

# Accelerate — Evolve a block over rounds

You run a multi-round optimization on one block: each round generates bold challengers, tests them against the current best, harvests a gate-valid winner, and builds the next round on it. You **orchestrate** two skills — `accelerate-design` (author each round's challengers) and `accelerate-test` (create, monitor, harvest, record) — and do not duplicate their mechanics. Read both before running this.

**Route elsewhere when:** the user wants one test, not a sequence → `accelerate-test`. The user wants a single version of a block → `accelerate-design`.

## Two modes

- **Attended (default).** Confirm each round's challengers before creating the test, and confirm each harvest. Annotate experiments `source: "ai"`.
- **Autopilot.** The user has explicitly asked for an unattended loop. You proceed round to round without per-step confirmation, annotate `source: "autopilot"`, and report progress as it happens. The stopping gate and harvest-before-next-round rules still bind exactly as in attended mode — autopilot removes the human click, not the discipline. The user's request to run autopilot is the standing approval for the mutations the loop makes.

## The round

1. **Establish the incumbent.** The control is the current best: round 1 it's the existing block content; later rounds it's the harvested champion from the round before. This is the benchmark every challenger must beat.
2. **Generate challengers (`accelerate-design`).** Field bold, *new-structure* challengers pulled novelty-first from the site's vocabulary (the brand pack) — composed redesigns (Visual Score 2+), never re-skins, never a lone timid arm. **Size the arm count to the traffic budget** (the rule in `accelerate-test` Planning step 5: low volume → control + one bold; ≥500 conv/month → 3–5). This is the bold-by-default doctrine, `docs/design-standards.md` §9.
3. **Create the test (`accelerate-test` → Creating).** Back up the block first, field control + challengers, name `"#<n> <Block>"`, set the goal, annotate the source. Verify it's actually running.
4. **Monitor to the gate (`accelerate-test` → Monitoring).** The binding stopping gate decides what won — per-arm minimums on **every** arm and ≥95% probability sustained across checks. Below it, the only verdict is "inconclusive"; never read a thin-data delta as a result.
5. **Harvest before the next round (mandatory).** A gate-valid winner you intend to carry forward **must** be harvested — `accelerate-test` → `declare_winner` — *before* round N+1, or the next round builds on un-harvested baseline content and the climb never materialises. Record the round's concept-level learning (`accelerate-learn` pattern) so later rounds don't re-field settled structures.
6. **Cull, escalate, or author.** A composed concept that lost cleanly is retired — climb the escalation ladder (`accelerate-test`), don't re-field it. When the site's existing vocabulary is spent, author a *new* section from what's winning (`accelerate-design`) and field that next.

## Stopping

Stop and report when any of these hold: the user stops it; a round comes back inconclusive after escalating through the ladder with no class left to climb; or several rounds produce no gate-valid improvement over the incumbent (convergence). Don't churn rounds that can't teach anything — say plainly that the block has plateaued and what the current best is.

## Reporting

Each round, in marketer language: what's being tested and why, what the current best is, the honest gate status (resolved / still resolving with an ETA), and one line on what the next round will try (and any escalation: *"copy framing hasn't moved this in two rounds — next round redesigns the section"*). Follow `docs/output-style.md`. Never narrate capabilities or show markup.

## Rules

- **One incumbent + bold new-structure challengers every round** — novelty-first from the site's own vocabulary, sized to the traffic budget, never a lone timid arm. `docs/design-standards.md` §9.
- **The stopping gate is binding.** Never declare, harvest, cull, or report a winner on thin data. A directional delta below the gate is noise — see `accelerate-test` Monitoring.
- **Harvest every carried winner before the next round.** A declared-but-unharvested winner captures zero real improvement and breaks the climb.
- **A loss only teaches if the challenger was bold.** Retire a concept only on a clean composed loss, never a timid one (anti-false-negative rule).
- **Author new only when the vocabulary is spent** — exhaust the site's real sections (recombined and extended) first.
- **Autopilot annotates `source: "autopilot"`** and keeps every gate and harvest rule; it removes the per-step click, not the discipline.
- **Confirm before mutating in attended mode**, and never leak developer jargon in anything the user reads.
