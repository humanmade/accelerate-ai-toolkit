# Decisions

## DEC-001 — Block Runner integration is an assist, not a publishing gate

**Status:** Accepted

Accelerate uses `block-runner@0.8.0` as the primary editor-validity pre-flight for Gutenberg markup it composes. Every generated or changed candidate is validated; an invalid candidate is fixed and validated again before it can be presented or written. A candidate that remains invalid is withheld.

The pre-flight is deliberately fail-open for unavailable tooling: an `npx` failure, timeout, or headless-Gutenberg boot failure falls back to the existing manual checks and is disclosed to the user. Exit `2` is a prominent broken-invocation warning followed by that same fallback. Block Runner does not decide brand, composition, factual, or conversion quality.

### Phases

- **P0 — markup pre-flight:** wire `validate` → `fix` → `validate` into the markup-emitting skills and retain the manual design-standard checks as the degraded path.
- **P1 — hosted-site context (upstream):** Block Runner/wesper will provide a REST collector for hosted WordPress sites using Application Passwords. This toolkit does not implement or emulate it. Until upstream ships it, use `accelerate/get-site-context`; do not advertise a non-existent `context --rest` command.

The vendor-maintained guide installed or printed by `block-runner skill` remains the source of truth for CLI use. Toolkit documentation owns only this integration contract.
