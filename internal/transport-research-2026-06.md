# Transport research — drop the npx proxy? (2026-06-11)

Question: can the toolkit replace the stdio `npx @automattic/mcp-wordpress-remote` proxy with Claude Code's native remote MCP (streamable HTTP) against `wp-json/mcp/mcp-adapter-default-server`?

## Verdict: GO-WITH-CAVEATS

The WordPress MCP Adapter speaks MCP streamable HTTP natively (JSON-RPC over POST, `Mcp-Session-Id` lifecycle per spec) and accepts application-password Basic auth through the standard WP REST layer. Claude Code supports `"type": "http"` servers with static `headers` (env-var expansion works in `url` and `headers`, including in plugin-bundled `.mcp.json`), and Codex CLI has equivalent HTTP MCP support (`http_headers` / `env_http_headers`), so both shipped manifests can switch. The proxy is officially documented as optional for clients with native header support.

**What we'd gain:** no npx startup (~460 ms registry revalidation + Node boot per session, seconds when cold), and persistent HTTP connections instead of the proxy's apparent per-call TCP setup (no keep-alive evidence in the proxy; Node default is `keepAlive: false` — single-source, unverified). Live-audit baseline: per-call wall ~30–900 ms, dominated by WP/ClickHouse time, so per-call savings are modest — the big win is session startup and removing a moving part (npx, registry, proxy version drift).

## Caveats

1. **Legacy-route sites** (`wp-json/wp/v2/wpmcp`, deprecated wordpress-mcp plugin) have no mcp-adapter endpoint; the proxy currently handles that fallback. Mitigation: keep the stdio proxy entry as a documented legacy variant.
2. **Basic-auth encoding**: Claude Code interpolates header strings but won't base64-encode `user:pass`. Either introduce a single pre-computed `WP_API_BASIC_TOKEN` env var, or ship a tiny `headersHelper` script (`${CLAUDE_PLUGIN_ROOT}/bin/basic-auth-header.sh`) that reads the existing `WP_API_USERNAME`/`WP_API_PASSWORD` and emits `{"Authorization": "Basic <b64>"}` — no end-user env change.
3. **Session handling**: adapter requires `Mcp-Session-Id` after initialize; standard streamable-HTTP behaviour Claude Code implements, but smoke-test on first deploy (also verify the adapter's response to a missing session id — 400 vs 404 — for resilience).

## Minimal config if we proceed

```json
{
  "mcpServers": {
    "wordpress": {
      "type": "http",
      "url": "${WP_API_URL}",
      "headersHelper": "${CLAUDE_PLUGIN_ROOT}/bin/basic-auth-header.sh"
    }
  }
}
```

Fallback: retain the current npx stdio entry as `wordpress-legacy` for sites without the mcp-adapter plugin; `/accelerate-connect` picks per-site.

## Not implemented this round

Per plan, this is a go/no-go note only. Next steps if pursued: ship `headersHelper` script, smoke-test session lifecycle against a 4.2.x site, update `/accelerate-connect` + installation docs, measure before/after session-start latency, release as 1.5.0.

Sources: Anthropic Claude Code MCP docs (verified), WordPress/mcp-adapter README + HttpTransport.php (verified), Automattic/mcp-wordpress-remote npm/GitHub (verified; keep-alive inference single-source), OpenAI Codex config reference (verified), npm cli issue #7295 (single-source). Full claim list in the research transcript.
