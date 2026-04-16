# Marketplace & Product Guidelines

Guardrails for building marketplace-compliant, on-brand skills, agents, and features for the Accelerate AI Toolkit. Every contributor and every AI agent working on this repo should treat this document as binding.

Sources: official Claude Code plugin documentation (code.claude.com/docs/en/plugins, plugins-reference, skills, plugin-marketplaces), Anthropic marketplace analysis (internal/claude-directory-best-practices.md), product north star (internal/NORTH-STAR.md), skills review (internal/SKILLS-REVIEW.md).

---

## 1. Plugin Structure & Manifest

### Directory layout

```
accelerate-ai-toolkit/
  .claude-plugin/
    plugin.json            # Plugin manifest (ONLY this file goes here)
    marketplace.json       # Marketplace catalog
  skills/                  # At plugin root, NOT inside .claude-plugin/
    accelerate/
      SKILL.md
    accelerate-review/
      SKILL.md
    ...
  agents/                  # At plugin root
  commands/                # At plugin root (legacy; prefer skills/)
  hooks/                   # At plugin root, hooks.json inside
  docs/                    # User documentation
  internal/                # Internal design docs (gitignored or non-user-facing)
```

**Hard rule:** `skills/`, `agents/`, `commands/`, `hooks/`, `bin/`, `settings.json`, `.mcp.json`, `.lsp.json` must live at the plugin root. Only `plugin.json` (and `marketplace.json`) go inside `.claude-plugin/`. Misplaced directories are silently ignored and components will not load.

### plugin.json required fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | Unique identifier, kebab-case (lowercase letters, digits, hyphens). Becomes the skill namespace prefix. |
| `description` | string | Recommended | Shown in plugin manager when browsing/installing. |
| `version` | string | Recommended | Semantic versioning (see section 4). |
| `author` | object | Optional | `{ "name": "Human Made" }` |
| `homepage` | string | Optional | Link to docs/website. |
| `repository` | string | Optional | Link to GitHub repo. |
| `license` | string | Optional | SPDX identifier, e.g. `"MIT"`. |
| `keywords` | array | Optional | Discovery tags. |

### marketplace.json required fields

| Field | Type | Required |
|-------|------|----------|
| `name` | string | Yes |
| `owner` | object | Yes (`owner.name` required) |
| `plugins` | array | Yes |

Each plugin entry needs at minimum `name` and `source`.

### Reserved marketplace names (do not use)

`claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `knowledge-work-plugins`, `life-sciences`. Names that impersonate official marketplaces (e.g. `official-claude-plugins`, `anthropic-tools-v2`) are also blocked.

### Path rules

- All paths in manifests must be relative and start with `./`.
- No path traversal (`../`) -- installed plugins are copied to a cache and external references break.
- Use `${CLAUDE_PLUGIN_ROOT}` for referencing bundled scripts/configs in hooks and MCP server definitions.
- Use `${CLAUDE_PLUGIN_DATA}` for persistent state that should survive plugin updates (e.g. `node_modules`, caches).

---

## 2. Skill Compliance

### SKILL.md structure

Every skill is a directory containing a `SKILL.md` file with YAML frontmatter and markdown body:

```yaml
---
name: accelerate-review
description: Site performance snapshot. Use when the user asks how their site is doing, wants a status check, or asks for a review of recent performance.
---

# Skill body (markdown instructions)
...
```

### Frontmatter fields

| Field | Required | Constraint |
|-------|----------|------------|
| `name` | No (defaults to directory name) | Lowercase letters, numbers, hyphens only. Max 64 characters. |
| `description` | Recommended | Front-load key use case. Combined `description` + `when_to_use` is truncated at **1,536 characters** in the skill listing. |
| `when_to_use` | No | Additional trigger context. Appended to `description`; counts toward the 1,536-char cap. |
| `disable-model-invocation` | No | Set `true` for user-only skills (e.g. `/accelerate-connect`). Prevents Claude from auto-loading. |
| `user-invocable` | No | Set `false` to hide from `/` menu (background knowledge only). |
| `allowed-tools` | No | Grants permission, does NOT restrict. Space-separated or YAML list. |
| `context` | No | Set `fork` to run in an isolated subagent. |
| `agent` | No | Which subagent type to use with `context: fork`. |
| `model` | No | Model override. |
| `effort` | No | `low`, `medium`, `high`, `max`. |
| `argument-hint` | No | Hint for autocomplete, e.g. `[page-url]`. |
| `paths` | No | Glob patterns limiting auto-activation to matching files. |

### Size limits

- **SKILL.md body: under 500 lines.** Move detailed reference material, ability catalogs, or long examples to separate files alongside SKILL.md and reference them with markdown links.
- **Compaction budget:** After context compaction, the first 5,000 tokens of each invoked skill are kept. All re-attached skills share a combined 25,000-token budget, filled most-recent-first.

### String substitutions available in skill content

| Variable | What it expands to |
|----------|-------------------|
| `$ARGUMENTS` | Full user input after the skill name |
| `$ARGUMENTS[N]` or `$N` | Specific argument by 0-based index |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Directory containing this SKILL.md |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin installation root |

### Shell injection

`` !`command` `` syntax runs shell commands before the skill content is sent to Claude. The output replaces the placeholder. Multi-line variant: open a fenced block with `` ```! ``.

Can be disabled organisation-wide via `"disableSkillShellExecution": true` in managed settings.

---

## 3. Agent Compliance

### Supported frontmatter fields

`name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation`.

### NOT supported in plugin agents (security restriction)

- `hooks`
- `mcpServers`
- `permissionMode`

These are silently ignored. Do not rely on them.

### Isolation

The only valid `isolation` value is `"worktree"`. Any other value is rejected.

---

## 4. Naming & Versioning

### Naming rules

- Plugin names and marketplace names: **kebab-case only** (lowercase letters, digits, hyphens).
- The Claude.ai marketplace sync rejects non-kebab-case names even if Claude Code accepts them locally.
- Skill names follow the same rule: max 64 characters.
- Plugin skills are namespaced as `/plugin-name:skill-name` to prevent conflicts.

### Semantic versioning

Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (incompatible behaviour changes).
- **MINOR**: New features (backward-compatible additions).
- **PATCH**: Bug fixes (backward-compatible fixes).
- Pre-release: `2.0.0-beta.1` for testing.

**Critical:** If you change plugin code but do not bump the version, existing users will not see updates due to caching. Always bump the version before distributing changes.

Set the version in **one place only** -- either `plugin.json` or the marketplace entry's `version` field. If both are set, `plugin.json` wins silently.

### CHANGELOG.md

Maintain a CHANGELOG.md documenting each version's changes. This is a best practice from the official docs and a trust signal for directory reviewers.

---

## 5. Marketplace Submission Checklist

### Submission forms

- **Claude.ai:** `claude.ai/settings/plugins/submit`
- **Console:** `platform.claude.com/plugins/submit`

### Before submitting

- [ ] Run `claude plugin validate .` (or `/plugin validate .` in-session). Fix all errors and warnings.
- [ ] Plugin name is kebab-case.
- [ ] `plugin.json` has `name`, `description`, `version`.
- [ ] `marketplace.json` has `name`, `owner.name`, at least one plugin in `plugins`.
- [ ] Skills, agents, and commands are at the plugin root, not inside `.claude-plugin/`.
- [ ] All internal paths start with `./` and contain no `../`.
- [ ] Version has been bumped since the last submission.
- [ ] README.md exists with installation and usage instructions.
- [ ] CHANGELOG.md exists.
- [ ] LICENSE file exists.
- [ ] All hook scripts are executable (`chmod +x`).
- [ ] MCP server commands use `${CLAUDE_PLUGIN_ROOT}` for paths.
- [ ] No secrets, credentials, or `.env` files included.

### Common validation warnings

| Warning | Fix |
|---------|-----|
| `Plugin name "x" is not kebab-case` | Rename to lowercase-letters-digits-hyphens. |
| `No marketplace description provided` | Add `metadata.description` to `marketplace.json`. |
| `Marketplace has no plugins defined` | Add at least one entry to the `plugins` array. |
| `YAML frontmatter failed to parse` | Fix YAML syntax in SKILL.md or agent file. |
| `Invalid JSON syntax` in hooks.json | Fix JSON. A malformed `hooks/hooks.json` prevents the entire plugin from loading. |

---

## 6. Directory Listing Optimisation

These rules apply when writing or revising the plugin's description, tagline, README, and example prompts for the official Claude Code directory at `claude.com/plugins`.

### Short tagline (grid card)

- Under 160 characters, one sentence max.
- Lead with an action verb or outcome, not "A plugin that..."
- Name the specific problem it solves OR the specific outcome it delivers.
- Avoid generic words: "access", "manage", "various", "integration", "provides", "supports".
- Use power words: "craft", "diagnose", "prioritise", "track", "automate", "generate".

**Formula:** `[Action verb] [specific outcome]. [Unique differentiator or anti-pain-point].`

### Long description (detail page)

- **Paragraph 1:** Problem statement + solution (what pain does this eliminate?).
- **Paragraph 2:** Architecture/methodology (how does it work differently?).
- **Paragraph 3:** Key capabilities with **bold text** for scanability.
- **"How to use:" section** with lowest-friction activation method stated first, then 3-4 example prompts.
- Total: 150-300 words, 3-5 paragraphs.
- The detail page supports **bold** and paragraph breaks, but NOT headers, bullet lists, code blocks, images, or links.

### Example prompts

Good examples are:
- **Specific:** "Which landing page has the worst bounce-to-conversion ratio?"
- **Contextual:** "Should I personalise content for visitors coming from Google?"
- **Imaginative:** "What should I A/B test on my pricing page this month?"
- **Complete sentences:** natural language the user would actually type.

Bad examples are:
- Generic: "check analytics"
- Terse: "run test"
- Feature-focused: "use the review tool"

### Trust signals (ranked by impact)

1. **Anthropic Verified badge** -- strongest signal. Apply when eligible.
2. **Brand name recognition** (Human Made, Accelerate).
3. **GitHub stars and contributor count.**
4. **Demo video or GIF** placed before install instructions in README.
5. **Personal author voice** and community channels (Discord, GitHub Discussions).
6. **Verification step** in README: "To verify it works, try..."

### Positioning ladder

| Level | Positioning | Install ceiling |
|-------|------------|-----------------|
| 5 | **Paradigm shift** -- changes how users work | 400K+ |
| 4 | **Problem eliminator** -- removes a named pain | 200K+ |
| 3 | **Capability unlock** -- enables something impossible before | 100K-200K |
| 2 | **Workflow integration** -- connects existing tools | 50K-100K |
| 1 | **Feature list** -- does X, Y, Z things | <50K |

**Accelerate should aim for Level 4:** "Your analytics already know what to fix. This toolkit turns that knowledge into prioritised actions, safe A/B tests, and clear verdicts -- no dashboards, no spreadsheets, no code."

---

## 7. Accelerate-Specific Product Rules

These rules come from the product north star and skills review. They apply to every skill, agent, command, and piece of user-facing copy in this repo.

### Audience

The user is a **non-technical marketer or site owner**. They understand marketing -- landing pages, bounce rates, conversions, campaigns -- but they do not want technical implementation details.

### Plug-and-play resilience

This toolkit must work the moment a user installs it. No custom scripts, no npm steps, no CLI prerequisites beyond Claude Code itself and a WordPress site with Accelerate. Every feature must assume the user has done nothing except run `/accelerate-connect`.

**Graceful degradation rules:**

- **Missing connection.** If the WordPress MCP server is not available, tell the user to run `/accelerate-connect`. Never error out silently or dump a stack trace.
- **Missing data.** If a site is brand new or a page has zero traffic, say so in plain English and suggest what the user can do to start generating data. Never treat missing data as a fatal error.
- **Missing brand context.** If no brand context file exists at `~/.config/accelerate-ai-toolkit/brand-<site-slug>.md`, fall back to sensible defaults derived from the live site via `get-site-context`. Never require the user to create config files manually.
- **Missing journal.** If no learning journal exists at `~/.config/accelerate-ai-toolkit/journal-<site-slug>.json`, skip journal consultation silently and proceed with generic reasoning. Do not tell the user the journal is missing -- just fall back. If the journal exists but is invalid JSON or has an unknown `schema_version`, also fall back silently. Never attempt to repair a corrupted journal from within a consuming skill -- only `accelerate-learn` writes the journal.
- **Capability not available.** If an Accelerate ability returns a permission or version error, explain what the user needs in plain English (e.g. "ask your site admin for Editor access") and continue with whatever data is available. Never stop the entire workflow because one data source is unavailable.
- **Partial results.** If some data sources return results and others fail, present what you have and note what is missing. A partial answer is better than no answer.

**Never require the user to:**

- Run terminal commands (beyond the initial install and `/accelerate-connect`).
- Edit config files, environment variables, or JSON.
- Install additional packages, dependencies, or tools.
- Understand file paths, directory structures, or technical setup.
- Read error messages that reference code, APIs, or system internals.

If a feature cannot work without manual setup, it is not ready to ship.

### Banned words in user-facing output

Never show these words in responses, skill descriptions, error messages, or documentation aimed at end users:

- `API`
- `schema`
- `MCP`
- `JSON`
- `tool call`
- `ability`
- `endpoint`
- `parameter`
- `GraphQL`
- `REST`

Translate everything into plain English. Say "your site data" not "the API response". Say "reusable block" not "synced pattern". See the terminology table in `skills/accelerate/SKILL.md` for the full mapping.

### Tone

Speak like a helpful marketing consultant who happens to have access to their analytics. Lead with the recommendation, then the reason, then the data. Never dump raw data or explain which tool was called.

### Mutation safety

**Never create anything without showing the user exactly what is about to be created and asking them to confirm.** This applies to:

- A/B tests
- Audiences
- Personalisation rules
- Broadcasts

This is a hard rule. No exceptions, no "smart defaults" that skip confirmation.

### Recommendation volume

Present **2-3 prioritised recommendations**, not 10. Each one gets: what to do, where, why (grounded in the data just fetched), and what to measure. Use priority markers: 🔴 high / 🟡 medium / 🟢 low.

### Real data only

Every meaningful recommendation must be grounded in real site data fetched during the session. Never recommend based solely on generic marketing playbooks. If data is not available, say so plainly and suggest how to get it.

### What Accelerate is NOT

Do not build features or skills that make the toolkit feel like any of these:

- A developer toolkit or API explorer.
- A 1:1 wrapper over every Accelerate capability.
- A clone of the WordPress admin.
- A generic assistant for every WordPress task.
- A bloated catalog of thin commands.

If a new feature makes the project feel more technical, more scattered, or more like an internal console, it is probably the wrong feature.

### Skill shape

Skills should be **workflow-shaped** (guided multi-step jobs matching a marketer's real task), not **wrapper-shaped** (thin pass-throughs to individual capabilities). See `internal/SKILLS-REVIEW.md` for the full analysis of workflow-shaped vs wrapper-shaped design.

### Router discipline

Every user question must have one clear owner in the router (`skills/accelerate/SKILL.md`). If a new skill is added, update the router's routing table and disambiguation rules. Ambiguous routing fragments trust and makes the toolkit feel broken.

### Prioritisation ownership

"What should I do first?", "What changed?", "Where should I focus this week?" -- these **always** route to `accelerate-opportunities`. Never to `accelerate-review` (status) or `accelerate-diagnose` (root cause). This disambiguation is documented in the router and must be maintained.

### Traffic-level awareness

Always check total site traffic before recommending A/B tests:

- **Under ~1,000 weekly visitors:** only big changes (new headlines, page structures, offers).
- **1,000-10,000 weekly:** medium tests (headlines, CTA placement, social proof).
- **10,000+:** fine-grained tests become viable (button colour, copy word choice). Still lead with higher-impact ideas.

### What Accelerate does not support

Do not suggest capabilities that Accelerate cannot deliver:

- Multivariate testing (only A/B or A/B/n on one variable at a time).
- Revenue or transaction tracking (use "form submission" or "click CTA" instead).
- Heatmaps or session recordings.
- Cross-domain experiments (single WordPress site only).

---

## 8. Design Standards for A/B Test Variants

When any skill proposes A/B test variants, check them against `docs/design-standards.md` and the site's brand context file before presenting to the user.

### Requirements

- **Differentiation:** variants must be different enough from the control to produce a meaningful result. Score 3/6 or higher on the differentiation rubric in `docs/design-standards.md`.
- **Slug-first:** use preset slugs from the site's design system, never hardcoded colour values, font sizes, or spacing. If a site brand context file exists at `~/.config/accelerate-ai-toolkit/brand-<site-slug>.md`, consult it for available slugs.
- **No generic AI patterns:** no slop words, no banned anti-patterns. See the anti-pattern list in `docs/design-standards.md`.

### Practical checks

Before presenting a variant to the user:

1. Does it look meaningfully different from the control?
2. Does it use the site's actual design tokens (slugs), not arbitrary values?
3. Could a reader tell it was written specifically for this site, not copy-pasted from a generic template?

If any answer is "no", revise the variant before presenting.

---

## 9. Multi-Platform Awareness

The toolkit targets multiple agent platforms. When adding features or skills:

- **Claude Code:** primary target. Skills live in `skills/`, manifest in `.claude-plugin/plugin.json`.
- **Codex CLI:** secondary target. Manifest in `.codex-plugin/`. Same shared `skills/` directory.
- **Cursor:** roadmap. Will reference shared `skills/`.
- **Gemini:** roadmap. Will use `gemini-extension.json`.

Skills should remain **vendor-agnostic** wherever possible. Avoid platform-specific tool names in skill bodies (e.g. prefer "the connected server" over "mcp__wordpress__..."). Platform-specific wiring belongs in router skills and connection commands, not in workflow skills.

---

## Quick Reference: The Rules That Matter Most

1. **Kebab-case names everywhere.** Plugin, marketplace, skills.
2. **Bump the version.** No bump = no update for users.
3. **Skills at root, not inside .claude-plugin/.**
4. **Description under 1,536 chars.** Front-load the key use case.
5. **SKILL.md under 500 lines.** Reference material in separate files.
6. **No banned words in user output.** API, schema, MCP, JSON, etc.
7. **Confirm before every mutation.** Tests, audiences, personalisation.
8. **2-3 recommendations, not 10.** Grounded in real data.
9. **Problem-first positioning.** Name the enemy, not the features.
10. **Validate before submitting.** `claude plugin validate .`
