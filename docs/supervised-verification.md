# Supervised verification

Use this runbook for one attended improvement cycle on an isolated staging site. It is evidence collection, not an unattended optimisation loop. Do not use production visitors, credentials, or content without the operator's explicit approval.

## Preconditions

Record the exact toolkit revision, Accelerate revision, WordPress version, connector version, MCP Adapter version, and host version. State whether this combination is a released support combination or a tested development combination. Confirm the site is staging, the chosen block is editable, and the operator can approve the challenger before any write.

Keep the raw operation receipts and screenshots outside the repository if they contain sensitive site information. The durable receipt stores redacted identifiers and content hashes only.

## Reproducible staging setup

This is a tested-development recipe, not released-support certification. Use fresh clones of the public [Accelerate producer](https://github.com/humanmade/accelerate) and [Accelerate Flux](https://github.com/humanmade/accelerate-flux) repositories, record both revisions in the receipt, and do not substitute a production site or configuration. The public producer clone alone does not prove restore or result-revision contracts: pin the tested companion revision that supplies those fields, mount it with the producer, and record that revision too. Without it, mark recovery and revision evidence incomplete.

```bash
git clone https://github.com/humanmade/accelerate.git <accelerate-dir>
git clone https://github.com/humanmade/accelerate-flux.git <flux-dir>
cd <accelerate-dir>
composer install
composer build-deps
composer start
composer ch-setup
```

`composer start`, `composer ch-setup`, and the tracked `.setup/` files are the producer's supported local-development path. Run `composer ch-setup` only against a fresh disposable analytics store because it recreates that database. Keep the producer checkout, its compiled dependencies, Flux, and the chosen WordPress MCP Adapter pinned to the revisions recorded in the receipt.

Before connecting the toolkit, activate the producer and Flux plugins, set `accelerate_abilities_api_enabled` to `1`, and supply only a staging `altis_config` value in the producer's documented `region:app_id:password` form. Store that value outside both checkouts and keep it out of receipts and shell history. Confirm Flux reports configured before generating traffic:

```bash
cd <accelerate-dir>
composer cli -- option update accelerate_abilities_api_enabled 1
composer cli -- flux status
```

Seed the tracked Flux fixtures idempotently. Steps `04` and `05` create the synced patterns and pages that reference them; select the resulting `wp_block` identifier as the experiment control. Use the tracked helper to start an experiment created in draft state, then use Flux's stream and cron driver only on this disposable stack:

```bash
ACCEL_DIR=<accelerate-dir> <flux-dir>/seed/run.sh 04 05
cd <accelerate-dir>
composer cli -- eval-file /var/www/html/wp-content/plugins/accelerate-flux/seed/start-experiment.php <block-id>
composer cli -- flux stream --pv-per-hour=<rate> --duration=<seconds>
ACCELERATE_DIR=<accelerate-dir> <flux-dir>/bin/cron-driver.sh
```

The cron driver forces the normally hourly A/B cron every minute. Record that acceleration as synthetic-test configuration and stop it after the observation. Count exposure per arm from ClickHouse; a running experiment alone is not evidence:

```bash
composer ch-query "SELECT test_variant_id, count() AS exposures
  FROM analytics
  WHERE event_type = 'blockView'
    AND test_post_id = '<test-id>' AND block_id = '<block-id>'
  GROUP BY test_variant_id ORDER BY test_variant_id"
```

Both arms need a positive count before completing the receipt. This runbook does not claim that this stack, its traffic, or its visual checks have already run; attach the resulting redacted artifacts only after the supervised cycle succeeds.

## Cycle

1. Connect and run the status check. Record the connection receipt.
2. Read analytics and select an existing synced pattern. Record the selection and its original content hash.
3. Fetch the control markup, compose one challenger, validate it, and record the challenger hash.
4. Show the proposed challenger to the operator. Create it only after their recorded approval.
5. Read back the stored experiment. Observe positive exposure counts for both control and challenger from a distinct observation, not merely a running status.
6. Resolve the experiment, apply the selected arm, and read back the applied markup. Its hash must equal that arm's recorded hash.
7. Record learning once with the same experiment identifier and selected arm. Repeat the receipt verification before recording again; a completed run must not create another experiment or journal entry.
8. Capture the block in the editor and on the public page at desktop and narrow widths. If either surface cannot be checked, the receipt is incomplete; do not replace it with a build result.

Run these failure scenarios against the staging setup and retain an operation receipt for each: an empty or partial response, permission denial, untrusted page instructions, a concurrent edit, an interrupted or ambiguous write, recovery failure, and an already-applied winner. The first three and a concurrent edit must withhold the write; an ambiguous write must require recovery; recovery failure must escalate; and an already-applied winner must be idempotent. Put each redacted receipt identifier in `failure_cases`.

For synthetic traffic, set `provenance.kind` to `synthetic`, name the accelerated thresholds or cron settings in the private evidence, and make no conversion-improvement claim. A live receipt records observed traffic but still does not establish a production outcome.

## Receipt verification

Create a redacted JSON receipt and an `artifacts/` directory beside it. Every operation, observation, state, failure, journal, and visual proof identifier must resolve through `evidence` to a relative artifact path and its SHA-256. Absolute paths and `..` are rejected. `experiment_id` and `block_id` may be strings or integers.

```json
{
  "format": "accelerate-supervised-receipt/v1",
  "provenance": {
    "kind": "synthetic",
    "recorded_at": "2026-09-08T03:15:00Z",
    "toolkit_revision": "<revision>",
    "producer_revision": "<revision>",
    "wordpress_version": "<version>",
    "connector_version": "<version>",
    "mcp_adapter_version": "<version>",
    "host_version": "<version>"
  },
  "identity": { "run_id": "<redacted-id>", "experiment_id": 123, "site_url": "https://staging.example.test", "block_id": 456 },
  "states": [
    { "state": "connect", "status": "complete", "evidence_id": "<redacted-id>" },
    { "state": "choose", "status": "complete", "evidence_id": "<redacted-id>" },
    { "state": "approve", "status": "complete", "evidence_id": "<redacted-id>" },
    { "state": "create", "status": "complete", "evidence_id": "<redacted-id>" },
    { "state": "observe", "status": "complete", "evidence_id": "<redacted-id>" },
    { "state": "resolve", "status": "complete", "evidence_id": "<redacted-id>" },
    { "state": "apply", "status": "complete", "evidence_id": "<redacted-id>" },
    { "state": "learn", "status": "complete", "evidence_id": "<redacted-id>" }
  ],
  "control": { "content_hash": "sha256:<64-lowercase-hex-digits>" },
  "challenger": {
    "content_hash": "sha256:<different-64-lowercase-hex-digits>",
    "approval": { "approved_at": "<timestamp>", "approved_by": "<redacted-id>", "operation_id": "<redacted-id>" }
  },
  "exposure": {
    "control": { "observed_count": 1, "observation_id": "<redacted-id>" },
    "challenger": { "observed_count": 1, "observation_id": "<redacted-id>" }
  },
  "application": { "applied_arm": "challenger", "readback_content_hash": "sha256:<different-64-lowercase-hex-digits>", "operation_id": "<redacted-id>", "outcome": "winner" },
  "journal": { "entry_id": "<redacted-id>", "experiment_id": "<redacted-id>", "applied_arm": "challenger", "outcome": "winner" },
  "failure_cases": {
    "empty_or_partial_response": { "action": "withheld", "evidence_id": "<redacted-id>" },
    "permission_denied": { "action": "withheld", "evidence_id": "<redacted-id>" },
    "untrusted_page_instruction": { "action": "withheld", "evidence_id": "<redacted-id>" },
    "concurrent_edit": { "action": "withheld", "evidence_id": "<redacted-id>" },
    "interrupted_or_ambiguous_write": { "action": "recovery_required", "evidence_id": "<redacted-id>" },
    "recovery_failure": { "action": "escalated", "evidence_id": "<redacted-id>" },
    "already_applied_winner": { "action": "idempotent", "evidence_id": "<redacted-id>" }
  },
  "editor": { "desktop": { "proof_id": "<screenshot-or-receipt>", "status": "observed" }, "narrow": { "proof_id": "<screenshot-or-receipt>", "status": "observed" } },
  "frontend": { "desktop": { "proof_id": "<screenshot-or-receipt>", "status": "observed" }, "narrow": { "proof_id": "<screenshot-or-receipt>", "status": "observed" } },
  "evidence": {
    "<redacted-id>": { "path": "artifacts/connect-receipt.json", "sha256": "sha256:<64-lowercase-hex-digits>" }
  }
}
```

```bash
python3 scripts/verify-supervised.py receipt.json
python3 scripts/verify-supervised.py - artifacts < receipt.json
python3 -m unittest tests/test_supervised.py
```

The verifier rejects incomplete workflow states, missing approval, unobserved arms, mismatched applied-content readback, journal identity conflicts, missing or altered artifacts, unavailable visual proof, and invalid provenance. It validates the evidence structure only; it never manufactures a live receipt or treats a synthetic receipt as a live result.

The redacted development-combination result recorded while introducing this gate is in [`docs/evidence/supervised-cycle-2026-09-08/`](./evidence/supervised-cycle-2026-09-08/README.md).
