# Reproduction boundaries

## Available now in this candidate

1. Read the primary tables in `results/summary.json`.
2. Reaggregate saved numerical rollout rows using `python -B analysis/summarize_results.py` (Python3.12+, standard library).
3. Add `--method delay_only`, `--method oracle_visibility`, or `--method Baseline` to inspect controls; `--all-grid` displays every saved cell without selecting a new configuration.
4. Inspect the original core TRACE/controller/client/parser source in `sfb/`, and source hashes in `results/source_inventory.json`.

`results/rollouts.jsonl.gz` has120960 rows: two lightings×three models×three worlds×240 routes×(one Baseline plus nine cells for each of three policies). The export is an explicit numerical field allowlist. It excludes response text, images, credentials, billing ledgers and server details. Scores and route identities are preserved; timing/HTTP call counts must not be inferred from replay row counts.

## Separate prerequisites for from-image reproduction

Full standalone RGB/semantic/mask packages and their licenses; matching model services and identity profiles; their actual generation settings; new run namespaces and budgets; current server-side contracts and an authorized inference runner. The included clients are implementation references, not ready-to-use access to the project's servers. Model weights/services are not bundled.

## Separate prerequisites for recollection

Licensed source assets, terrain products, USD scene bundles, frozen layouts/routes, local Isaac runtime and the matching capture launch configuration. These are not included in the small public candidate. The completed original campaign ran on Windows, Isaac Sim6.0.1 and RTX4090; no cross-platform or other-GPU equivalence is claimed.

## What was done during packaging

Existing data and results were read offline. No new model inference, simulator render, unit test suite or new scientific experiment was requested for packaging. File export/hash and local-page inspection evidence is stored outside the proposed public repository in the local release audit. Actual execution status is recorded there; this document does not claim the commands above were run as tests.
