# Limitations and negative results

## Task validity

The mainline uses fixed scripted T trajectories. It evaluates visibility judgments and semantic stopping in simulation. It does not establish autonomous route planning, real-robot navigation, manipulation, flight dynamics or historical author-campaign equivalence. Development follows a supplied document independently; legacy UE/AirSim source compatibility is outside the agreed delivery scope and remains unverified.

## Lighting and model differences

Seven of nine TRACE model×world groups worsen under the second lighting, while two improve. TRACE is below delay-only in nine baseline and eight second-light groups. No statistical significance is asserted. Route identities repeat across models and conditions. Nova's native cloud weights and full request transformations are not independently observable (`campaign_match_verified=false`).

## Online confirmation

Only Qwen's180 baseline dev routes underwent the full online confirmation. Action/pose prefixes and same-answer controller replay agree on180/180. Stop frames agree on164/180, reasons on172/180 and common answers on1229/1258. Those checks have different denominators; none should be called universal bitwise equivalence.

## Cabin repeatability and timing

83/1086 original-light versus online-recaptured frame pairs are below40dB PSNR. This is not a comparison between the intentional two lighting conditions. An offline investigation of83 flagged pairs plus22 controls found no acquisition-association/annotation error. Independent renderer candidates did not eliminate cross-process variation and were not adopted into the formal dataset.

The original300 Cabin routes have a route-inner capture average1.273192s/frame, measured from first capture_begin to last capture_saved, including inter-frame work but excluding initialization, first-pose preparation, shutdown and model HTTP. One route mean exceeds1.5s. The old1.236845s value is a narrower event measure. The HTTP-inclusive online loop remains1.840710s: render0.735464, amortized HTTP0.667040 and save/check/control0.438206s. These boundaries must not be conflated.

## Supplement and failures

MoonA/CabinA first30-route full-frame supplementation was retrospective and descriptive, including fixed dev/test routes. It did not tune prompts/layouts/parameters or rewrite original grades. Raw invalid/UNKNOWN responses and explicit authorized replacement attempts remain in the private engineering audit. Public numerical metrics preserve final outcomes but do not provide the complete request-level audit or billing record.

## Availability

Full image data, third-party assets, weights and private model services are not in this candidate. Licenses and attribution require owner confirmation before publication. The project does not claim that every original document acceptance threshold passed without exception.
