# Cursor support — coming in v1.1

The Accelerate AI Toolkit is vendor-agnostic by design. All skills live in the shared `/skills/` directory at the repo root and can be exposed to any agent that supports markdown-based skill files.

A working Cursor manifest is planned for v1.1. See [ROADMAP.md](../ROADMAP.md) for status.

**Want to help land it sooner?** PRs welcome. The scope is:

1. Create `.cursor-plugin/plugin.json` following Cursor's manifest spec
2. Point it at `../skills/` as the source
3. Test installation via the Cursor marketplace flow
4. Update the README "Supported agents" table

Reference: [Shopify AI Toolkit's `.cursor-plugin/`](https://github.com/Shopify/Shopify-AI-Toolkit/tree/main/.cursor-plugin) is a clean example of the pattern.
