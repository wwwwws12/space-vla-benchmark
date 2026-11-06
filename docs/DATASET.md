# Dataset card

Two lighting conditions share **900 route IDs across 9 scenes**. Each condition has **32,800 frames**, for **65,600 frames in total**. Each scene has 100 routes (20 dev + 80 test); each world has 300 routes (60 dev + 240 test). Splits, routes, targets and camera settings are shared between lighting conditions.

| World | Scenes | Routes | Frames per condition | Lighting |
|---|---:|---:|---:|---|
| Mars | 3 | 300 | 9,879 | Solar elevation 35° → 8° |
| Moon | 3 | 300 | 10,821 | A/B sunlit → sun_east; C psr → sunlit |
| Cabin | 3 | 300 | 12,100 | normal → dim |

Mars uses USGS Jezero terrain products with procedural objects and surface detail. Moon uses LOLA-derived terrain with explicitly synthetic additions. Cabin uses ISS interior geometry with experimental target layouts. Source terrain resolution is not improved by mesh interpolation. Moon C solar-on is an artificial paired condition.

## Complete dataset downloads

The RGB images, semantic annotations, target masks and route metadata are packaged separately from this code repository. Six groups cover each world × lighting combination. A group may contain several independently extractable ZIP files. Download every part of a selected group and extract them into the same directory. Download all six groups for the complete dataset.

The [download panel](../site/dist/index.html#dataset-downloads) lists actual archive sizes, SHA256 values and availability. Local packages are served by `scripts/preview_site.ps1`; public hosting URLs have not yet been configured. See the bilingual [download guide](DOWNLOADS.md).

```text
space-vla-dataset-v1/
  <world>/<baseline-or-second>/
    dataset_manifest.json
    README.md
    ASSET_ATTRIBUTION.md
    verify_dataset_download.py
    _checksums/partNN.json
    <scene>/<variant>/T/
      dataset_manifest.json
      route_directory_index.json
      judger_frame_index.jsonl
      truth_EVALUATION_ONLY.jsonl
      <route_id>/
        record.json
        rgb/frame_*.png
        semantic/frame_*.npz
        semantic/frame_*_labels.json
        mask/frame_*.png
```

Read frame relationships from `captures[].files` in each `record.json`. These paths are relative to that route's directory; the optional top-level `image_path` is not a path rooted at the downloaded directory. Do not guess a target or split from filenames. Images are 1920 × 1080 RGB; mask values are 0/255; NPZ contains integer semantic IDs. All-black target masks may be valid negative observations. `captures[].sha256` preserves the original per-frame payload digests.

The download container uses **`sfb.download.v1`**. Its scene and group manifests describe the exported content. Route records retain the original source `schema_id` marker and task values, with a declared metadata projection: internal `source` fields, the historical lighting-profile path and the renderer module's machine path are omitted. `download_provenance` adds the original record, scene manifest and freeze SHA256 values. Thus the exported record digest differs from its original record digest; image and label bytes are unchanged. This projection is not the original standalone archive format.

Use the dedicated verifier after extracting all parts. From this repository:

```bash
python -B scripts/verify_dataset_download.py PATH_TO_EXTRACTED/space-vla-dataset-v1
```

Alternatively, run the `verify_dataset_download.py` included in a group's directory against that directory. The verifier checks the saved byte lengths and SHA256 values against every part's inventory. This is a transfer-integrity check, not a rerun of task-semantic validation, rendering or model evaluation. Check each ZIP against the accompanying `SHA256SUMS` before extraction.

## Evaluation truth and provenance

The separate `truth_EVALUATION_ONLY.jsonl` files contain evaluation truth. Distances, visibility truth, semantic labels, masks and poses must not be sent to the visual Judger as model input. The model receives only the RGB image and target phrase, following the [protocol](PROTOCOL.md).

The saved truth-index naming differs by condition: baseline rows use `distance_m`, while second-light rows use `target_distance_m`. Read either key when comparing those files. Route-record captures consistently use `target_distance_m`. These original indices are preserved byte for byte.

The included [source package index](../results/datasets.json) stores counts and original freeze digests. [Route splits](../results/route_splits.json) store the original IDs, targets, splits and record digests for both lightings. These numerical metadata remain bound to the original experiment data, while the download manifest describes the derived portable package.

The original internal standalone format is documented in [dataset_format_v1.json](../protocols/dataset_format_v1.json). `tools/verify_dataset.py` applies to that complete internal format, including its `_provenance` tree; use `scripts/verify_dataset_download.py` for these downloadable packages.

The download packages omit scene source meshes/textures, model weights, inference services and private execution logs. Source attribution and distribution status are recorded in [DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md); package preparation does not grant additional third-party rights.
