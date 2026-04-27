# Changelog

## 1.3.2

**Repo-level sync, hygiene, and resilience.** Catch-up sweep after #11–#13 to bring docs, model instructions, release manifests, and workflow assumptions back in line with the current upstream contract.

- **3-tier permission model** documented everywhere it was previously framed as 2 tiers. Added the `view_accelerate_analytics` capability (real read-only marketing role, no experiment-creation rights) to authentication, ability-reference, installation, and the router skill's permission-error guidance. Per-tier counts corrected: 27 view + 9 create + 3 manage = 39 (previously misreported as 35 + 3 = 38).
- **Install docs aligned** with the marketplace shipping. `docs/installation.md` now leads with `claude plugin install accelerate-ai-toolkit` and shows local-checkout as a fallback for Codex CLI and development. Roadmap entry marked as shipped.
- **Broken README link fixed** — `./prd/ROADMAP.md` (gitignored, doesn't ship) → `./internal/ROADMAP.md`.
- **Release versions synced to 1.3.2** across `plugin.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, and `package.json` (was 1.3.1 / 1.2.0 / 1.3.1 / 1.0.0 / 1.0.0).
- **Degraded-path fallbacks** added to the four skills that depend on `accelerate/get-landing-pages` — landing-page optimisation, opportunities, campaigns, diagnose. When the upstream bug `humanmade/accelerate#609` triggers, workflows continue with `get-top-content` + `get-engagement-metrics` + `search-content` instead of aborting.
- **New `docs/maintenance.md`** — a six-item checklist for re-verifying the upstream contract, ability count, per-tier counts, version manifests, README link integrity, and workflow fallbacks before each release.

Closes [#14](https://github.com/humanmade/accelerate-ai-toolkit/issues/14).

## 1.3.1

**`/accelerate-status` now reports the real Accelerate capability count.** Healthy connections previously surfaced "3 WordPress abilities" — that figure was the count of MCP wrapper tools, not the actual Accelerate surface, so it read as "barely working" when the toolkit was fully operational.

- Layer 9 (Live data check) now calls `mcp__wordpress__mcp-adapter-discover-abilities` first, filters to `accelerate/*`, and surfaces that count. Smoke tests against `get-site-context` and `get-audience-fields` still confirm the connection is usable.
- If `discover-abilities` errors but the smoke tests succeed, the status block stays confident — it just omits the count line rather than printing a misleading number.
- Synced docs to the current 39-ability registry: added `accelerate/list-experiments` (paginated historical experiment discovery) to `docs/ability-reference.md` and `skills/accelerate-abilities-reference/SKILL.md`, bumped the discovery section count and the total in `README.md`, `docs/installation.md`, `agents/accelerate-analyst.md`, and `docs/skill-development.md`.

Closes [#12](https://github.com/humanmade/accelerate-ai-toolkit/issues/12).

## 1.3.0

**No more mu-plugin workaround for the WordPress connector address.** Recent versions of the WordPress MCP Adapter changed their default route, which previously forced users to install a server-side PHP file to bring the toolkit back online. The upstream `@automattic/mcp-wordpress-remote` client now accepts a full connector URL in `WP_API_URL`; this release teaches the toolkit to use that.

- `/accelerate-connect` now probes both the modern adapter route and the legacy `wpmcp` route, then saves whichever full URL responds. The mu-plugin instructions are gone from the normal flow.
- `/accelerate-status` learns to recognise both legacy bare-root and new full-URL configs, derives the site root from whichever it finds, and tells you to rerun `/accelerate-connect` if your saved value is stale.
- Existing installs keep working: legacy `wordpress-mcp` sites with a bare-root saved value continue to pass status checks unchanged. Adapter sites that were saved as bare roots will be flagged once and fixed by a single rerun of `/accelerate-connect`.
- Documentation (`docs/authentication.md`, `docs/installation.md`, `docs/self-optimising.md`, `docs/examples/workflow-accelerate-learn.yml`) and the upstream-asks roadmap are updated to reflect the new contract.

Closes [#11](https://github.com/humanmade/accelerate-ai-toolkit/issues/11).

## 1.2.0

**Self-optimising recommendations.** The toolkit now learns what works on your specific site.

- New `/accelerate-learn` skill reads your completed A/B test results, classifies each by suggestion pattern, and writes a per-site learning journal.
- Other skills (opportunities, test planning, site review) consult the journal to tailor recommendations -- winning patterns get priority, losing patterns come with context.
- 15 canonical suggestion patterns tracked, with a strict 3-test minimum before any pattern influences recommendations.
- Optional weekly automation via a GitHub Actions template (`docs/examples/workflow-accelerate-learn.yml`) that creates a PR with journal updates for review.
- Tests created via the toolkit are now tagged with pattern annotations for reliable classification.
- Full guide at `docs/self-optimising.md`.

Also: updated AGENTS.md with current permission model (3-tier with `view_accelerate_analytics`), corrected hook documentation (command-based, not prompt-based), clarified skill invocation policy.

## 1.0.13

- Added a centralised output style guide (`docs/output-style.md`) so all skills present data consistently -- tables, priority cards, trend indicators, callouts, and hand-off prompts follow the same patterns.

## 1.0.12

- Added `/accelerate` command as a guaranteed entry point — type `/accelerate` followed by your question and the router fires every time, no reliance on auto-detection.
- Rewrote all skill descriptions to be 58% smaller and use natural trigger phrases instead of boilerplate. Skills should now auto-trigger more reliably even when many plugins are installed.

## 1.0.11

- Fixed the root cause of empty A/B test variants (upstream fix in Accelerate plugin). Creating tests, adding variants, updating variants, and creating personalization rules now correctly preserve content. The backup/verify/rollback safety net in the testing skill is kept as defence-in-depth.

## 1.0.10

- Fixed a bug where the A/B test safety hook interrupted Claude after every site data request, not just test creation calls. Claude now continues smoothly through multi-step analysis workflows without getting cut off.

## 1.0.9

- Credentials now persist reliably across session restarts. `/accelerate-connect` saves to Claude Code's `settings.local.json` (the documented mechanism for injecting environment variables into background processes) instead of relying on shell profile sourcing, which Claude Code doesn't read. The backup env file and Codex CLI shell profile flow are preserved for non-Claude-Code agents.
- `/accelerate-status` now detects when credentials are saved but the session needs a restart to load them.

## 1.0.8

- Setup and status diagnostics now detect shell tools that intercept Node.js commands (checks the actual binary path, not just the version number).
- `/accelerate-status` now separates "Accelerate not installed" from "WordPress connector not registered" instead of showing a generic message when both fail.
- Removed technical jargon from all user-facing diagnostic messages (connection checks, status output, README notes).
- Permission diagnostic now correctly describes the two-tier access model instead of a blanket "Editor or higher".

## 1.0.7

- A/B testing and landing page optimisation skills now check whether the target content is a reusable block before proposing changes. If it isn't, the toolkit explains the requirement and walks you through converting it -- instead of spending time on a hypothesis you can't test.

## 1.0.6

- The router skill can now properly delegate to workflow skills. Previously, all sub-skills blocked programmatic invocation, forcing the agent to work around the skill system. Setup (`/accelerate-connect`) and advanced reference remain manual-only.

## 1.0.5

- README and installation docs now explicitly mention the MCP Adapter bundling and endpoint compatibility note.

## 1.0.4

- `/accelerate-status` is now a layered diagnostic that checks environment variables, npx, site reachability, authentication, endpoint compatibility, and MCP tool availability in order. It reports the first failing layer with a specific fix instead of a generic "run /accelerate-connect".

## 1.0.3

- `/accelerate-connect` now checks that `npx` is working correctly before completing setup. If another tool in your shell is intercepting `npx`, the setup wizard explains the problem instead of failing silently.
- `/accelerate-status` diagnoses `npx` interception when the connection appears missing.
- Installation troubleshooting updated with workaround for `npx` interception (project-level override with the full binary path).

## 1.0.2

- `/accelerate-connect` now double-quotes all values in the credentials file, fixing a bug where Application Passwords (which always contain spaces) were truncated by shell word-splitting.

## 1.0.1

- `/accelerate-connect` now detects when your site's WordPress connector plugin uses a different address than expected (common with MCP Adapter 0.4.1+) and provides clear instructions to fix it, instead of failing silently.
- `/accelerate-status` gives better guidance when a connection fails due to this endpoint mismatch.
- Installation docs updated with troubleshooting for the most common first-run connection failure.

## 1.0.0

- Initial release: 12 skills covering site review, diagnosis, opportunities, landing page optimisation, A/B testing, personalisation, campaigns, content planning, and real-time monitoring.
