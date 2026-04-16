# AGENTS.md

Instructions for any agent (Claude Code, Codex, Cursor, future agents) working **inside** this repo. Not for the marketer who runs the toolkit — that's `README.md`.

---

## Hard rules

1. **Never leak developer jargon to the user.** Banned in any skill output the marketer reads: "ability", "endpoint", "API", "MCP", "schema", "parameter", "JSON", "tool call", "WP_API_*". Internal skill bodies may use them; user-facing prose must not. Full translation table in `skills/accelerate/SKILL.md`.

2. **Skills are workflows, not capability wrappers.** Each skill composes multiple Accelerate capabilities into a marketer-meaningful job. Do not add a skill that just proxies a single capability — the reference skill (`skills/accelerate-abilities-reference/SKILL.md`) covers that layer.

3. **Confirm before mutating.** Any skill that creates, updates, or deletes anything must show the user exactly what it's about to do and wait for explicit confirmation. Reference patterns: `skills/accelerate-test/SKILL.md`, `skills/accelerate-personalize/SKILL.md`.

4. **Prioritisation belongs to `accelerate-opportunities`.** Questions like "what should I do first?", "what changed?", "where should I focus this week?", "give me a plan for this month" route to `accelerate-opportunities`. Not `accelerate-review` (that's status). Not `accelerate-diagnose` (that's root-cause for a known problem). The router in `skills/accelerate/SKILL.md` has a dedicated disambiguation section — respect it.

5. **Permission model is two tiers, not three.** `edit_posts` gates 35 analytics/experimentation capabilities. `manage_options` gates three admin capabilities (`stop-experiment`, `broadcast-content`, `export-events`). Verified in `../altis-accelerate/inc/abilities/namespace.php`. Do **not** reintroduce a fake `view_accelerate_analytics` read tier — it does not exist. A stricter read-only tier is an upstream ask tracked in `ROADMAP.md`.

6. **Do not add developer-facing skills.** This toolkit is for non-technical marketers. Developer workflows live in the sibling `altis-accelerate` repo's own `.claude/skills/`, not here.

7. **Do not modify `../altis-accelerate/`.** This repo is a consumer; that one is the producer. Upstream changes go through separate PRs to that repo, never from here.

8. **Do not invent capability names.** Before referencing any `accelerate/...` capability in a skill body, grep `../altis-accelerate/inc/abilities/*.php` for it. If there is no `wp_register_ability( 'accelerate/<name>'` match, the capability does not exist.

9. **Never commit without explicit user approval.** Per the user's global rules.

10. **No telemetry, no phone-home code, no tracking.** The toolkit explicitly ships with zero telemetry in v1.

11. **Never write credentials or `.env*` files inside the repo.** The canonical location is `~/.config/accelerate-ai-toolkit/env`, outside the repo, `chmod 600`.

---

## What this repo is

The Accelerate AI Toolkit is a vendor-agnostic Claude Code + Codex CLI plugin that gives non-technical marketers conversational access to a WordPress site running the Accelerate plugin. It wraps Accelerate's 38-capability Abilities API behind a set of workflow skills. Users install the toolkit into their agent, run `/accelerate-connect` once, then ask questions in plain English.

---

## Directory layout

```
accelerate-ai-toolkit/
├── .claude-plugin/               # Claude Code manifest + marketplace entry
├── .codex-plugin/                # Codex CLI manifest
├── .cursor-plugin/               # Stub — v1.1 roadmap
├── .mcp.json                     # MCP server wiring (do not edit casually)
├── agents/
│   └── accelerate-analyst.md     # Deep-dive sub-agent
├── commands/                     # Slash commands
├── docs/                         # Long-form human documentation
├── hooks/
│   └── hooks.json                # Claude Code safety hooks (see below)
├── skills/
│   ├── accelerate/               # Router (always visible)
│   ├── accelerate-connect/       # Setup walkthrough
│   ├── accelerate-opportunities/ # Prioritisation front door
│   ├── accelerate-review/        # Business check-in
│   ├── accelerate-diagnose/      # Underperformance root-cause
│   ├── accelerate-optimize-landing-page/
│   ├── accelerate-test/          # A/B lifecycle
│   ├── accelerate-personalize/   # Audiences + personalisation
│   ├── accelerate-content-plan/  # Content planning
│   ├── accelerate-realtime/      # Live monitoring
│   ├── accelerate-campaigns/     # UTM + attribution
│   └── accelerate-abilities-reference/  # Advanced reference
├── README.md                     # User-facing quickstart
├── ROADMAP.md                    # Future work
├── SKILLS-REVIEW.md              # Shopify/PostHog benchmark (context, not a target)
└── AGENTS.md                     # This file
```

12 workflow skills in v1. The sibling `../altis-accelerate/` checkout is authoritative for everything about the Abilities API.

---

## Key entry points

| File | Purpose |
|---|---|
| `skills/accelerate/SKILL.md` | Router + terminology + routing disambiguation. Every new skill must be added here. |
| `skills/accelerate-abilities-reference/SKILL.md` | Full internal reference for all 38 capabilities. Updated when capabilities change upstream. |
| `.mcp.json` | MCP transport wiring. Site-root `WP_API_URL`, `OAUTH_ENABLED: "false"`. Do not change casually. |
| `commands/accelerate-connect.md` | Credential setup slash command. |
| `commands/accelerate-status.md` | Connection health check. |
| `docs/skill-development.md` | Full tutorial for adding a skill. Read this before writing a new one. |
| `docs/ability-reference.md` | Human-readable capability catalogue. |
| `docs/authentication.md` | Credential flow and security model. |
| `docs/design-standards.md` | Design guardrails for variant proposals: anti-patterns, differentiation rubric, slug-first brand consistency, copy quality. |
| `hooks/hooks.json` | Claude Code safety hooks. Enforces backup-before-mutation and verify-after-creation for A/B tests. |
| `../altis-accelerate/inc/abilities/*.php` | **Source of truth** for capability names, inputs, outputs, and permissions. |

---

## When adding or editing a skill

Short checklist. Full tutorial lives in `docs/skill-development.md`.

- Folder name is kebab-case and matches the `name:` in frontmatter.
- Required frontmatter: `name`, `description`, `license: MIT`, `category`.
- For sub-skills that should not occupy startup attention budget: add `parent: accelerate` and `disable-model-invocation: true`. Only the router stays always-visible.
- `description:` must be keyword-dense. The router matches on it. Include every phrasing a user might say.
- User-facing prose obeys Hard Rule 1 (tone ban list).
- Workflow body cites real capability names — grep `../altis-accelerate/inc/abilities/*.php` to confirm each one exists.
- If the skill mutates, confirm before calling (Hard Rule 3).
- Update `skills/accelerate/SKILL.md` routing table to include the new skill.
- If the skill proposes variant content for A/B tests, it must apply the design standards from `docs/design-standards.md` and check brand consistency before presenting variants to the user.
- If the skill overlaps with an existing one, add an explicit "NOT for X — use Y instead" note to both descriptions.

---

## MCP transport contract

- `WP_API_URL` is the WordPress **site root** (e.g. `https://example.com`). Not a full `/wp-json/...` path. The `@automattic/mcp-wordpress-remote` client handles routing internally.
- `OAUTH_ENABLED: "false"` is set in `.mcp.json` so the Application Password flow works against upstream's new OAuth default.
- Credentials live in `~/.config/accelerate-ai-toolkit/env`, outside the repo, `chmod 600`.
- The canonical setup flow is `/accelerate-connect`. Do not invent alternatives.

Full details: `docs/authentication.md`.

---

## Anti-patterns (from the benchmark review)

See `SKILLS-REVIEW.md` for the full analysis. The short version:

- Do not copy Shopify's developer tone or GraphQL-validation rhythm. Shopify targets app developers; we target marketers.
- Do not copy PostHog's engineering surfaces (logs, SQL, error tracking, workspace) as top-level marketer skills. Those belong to product engineers, not marketers.
- Do not expand the slash-command catalogue without a clear discoverability reason. Keep `/accelerate-connect` and `/accelerate-status` and stop.
- Do not expose the raw capability catalogue as the primary surface. That's what `accelerate-abilities-reference` is for, and it stays hidden.

---

## Verification checklist (run before calling a change done)

- [ ] All JSON manifests parse: `.mcp.json`, `plugin.json`, `package.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `gemini-extension.json`, `hooks/hooks.json`.
- [ ] Every skill has valid frontmatter (at minimum `name` and `description`).
- [ ] Every file ends with a final newline.
- [ ] No banned words in user-facing skill prose (grep the ban list from Hard Rule 1).
- [ ] Skill count in `README.md` matches the actual number of folders in `skills/`.
- [ ] All cross-references updated after any rename (grep the repo for the old name).
- [ ] Every capability referenced in a skill body exists in `../altis-accelerate/inc/abilities/*.php`.
- [ ] The router (`skills/accelerate/SKILL.md`) mentions any new skill.

---

## Safety hooks (Claude Code only)

The `hooks/hooks.json` file defines prompt-based `PreToolUse` and `PostToolUse` hooks that fire on `mcp__wordpress__mcp-adapter-execute-ability` calls. These are a hard safety net for mutations — they enforce guardrails even if the AI skips skill instructions.

Currently implemented:

| Hook | When | What it does |
|---|---|---|
| `PreToolUse` | Before `create-ab-test` | Blocks the call if the agent hasn't backed up the target block's content first |
| `PostToolUse` | After `create-ab-test` | Verifies variants aren't empty; triggers rollback if they are |

**Why prompt-based, not command-based:** Command hooks would need SSH/WP-CLI access on the user's machine, which isn't guaranteed. Prompt-based hooks work everywhere because they instruct the AI to do the verification using the tools already available (MCP calls, WP-CLI if configured).

**Cross-vendor note:** The `hooks/` directory is Claude Code-specific. Codex CLI, Cursor, and Gemini ignore it. The skill-level guardrails in `skills/accelerate-test/SKILL.md` (backup, verify, rollback instructions) are the vendor-agnostic layer and apply everywhere. Hooks are an additional safety net for Claude Code users.

---

## Pointers

| For… | Read |
|---|---|
| User-facing quickstart | `README.md` |
| Future work | `ROADMAP.md` |
| Benchmark analysis against Shopify + PostHog | `SKILLS-REVIEW.md` |
| Installation walkthrough | `docs/installation.md` |
| Credential flow + security model | `docs/authentication.md` |
| Adding a skill (full tutorial) | `docs/skill-development.md` |
| Complete capability reference | `docs/ability-reference.md` |
| Upstream Abilities API source of truth | `../altis-accelerate/inc/abilities/` |
