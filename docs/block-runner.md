# Block Runner in Accelerate

[Block Runner](https://github.com/humanmade/block-runner) is the optional, authoritative **editor-validity** check for Gutenberg markup that Accelerate generates. It answers only whether WordPress will accept the markup; brand fit, composition, factual grounding, and conversion judgement remain the responsibilities of the composing skill and `docs/design-standards.md`.

This is an Accelerate adapter, not a second copy of Block Runner's agent documentation. For the vendor-maintained guide, run:

```sh
npx -y block-runner@0.8.0 skill
```

Do not run `skill --install` automatically: it writes a skill into the user's agent environment and requires their explicit approval. The vendor guide owns command selection, intent trees, mappings, media and token handling, report formats, and CLI details.

## Required pre-flight

`accelerate-design` and `accelerate-test` must run this loop for every Gutenberg markup candidate they compose or change, **before** showing it to the user or passing it to a write ability:

1. Run `npx -y block-runner@0.8.0 validate <candidate-file-or-> --json`, with a roughly 60-second time limit. Read the JSON report; do not infer success from terminal text.
2. On exit `0`, use the candidate unchanged.
3. On exit `1`, run `npx -y block-runner@0.8.0 fix <candidate-file-or-> --json` on that exact candidate, then run `validate` on the repaired output. Use the repaired `output` only when that second validation exits `0`.
4. If repair fails or the repaired output is still invalid, withhold that candidate from both presentation and every write ability. Recompose it, then begin the loop again; do not "hand-check it through."
5. If markup changes after a successful pre-flight, repeat the loop before it is presented or written.

The current control in an A/B test is preserved verbatim: this loop applies to markup the toolkit generated or changed. Do not silently repair an existing control as part of creating a test.

## Fail-open is binding

Validation assists authoring; it never strands the user.

- If `npx` cannot start or download, the call times out, or Block Runner exits `3` because headless Gutenberg could not boot, fall back to the manual §2 checks in `docs/design-standards.md`. Continue the skill and say: *"Automatic WordPress markup validation was unavailable, so I completed the normal compatibility checks manually."*
- Exit `2` is a broken invocation or changed CLI contract, not a transient infrastructure problem. Warn prominently, then complete the same manual fallback: *"Warning: automatic WordPress markup validation is misconfigured. I completed compatibility checks manually; please review this markup before publishing."*
- Exit `1` from `validate` is a markup failure, not a reason to fail open. Attempt `fix` and re-validate; withhold the candidate if it remains invalid.

Do not describe a fallback as a successful Block Runner validation. Keep any failure details internal unless the user needs the warning above to decide whether to publish.

## Site context transport

`block-runner@0.8.0` can collect site context through WP-CLI only. The hosted-site REST collector (Application Password transport) is **pending upstream** in Block Runner/wesper; `context --rest` does not exist and must not be shown as a runnable command. Until it ships, use `accelerate/get-site-context` and the ingestion in `docs/brand-pack.md`. A missing collector is not a blocker for composition or pre-flight validation.
