# Output style

How every skill in the toolkit should present data, recommendations, and status to the user. Not a rigid template -- a set of composable building blocks. Pick the ones that fit what you're showing.

---

## Principles

1. **Lead with the insight, not the data.** Say what it means before showing the numbers.
2. **One format per information type.** Tables for comparison, bold labels for recommendations, inline for single metrics. Don't mix.
3. **Every number earns its place.** If it doesn't change what the user does next, cut it.

---

## Building blocks

### Summary line

One bold sentence that frames the entire response. Always comes first.

```
**Site review -- last 7 days**
```

```
**Right now** -- 247 people on the site.
```

```
**Optimising [Page Title]**
```

Use `**bold**` for the framing, not a markdown heading. The heading level is reserved for section structure within the response.

---

### Data table

For comparing items -- pages, sources, variants, campaigns. Clean markdown tables.

```
| Page | Visitors | Bounce | Conv. rate |
|------|----------|--------|------------|
| Pricing | 1,240 | 78% | 2.1% |
| Homepage | 3,410 | 52% | 4.3% |
| Blog index | 890 | 71% | 0.8% |
```

**Rules:**
- Max **5 rows** by default. If the user asks for more, expand.
- Max **5 columns**. If you need more dimensions, split into two tables or use a callout.
- **Bold the standout value** -- the best, worst, or most surprising cell.
- Use short column headers. "Conv. rate" not "Conversion Rate (%)".
- Include trend arrows (`↑ 12%`) in a "vs. previous" column only when comparison data exists. Never fabricate trends.

---

### Trend indicators

Inline after a number, for period-over-period comparison:

- `↑ 12%` -- up
- `↓ 3%` -- down
- `→ flat` -- no meaningful change

Only use when you have real comparison data. If the previous period is missing, omit the indicator entirely -- don't write `→ no data`.

---

### Priority cards

For ranked recommendations -- what to do, in what order. Used by opportunities, landing page optimisation, and content planning skills.

```
### 🔴 [one-line action]
**What:** [concrete action the user can take]
**Why:** [specific number from the data -- e.g. "78% bounce rate on 1,240 weekly entries"]
**Next step:** [verb matching a downstream skill]
```

Three tiers:
- 🔴 high impact / urgent
- 🟡 medium impact / worthwhile
- 🟢 lower impact / good to know

Always **2-3 cards**. Never 1, never more than 3. Each card must cite a real number from fetched data in the **Why** line.

---

### Callout line

One bold interpretive sentence after a table. Tells the user what the table means.

```
**Best performer:** your newsletter -- small audience, but they convert 3.7x better than Google.
```

```
**Watch out:** the pricing page bounced 78% of 1,240 visitors this week. That's your biggest leak.
```

Use after every data table. The table shows the numbers; the callout says what to do about them.

---

### Status indicator

For connection health, test states, and yes/no verdicts:

- ✅ healthy / connected / winning
- ❌ broken / failed / not connected
- ⚠️ partial / limited / needs attention

Used by `/accelerate-status` and test monitoring. Keep to a single status block -- one indicator per response.

---

### Hand-off prompt

End actionable responses with one offer to continue. Italicised, phrased as a question.

```
*"Want me to dig into the pricing page? I can run a full diagnosis."*
```

```
*"Want me to set up an A/B test for the first recommendation?"*
```

**Rules:**
- Exactly one hand-off per response. Don't offer three options.
- The verb should match the logical next skill (diagnose, test, personalise, review).
- If the response is purely informational with no obvious next action, skip the hand-off.

---

## Anti-patterns

- **No ASCII boxes or dividers.** Use markdown structure.
- **No code blocks for non-code content.** Data goes in tables, not fenced blocks.
- **No walls of numbers without interpretation.** Always pair data with a callout.
- **No emoji beyond the standard set.** Only use: 🔴 🟡 🟢 (priority), ✅ ❌ ⚠️ (status), ↑ ↓ → (trends). No decorative emoji.
- **No raw data dumps.** Summarise first. If the user wants the full dataset, they'll ask.
- **No "I called X and got Y" narration.** Present results as if you looked them up yourself.
