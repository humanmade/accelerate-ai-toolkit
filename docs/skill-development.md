# Skill development

How to add new skills to the Accelerate AI Toolkit. Start here if you want to contribute a workflow the toolkit doesn't cover yet.

---

## The mental model

The toolkit is a shared `/skills/` directory plus per-agent manifests that reference it. Adding a skill means:

1. Create a folder in `/skills/` with a `SKILL.md` inside.
2. Follow the frontmatter and tone conventions.
3. The skill is automatically picked up by every agent manifest that references `/skills/` — Claude Code, Codex CLI, and (when they ship) Cursor and Gemini.

There is no build step. There is no compilation. Skills are pure markdown that the agent reads at runtime.

---

## Skill file structure

Each skill lives in its own folder:

```
skills/
└── accelerate-your-skill/
    └── SKILL.md
```

The folder name should be `accelerate-` prefixed, kebab-case, and match the `name` in the frontmatter.

---

## Frontmatter

Every `SKILL.md` starts with YAML frontmatter:

```yaml
---
name: accelerate-your-skill
description: One dense sentence describing when to use this skill. The model uses this for routing, so include plenty of keywords the user might use. Example keywords: X, Y, Z.
license: MIT
category: one-word-category
parent: accelerate
disable-model-invocation: true
---
```

Required fields:

- **`name`** — matches the folder name exactly.
- **`description`** — this is the single most important field. The model reads every skill description at startup and decides which to route to based on keyword matching. Pack it with words the user might actually use. Aim for 1–3 sentences.
- **`license`** — always `MIT` for toolkit-native skills.
- **`category`** — one word that groups the skill (`analysis`, `experimentation`, `personalization`, `reference`, etc.).

Optional fields:

- **`parent: accelerate`** — marks this as a sub-skill of the main router. Keeps the skill out of the top-level discoverable set.
- **`disable-model-invocation: true`** — used alongside `parent`. Tells the agent to hide this skill from the always-visible pool and only load it when the router explicitly routes to it. Keeps the startup token budget low.

---

## Tone and voice

**This is the rule that matters most.** Every skill in the toolkit targets a non-technical marketer. The user never sees developer jargon.

### Banned words in user-facing output

Do not use any of these in prose the user reads:

- "ability", "endpoint", "API", "MCP", "schema", "parameter", "JSON", "tool call", "ability identifier"
- Raw ability names like `accelerate/get-performance-summary`
- Raw field names like `endpoint.Attributes.referer`
- Environment variables like `WP_API_*`

### Replacements

- "your traffic breakdown" instead of "the get-traffic-breakdown ability output"
- "your top pages" instead of "top content by views"
- "visitors from Google" instead of "the `endpoint.Attributes.referer = google.com` segment"
- "your site's capabilities" instead of "the Abilities API"

### Voice

Speak like a helpful marketing consultant. Lead with the recommendation, then the reason, then the data.

❌ **Bad:** *"I'll call `accelerate/get-landing-pages` to fetch the top entry pages and then use `get-engagement-metrics` to analyse their bounce rates..."*

✅ **Good:** *"Your homepage is the biggest opportunity — it gets the most entries but also the highest bounce rate. Here's what I'd try..."*

---

## Skill body structure

Most workflow skills follow this structure:

```markdown
# Accelerate — [Skill name]

[One-paragraph description of the skill's purpose, for the model to orient itself.]

## Phase detection (if applicable)

[Table mapping user intent to which sub-flow to run.]

## What to fetch

[Numbered list of ability calls, with their ability names and inputs. This section is for the model — the user never sees it.]

## How to present the result

[Example output, with tables and plain-English prose. This is the user-facing output format.]

## Rules

[Bullet list of hard rules. What to always do, what to never do, how to handle edge cases.]

## Edge cases

[Situations that break the happy path and how to handle them.]
```

---

## Calling abilities

The toolkit exposes Accelerate via a single MCP tool: `mcp__wordpress__mcp-adapter-execute-ability`. It takes an ability name (e.g. `accelerate/get-top-content`) and an input object.

**Inside the skill body**, document the calls you want the model to make by name:

```markdown
1. Call `accelerate/get-top-content` with `limit: 10` and `date_range_preset: "7d"`.
2. Call `accelerate/get-engagement-metrics` with `entity_type: "site"` in parallel.
```

The model will translate these into the actual tool call at runtime. You don't need to write code.

For the full list of available abilities, see [`skills/accelerate-abilities-reference/SKILL.md`](../skills/accelerate-abilities-reference/SKILL.md) or the user-facing [`docs/ability-reference.md`](./ability-reference.md).

---

## Confirming mutations

Any skill that creates, updates, or deletes things **must** ask the user to confirm before calling the mutating ability. This is a hard rule.

Pattern:

1. Build the proposed change in working memory.
2. Show the user exactly what you're about to do, including all user-visible content (variant text, audience rules, etc.).
3. Ask "sound good?" (or similar) and wait for explicit confirmation.
4. Only then call the mutating ability.

Destructive abilities (`remove-variant`, `stop-experiment`, `broadcast-content`) carry a `destructive: true` flag in Accelerate's own metadata; treat those as requiring extra-clear confirmation.

---

## Testing your skill

The toolkit doesn't have an automated test framework — skills are markdown, not code. To test a new skill:

1. Install the toolkit locally via `/plugin install ./`.
2. Restart your agent session.
3. Craft 3–5 prompts that should trigger your skill based on its `description` frontmatter. Run them and see whether the router picks the right one.
4. For each prompt, read the raw response and verify:
   - It used the correct abilities.
   - The output matches the tone rules (no jargon).
   - The output follows the format you specified.
   - Edge cases (no data, low traffic, permission errors) are handled gracefully.
5. If you change the `description` or tone, retest the routing — small wording changes can shift which skill the model picks.

---

## Submitting a new skill

1. Fork the repository.
2. Create your skill folder and `SKILL.md`.
3. Update `docs/ability-reference.md` if you're using capabilities that weren't previously covered by any skill.
4. Update the `README.md` "What's inside" section if the new skill expands toolkit coverage meaningfully.
5. Open a pull request.

Reviewers will check:

- Tone matches the toolkit's conventions (no jargon in user-facing output).
- The description routes correctly for likely user phrasings.
- Mutations (if any) require explicit confirmation.
- No overlap with existing skills (if there is, either merge scopes or rename to clarify).

---

## What not to build

Some ideas that sound like skills but shouldn't be:

- **A skill per ability.** The toolkit deliberately does not ship a 1:1 wrapper around each of the 39 abilities. The MCP adapter already exposes each ability; skills add value by composing multiple abilities into a workflow.
- **A developer-facing skill.** There's a separate skill bundle inside the Accelerate plugin repository itself (`altis-accelerate/.claude/skills/`) that targets developers. The toolkit is for end users.
- **A skill that replaces the WordPress admin.** If the user just wants to see their analytics, the Accelerate admin UI is better. Skills should do things the admin UI can't: reasoning, recommending, cross-referencing, synthesising.
