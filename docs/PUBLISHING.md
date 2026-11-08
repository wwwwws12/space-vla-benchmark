# Local preview and publication / 预览与发布

## Live project page

GitHub Pages was deployed successfully on 2026-11-08 from reviewed commit `f438a34b9b3a53837cb13bcc4f7b17d116b47248`, serving `site/dist/`.

- [English project page](https://wwwwws12.github.io/space-vla-benchmark/)
- [中文项目介绍页](https://wwwwws12.github.io/space-vla-benchmark/index.zh-CN.html)
- [Successful deployment run](https://github.com/wwwwws12/space-vla-benchmark/actions/runs/42464977840)

The repository is public. The dataset Release remains a draft; deploying the website does not enable its public download links.

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

The 29 ZIP files and two metadata files have been uploaded and SHA256-verified in the `dataset-v1.0` draft Release. Public dataset downloads are not enabled. See [DOWNLOADS.md](DOWNLOADS.md) for package layout and verification, and [DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md) for source attribution and distribution status.

## GitHub Pages

The included `.github/workflows/pages.yml` publishes only `site/dist/`. It has a manual `workflow_dispatch` trigger; an ordinary push does not deploy it. After reviewing the material and uploading the repository, choose **Settings → Pages → Source: GitHub Actions**, then manually run **Publish reviewed project page** in Actions.

The workflow completed successfully on 2026-11-08. The Pages source is GitHub Actions and HTTPS is enforced. Action versions/configuration follow the official [GitHub custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), consulted2026-11-05. Future website updates require a new manual workflow run after pushing the reviewed files.

中文：GitHub Pages 已于2026-11-08部署成功，可通过上方中英文链接访问。仓库使用独立发布目录，原工程remote与历史保留。后续网页更新需要在推送审核后的文件后，手动运行上述工作流。数据集Release仍为草稿，公开下载尚未开放；署名、许可证及素材发布范围的待确认状态以相应文档为准。
