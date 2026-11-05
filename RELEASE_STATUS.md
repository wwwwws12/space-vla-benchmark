# Private repository staging candidate / 私有仓库发布候选包

Prepared offline on2026-11-05 for user-authorized private GitHub staging. Public release and GitHub Pages deployment remain pending. No new inference or render was performed.

## Prepared

- English/Chinese research README and static project page.
- Real paired dev illustrations with SHA provenance; current Mars8 results only.
- 18 original core modules and the standalone data verifier.
- 120960 numerical rollout rows,72 primary result rows, fixed route splits and public protocol projection.
- Offline table-aggregation script and manual GitHub Pages workflow.

## Confirmed repository

[wwwwws12/space-vla-benchmark](https://github.com/wwwwws12/space-vla-benchmark)

HTTPS clone URL: `https://github.com/wwwwws12/space-vla-benchmark.git`. The web address is configured in both READMEs and both project pages. Authenticated GitHub API inspection confirmed this destination is private and writable; its remote refs were empty before the initial upload. Public Pages deployment is not part of this upload.

## Owner decisions before public release

1. Authors, affiliations and public contact (do not invent an institution or paper).
2. License for project-owned code and numerical data.
3. Approval/rights for the six rendered examples and any later full-data distribution.

These decisions can remain pending during private staging. No open-source license has been granted by this candidate.

The repository URL is filled in `release-metadata.json` and `site/dist/release-config.js`; add the remaining approved metadata when decided. No LICENSE/CITATION file is fabricated. The publication workflow is manual-only and cannot deploy on an ordinary push.

## Boundaries

The small candidate contains core source and saved numerical results, not full datasets/world assets or a turnkey original-campaign launcher. See `docs/CODE_SCOPE.md` and `docs/REPRODUCIBILITY.md`. Local original data, caches, failures, old Git history and reports remain unchanged. A new repository does not erase anything already present in the old repository.

本地预览：打开`site/dist/index.zh-CN.html`。正式上传只使用本目录`repository`的内容，不上传外层audit、原工程的runs/backup或旧.git。
