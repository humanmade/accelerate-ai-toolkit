# Self-optimising recommendations

The toolkit learns what works on your specific site and tailors future suggestions accordingly. After a few weeks of A/B testing, it stops giving you generic marketing advice and starts giving you advice grounded in your own results.

---

## How it works

1. You run A/B tests through the toolkit (using `/accelerate-test` or the optimise landing page workflow).
2. Over time, experiments conclude -- some changes win, some don't.
3. You run `/accelerate-learn` to update the toolkit's memory of what's worked.
4. The toolkit records which *types* of changes win and lose on your site in a local file called the learning journal.
5. Next time you ask for recommendations, the toolkit leans on patterns that have won here and warns you about patterns that haven't.

---

## Running it manually

Inside your agent session:

```
/accelerate-learn
```

The skill reads your completed A/B test results, classifies each one, updates the journal, and prints a summary of what it found. This is the default path -- zero setup beyond what you already have.

**When to run it:** After experiments conclude. A good cadence is every 1-2 weeks, or whenever you see a test reach a verdict. Running it more often is harmless but won't produce new signal until experiments finish.

**What it reads:** Completed experiment results from your site (via the same connection you set up with `/accelerate-connect`).

**What it writes:** Two files on your machine:
- A machine-readable journal (used by other skills to tailor recommendations)
- A human-readable summary you can open and read any time

Both live at `~/.config/accelerate-ai-toolkit/` and are private to your machine.

---

## The learning journal

The journal tracks ~15 types of changes (called "patterns") that A/B tests commonly exercise:

| Pattern | Example |
|---------|---------|
| Rewrite headline to match search intent | "Fix your slow site" instead of "Welcome to our site" |
| Move call-to-action higher on the page | Put the signup button in the hero, not below the fold |
| Add social proof near the call-to-action | Customer quote right above the button |
| Simplify the hero section | Remove clutter, focus on one message |
| Personalise by traffic source | Show different content to Google vs social visitors |
| Change hero image | Swap the stock photo for something specific |

Each pattern gets one of four statuses:

- **Won** -- at least 3 decisive tests, 75%+ win rate. The toolkit leans on these.
- **Lost** -- at least 3 decisive tests, 25% or lower win rate. The toolkit warns you.
- **Mixed** -- enough tests, but no clear trend. Treated as neutral.
- **Not enough data** -- fewer than 3 decisive tests. Ignored until more evidence arrives.

You can read the journal any time by opening `~/.config/accelerate-ai-toolkit/journal-<your-site>.md` in any text editor.

---

## Running it on a schedule (optional)

If you want the journal to update automatically, you can set up a weekly GitHub Actions workflow. This is optional -- the manual path works fine.

### Prerequisites

- A GitHub account
- A repository (can be private) where you want the journal snapshots stored
- Basic familiarity with GitHub Secrets

### Setup

1. Copy `docs/examples/workflow-accelerate-learn.yml` from this toolkit into `.github/workflows/accelerate-learn.yml` in your own repo.

2. Add four secrets to your repo (Settings > Secrets and variables > Actions):
   - `ANTHROPIC_API_KEY` -- your Claude API key
   - `WP_API_URL` -- the full WordPress connector URL saved by `/accelerate-connect` (e.g. `https://example.com/wp-json/mcp/mcp-adapter-default-server`)
   - `WP_API_USERNAME` -- your WordPress username
   - `WP_API_PASSWORD` -- your Application Password

3. The workflow runs every Sunday at 03:00 UTC. It creates a pull request with the updated journal so you can review the diff before merging.

### What happens each week

1. The workflow runs `/accelerate-learn` against your site.
2. The journal files are copied into a `learnings/` directory in your repo.
3. A pull request is opened showing what changed.
4. You review and merge (or close if something looks off).

The PR is a snapshot for review. Your local journal (`~/.config/`) remains the canonical copy that the toolkit reads during sessions.

### Cost

The workflow is constrained to 6 Claude turns and 15 minutes maximum. On the GitHub Actions free tier (2,000 minutes/month), a weekly run is negligible.

---

## How it affects recommendations

Once you have a journal with qualifying data:

- **Opportunities** (`/accelerate-opportunities`): patterns that have won get priority. Patterns that have lost are flagged with context instead of being suggested first.
- **A/B test planning** (`/accelerate-test`): hypotheses lean toward winning patterns. Losing patterns come with a warning.
- **Site reviews** (`/accelerate-review`): a new section shows your top winning and losing patterns.

The toolkit always tells you when it's leaning on learned data: *"I'm suggesting this because headline rewrites have won 4 of 5 tests on your site."* This keeps the loop transparent -- you can push back if the weighting feels wrong.

---

## Troubleshooting

### "No learning data yet"

Run `/accelerate-learn`. If your site has no completed A/B tests, the journal will be empty. Run some tests first and check back in a few weeks.

### The journal seems wrong

You can delete `~/.config/accelerate-ai-toolkit/journal-<your-site>.json` and run `/accelerate-learn` again to rebuild from scratch. The skill reads all completed experiments from your site, so nothing is lost.

### The scheduled workflow fails

Check your repo's Actions tab for the error. Common causes:
- Expired Application Password -- regenerate via `/accelerate-connect` and update the GitHub Secret.
- API key issue -- verify `ANTHROPIC_API_KEY` is set and valid.
- Site unreachable -- check that `WP_API_URL` points to a live WordPress MCP connector URL (the value `/accelerate-connect` saved locally).

### The PR never merges

That's fine. The local journal on your machine is the source of truth. The repo copy is a review snapshot, not the authoritative state. Your local and repo copies may diverge -- this is expected.

---

## FAQ

**How is this different from Accelerate's built-in analytics?**
Accelerate shows you what happened. The toolkit's learning loop turns that into *what works here* -- a site-specific memory that shapes future recommendations.

**Do I need GitHub to use this?**
No. The default path is manual: run `/accelerate-learn` inside your agent. GitHub Actions is an optional add-on for automation.

**Does this learn across sites?**
No. Each site has its own journal. A pattern that wins on one site does not automatically apply to another.

**Can I edit the journal by hand?**
Yes, but the next `/accelerate-learn` run may overwrite your changes if the pattern you edited also gets updated from new test results.

**What if I've never run an A/B test?**
The journal will be empty and the toolkit falls back to its generic recommendations. Start testing, and the journal fills up naturally.
