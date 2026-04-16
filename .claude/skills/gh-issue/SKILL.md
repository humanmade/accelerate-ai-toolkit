---
name: gh-issue
description: Fetch a GitHub issue and execute it in full context of the project's product standards, marketplace guidelines, and north star. Use when a contributor pastes an issue number to be implemented.
disable-model-invocation: true
argument-hint: "[issue-number]"
allowed-tools: Bash(gh *)
---

# Execute GitHub Issue

You are implementing a GitHub issue for the **Accelerate AI Toolkit** -- a Claude Code plugin for non-technical WordPress marketers. Thousands of users will install this plugin from the official marketplace. Every change you make ships to real people, so quality, consistency, and restraint matter more than speed.

## Issue context

```!
gh issue view $ARGUMENTS --json number,title,body,labels,assignees,milestone,comments --jq '{number,title,body,labels: [.labels[].name], assignees: [.assignees[].login], milestone: .milestone.title, comments: [.comments[] | {author: .author.login, body: .body}]}'
```

## Before you touch any code

Read these files. They are your guardrails. Do not skip them.

1. **[internal/GUIDELINES.md](internal/GUIDELINES.md)** -- marketplace compliance, skill structure rules, naming conventions, banned words, mutation safety, design standards. This is the primary reference.
2. **[internal/NORTH-STAR.md](internal/NORTH-STAR.md)** -- product philosophy. What great looks like, what we will not become. Use this to judge whether the issue's intent aligns with the product direction.
3. **[internal/SKILLS-REVIEW.md](internal/SKILLS-REVIEW.md)** -- if the issue touches skills, read this for the rationale behind the current skill map and the benchmarks we measured against.
4. **[internal/ROADMAP.md](internal/ROADMAP.md)** -- if the issue references a roadmap item, read this for upstream dependencies and sequencing constraints.

Read any other files the issue references before starting work.

## How to work

### 1. Understand the issue

Read the issue title, body, and comments above. Identify:

- **What** needs to change (new skill, skill edit, docs, manifest, config, etc.)
- **Why** it matters (the user problem or product gap it addresses)
- **Where** it fits in the codebase (which files, which skills, which docs)
- **What it should NOT do** (scope boundaries -- if the issue is vague, be conservative)

### 2. Show the plan first

Before writing any code, present a short plan:

- Files to create or modify (with paths)
- What each change does in one line
- Anything you are intentionally NOT doing and why

Wait for confirmation before proceeding.

### 3. Make the change

Follow these rules while implementing:

- **Match existing patterns.** Read a neighbouring file before writing a new one. Skill frontmatter, section structure, tone, and terminology should be consistent with what already exists in `skills/`.
- **Marketer language only.** If the change produces user-facing output, it must pass the banned-words check in GUIDELINES.md section 7. No API, schema, MCP, JSON, tool call, ability, endpoint, parameter.
- **Mutation safety.** If the change creates, modifies, or deletes anything on the user's WordPress site, it must include an explicit confirmation gate. No exceptions.
- **Minimal footprint.** Change the least amount of code necessary. Do not refactor surrounding code, add speculative features, or "improve" things the issue did not ask for.
- **File formatting.** All text files must end with a final newline.
- **Skill size.** SKILL.md files must stay under 500 lines. Move reference material to separate files.
- **Skill descriptions.** Combined `description` + `when_to_use` must stay under 1,536 characters.
- **Kebab-case names.** Any new skill, command, or plugin name must be lowercase-letters-digits-hyphens only.
- **Version bump.** If the change affects the shipped plugin (skills, agents, commands, hooks, manifests), bump the patch version in `.claude-plugin/plugin.json`.
- **Router update.** If a new skill is added or an existing skill is renamed, update the routing table and disambiguation rules in `skills/accelerate/SKILL.md`.

### 4. Keep docs in sync

Every change has a documentation surface. Update it -- but keep it tight.

**What to update:**

- **README.md** -- if a user-visible workflow was added, removed, or renamed, update the workflow table. If a new slash command was added, mention it. But the README is a marketing document for end users, not a changelog or dev journal. One line in the right table row is usually enough. Never add implementation details, architecture notes, or contributor instructions to the README.
- **docs/** -- if the change affects installation, authentication, capabilities, skill development, or design standards, update the relevant doc file. These are reference docs for users; keep them factual and concise.
- **internal/** -- if the change reveals a new product principle, a constraint worth remembering, an upstream dependency, or a decision that future issues should know about, update the relevant internal doc (GUIDELINES.md, ROADMAP.md, SKILLS-REVIEW.md, NORTH-STAR.md). Internal docs are for us. They can be detailed.
- **CHANGELOG.md** -- if the version was bumped, add a brief entry describing what changed from the user's perspective.
- **Router** -- already covered in step 3, but restated: if a skill was added, removed, or renamed, the routing table in `skills/accelerate/SKILL.md` must reflect it.

**What NOT to do:**

- Do not add "developer setup" or "how to contribute" sections to the README. The README is for people installing the plugin, not building it.
- Do not duplicate information across files. If something is explained in `docs/authentication.md`, the README should link to it, not repeat it.
- Do not pad the README with badges, status tables, feature matrices, or screenshots that don't exist yet.
- Do not add verbose explanations for small changes. A one-line CHANGELOG entry and a one-cell table update are usually the right size.

**Rule of thumb:** if a user would notice the change, update user-facing docs. If only contributors would notice, update internal docs. If nobody would notice, don't update anything.

### 5. Verify

After making the change:

- If you created or modified a skill, confirm it has valid YAML frontmatter by reading it back.
- If you modified `plugin.json` or `marketplace.json`, confirm valid JSON.
- If you modified the router, confirm every skill in `skills/` has exactly one routing entry.
- If you updated the README or docs, re-read them to make sure they still read cleanly end-to-end -- no orphaned references, no stale workflow names, no broken links.
- Run `claude plugin validate .` if manifest files changed.

### 6. Summarise

When done, provide a short summary:

- What was changed and why
- Files created or modified (including any docs updated)
- Anything the issue asked for that you did NOT do, and why
- Suggested next steps if any remain
