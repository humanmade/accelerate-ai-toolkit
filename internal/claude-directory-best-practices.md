# Claude Plugin Directory: Best Practices Analysis

> Research date: 2026-04-12
> Source: https://claude.com/plugins (60+ plugins analyzed)
> Scope: Top 20 plugins by install count, 12 GitHub READMEs, plugin submission docs

---

## Table of Contents

1. [Directory Landscape](#1-directory-landscape)
2. [How the Directory Works](#2-how-the-directory-works)
3. [Plugin Detail Page Anatomy](#3-plugin-detail-page-anatomy)
4. [Top 20 Plugin Deep-Dive](#4-top-20-plugin-deep-dive)
5. [GitHub README Analysis (12 Repos)](#5-github-readme-analysis-12-repos)
6. [Pattern Synthesis: What Separates Tiers](#6-pattern-synthesis-what-separates-tiers)
7. [Marketing Language Patterns](#7-marketing-language-patterns)
8. [The "How to Use" Section Formula](#8-the-how-to-use-section-formula)
9. [Concrete Recommendations & Checklist](#9-concrete-recommendations--checklist)

---

## 1. Directory Landscape

### Full Ranking: Top 40 Plugins by Installs

| Rank | Plugin | Installs | Author | Verified | Type |
|------|--------|----------|--------|----------|------|
| 1 | Frontend Design | 455,628 | Anthropic | Yes | Skills |
| 2 | Superpowers | 355,657 | Jesse Vincent | Yes | Skills Framework |
| 3 | Context7 | 231,346 | Upstash | Yes | MCP Server |
| 4 | Code Review | 212,871 | Anthropic | Yes | Skills |
| 5 | Code Simplifier | 178,204 | Anthropic | Yes | Skills |
| 6 | GitHub | 172,828 | GitHub | No | MCP Server |
| 7 | Feature Dev | 155,235 | Anthropic | Yes | Skills |
| 8 | Playwright | 150,132 | Microsoft | No | MCP Server |
| 9 | Skill Creator | 131,592 | Anthropic | Yes | Skills |
| 10 | Ralph Loop | 129,572 | Anthropic | Yes | Hooks/Skills |
| 11 | CLAUDE.md Management | 125,973 | Anthropic | Yes | Skills |
| 12 | TypeScript LSP | 125,780 | Anthropic | Yes | LSP |
| 13 | Security Guidance | 107,637 | Anthropic | Yes | Hooks |
| 14 | Commit Commands | 102,020 | Anthropic | Yes | Skills |
| 15 | Figma | 88,279 | Figma | No | MCP Server |
| 16 | Claude Code Setup | 73,178 | Anthropic | Yes | Skills |
| 17 | PR Review Toolkit | 68,342 | Anthropic | Yes | Skills |
| 18 | Serena | 66,889 | Oraios | No | MCP Server |
| 19 | Pyright LSP | 63,965 | Anthropic | Yes | LSP |
| 20 | Supabase | 55,887 | Supabase | No | MCP Server |
| 21 | Atlassian | 50,176 | Atlassian | No | MCP Server |
| 22 | Agent SDK Dev | 44,758 | Anthropic | Yes | Skills |
| 23 | Telegram | 44,480 | — | No | MCP Server |
| 24 | Explanatory Output Style | 41,601 | Anthropic | Yes | Skills |
| 25 | Plugin Developer Toolkit | 40,965 | Anthropic | Yes | Skills |
| 26 | Slack | 40,012 | Anthropic | Yes | MCP Server |
| 27 | Greptile | 38,217 | Greptile | No | MCP Server |
| 28 | Vercel | 35,662 | Vercel | No | MCP Server |
| 29 | Hookify | 35,549 | Anthropic | Yes | Hooks |
| 30 | Playground | 33,613 | Anthropic | Yes | Skills |
| 31 | Linear | 28,316 | — | No | MCP Server |
| 32 | Learning Output Style | 27,214 | Anthropic | Yes | Skills |
| 33 | Go LSP (gopls) | 24,996 | Anthropic | Yes | LSP |
| 34 | C# LSP | 24,783 | Anthropic | Yes | LSP |
| 35 | Sentry | 22,673 | Sentry | No | MCP Server |
| 36 | GitLab | 22,313 | — | No | MCP Server |
| 37 | Rust Analyzer LSP | 21,324 | Anthropic | Yes | LSP |
| 38 | Chrome DevTools | 20,829 | — | No | MCP Server |
| 39 | Stripe | 20,268 | Stripe | No | MCP Server |
| 40 | Java LSP | 19,442 | Anthropic | Yes | LSP |

### Key Observations

- **Anthropic dominates**: 20 of top 40 are Anthropic-verified first-party plugins
- **First-party advantage**: Average installs for Anthropic plugins = ~120K; third-party = ~50K
- **MCP servers are the most common third-party type**: GitHub, Playwright, Figma, Serena, Supabase, Atlassian, etc.
- **Skills-only plugins can win**: Frontend Design (#1), Superpowers (#2), Code Review (#4) are all skills-based
- **Brand name matters**: GitHub (172K), Playwright/Microsoft (150K), Figma (88K) — big names pull installs even without verification badges
- **The 100K threshold**: Only 14 plugins cross 100K installs. Getting above this requires either Anthropic verification or a strong brand

---

## 2. How the Directory Works

### Directory Page Structure

The directory at `claude.com/plugins` shows:
- **Grid of plugin cards** with: name, short tagline, verification badge, install count
- **Filters**: "Works with" (Cowork, Claude Code)
- **Search bar** (text search)
- **"Submit your plugin"** CTA with link to `clau.de/plugin-directory-submission`

### Plugin Submission Requirements

From the official docs (`code.claude.com/docs/en/plugins`):

**plugin.json manifest fields:**
- `name` — unique identifier and skill namespace
- `description` — shown in plugin manager when browsing/installing
- `version` — semantic versioning
- `author` — name (optional but helpful for attribution)
- `homepage` — link to docs/website
- `repository` — link to GitHub repo
- `license` — license type

**Submission paths:**
- `claude.ai/settings/plugins/submit`
- `platform.claude.com/plugins/submit`

**Plugin components:**
- `skills/` — SKILL.md files (slash commands + auto-invoked skills)
- `agents/` — custom agent definitions
- `hooks/` — event handlers (hooks.json)
- `.mcp.json` — MCP server configurations
- `.lsp.json` — LSP server configurations
- `bin/` — executables added to PATH
- `settings.json` — default settings

---

## 3. Plugin Detail Page Anatomy

Every plugin detail page on `claude.com/plugins/<name>` has the same structure:

### Fields Present

| Field | Source | Notes |
|-------|--------|-------|
| **Plugin name** | plugin.json `name` | Displayed as title |
| **Short tagline** | Appears in directory cards | ~20-30 words, shown in grid view |
| **Verification badge** | Anthropic review | "Anthropic Verified" label |
| **"Install in" button** | Auto-generated | Links to Claude Code install |
| **"Made by"** | plugin.json `author` | Linked to author URL |
| **Install count** | Auto-tracked | Cumulative installs |
| **Video placeholder** | Optional | "Play video" button (most show placeholder) |
| **Long description** | Submitted content | 3-5 paragraphs, supports **bold** and formatting |
| **"How to use" section** | Part of long description | Usually last paragraph(s) |
| **Related plugins** | Auto-generated | 4 related plugins shown |

### Character/Format Constraints (Observed)

- **Short tagline**: ~100-160 characters (one sentence max)
- **Long description**: 3-5 paragraphs typical, ~150-300 words
- **Supports**: Bold text, line breaks, paragraph breaks
- **Does NOT support**: Headers, bullet lists, code blocks, images, links in the body
- **"How to use"** is a convention, not a forced field — it's just bolded text in the description

---

## 4. Top 20 Plugin Deep-Dive

### Tier 1: The Mega-Plugins (200K+ installs)

#### #1 Frontend Design (455K) — Anthropic

**Short tagline:** "Craft production-grade frontends with distinctive design. Generates polished code that avoids generic AI aesthetics."

**Description strategy:** Problem-first positioning. Opens by naming the enemy (generic AI aesthetics), then presents the solution (design framework before coding). Lists specific aesthetic directions (brutalist, maximalist, retro-futuristic). Key design areas spelled out with specifics.

**How to use:** "Simply ask Claude to build frontend interfaces and this skill activates automatically." Three example prompts with specific contexts (music streaming, AI security startup, settings panel with dark mode).

**Why it wins:**
- Solves a **higher-order problem** — not "generate code" but "generate code that doesn't look like AI made it"
- Zero-friction activation — works automatically, no slash command needed
- Aspirational language: "bold aesthetic choices," "distinctive typography," "production-grade"
- Specific, imaginative example prompts that spark ideas

---

#### #2 Superpowers (355K) — Jesse Vincent (obra)

**Short tagline:** "Claude learns brainstorming, subagent development with code review, debugging, TDD, and skill authoring through Superpowers."

**Description strategy:** Methodology-first. Presents a structured software development philosophy (TDD, systematic debugging, Socratic brainstorming). Emphasizes disciplined practices and frameworks, not features.

**How to use:** Slash commands with workflow progression (`/brainstorming` then `/execute-plan`). Describes the code-reviewer agent role.

**GitHub README (github.com/obra/superpowers):**
- Narrative opening: "It starts from the moment you fire up your coding agent..."
- Story-driven: walks through what happens step by step
- Multi-platform install (Claude Code, Amplifier, Codex, etc.)
- "Verify Installation" section — tells you exactly how to test
- Personal voice: "Thanks! - Jesse"
- 147K GitHub stars
- Discord community link
- Sponsorship section ("If Superpowers has helped you do stuff that makes money...")

**Why it wins:**
- Not selling features — selling a **development philosophy**
- "Enforces disciplined practices" appeals to senior developers
- The GitHub README tells a story instead of listing features
- Huge open-source social proof (147K stars)
- Community (Discord) shows living ecosystem
- Personal author voice builds trust

---

#### #3 Context7 (231K) — Upstash

**Short tagline:** "Upstash Context7 MCP server for live docs lookup. Pull version-specific docs and code examples from source repos into LLM context."

**Description strategy:** Pain-point-first. Opens with "solves a common problem with LLMs: outdated training data leading to hallucinated APIs." Then explains the two tools and how they work.

**How to use:** Dead simple — "add 'use context7' to any prompt." Two real-world example prompts with full sentences.

**GitHub README (github.com/upstash/context7):**
- Opens with "Context7 Platform — Up-to-date code documentation for LLMs and AI code editors"
- Structured as: What → Why → How → Install
- Clean, focused, ~560 lines

**Why it wins:**
- Extremely clear value prop: "your training data is outdated, this fixes it"
- Lowest possible friction: just add "use context7" to any prompt
- Names the specific problem (hallucinated APIs) and specific solution (live docs from source)
- Strong brand (Upstash)

---

#### #4 Code Review (212K) — Anthropic

**Short tagline:** "AI code review with specialized agents and confidence-based filtering for pull requests"

**Description strategy:** Architecture-first. Explains the five independent reviewers, the 0-100 confidence scale, and the 80-threshold default. Emphasizes what it filters out (noise, false positives).

**How to use:** "Run `/code-review` on any PR branch." Customization options mentioned.

**Why it wins:**
- Solves a meta-problem: not just "review code" but "review code without drowning in false positives"
- Specific numbers (5 reviewers, 0-100 scale, 80 threshold) build credibility
- "Dramatically reducing false positives" — addresses the #1 complaint about AI code review
- Intelligent skip logic (draft PRs, automated PRs) shows sophistication

---

### Tier 2: The Strong Performers (100K-200K installs)

#### #5 Code Simplifier (178K) — Anthropic

**Tagline:** "Code clarity agent: simplifies and refines recently modified code while preserving functionality and consistency."

**Key insight:** Proactive — works on your recent changes automatically. You don't invoke it; it watches what you do.

---

#### #6 GitHub MCP (172K) — GitHub

**Tagline:** "Official GitHub MCP server for repo management. Create issues, manage PRs, review code, search repos, and access GitHub's API from Claude Code."

**GitHub README (github.com/github/github-mcp-server):**
- "GitHub's official MCP Server" — authority positioning
- Extensive (~1,900 lines) with full API reference
- Multiple installation methods
- Comprehensive tool documentation

**Key insight:** Brand authority + "official" label does heavy lifting. The README is a reference doc, not a marketing piece — because it doesn't need to sell.

---

#### #7 Feature Dev (155K) — Anthropic

**Tagline:** "Feature development workflow with agents for exploration, design, and review"

**Key insight:** Structured 7-phase workflow. Three named agents (code-explorer, code-architect, code-reviewer). Appeals to developers who want guardrails on feature development.

---

#### #8 Playwright (150K) — Microsoft

**Tagline:** "Browser automation and end-to-end testing MCP server by Microsoft. Enables Claude to interact with web pages, take screenshots, fill forms, and automate testing workflows."

**GitHub README (github.com/microsoft/playwright-mcp):**
- Technical, comprehensive (~1,700 lines)
- Multi-client setup (VS Code, Cursor, Claude Code, etc.)
- "Accessibility data rather than screenshots" — unique differentiator called out early
- Tool reference with detailed capabilities

**Key insight:** Microsoft brand + clear technical differentiator (accessibility tree, not screenshots). README is documentation, not marketing.

---

#### #9-14: Anthropic Skills Bundle

Skill Creator (131K), Ralph Loop (129K), CLAUDE.md Management (125K), TypeScript LSP (125K), Security Guidance (107K), Commit Commands (102K) — all Anthropic-verified.

**Common pattern:** Short, clear taglines. Focused single-purpose tools. "How to use" with specific slash commands. Anthropic verification badge provides trust.

---

### Tier 3: The Brand-Powered Mid-Tier (50K-100K installs)

#### #15 Figma (88K) — Figma

**Tagline:** "Figma integration: access design files, extract components, read tokens, translate to code. Bridge design-development gap."

**GitHub README (github.com/figma/mcp-server-guide):**
- "Figma MCP Server Guide" — positions as a guide, not just docs
- Features section with bold subheadings
- Client-specific installation (VS Code, Cursor, Claude Code, Gemini)
- "Prompting your MCP client" section with tips
- 16+ individual tools documented
- "MCP best practices" section — positions Figma as expert

**Key insight:** Multiple slash commands (`/implement-design`, `/create-design-system-rules`, `/code-connect-components`) give it breadth. The "bridge design-development gap" tagline nails the value prop.

---

#### #18 Serena (66K) — Oraios

**Tagline:** "Semantic code analysis MCP server for intelligent code understanding, refactoring, and navigation via language server protocol."

**GitHub README (github.com/oraios/serena):**
- Logo + tagline: "Serena is the IDE for your coding agent"
- Strong positioning statement: "agent-first design"
- Embedded demo videos before installation
- "Details" dropdowns for progressive disclosure
- 30+ programming language support highlighted
- 22.8K GitHub stars, 144 contributors

**Key insight:** "The IDE for your coding agent" is a brilliant positioning line. Demo videos are placed strategically before install instructions. Shows the result before asking for commitment.

---

#### #20 Supabase (55K) — Supabase

**Tagline:** "Supabase MCP: Database ops, auth, storage, real-time. Manage projects, run SQL, interact with your backend."

**GitHub README (github.com/supabase-community/supabase-mcp):**
- "Connect Supabase to your AI assistants" — benefit-first
- 20+ tools listed for breadth
- Natural language examples for all operations
- TypeScript type generation highlighted as unique feature

**Key insight:** Breadth positioning (20+ tools) works for platform integrations. "Natural conversation" framing makes complex DB ops feel accessible.

---

### Tier 4: Mid-Tier Third-Party (20K-50K installs)

#### Atlassian (50K)

**GitHub README (github.com/atlassian/atlassian-mcp-server):**
- Logo at top — visual anchor
- Enterprise-grade structure: Supported clients → Prerequisites → Data & security → Workflows → Tips → Admin notes
- 22+ sections, deeply hierarchical
- Real-world workflow examples (Jira, Confluence, Compass)
- Admin notes section targets decision-makers
- "Tips and tricks" section shows maturity

**Key insight:** Enterprise README = sales document. Comprehensive depth compensates for less exciting value prop.

---

#### Vercel (35K)

**GitHub README (github.com/vercel/vercel-mcp-overview):**
- Single sentence hook: "Vercel's official MCP server gives AI tools secure access to your Vercel projects."
- Quick Start as section #2
- URL-based connection (https://mcp.vercel.com — no local setup)
- Only ~332 lines — extremely minimal
- Links out to comprehensive docs at vercel.com/docs

**Key insight:** Highest efficiency ratio (105 installs/line). Brand authority + hosted service + extreme minimalism. Delegates depth to external docs. Only works if you have a known brand.

---

#### Sentry (22K)

**GitHub README (github.com/getsentry/sentry-mcp):**
- Audience-first hook: "primarily designed for human-in-the-loop coding agents"
- Deployed service ready (https://mcp.sentry.dev)
- Both remote + stdio transport options
- Claude Code Plugin installation prominently featured
- Dev notes on AI-powered search (transparency)

**Key insight:** Audience-first positioning ("for human-in-the-loop coding agents") is unique and specific.

---

#### PostHog (6K)

**GitHub README (github.com/PostHog/mcp):**
- Archived/redirected to monorepo — signals abandonment
- Minimal content, no story, no depth

**Key insight:** Archived repos kill installs. Even a redirect feels like neglect.

---

## 5. GitHub README Analysis (12 Repos)

### Structural Patterns Across All READMEs

| Element | Top Tier (200K+) | Mid Tier (50-200K) | Lower Tier (<50K) |
|---------|-------------------|---------------------|---------------------|
| **Opening line** | Problem/benefit-first | Feature-first | Definition-first |
| **Install position** | Section 2-3 | Section 2-4 | Varies widely |
| **Multi-platform install** | Always | Usually | Sometimes |
| **Example prompts** | Specific, contextual | Generic | Often missing |
| **Demo/video** | Sometimes | Rarely | Never |
| **Social proof** | Stars, community | Some stars | Minimal |
| **Personal voice** | Strong (Superpowers) | Corporate | Neutral |
| **Verification step** | Yes | Sometimes | Rarely |
| **Contributing guide** | Yes | Yes | Sometimes |

### README Length vs. Installs

| Plugin | README Lines | Installs | Installs/Line |
|--------|-------------|----------|---------------|
| Superpowers | ~615 | 355K | 577 |
| Context7 | ~563 | 231K | 410 |
| Vercel | ~332 | 35K | 105 |
| Serena | ~663 | 66K | 100 |
| Atlassian | ~654 | 50K | 76 |
| Supabase | ~717 | 55K | 77 |
| GitHub MCP | ~1,887 | 172K | 91 |
| Playwright | ~1,679 | 150K | 89 |
| Sentry | ~655 | 22K | 34 |
| Linear | ~492 | 28K | 57 |
| Figma | ~970 | 88K | 91 |
| PostHog | ~396 | 6K | 15 |

**Takeaway:** README length alone doesn't predict success. Superpowers and Context7 achieve highest efficiency with focused, story-driven READMEs under 650 lines. Massive reference docs (GitHub MCP, Playwright) work for established brands but aren't necessary.

---

## 6. Pattern Synthesis: What Separates Tiers

### The 5 Differentiators

#### 1. Problem-First vs Feature-First Positioning

**Top tier plugins solve a named problem:**
- Frontend Design: "avoids generic AI aesthetics"
- Context7: "outdated training data leading to hallucinated APIs"
- Code Review: "false positives and review noise"
- Superpowers: "undisciplined, ad-hoc development"

**Mid/lower tier plugins describe what they do:**
- Atlassian: "Connect to Jira & Confluence"
- Linear: "create issues, manage projects, update statuses"
- Sentry: "Access error reports, analyze stack traces"

**The gap:** Top plugins name an enemy. Lower plugins describe features.

---

#### 2. Unified Philosophy vs Feature List

**Top tier has a methodology:**
- Superpowers: TDD + systematic debugging + Socratic brainstorming
- Frontend Design: Design framework (purpose → audience → aesthetic direction) before coding
- Code Review: 5-agent parallel review with confidence scoring
- Feature Dev: 7-phase structured workflow

**Lower tier has a feature list:**
- Supabase: "20+ tools for managing your infrastructure"
- PostHog: "27+ tools, 10+ commands"
- Atlassian: "Search, create, update issues and docs"

**The gap:** Methodology implies expertise and thought leadership. Feature lists imply commodity.

---

#### 3. Zero/Low Friction Activation

**Top tier makes it effortless:**
- Frontend Design: Activates automatically — "simply ask Claude to build frontend interfaces"
- Context7: "add 'use context7' to any prompt"
- Code Review: Single `/code-review` command
- Code Simplifier: Works proactively on recent changes

**Lower tier requires setup:**
- Figma: OAuth, API keys, Figma URLs
- Atlassian: OAuth 2.1, site configuration, API tokens
- Sentry: Auth token, project configuration

**The gap:** Every setup step is a dropout point. The top plugins have near-zero activation energy.

---

#### 4. Specific, Imaginative Example Prompts

**Top tier examples spark imagination:**
- Frontend Design: "Create a dashboard for a music streaming app", "Build a landing page for an AI security startup"
- Context7: "Create a Next.js middleware that checks for a valid JWT in cookies. use context7"
- Code Review: "customize confidence threshold or focus areas (security, performance, accessibility)"

**Lower tier examples are generic:**
- Linear: "create an issue", "update status"
- Supabase: "List all my projects", "Run a SQL query"
- Sentry: "show me failed GitHub Actions runs"

**The gap:** Top tier examples show *what's possible*. Lower tier examples show *what buttons exist*.

---

#### 5. Trust Signals

**Highest-trust signals (in order of impact):**
1. **Anthropic Verified badge** — strongest signal in the directory
2. **Brand name recognition** (GitHub, Microsoft, Figma, Supabase)
3. **GitHub stars** (Superpowers: 147K, Serena: 22.8K)
4. **Contributor count** (shows community health)
5. **Personal author voice** (Superpowers: "Thanks! - Jesse")
6. **Community channels** (Discord, GitHub Discussions)
7. **Demo videos** (Serena places these before install)

---

## 7. Marketing Language Patterns

### Words That Win (Used by 200K+ Plugins)

| Category | High-Performers Use | Low-Performers Use |
|----------|--------------------|--------------------|
| **Outcomes** | "production-grade," "distinctive," "polished" | "access," "manage," "connect" |
| **Problems** | "avoids generic," "reduces noise," "prevents false positives" | (don't name problems) |
| **Specificity** | "brutalist, maximalist, retro-futuristic" | "various options" |
| **Authority** | "methodology," "framework," "disciplined practices" | "tools," "features," "capabilities" |
| **Action** | "crafts," "enforces," "pulls," "activates" | "provides," "enables," "supports" |
| **Simplicity** | "simply ask," "just add," "automatically" | "configure," "set up," "connect your account" |

### Tagline Formulas That Work

**Formula 1: [Outcome] without [pain point]**
- "Craft production-grade frontends with distinctive design" (avoids generic aesthetics)
- "Live docs lookup — pull version-specific docs" (avoids hallucinated APIs)

**Formula 2: [Action verb] + [specific what] + [for whom/when]**
- "AI code review with specialized agents and confidence-based filtering for pull requests"
- "Semantic code analysis MCP server for intelligent code understanding"

**Formula 3: [Tool] learns/gains [capability] through [method]**
- "Claude learns brainstorming, subagent development with code review, debugging, TDD"

### Words to Avoid

- "Access" — passive, implies friction
- "Various" / "multiple" — vague
- "Provides" — weak verb
- "Integration" — commodity word
- "Supports" — passive, implies limitation
- Feature count as selling point ("27+ tools") — commodity positioning

---

## 8. The "How to Use" Section Formula

Every top plugin follows the same pattern in the directory detail page:

### The Winning Structure

```
Paragraph 1: What it is + what problem it solves (2-3 sentences)
Paragraph 2: How it works under the hood (architecture, agents, methodology)
Paragraph 3: Key features/capabilities with **bold** emphasis
**How to use:** [activation method]. [2-4 example prompts with specific contexts].
```

### Activation Methods (Ranked by Friction)

1. **Auto-activation** — "Simply ask Claude to... and this skill activates automatically" (Frontend Design)
2. **Keyword injection** — "Add 'use context7' to any prompt" (Context7)
3. **Single slash command** — "Run `/code-review` on any PR branch" (Code Review)
4. **Multiple slash commands** — "Use `/implement-design`, `/create-design-system-rules`" (Figma)
5. **Guided workflow** — "Run `/feature-dev` to start the guided workflow" (Feature Dev)
6. **Account connection** — "After connecting your [X] account..." (Supabase, Atlassian)

### Example Prompt Qualities

**Good examples are:**
- Specific: "Create a dashboard for a music streaming app" (not "create a dashboard")
- Contextual: "Create a Next.js middleware that checks for a valid JWT in cookies"
- Imaginative: "Build a landing page for an AI security startup"
- Complete sentences: Shown as natural language the user would actually type

**Bad examples are:**
- Generic: "create an issue"
- Terse: "list projects"
- Feature-focused: "use the search tool"

---

## 9. Concrete Recommendations & Checklist

### For Directory Listing Optimization

#### Short Tagline (shown in grid cards)

- [ ] Under 160 characters
- [ ] Leads with an action verb or outcome, not "A plugin that..."
- [ ] Names the specific problem it solves OR the specific outcome it delivers
- [ ] Avoids generic words (access, manage, various, integration)
- [ ] Uses power words (craft, enforce, pull, automate, generate)

**Formula:** `[Action verb] [specific outcome]. [Unique differentiator or anti-pain-point].`

**Example:** "Craft production-grade frontends with distinctive design. Generates polished code that avoids generic AI aesthetics."

---

#### Long Description (detail page)

- [ ] **Paragraph 1:** Problem statement + solution (what pain does this eliminate?)
- [ ] **Paragraph 2:** Architecture/methodology (how does it work differently?)
- [ ] **Paragraph 3:** Key capabilities with **bold text** for scanability
- [ ] **"How to use:" section** with:
  - [ ] Lowest-friction activation method stated first
  - [ ] 3-4 example prompts that are specific and imaginative
  - [ ] Example prompts that show *what's possible*, not just what buttons exist
- [ ] Total length: 150-300 words (3-5 paragraphs)
- [ ] No jargon without context
- [ ] Names the problem/enemy explicitly

---

#### GitHub README

- [ ] **Line 1:** Logo/banner (if available)
- [ ] **Line 2-3:** One-sentence tagline that's benefit-driven
- [ ] **Section 1:** What it does + why (problem it solves)
- [ ] **Section 2:** How it works (brief architecture or methodology)
- [ ] **Section 3:** Installation (multi-platform, copy-paste ready)
- [ ] **Section 4:** Quick Start / Verify Installation
- [ ] **Section 5:** Usage examples (specific, contextual prompts)
- [ ] **Section 6+:** Deep documentation (tools reference, API, etc.)
- [ ] **Final sections:** Contributing, Community, License
- [ ] Verification step: "To verify it works, try..."
- [ ] Demo video or GIF before installation section
- [ ] Progressive disclosure (details/dropdowns for deep content)
- [ ] Personal voice where appropriate
- [ ] Social proof: stars badge, contributor avatars, community link
- [ ] Total: 500-700 lines for focused plugins, 1000+ for platforms

---

#### Trust & Social Proof

- [ ] Apply for Anthropic Verified badge (biggest single lever)
- [ ] GitHub stars badge in README
- [ ] Contributor count/avatars visible
- [ ] Community channel (Discord, GitHub Discussions)
- [ ] "Used by" or testimonial section if applicable
- [ ] Demo video showing the plugin in action
- [ ] Clear author attribution with link

---

#### Friction Reduction

- [ ] Can be activated in one step (slash command or keyword)
- [ ] No account connection required for core functionality (if possible)
- [ ] Install is one command: `/plugin install <name>`
- [ ] "Verify it works" step included
- [ ] Auto-activation for skill-based plugins (no explicit invocation needed)

---

### The Positioning Ladder

Where you sit on this ladder determines your install ceiling:

| Level | Positioning | Install Ceiling | Example |
|-------|------------|-----------------|---------|
| 5 | **Paradigm shift** — changes how developers work | 400K+ | Frontend Design, Superpowers |
| 4 | **Problem eliminator** — removes a specific, named pain | 200K+ | Context7, Code Review |
| 3 | **Capability unlock** — enables something previously impossible | 100K-200K | Playwright, GitHub MCP |
| 2 | **Workflow integration** — connects existing tools | 50K-100K | Figma, Supabase, Atlassian |
| 1 | **Feature list** — does X, Y, Z things | <50K | Linear, Sentry, PostHog |

**To climb the ladder:** Stop listing features. Name the problem. Present a methodology. Show the transformation.

---

### Quick Wins (Highest Impact, Lowest Effort)

1. **Rewrite the tagline** using the problem-first formula
2. **Add 3-4 imaginative example prompts** to the "How to use" section
3. **Add a demo video or GIF** to the GitHub README
4. **Add a "Verify Installation" section** to the README
5. **Replace "provides/enables/supports" with active verbs** (crafts, enforces, pulls, generates)
6. **Name the enemy** — what specific problem does this eliminate?
7. **Apply for Anthropic Verified** if eligible
8. **Add a one-line "what problem this solves" opener** to the README

---

## Appendix: GitHub Repos Analyzed

| Plugin | GitHub Repo | Stars |
|--------|-------------|-------|
| Superpowers | github.com/obra/superpowers | 147K |
| Context7 | github.com/upstash/context7 | — |
| GitHub MCP | github.com/github/github-mcp-server | — |
| Playwright | github.com/microsoft/playwright-mcp | — |
| Figma | github.com/figma/mcp-server-guide | — |
| Serena | github.com/oraios/serena | 22.8K |
| Supabase | github.com/supabase-community/supabase-mcp | — |
| Atlassian | github.com/atlassian/atlassian-mcp-server | — |
| Sentry | github.com/getsentry/sentry-mcp | — |
| Vercel | github.com/vercel/vercel-mcp-overview | — |
| PostHog | github.com/PostHog/mcp | — |
| Linear | github.com/jerhadf/linear-mcp-server | — |
