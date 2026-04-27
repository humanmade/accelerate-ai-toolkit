# Maintenance checklist

Six things to re-verify before cutting a release or merging a contract-touching PR. These are the drift traps that produced toolkit issues #11–#14.

## 1. Permission model matches upstream

The toolkit's permission docs must match the three callbacks in `../altis-accelerate/inc/abilities/namespace.php`:

```bash
grep -A 3 "function can_view_analytics\|function can_create_experiments\|function can_manage_experiments" \
  ../altis-accelerate/inc/abilities/namespace.php
```

If a callback's WordPress capability changes (e.g. a new dedicated capability is added), update:
- `docs/authentication.md` — Required WordPress capabilities table
- `docs/ability-reference.md` — Permission tiers table + footer breakdown
- `docs/installation.md` — prereq bullet + permission-error troubleshooting paragraph
- `skills/accelerate/SKILL.md` — model permission-error guidance
- `AGENTS.md` — permission-model-is-three-tiers note

## 2. Total ability count matches upstream registrations

```bash
grep -rh "wp_register_ability( 'accelerate/" ../altis-accelerate/inc/abilities/*.php | sort -u | wc -l
```

If the count changes, update:
- `docs/ability-reference.md` — section header counts and total
- `skills/accelerate-abilities-reference/SKILL.md` — add or remove the entry
- `README.md` — `All N Accelerate capabilities` link text
- `AGENTS.md` — `N-capability Abilities API` mentions
- `docs/installation.md` — sample healthy status block

## 3. Per-tier counts are correct

```bash
for cb in can_view_analytics can_create_experiments can_manage_experiments; do
  printf "%-30s " "$cb"
  grep -rl "permission_callback.*$cb" ../altis-accelerate/inc/abilities/*.php \
    | xargs grep -c "permission_callback.*$cb" \
    | awk -F: 'BEGIN{s=0} { gsub(/^.*\//, "", $1); s += $2 } END { print s }'
done
```

The view + create + manage totals should add up to the result of step 2.

## 4. Release versions agree across all manifests

```bash
grep -E '"version"' plugin.json .claude-plugin/plugin.json .claude-plugin/marketplace.json \
  .codex-plugin/plugin.json package.json
```

All five must match. Bump them together when releasing.

## 5. `README.md` `./` links resolve against the working tree

The `/prd` directory is gitignored (`.gitignore`), so `./prd/...` links break for external readers. Quick check:

```bash
grep -oE '\(\.\/[^)]+\)' README.md | sed 's/[()]//g' | while read p; do
  test -e "$p" || echo "BROKEN: $p"
done
```

## 6. Workflow resilience for known-failing abilities

Any skill that depends on a single ability known to fail on some sites must declare a fallback path. The current case is `accelerate/get-landing-pages` (upstream bug `humanmade/accelerate#609`). Affected skills must mention the issue number in their fallback prose:

```bash
for f in skills/accelerate-optimize-landing-page/SKILL.md \
         skills/accelerate-opportunities/SKILL.md \
         skills/accelerate-campaigns/SKILL.md \
         skills/accelerate-diagnose/SKILL.md; do
  grep -q "humanmade/accelerate#609" "$f" || echo "MISSING fallback in: $f"
done
```

When the upstream bug is fixed, sweep these fallbacks (search for `humanmade/accelerate#609`) and remove or simplify them as appropriate.
