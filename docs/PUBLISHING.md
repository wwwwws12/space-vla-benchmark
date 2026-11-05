# Local preview and publication / 预览与发布

## Preview now

Open `site/dist/index.html` or `site/dist/index.zh-CN.html`. Both work without a build or server. Optional loopback preview from the repository root:

```bash
python -m http.server 8765 --bind 127.0.0.1 --directory site/dist
```

Then visit http://127.0.0.1:8765/ . The page loads its CSS, JavaScript, six real examples and numerical data locally. No npm install, CDN, analytics or inference endpoint is used.

## Prepare the new repository

Use [wwwwws12/space-vla-benchmark](https://github.com/wwwwws12/space-vla-benchmark) as the clean release destination. The HTTPS clone URL is `https://github.com/wwwwws12/space-vla-benchmark.git`. Upload only the `repository/` contents, preserving its structure and dotfiles. Do not copy the old development `.git`, its history, private logs, credentials, backup or audit directory.

The repository URL is configured. Private staging may retain pending metadata. Before public release, fill owner-approved authors, code/data license and asset permissions in `release-metadata.json` and update `site/dist/release-config.js` as needed. Update README citation/release status accordingly. These fields are intentionally not guessed. Source images are present for local review and still need publication clearance.

The prepared page has no fake Paper/DOI/Dataset download links. When a real public dataset location becomes available, add it with its version, checksum and license. Do not call the small result export the full dataset.

## GitHub Pages

The included `.github/workflows/pages.yml` publishes only `site/dist/`. It has a manual `workflow_dispatch` trigger; an ordinary push does not deploy it. After reviewing the material and uploading the repository, choose **Settings → Pages → Source: GitHub Actions**, then manually run **Publish reviewed project page** in Actions.

The workflow has been prepared, not run or deployed. Action versions/configuration follow the official [GitHub custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), consulted2026-11-05. Repository permissions and Pages setup must be confirmed on the actual new repository.

中文：仓库地址已接入，先审阅本地页面。私有暂存阶段可暂不填写许可证；正式公开前补齐署名、许可证及素材发布范围。上传范围仅为本候选包的repository目录内容，包括点文件。本次私有上传使用独立Git仓库，原工程remote与历史保留。GitHub Pages仍未部署，不把预计页面地址当作已上线链接。
