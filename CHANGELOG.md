# Changelog

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
