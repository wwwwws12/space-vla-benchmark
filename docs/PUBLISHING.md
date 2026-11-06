# Local preview and publication / 预览与发布

## Preview now

Open `site/dist/index.html` or `site/dist/index.zh-CN.html` to view the page. For local dataset downloads, use the loopback preview from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\preview_site.ps1
```

Then visit `http://127.0.0.1:8766/index.html` or `http://127.0.0.1:8766/index.zh-CN.html`. The page loads its CSS, JavaScript, scene media and numerical data locally. No npm install, CDN, analytics or inference endpoint is used. Keep the preview window open during downloads. If a preview was already running before the download module was added, stop that preview with Ctrl+C and start it again.

In the development workspace, the launcher locates the prepared packages automatically. For another local copy, pass `-DatasetDirectory 'PATH_TO_PACKAGES'`; keep the accompanying `COMPLETE.json` in that directory's parent. The launcher serves only the listed archive files and manifests. A generic static file server cannot serve these separate data packages.

## Prepare the new repository

Use [wwwwws12/space-vla-benchmark](https://github.com/wwwwws12/space-vla-benchmark) as the clean release destination. The HTTPS clone URL is `https://github.com/wwwwws12/space-vla-benchmark.git`. Upload only the `repository/` contents, preserving its structure and dotfiles. Do not copy the old development `.git`, its history, private logs, credentials, backup or audit directory.

The repository URL is configured. Private staging may retain pending metadata. Before public release, fill owner-approved authors, code/data license and asset permissions in `release-metadata.json` and update `site/dist/release-config.js` as needed. Update README citation/release status accordingly. These fields are intentionally not guessed. Source images are present for local review and still need publication clearance.

## Dataset hosting

The six dataset groups are separate from the code checkout and the static site. Their names, sizes and SHA256 values are in `site/dist/downloads/dataset-downloads.json`; `site/dist/dataset-downloads-data.js` contains the same catalog for the page. Local packages have `status: local_ready`; their public `url` fields remain null until the actual files have been hosted.

When publishing the dataset, upload the ZIP files plus `dataset_manifest.json` and `SHA256SUMS` to the chosen dataset host. Set each archive's and both manifest links' `url` to its actual HTTPS download URL in both site catalogs. Preserve filenames, byte sizes and SHA256 values. Confirm the public links before uploading the updated website. The preview-only `local_url` values are ignored on public hosts. Keep large ZIPs outside this code repository and `site/dist/`.

The current local preparation has not uploaded or published these data. See [DOWNLOADS.md](DOWNLOADS.md) for package layout and verification, and [DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md) for source attribution and distribution status.

## GitHub Pages

The included `.github/workflows/pages.yml` publishes only `site/dist/`. It has a manual `workflow_dispatch` trigger; an ordinary push does not deploy it. After reviewing the material and uploading the repository, choose **Settings → Pages → Source: GitHub Actions**, then manually run **Publish reviewed project page** in Actions.

The workflow has been prepared, not run or deployed. Action versions/configuration follow the official [GitHub custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), consulted2026-11-05. Repository permissions and Pages setup must be confirmed on the actual new repository.

中文：仓库地址已接入，先审阅本地页面。私有暂存阶段可暂不填写许可证；正式公开前补齐署名、许可证及素材发布范围。上传范围仅为本候选包的repository目录内容，包括点文件。本次私有上传使用独立Git仓库，原工程remote与历史保留。GitHub Pages仍未部署，不把预计页面地址当作已上线链接。
