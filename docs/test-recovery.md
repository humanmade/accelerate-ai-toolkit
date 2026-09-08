# Recovering an interrupted A/B test setup

This guide is for the test-creation workflow. It describes the local recovery
receipt and the supported server-side recovery path; it does not perform any
site change by itself.

## Durable receipt

Before a confirmed test is created, read the current block and its experiment
state. Save a receipt with `scripts/recovery.py` under the existing per-site
store:

`~/.config/accelerate-ai-toolkit/sites/<site-key>/test-recovery/`

The receipt is written atomically. Its directory is owner-only (`0700`) and its
file is owner-readable only (`0600`). It contains the site key and URL, block
identity, exact original markup and state, original markup hash, request ID, and
the hash of the exact approved create payload. It contains no credentials.

Pass structured input on standard input. Do not put copied markup in a command
argument, shell variable, or log. A successful save records only a local
receipt; it does not say that the site has changed.

The receipt's lifecycle is:

1. `prepared` — creation may proceed once a new block read has the saved
   original-content hash and the create payload still has the saved payload hash.
2. `created` — the server returned a known successful result. Record its
   current-content hash and experiment identity, then verify the block and
   experiment state before saying the test is live.
3. `outcome_unknown` — a timeout, interruption, or unusable response occurred.
   Re-read and reconcile the site. Never submit create again for this request.
4. `restored` — a supported restore completed and the original markup plus the
   relevant state were confirmed by read-back.
5. `completed` — the known created markup and experiment identity matched a
   read-back. This is the only non-restore terminal state that permits a new
   receipt for the block.
6. `recovery_required` — read-back did not match. Stop further mutations and
   tell the marketer that recovery still needs attention.

The helper rejects a changed original, a different site, a different request,
or a changed approved payload. Saving the same request returns the original
receipt only when every immutable identity value matches; it never resets the
state. A different request is rejected until the existing receipt is verified
as restored or completed.

## Supported create and restore contract

Use this path only when the installed Accelerate version supports both recovery
fields on creation and the matching restore operation:

- Create receives the paired `expected_content_hash` and `request_id` values.
  `expected_content_hash` is the SHA-256 hash of the fresh exact `raw_markup`.
  The server rejects a missing partner, stale markup, active experiment, or
  personalization state before it changes the block.
- A successful create response includes the request ID, original and current
  content hashes, and `recovery_available: true`.
- Restore receives `block_id`, `request_id`, and `expected_current_hash` from
  a fresh current-content read. It restores only when that hash still matches
  the content created for this request. A successful repeat restore is safe.

For a plugin without this supported contract, stop before the create write and
say that the site needs an Accelerate update for safe recovery. Do not attempt a
partial rollback by editing one variant or use a local WordPress command as an
undisclosed substitute.

## Recovery sequence

1. Validate each challenger with the normal Block Runner
   `validate` -> `fix` -> `validate` process. If that infrastructure is
   unavailable, retain its disclosed manual fallback; it does not provide
   recovery.
2. Save the receipt, re-read the block, and run the receipt preflight against
   the exact approved create payload. If any identity or hash differs, stop and
   re-plan.
3. Call create exactly once. Record `created` only from a complete, known
   success response, including its current-content hash and experiment identity;
   record `outcome_unknown` for a timeout, interruption, or incomplete result.
4. Re-read the block and experiment state. Empty/malformed variants, a missing
   active experiment, or an unknown result require reconciliation rather than a
   create retry.
5. Build a restore plan from the receipt and fresh current content. Call the
   supported restore operation once with the plan's `expected_current_hash`.
6. Re-read original markup and relevant state. Mark the receipt `restored` only
   when both match. Otherwise it is `recovery_required`; do not say that nothing
   changed.
7. For a healthy live test, archive the receipt as `completed` only when the
   created markup hash and recorded experiment identity both match read-back.

Claude Code's hooks receive the connector's create fields as
`tool_input.parameters`. Their normal event does not include a site identity or
fresh block read, so it remains a useful reminder in that case. When a host
supplies both values alongside the normal event, a receipt mismatch exits the
pre-create hook with status 2 and blocks the call. This is not universal
enforcement; the workflow above applies on every supported host.
