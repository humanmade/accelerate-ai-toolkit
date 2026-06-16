#!/usr/bin/env bash
#
# validate.sh — standards / vendor-compliance check for the toolkit's HARD files
# (manifests, MCP configs, the Hermes plugin, scripts). This is NOT a test of
# skill *content* — it checks that the files agents actually load are well-formed
# and consistent across vendors. It is the automated form of the "Verification
# checklist" in AGENTS.md.
#
# Usage:  bash scripts/validate.sh
# Exit:   0 = all checks passed, 1 = one or more failed.
#
# Dependencies: python3 (parsing). Uses `claude` if on PATH (official Claude
# plugin validator); skips that one check gracefully if absent.

set -u
cd "$(dirname "$0")/.." || exit 2
ROOT="$(pwd)"

PASS=0; FAIL=0; SKIP=0
ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[31m✘\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
skip() { printf '  \033[33m–\033[0m %s\n' "$1"; SKIP=$((SKIP+1)); }
section() { printf '\n\033[1m%s\033[0m\n' "$1"; }

# JSON manifests every supported agent reads.
JSON_MANIFESTS=(
  .mcp.json package.json plugin.json
  .claude-plugin/plugin.json .claude-plugin/marketplace.json
  .codex-plugin/plugin.json
  .cursor-plugin/plugin.json .cursor-plugin/marketplace.json
  gemini-extension.json
  hooks/hooks.json
)

# ---------------------------------------------------------------------------
section "1. Official validators"

if command -v claude >/dev/null 2>&1; then
  if claude plugin validate --strict ./ >/tmp/aat-claude-validate.log 2>&1; then
    ok "claude plugin validate --strict ./"
  else
    bad "claude plugin validate --strict ./ (see /tmp/aat-claude-validate.log)"
  fi
else
  skip "claude not on PATH — skipping official Claude plugin validation"
fi

# ---------------------------------------------------------------------------
section "2. Manifests parse"

for f in "${JSON_MANIFESTS[@]}"; do
  if [ ! -f "$f" ]; then bad "missing: $f"; continue; fi
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
    ok "JSON parses: $f"
  else
    bad "JSON invalid: $f"
  fi
done

if python3 -c "import yaml" 2>/dev/null; then
  if python3 -c "import yaml; yaml.safe_load(open('.hermes-plugin/plugin.yaml'))" 2>/dev/null; then
    ok "YAML parses: .hermes-plugin/plugin.yaml"
  else
    bad "YAML invalid: .hermes-plugin/plugin.yaml"
  fi
else
  skip "PyYAML absent — skipping plugin.yaml parse"
fi

if python3 -c "import ast; ast.parse(open('.hermes-plugin/__init__.py').read())" 2>/dev/null; then
  ok "Python parses: .hermes-plugin/__init__.py"
else
  bad "Python invalid: .hermes-plugin/__init__.py"
fi

if bash -n .hermes-plugin/install.sh 2>/dev/null; then
  ok "Bash syntax: .hermes-plugin/install.sh"
else
  bad "Bash syntax error: .hermes-plugin/install.sh"
fi

# ---------------------------------------------------------------------------
section "3. Version consistency"

python3 - "$ROOT" <<'PY'
import json, os, re, sys
root = sys.argv[1]
versions = {}
json_files = [
    "package.json", "plugin.json",
    ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json", ".cursor-plugin/marketplace.json",
    "gemini-extension.json",
]
def find_versions(obj):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "version" and isinstance(v, str):
                out.append(v)
            else:
                out += find_versions(v)
    elif isinstance(obj, list):
        for it in obj:
            out += find_versions(it)
    return out
for f in json_files:
    p = os.path.join(root, f)
    if os.path.exists(p):
        for v in find_versions(json.load(open(p))):
            versions.setdefault(v, []).append(f)
# Hermes yaml version (read without PyYAML dependency)
hy = os.path.join(root, ".hermes-plugin/plugin.yaml")
if os.path.exists(hy):
    m = re.search(r"(?m)^version:\s*(\S+)", open(hy).read())
    if m:
        versions.setdefault(m.group(1), []).append(".hermes-plugin/plugin.yaml")
if len(versions) == 1:
    print("OK", next(iter(versions)))
else:
    print("FAIL")
    for v, files in sorted(versions.items()):
        print(f"  {v}: {', '.join(files)}")
PY
if [ "$(python3 - "$ROOT" <<'PY'
import json, os, re, sys
root = sys.argv[1]
versions = set()
json_files = ["package.json","plugin.json",".claude-plugin/plugin.json",".claude-plugin/marketplace.json",".codex-plugin/plugin.json",".cursor-plugin/plugin.json",".cursor-plugin/marketplace.json","gemini-extension.json"]
def fv(o):
    r=[]
    if isinstance(o,dict):
        for k,v in o.items():
            r += [v] if k=="version" and isinstance(v,str) else fv(v)
    elif isinstance(o,list):
        for it in o: r+=fv(it)
    return r
for f in json_files:
    p=os.path.join(root,f)
    if os.path.exists(p):
        versions.update(fv(json.load(open(p))))
hy=os.path.join(root,".hermes-plugin/plugin.yaml")
if os.path.exists(hy):
    m=re.search(r"(?m)^version:\s*(\S+)",open(hy).read())
    if m: versions.add(m.group(1))
print("OK" if len(versions)==1 else "FAIL")
PY
)" = OK ]; then ok "all manifests share one version"; else bad "manifest versions differ (see list above)"; fi

# ---------------------------------------------------------------------------
section "4. Hermes provides_skills == skills/ dirs"

if python3 - <<'PY'
import os, re, sys
text = open(".hermes-plugin/plugin.yaml").read()
# parse the simple provides_skills: list without PyYAML
block = re.search(r"(?ms)^provides_skills:\s*\n((?:\s*-\s*\S+\n?)+)", text)
declared = set(re.findall(r"-\s*(\S+)", block.group(1))) if block else set()
actual = {d for d in os.listdir("skills") if os.path.isdir(os.path.join("skills", d))}
sys.exit(0 if declared == actual else 1)
PY
then ok "provides_skills matches skills/ exactly"; else bad "provides_skills drift vs skills/"; fi

# ---------------------------------------------------------------------------
section "5. MCP server config shape (.mcp.json, gemini-extension.json)"

for f in .mcp.json gemini-extension.json; do
  if python3 - "$f" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
srv = d.get("mcpServers", {}).get("wordpress")
assert isinstance(srv, dict), "no wordpress server"
assert isinstance(srv.get("command"), str), "command must be a string"
assert isinstance(srv.get("args"), list), "args must be a list"
assert isinstance(srv.get("env"), dict), "env must be an object"
PY
  then ok "wordpress MCP server well-formed: $f"; else bad "wordpress MCP server malformed: $f"; fi
done

# ---------------------------------------------------------------------------
section "6. Skill frontmatter (name + description present)"

sf_fail=0
for d in skills/*/; do
  smd="${d}SKILL.md"
  [ -f "$smd" ] || { bad "no SKILL.md in $d"; sf_fail=1; continue; }
  head -1 "$smd" | grep -q '^---' || { bad "no frontmatter: $smd"; sf_fail=1; continue; }
  grep -q '^name:' "$smd" && grep -q '^description:' "$smd" || { bad "missing name/description: $smd"; sf_fail=1; }
done
[ "$sf_fail" -eq 0 ] && ok "all skills have frontmatter with name + description"

# ---------------------------------------------------------------------------
section "7. Skill count consistency"

N="$(find skills -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
if grep -q "$N skills" AGENTS.md 2>/dev/null && grep -q "$N purpose-built skills" README.md 2>/dev/null; then
  ok "skill count ($N) matches README + AGENTS.md"
else
  bad "skill count ($N) not reflected in README and/or AGENTS.md"
fi

# ---------------------------------------------------------------------------
section "8. Final newline on shipped text files"

nl_fail=0
while IFS= read -r f; do
  [ -s "$f" ] || continue
  if [ -n "$(tail -c1 "$f")" ]; then bad "no final newline: $f"; nl_fail=1; fi
done < <(find . \
  -path ./.git -prune -o -path ./.firecrawl -prune -o -path ./knowledge -prune \
  -o -path ./node_modules -prune -o -path ./internal -prune \
  -o -type f \( -name '*.json' -o -name '*.md' -o -name '*.sh' -o -name '*.yaml' -o -name '*.yml' -o -name '*.py' \) -print)
[ "$nl_fail" -eq 0 ] && ok "all shipped text files end with a newline"

# ---------------------------------------------------------------------------
printf '\n\033[1mSummary:\033[0m %d passed, %d failed, %d skipped\n' "$PASS" "$FAIL" "$SKIP"
[ "$FAIL" -eq 0 ]
