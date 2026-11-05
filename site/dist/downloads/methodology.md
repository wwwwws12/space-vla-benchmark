# Evaluation protocol

This is an independent document-based engineering benchmark. The authoritative public projection is evaluation.json; it records the SHA256 of the unchanged internal source protocols and common-parameter freeze.

## Task

Scripted T trajectories provide discrete candidate actions and poses. Isaac Sim is the renderer. The visual Judger sees the current RGB image and target phrase, with the exact prompt:

> Is {target_description} visible in this image? Answer Yes or No only.

RGB PNG is encoded once as RGB JPEG at Q85. Identity and cache correlation include the target, model/profile, prompt and the SHA of actual sent JPEG bytes. Labels, masks, target coordinates, distances, poses and prior answers are never prompt inputs.

## Split and selection

Each scene contributes 20 dev and 80 test routes; three scenes per world yield 60 dev and 240 test. Baseline dev results from all three models are weighted equally. Selection candidates are K=2,3 and q=1,2,3, ranked by mean SR, mean SPL, fewer logical queries, smaller K, then smaller q. Frozen choices are Mars3/3, Moon2/3 and Cabin3/3. The reported test grid additionally includes K=1. Second-light results use the same freeze; no test-based adjustment.

## Stop rules

- **Baseline**: terminate at the scripted trajectory endpoint.
- **TRACE**: check native STOP before any query; otherwise query at t=0,q,2q,...; stop before the candidate action when K consecutive answers are Yes. No resets the count.
- **delay-only**: after the first Yes, wait (K−1)q action steps before stopping; preserve native STOP priority.
- **oracle_visibility**: replace the model answer with pixel-based visibility and replay TRACE. Visibility is not the same as being within the distance-success region.

The frozen core controller and parser are supplied unchanged in `sfb/`. Queries follow each model's actual answers; model frontiers are not copied across models. Parameter replay reads saved answers rather than calling the model again.

## Metrics and truth

SR uses a strict distance threshold: distance <20m for Mars/Moon, <2m for Cabin. SPL weights successful outcomes by path efficiency; OSR counts whether the executed prefix ever enters the region. NE and PL are in meters. Logical queries describe a replay's decisions, not new HTTP calls.

Visibility requires at least400 target pixels; Moon additionally requires mean target luminance≥10 on display-referred RGB8. All truth is evaluation-only.

## Model outputs and failures

Formal test uses the explicitly approved leading independent Yes/No parser, rejecting ambiguous/opposite labels, contradictions and refusal/uncertainty. A correlated completed model-format422 may provide a separate derived label; the raw response is never rewritten. Missing/unknown/authentication/protocol/identity errors are not No. Automatic retries are disabled. Individually authorized replacement attempts are linked to original failures, which remain retained in the private audit.

The 30-route post-hoc full-frame supplement uses the strict original client and is separately reported. It did not tune parameters or revise formal test results.

## Model identity

- Qwen: Qwen/Qwen2.5-VL-3B-Instruct, revision66285546d2b821cf421d4f5eb2576359d3770cd3.
- Lance: bytedance-research/Lance/Lance_3B, revision7395315758865e6f56ab87ad06a88c7ac172f056.
- Nova: amazon.nova-lite-v1:0 / amazon/nova-lite-v1, endpointamazon-bedrock/eu-west-1, contractspace-nova-lite-openrouter-judger-v2; max_tokens8, temperature0.00001, top_k1. This is first-generation Nova Lite.

Cloud internals are not independently observable. Historical campaign equivalence is not claimed.
