# Supervised cycle evidence — 2026-09-08

This records a functional acceptance run on an isolated staging site. Traffic and conversions were synthetic, so the run proves workflow behaviour and does not claim a real conversion improvement.

## Tested combination

- Toolkit: baseline `e136dbb`, with the changes in the pull request containing this receipt
- Accelerate: `92503f97f5f45a937512cab97ca1e15eb9c9033f`
- Accelerate Flux: `414af564777a50592fedd3fdd5bdf1c49f17498e`
- WordPress: `7.1`
- WordPress MCP Adapter: `0.5.0`
- WordPress connector: `0.4.0`
- Claude Code: `2.1.263`

## Cycle result

The host connected through the pinned connector, read current site and block state, selected an existing synced pattern, preserved the control verbatim, proposed one challenger, and created one recoverable experiment after approval. The producer test suite separately verified that repeating this request identity reconciles to the existing experiment instead of creating another row.

Independent event data recorded 119 control exposures and 101 challenger exposures. The experiment result reported 106 control impressions with 4 conversions and 93 challenger impressions with 4 conversions. The challenger was selected manually; the result correctly labels that choice as manual and explicitly says it is not statistical evidence.

After application, the synced pattern returned to standard content with no experiment wrappers. Its read-back hash was `de3a71e21d93e965c850229a4b5c36fc65849c982a3fbe3b3c8487df72d8a916`, matching the approved challenger exactly. A repeated learning refresh made no historical detail reads and did not add a duplicate journal entry.

A separate recovery exercise created a test from original hash `80b30b329a46fdc6bc71093b557959b8a00ba78a3ff40d390a42a7725f7064cf`, restored it through the public recovery operation, read back the same original hash, removed only the newly created experiment, and returned the same successful result on a repeated restore.

The recorded lifecycle evaluation covered running, paused, confirming, completed and applied, completed but unresolved, manual selection, partial response, permission denial, untrusted content, concurrent edits, ambiguous writes, and recovery failure. All twelve cases chose the required safe action and wording. The repository keeps those inputs and expected invariants in `tests/fixtures/lifecycle-evaluations.md`.

## Visual evidence

The applied challenger was observed on the public page and in the editor's editable code view at desktop and narrow widths.

- [Public page — desktop](frontend-desktop.png)
- [Public page — narrow](frontend-mobile.png)
- [Editor — desktop](editor-desktop.png)
- [Editor — narrow](editor-mobile.png)

## Verification boundary

This is development-combination evidence for one supervised synthetic run. It does not certify production traffic, other hosts, or unattended operation.
