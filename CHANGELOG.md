# Changelog

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
