# Attribution and distribution scope

This local candidate is not a license grant. The project owner has not selected a software/data license. Third-party asset permissions must be assessed separately before public distribution of the included rendered examples. Source meshes, textures and model weights are absent.

| Component | Recorded source / attribution | Status |
|---|---|---|
| Mars terrain | USGS ASC Mars2020 TRN; Fergason et al.2020; DOI10.5066/P9REJ9JN | Preserve source attribution; no blanket CC0 claim |
| Moon terrain | PGDA/LOLA; Barker et al.2021 DOI10.1016/j.pss.2020.105119; Barker et al.2023 DOI10.3847/PSJ/acf3e1 | Product-specific distribution review |
| Lunar assets | Space Robotics Bench contributors; pinned asset provenance remains in source project | Per-asset attribution; no NASA endorsement |
| Rock material | Poly Haven Rock01; Dario Barresi, Greg Zaal, Jenelle van Heerden, Rico Cilliers; recorded CC0 source | Simulated lunar material, not measured lunar rock |
| Cabin / Astrobee | nasa/astrobee_media commit1cb0620121099cc848f5a3db480464188dc91ea3; source README identifies IGOAL ISS Interior | Code license does not automatically cover all media |
| Int-Ball assets in the full dataset | Space Robotics Bench commit16c5250f4359278abca646c2ef89da9e3ab2a747 | Independent rights pending; no source asset included |
| Code / labels / procedural geometry | Independently developed project | Owner's license decision pending |

## Included real illustrations

Exactly six original PNGs are copied unchanged, using the three pre-existing dev examples selected in the internal paired-light report:

- MarsA / mars_a_formal_007 / frame11, baseline35° and low_sun8°.
- MoonC / moon_c_formal_003 / frame11, psr and artificial sunlit comparison.
- CabinA / cabin_a_formal_v2_000 / frame12, normal and dim.

SHA256 and displayed-condition mapping are in [illustrations.json](../results/illustrations.json). The website may crop thumbnails through layout; the paired examples display the full16:9 RGB frame. No image generation, repainting, relighting or image re-encoding was used for this candidate.

The two result-chart PNGs are unchanged exports from the current Mars8 report. Original numeric reports are fingerprinted in [provenance.json](../results/provenance.json). Complete asset manifests and original failure evidence remain in the private development workspace.

Before publishing: confirm the six render examples' display rights, finalize author/owner attribution, select licenses separately for code and numerical data, and either clear or omit any unresolved asset-bearing material. New licenses must not silently override third-party terms.
