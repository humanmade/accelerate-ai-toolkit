# Skills Review: Shopify + PostHog Benchmarks for Accelerate

Purpose: review the current Accelerate skill design against Shopify AI Toolkit and PostHog AI Plugin, specifically for a non-technical business and marketing audience, then recommend a better vNext skill map for Accelerate.

Reviewed implementation:

- `skills/accelerate/SKILL.md`
- `skills/accelerate-analyze/SKILL.md`
- `skills/accelerate-diagnose/SKILL.md`
- `skills/accelerate-optimize-landing-page/SKILL.md`
- `skills/accelerate-test/SKILL.md`
- `skills/accelerate-personalize/SKILL.md`
- `skills/accelerate-campaigns/SKILL.md`
- `skills/accelerate-brief/SKILL.md`
- `skills/accelerate-realtime/SKILL.md`
- `skills/accelerate-abilities-reference/SKILL.md`
- `agents/accelerate-analyst.md`
- `commands/accelerate-connect.md`
- `commands/accelerate-status.md`

## Executive summary

Accelerate already has the best audience fit of the three systems. Its router explicitly frames the user as a "non-technical marketer or site owner" and bans developer-language output like API, schema, MCP, JSON, and tool call (`skills/accelerate/SKILL.md:10-16`). That is the right product posture for Accelerate.

Shopify is not the model to copy for voice, shape, or front-door UX. It is a strong benchmark for taxonomy discipline, strict routing, and separation of generation from execution. Shopify's own toolkit is built around documentation lookup, schema validation, code generation, and CLI store execution, which is excellent for developers and the wrong primary UX for marketers.

PostHog is the stronger benchmark for breadth. Its plugin exposes a much wider operating surface, with direct entry points for experiments, insights, dashboards, errors, surveys, search, workspace, logs, and LLM analytics. That makes it feel like a conversational operating layer over the product. The useful lesson for Accelerate is not to copy feature flags or logs, but to notice that PostHog has clear "product area" front doors for the major jobs a user wants to do.

Accelerate's weakness is not tone. It is orchestration. The current skills do a good job once the user already knows the kind of thing they want, but there is no single strong owner for:

- "What should I improve first?"
- "What changed and what should I do now?"
- "Should I test or personalize something?"
- "Give me a plan for this month"

That is the main gap to fix.

Bottom line:

- Do not copy Shopify's developer-heavy skill style.
- Borrow Shopify's routing discipline.
- Borrow PostHog's breadth and operator posture, but only within Accelerate's marketing domain.
- Add one new prioritization skill and rename one content skill.

## Baseline comparison

| System | Primary audience | Surface shape | What it is best at | Main mismatch for Accelerate |
|---|---|---|---|---|
| Shopify AI Toolkit | Developers building on Shopify | API- and implementation-oriented skills | Clean domain segmentation, docs-first validation, execution wrappers | Too technical, too code-centric, too platform-oriented |
| PostHog AI Plugin | Product teams, analysts, engineers, operators | Product-surface and slash-command oriented | Broad operational coverage across the product | Still skewed toward product engineering and analytics tooling |
| Accelerate | Marketers and site owners | Workflow-oriented marketer jobs | Plain-English site improvement workflows | Missing a top-level prioritization and operating-plan surface |

## Shopify review

### What Shopify actually exposes

Shopify's official AI Toolkit docs say the toolkit connects AI tools to Shopify through documentation, API schemas, code validation, and store execute capabilities, and recommends plugin installation first: <https://shopify.dev/docs/apps/build/ai-toolkit>.

The available skill set is segmented by platform surface, not by merchant job. Current public skills include domains such as:

- `shopify-admin-execution`
- `shopify-admin`
- `shopify-custom-data`
- `shopify-customer-account`
- `shopify-dev`
- `shopify-functions`
- `shopify-hydrogen`
- `shopify-liquid`
- `shopify-partner`
- `shopify-payments-apps`
- `shopify-polaris-*`
- `shopify-pos-ui-extensions`
- `shopify-storefront-graphql`

Source: <https://github.com/Shopify/shopify-ai-toolkit/tree/main/skills>

The important point is what these skills expect from the user and the model:

- `shopify-admin` requires documentation search and validation before every response, then returns GraphQL operations for the Admin API.
- `shopify-storefront-graphql` does the same for Storefront GraphQL.
- `shopify-liquid` is a theme-development skill with schema and file-structure rules.
- `shopify-admin-execution` wraps a validated GraphQL operation inside `shopify store auth` and `shopify store execute` CLI flows.

Sources:

- <https://raw.githubusercontent.com/Shopify/shopify-ai-toolkit/main/skills/shopify-admin/SKILL.md>
- <https://raw.githubusercontent.com/Shopify/shopify-ai-toolkit/main/skills/shopify-storefront-graphql/SKILL.md>
- <https://raw.githubusercontent.com/Shopify/shopify-ai-toolkit/main/skills/shopify-liquid/SKILL.md>
- <https://raw.githubusercontent.com/Shopify/shopify-ai-toolkit/main/skills/shopify-admin-execution/SKILL.md>

### What Shopify gets right

Shopify is a very good benchmark for skill taxonomy discipline.

Good patterns worth copying:

- Clear routing boundaries. Each skill has a crisp domain and low ambiguity.
- Strong "use this when..." descriptions.
- Separation between planning/generation and execution. `shopify-admin` and `shopify-admin-execution` are distinct on purpose.
- Strong fallback behavior. `shopify-dev` exists as a docs-search fallback when no domain-specific skill fits.

These are all valuable for Accelerate.

### What Shopify gets wrong for this audience

For a non-technical business or marketing user, Shopify is the wrong surface model.

Why:

- The toolkit assumes API, GraphQL, theme, CLI, and app-platform literacy.
- The user jobs are builder jobs, not operator jobs.
- Even the "execution" layer is command-oriented, not decision-oriented.
- The validation-first loop is correct for codegen, but it adds visible cognitive weight that marketers do not want.

Representative marketer prompts fit poorly:

| Prompt | Shopify fit | Why |
|---|---|---|
| "How is my site doing this week?" | Poor | No obvious analytics-review front door |
| "What should I improve first?" | Poor | No prioritization workflow for business users |
| "Which landing page needs work?" | Poor | Storefront dev skills are not landing-page diagnosis skills |
| "What should I A/B test next?" | Weak | Can help a developer implement tests, not guide a marketer on what to test |
| "Should I personalize anything?" | Weak | Personalization is implementation-led, not audience-opportunity-led |

### Shopify takeaway for Accelerate

Use Shopify as a benchmark for:

- skill segmentation
- routing discipline
- execution wrapper design

Do not use Shopify as a benchmark for:

- tone
- user-facing interaction style
- primary capability map

If Accelerate copied Shopify too closely, it would become tool-shaped instead of job-shaped.

## PostHog review

### What PostHog actually exposes

PostHog's README describes the plugin as official access to analytics, feature flags, experiments, and error tracking from AI clients, and lists slash commands for:

- `flags`
- `insights`
- `errors`
- `experiments`
- `dashboards`
- `surveys`
- `query`
- `logs`
- `llm-analytics`
- `docs`
- `actions`
- `search`
- `workspace`

Source: <https://github.com/PostHog/ai-plugin>

The commands directory confirms this product-area layout:

- `actions.md`
- `dashboards.md`
- `docs.md`
- `errors.md`
- `experiments.md`
- `flags.md`
- `insights.md`
- `llm-analytics.md`
- `logs.md`
- `query.md`
- `search.md`
- `surveys.md`
- `workspace.md`

Source: <https://github.com/PostHog/ai-plugin/tree/main/commands>

The PostHog MCP docs show that the actual server breadth is wider than the README command list. It exposes feature categories including:

- `workspace`
- `actions`
- `activity_logs`
- `alerts`
- `annotations`
- `cohorts`
- `dashboards`
- `data_schema`
- `data_warehouse`
- `debug`
- `docs`
- `early_access_features`
- `error_tracking`
- `events`
- `experiments`
- `flags`
- `hog_functions`
- `hog_function_templates`
- `insights`
- `llm_analytics`
- `prompts`
- `logs`
- `notebooks`
- `persons`
- `search`
- `sql`
- `surveys`
- `workflows`

Source: <https://posthog.com/docs/model-context-protocol>

One useful detail: the command files are intentionally thin. For example, `experiments.md` is mostly a short wrapper around the experiment MCP tools plus example prompts, not a long, guided business workflow: <https://github.com/PostHog/ai-plugin/blob/main/commands/experiments.md>

### Why PostHog is the better benchmark for Accelerate

PostHog feels closer to a conversational operating layer than Shopify does.

Useful patterns:

- Product-area entry points are obvious.
- The user can speak in natural product terms instead of API terms.
- There is wide coverage across operational jobs.
- Search and workspace give the model better orientation across the product.
- Natural-language analytics and query access make the system feel broadly capable.

That overall posture is relevant for Accelerate. A business user should feel that the assistant can help them run the site, not just answer a narrow list of canned reports.

### Where PostHog still does not match Accelerate's audience

PostHog is broader, but it is not truly marketer-first.

Limits for Accelerate benchmarking:

- Much of the surface is product-engineering oriented: flags, logs, error tracking, SQL, debug.
- It assumes a product analytics mental model.
- It is broad partly because PostHog is a very broad product. Accelerate should not imitate that breadth outside its own domain.
- The command files are discoverable, but not especially guided for non-technical business users.

Representative marketer prompts fit better than Shopify, but still unevenly:

| Prompt | PostHog fit | Why |
|---|---|---|
| "How is my site doing this week?" | Good | Insights, dashboards, or query can answer it |
| "What should I improve first?" | Medium | Possible, but no obvious single prioritization surface |
| "Which landing page needs work?" | Medium | Can analyze if data is instrumented, but not native as a landing-page optimization job |
| "What should I A/B test next?" | Good | Experiments surface exists, but usually in a product-analytics frame |
| "Should I personalize anything?" | Weak to medium | Cohorts and flags exist, but not content-personalization guidance |
| "What changed and what should I do now?" | Medium | Broad enough to answer, but not strongly packaged for that business ask |

### PostHog takeaway for Accelerate

Use PostHog as the benchmark for:

- breadth of major product surfaces
- natural front doors for major jobs
- feeling like an operational assistant rather than a narrow report generator

Do not use PostHog as the benchmark for:

- engineering-heavy categories
- thin slash-command wrappers as the primary UX
- product-analytics vocabulary as the user-facing language

## Accelerate assessment

### What the current implementation gets right

The current Accelerate implementation is already stronger than both benchmarks on audience fit.

Key strengths:

- The router is explicitly non-technical and marketer-first (`skills/accelerate/SKILL.md:10-16`).
- The skill map is based on business jobs, not internal APIs (`skills/accelerate/SKILL.md:42-59`).
- Mutation safety is excellent. The router and the mutation skills repeatedly require explicit confirmation before creating tests, audiences, or personalization rules (`skills/accelerate/SKILL.md:84-86`, `skills/accelerate-test/SKILL.md:46-58`, `skills/accelerate-personalize/SKILL.md:57-89`).
- The specializations are genuinely useful for marketers:
  - `accelerate-analyze` gives a site review (`skills/accelerate-analyze/SKILL.md:12-24`).
  - `accelerate-diagnose` turns underperformance into prioritized fixes (`skills/accelerate-diagnose/SKILL.md:12-23`, `skills/accelerate-diagnose/SKILL.md:46-74`).
  - `accelerate-optimize-landing-page` is a direct marketer job with page-level recommendations (`skills/accelerate-optimize-landing-page/SKILL.md:12-18`, `skills/accelerate-optimize-landing-page/SKILL.md:44-90`).
  - `accelerate-test` covers the full A/B testing lifecycle in marketer language (`skills/accelerate-test/SKILL.md:12-29`, `skills/accelerate-test/SKILL.md:44-104`).
  - `accelerate-personalize` treats personalization as audience opportunity, not implementation detail (`skills/accelerate-personalize/SKILL.md:12-40`).
  - `accelerate-campaigns` is explicitly UTM and attribution oriented (`skills/accelerate-campaigns/SKILL.md:12-21`, `skills/accelerate-campaigns/SKILL.md:57-102`).
  - `accelerate-brief` is a strong content idea rooted in site data, which neither Shopify nor PostHog offers in this form (`skills/accelerate-brief/SKILL.md:12-25`, `skills/accelerate-brief/SKILL.md:34-77`).
  - `accelerate-realtime` gives a clean "what's happening right now" surface (`skills/accelerate-realtime/SKILL.md:12-32`, `skills/accelerate-realtime/SKILL.md:34-71`).
- Advanced/raw capability access is already isolated in `accelerate-abilities-reference`, which is exactly where it belongs (`skills/accelerate-abilities-reference/SKILL.md:12-18`, `skills/accelerate-abilities-reference/SKILL.md:42-106`).
- The `accelerate-analyst` agent is a useful escalation path for deeper strategic questions, but it stays out of the front-door UX (`agents/accelerate-analyst.md:11-24`, `agents/accelerate-analyst.md:26-57`).

This is a strong base. The direction is correct.

### Where the current skill map is weak

The current system is slightly too dependent on the user already knowing which workflow they want.

Main gaps:

- There is no single strong owner for prioritization.
  - "How is my site doing?" maps to `accelerate-analyze`.
  - "Why is this underperforming?" maps to `accelerate-diagnose`.
  - "Improve this landing page" maps to `accelerate-optimize-landing-page`.
  - But "What should I do first?" has no obvious home.
- There is no clear monthly or weekly operating cadence skill.
  - `accelerate-analyze` is a report.
  - `accelerate-analyst` is a deep investigation.
  - Neither is the obvious "give me a plan" front door.
- `accelerate-brief` is valuable, but the name is narrower and more editorial than most marketers will think.
  - The underlying job is closer to "content opportunities" or "content plan."
- Discoverability is slightly fragmented around analysis versus diagnosis versus optimization.
  - That is not a reason to merge them.
  - It is a reason to add a better top-level entry point.
- Commands are intentionally minimal, which is fine.
  - The issue is not lack of commands.
  - The issue is lack of one top-level operator skill.

### Scorecard

Scored for a non-technical business and marketing audience.

| Dimension | Shopify | PostHog | Accelerate | Notes |
|---|---|---|---|---|
| Audience fit | 1/5 | 3/5 | 4.5/5 | Accelerate is the only one explicitly written for marketers |
| Capability breadth in-domain | 1.5/5 | 4.5/5 | 3.5/5 | Accelerate is narrower than PostHog, but more relevant |
| Workflow usefulness | 2/5 | 3.5/5 | 4.5/5 | Accelerate workflows are more guided and actionable |
| Discoverability | 4/5 | 4/5 | 3/5 | Accelerate needs a clearer "what next" front door |
| Mutation safety | 4/5 | 3/5 | 5/5 | Explicit confirmation is a major strength |
| Analytical depth | 1.5/5 | 4.5/5 | 4/5 | Analyst path helps Accelerate, but top-level packaging is thinner |
| Talk-to-my-business readiness | 1/5 | 3.5/5 | 4/5 | Accelerate is close, but missing the operator/prioritization layer |

### Representative prompt test

| Prompt | Shopify | PostHog | Accelerate | Verdict |
|---|---|---|---|---|
| How is my site doing this week? | Poor | Good | Strong | Accelerate already handles this well |
| What should I improve first? | Poor | Medium | Partial | Accelerate needs a dedicated owner |
| Which landing page needs work? | Poor | Medium | Strong | Accelerate is best here |
| What should I A/B test next? | Weak | Good | Strong | Accelerate fits marketers better |
| Should I personalize anything? | Weak | Weak to medium | Strong | Accelerate is clearly differentiated |
| Which campaign is working? | Weak | Medium | Strong | Accelerate is more UTM- and attribution-native |
| What's happening right now? | Poor | Medium | Strong | Realtime is already a good surface |
| Give me a plan for this month | Poor | Medium | Partial | Another signal for a prioritization skill |
| What changed and what should I do now? | Poor | Medium | Partial | Another signal for a prioritization skill |

## Recommendations for Accelerate

### Keep as-is

- Keep the marketer-first tone and hard ban on technical jargon.
- Keep the workflow-first shape. This is better for the audience than Shopify's API map or PostHog's thinner command wrappers.
- Keep `accelerate-diagnose` separate from `accelerate-analyze`.
  - `analyze` is status and summary.
  - `diagnose` is root cause and triage.
  - Merging them would create a bloated front door.
- Keep `accelerate-optimize-landing-page` as a dedicated skill. It is one of the clearest marketer jobs in the toolkit.
- Keep `accelerate-test`, `accelerate-personalize`, `accelerate-campaigns`, and `accelerate-realtime` as top-level skills.
- Keep `accelerate-abilities-reference` hidden and advanced.
- Keep `accelerate-analyst` as an internal escalation path, not a primary surface.

### Refine

- Reframe `accelerate-analyze` as a review skill, not just a report skill.
  - Best option: rename the concept to `accelerate-review` or `accelerate-site-review`.
  - Goal: make it sound like a business check-in rather than a technical analysis task.
- Reframe `accelerate-brief` as a content planning skill.
  - Best option: rename the concept to `accelerate-content-plan` or `accelerate-content-opportunities`.
  - "Brief" is narrower than the real value of the skill.
- Tighten router ownership for prioritization prompts.
  - Right now, "what should I improve first?" can plausibly land in three places.
  - That ambiguity should be removed at the router layer.

### Add

Add one new top-level skill: `accelerate-opportunities`.

This should become the front door for:

- what should I improve first
- what changed
- what should I do now
- where should I focus this week
- what should I test next
- should I personalize anything
- give me a plan for this month

This skill should synthesize:

- site review
- underperformance diagnosis
- landing pages
- campaigns
- active tests
- personalization opportunities

Its output should be a short prioritized operating plan, not just a report.

Suggested behavior:

- Pull the most important changes and opportunities across the site.
- Rank 3 actions by expected impact.
- For each action, state whether the right follow-up is:
  - diagnose deeper
  - run an A/B test
  - personalize
  - improve a landing page
  - leave it alone

If only one net-new skill is added in the next version, this is the one to add.

### Do not copy

- Do not copy Shopify's API-surface taxonomy into the user-facing Accelerate map.
- Do not copy Shopify's docs-search-plus-validation rhythm into the visible UX.
- Do not copy PostHog's engineering-heavy surfaces like logs, SQL, error tracking, and workspace as top-level marketer skills.
- Do not make the primary Accelerate surface mirror the raw ability catalog.
- Do not expand to a giant slash-command catalog unless there is a real discoverability reason.

If commands are expanded later, keep them narrow and marketer-friendly. The only obvious candidates are:

- `/accelerate-review`
- `/accelerate-opportunities`
- `/accelerate-realtime`

## Suggested target skill map for vNext

### Top-level user jobs

| User job | Proposed skill | Recommendation |
|---|---|---|
| How are we doing? | `accelerate-review` | Rename/reframe current `accelerate-analyze` |
| What should we do next? | `accelerate-opportunities` | New |
| Why is this underperforming? | `accelerate-diagnose` | Keep |
| Improve this landing page | `accelerate-optimize-landing-page` | Keep |
| What should we A/B test or how is a test going? | `accelerate-test` | Keep |
| Should we personalize anything? | `accelerate-personalize` | Keep |
| Which channels or campaigns are working? | `accelerate-campaigns` | Keep |
| What content should we make next? | `accelerate-content-plan` | Rename/reframe current `accelerate-brief` |
| What is happening right now? | `accelerate-realtime` | Keep |

### Advanced or internal surfaces

| Surface | Recommendation |
|---|---|
| `accelerate-analyst` | Keep internal or advanced only |
| `accelerate-abilities-reference` | Keep hidden/advanced only |
| setup commands | Keep minimal and separate from the marketer workflow layer |

### Practical vNext map

If the goal is minimum change with maximum product improvement, the target map should be:

- `accelerate-review`
- `accelerate-opportunities`
- `accelerate-diagnose`
- `accelerate-optimize-landing-page`
- `accelerate-test`
- `accelerate-personalize`
- `accelerate-campaigns`
- `accelerate-content-plan`
- `accelerate-realtime`
- hidden: `accelerate-abilities-reference`
- internal: `accelerate-analyst`

That keeps the current strengths, fixes the biggest gap, and still preserves a marketer-first surface.

## Final recommendation

Accelerate should position itself as the best conversational operating layer for a marketer running a WordPress site with Accelerate, not as a generic MCP wrapper and not as a developer toolkit.

That means:

- borrow Shopify's discipline
- borrow PostHog's sense of breadth
- keep Accelerate's marketer language
- add a strong prioritization skill
- keep raw capabilities behind the curtain

The current implementation is already directionally right. The next step is not more technical depth. It is better top-level packaging around "what matters now" and "what should I do next."

## Benchmark sources

- Shopify AI Toolkit docs: <https://shopify.dev/docs/apps/build/ai-toolkit>
- Shopify skills directory: <https://github.com/Shopify/shopify-ai-toolkit/tree/main/skills>
- Shopify admin skill: <https://raw.githubusercontent.com/Shopify/shopify-ai-toolkit/main/skills/shopify-admin/SKILL.md>
- Shopify admin execution skill: <https://raw.githubusercontent.com/Shopify/shopify-ai-toolkit/main/skills/shopify-admin-execution/SKILL.md>
- Shopify Storefront GraphQL skill: <https://raw.githubusercontent.com/Shopify/shopify-ai-toolkit/main/skills/shopify-storefront-graphql/SKILL.md>
- Shopify Liquid skill: <https://raw.githubusercontent.com/Shopify/shopify-ai-toolkit/main/skills/shopify-liquid/SKILL.md>
- PostHog AI plugin README: <https://github.com/PostHog/ai-plugin>
- PostHog commands directory: <https://github.com/PostHog/ai-plugin/tree/main/commands>
- PostHog experiments command: <https://github.com/PostHog/ai-plugin/blob/main/commands/experiments.md>
- PostHog MCP docs: <https://posthog.com/docs/model-context-protocol>
