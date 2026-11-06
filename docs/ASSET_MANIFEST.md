# Project-page video asset manifest

Version: `project-page-dev-replay-20261105-v1`. These assets are locally generated presentation exports, not newly collected experiment data.

| Asset | Provenance | Format / size | Version / license | Local path |
|---|---|---|---|---|
| mars | isaac_mars_a / `mars_a_formal_007` / baseline dev; 33 saved RGB frames | MP4 H.264 yuv420p, 1920×1080, 30fps, 19.8s, 2076718 bytes, no audio | 20261105-v1; project license unselected, per-source public rights pending | `site/dist/videos/mars-dev.mp4` |
| moon | isaac_moon_c / `moon_c_formal_003` / baseline dev; 34 saved RGB frames | MP4 H.264 yuv420p, 1920×1080, 30fps, 20.4s, 1883585 bytes, no audio | 20261105-v1; project license unselected, per-source public rights pending | `site/dist/videos/moon-dev.mp4` |
| cabin | isaac_cabin_a / `cabin_a_formal_v2_000` / baseline dev; 37 saved RGB frames | MP4 H.264 yuv420p, 1920×1080, 30fps, 22.2s, 2008069 bytes, no audio | 20261105-v1; project license unselected, per-source public rights pending | `site/dist/videos/cabin-dev.mp4` |

Each source frame is held for0.6s with no interpolation. Full-route frame order is retained. No scores or invented model answers are added.

[Video file and input-frame SHA256](../results/videos.json) · [Third-party source attribution](ASSETS.md)

The existing paired-light illustration selection is reused. Posters retain their original PNG bytes. No external download, model request or Isaac rendering was performed.

## Inline playback compatibility exports (20261105-v2)

- `site/dist/videos/mars-dev.webm`: 4150704 bytes, WebM VP8, 1920x1080, 30fps, silent, 19.8s. Same `mars_a_formal_007` frozen dev RGB source and timing as the MP4 above. Version v2; same pending source rights and unselected project license. SHA256: `6c55b2e6c6b2a3dc7d06a990109fda95cb8e7c1f459596e5e5f82845e0d81dd9`.
- `site/dist/videos/moon-dev.webm`: 3012738 bytes, WebM VP8, 1920x1080, 30fps, silent, 20.4s. Same `moon_c_formal_003` frozen dev RGB source and timing as the MP4 above. Version v2; same pending source rights and unselected project license. SHA256: `188d38b733923e3d4191b5e20c42243cf9eed9c52e5c3cd82b6281eafd8f03b8`.
- `site/dist/videos/cabin-dev.webm`: 3542780 bytes, WebM VP8, 1920x1080, 30fps, silent, 22.2s. Same `cabin_a_formal_v2_000` frozen dev RGB source and timing as the MP4 above. Version v2; same pending source rights and unselected project license. SHA256: `d9b7c599742cba17ed1a02467da285a46a0e02e4aa6addfe0fd8df8eba17dce6`.

## TRACE K/q grid figures (20261105 document layout)

- `site/dist/assets/trace_grid_baseline.png`: 177208 bytes, PNG, unchanged from `runs/deliveries/benchmark_delivery_20261105_02/charts/trace_grid_baseline.png`; version `benchmark_delivery_20261105_02`; license: Project chart; owner license selection pending. SHA256 `c837f783cbc5705b11b217d72dfb7060149f9d0f15ee5f3579370a9a27395312`.
- `site/dist/assets/trace_grid_second.png`: 175163 bytes, PNG, unchanged from `runs/deliveries/benchmark_delivery_20261105_02/charts/trace_grid_second.png`; version `benchmark_delivery_20261105_02`; license: Project chart; owner license selection pending. SHA256 `63ee55076c934e038c6fb1f4ee8dd424423977ba605f7ded9eb2fb5d2294392d`.

## README animated preview

- `site/dist/assets/scene-preview.gif`: 1633090 bytes; GIF, 720x405, 5fps, 128 colors, silent looping preview; 14.4s total (first4.8s from each existing Mars/Moon/Cabin MP4). Version `readme-layout-20261105-v1`. Source rights unchanged and pending; see `results/preview.json` for exact sources and SHA256. Output SHA256 `33692a14aaad3e3715455b4ed121b5e821dbfeb1e8d4693ac9d80cbdfb637338`. No rendering or model inference.
