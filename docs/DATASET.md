# Dataset card

Two lighting conditions share900 route IDs across9 scenes. Each condition has32800 frames. Full image data are not bundled with this candidate; no public download URL has been announced.

| World | Scenes | Routes | Frames per condition | Lighting |
|---|---:|---:|---:|---|
| Mars | 3 | 300 | 9879 | Solar elevation35°→8° |
| Moon | 3 | 300 | 10821 | A/B sunlit→sun_east; C psr→sunlit |
| Cabin | 3 | 300 | 12100 | normal→dim |

Mars uses USGS Jezero terrain products with procedural objects and surface detail. Moon uses LOLA-derived terrain with explicitly synthetic additions. Cabin uses ISS interior geometry with experimental target layouts. Source terrain resolution is not improved by mesh interpolation. MoonC solar-on is an artificial paired condition.

The included [package index](../results/datasets.json) stores counts and original freeze digests. [Route splits](../results/route_splits.json) store the actual IDs/targets/splits for both lightings, with record digests. They contain no RGB, semantic or mask payloads.

When the separately distributed standalone data become available, each scene package has:

```text
<scene>/<variant>/T/
  dataset_manifest.json
  dataset_freeze.json
  data_sha256.json
  source_sha256.json
  route_directory_index.json
  judger_frame_index.jsonl
  truth_EVALUATION_ONLY.jsonl
  _provenance/
  <route_id>/
    record.json
    rgb/frame_*.png
    semantic/frame_*.npz
    semantic/frame_*_labels.json
    mask/frame_*.png
```

Read frame relationships from `record.json`, never guess a target or split from a filename. Images are1920×1080 RGB; mask values are0/255; NPZ contains integer semantic IDs. All-black target masks may be valid negatives. Truth must not be sent to a model. The exact contract is [dataset_format_v1.json](../protocols/dataset_format_v1.json).

After obtaining a complete standalone T directory:

```bash
python -B tools/verify_dataset.py --dataset PATH_TO_SCENE_T_DIRECTORY
```

This verifies saved files and associations; it does not perform model or renderer validation. The six demonstration PNGs in the website are real dev illustrations, not a representative training dataset. Publication rights remain subject to the asset review.
