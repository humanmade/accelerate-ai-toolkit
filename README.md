# Accelerate AI Toolkit

Every WordPress analytics plugin shows you numbers. None of them tell you what to change, help you change it safely, and report back on whether it worked.

This toolkit closes that loop. Ask your [Accelerate](https://www.accelerateplugin.com/) site what to fix. It diagnoses the problem, recommends a test, creates it for you, and tracks the result. One conversation, from insight to action to outcome.

> Built for marketers, not developers. No dashboards. No spreadsheets. No code.

---

## What a session looks like

You open Claude Code and ask:

> *"Which landing page needs the most work?"*

The toolkit pulls your real traffic data, finds the page with the worst bounce-to-conversion ratio, explains why it's underperforming, and proposes 2-3 testable improvements. You say "set up that A/B test" and it creates the test, applies your brand's design standards, and confirms before publishing. A week later, you ask "did it work?" and get a clear verdict with the numbers behind it.

**More things you can ask:**

- *"How is my site doing this week?"* - performance snapshot, not a wall of charts
- *"What should I do first?"* - prioritised recommendations backed by your data
- *"What's driving the traffic spike right now?"* - real-time investigation
- *"Should I personalise content for visitors from Google?"* - audience analysis with a clear yes/no
- *"Which campaign is converting best this month?"* - attribution breakdown, first-touch vs last-touch

---

## Install

```bash
claude plugin install accelerate-ai-toolkit
```

Then connect your site:

```
/accelerate-connect
```

The command walks you through generating a WordPress Application Password and saving it securely. Run `/accelerate-status` to verify the connection, then ask your first question.

<details>
<summary><strong>Requirements</strong></summary>

- WordPress 6.9+ with [Accelerate](https://www.accelerateplugin.com/) 4.1+ (Abilities API enabled)
- [WordPress MCP Adapter](https://github.com/WordPress/mcp-adapter) plugin (0.4.1+) installed and active on the site
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [Codex CLI](https://github.com/openai/codex)
- Node.js 18+

**Note:** The MCP Adapter's default endpoint (`/mcp/mcp-adapter-default-server`) does not match what the toolkit's transport layer expects (`/wp/v2/wpmcp`). You'll need to add a small mu-plugin to remap it — `/accelerate-connect` will detect this and walk you through it.

</details>

<details>
<summary><strong>Install from source</strong></summary>

```bash
git clone https://github.com/humanmade/accelerate-ai-toolkit.git
cd accelerate-ai-toolkit
claude plugin install ./
```

For Codex CLI: run `codex`, open `/plugins`, choose "Install from local path".

</details>

---

## How it works

The toolkit is not a wrapper around your analytics API. It's 12 purpose-built workflows that compose raw data into decisions:

| Workflow | What it does |
|----------|-------------|
| **Review** | Site performance snapshot: visitors, bounce rate, top pages, traffic breakdown |
| **Diagnose** | Root-cause analysis: why a page is bouncing, where traffic is mismatched |
| **Opportunities** | The front door: synthesises everything into 3 ranked next actions |
| **Optimize landing page** | Deep-dive on one page: engagement metrics, 2-3 testable improvements, A/B test hand-off |
| **Test** | Full A/B test lifecycle: plan, create, monitor, review, declare a winner |
| **Personalize** | Audience creation and content personalization: by referrer, geography, behaviour, device |
| **Content plan** | Proposes upcoming posts grounded in what's actually working on your site |
| **Realtime** | What's happening right now: concurrent visitors, trending content, spike investigation |
| **Campaigns** | Attribution analysis: source breakdown, UTM performance, channel comparison |

A **router skill** reads your question and sends it to the right workflow automatically. For complex investigations ("why did conversions drop last month?"), a specialised **analyst agent** runs multi-step research across several data sources and reports back with findings, interpretation, and concrete next steps.

Every workflow that creates or changes something (A/B tests, personalization rules, audiences) asks for your explicit confirmation first. Nothing ships without your say-so.

---

## Supported agents

| Agent | Status |
|---|---|
| Claude Code | ✅ v1 |
| Codex CLI | ✅ v1 |
| Cursor | 🚧 Roadmap |
| Gemini | 🚧 Roadmap |

All skills are vendor-agnostic and live in a shared `/skills/` directory. See [ROADMAP.md](./prd/ROADMAP.md) for what's coming next.

---

## Documentation

- [Installation guide](./docs/installation.md)
- [Authentication & security](./docs/authentication.md)
- [All 38 Accelerate capabilities](./docs/ability-reference.md)
- [Adding your own skills](./docs/skill-development.md)
- [Design standards for A/B test variants](./docs/design-standards.md)

---

Built by [Human Made](https://humanmade.com/) · MIT License
