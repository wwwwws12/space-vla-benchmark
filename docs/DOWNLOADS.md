# Dataset downloads / 数据下载

The full baseline and second-light image datasets are packaged in six world × lighting groups. The two conditions share **900 unique paired routes**, with **65,600 frames in total**. Each group covers 300 routes, including 60 dev and 240 test routes.

完整数据按三个世界、两种光照分成六组。每组 300 条路线，含 60 dev 与 240 test；两种光照共享路线，不能算作 1,800 条独立路线。

| World / 世界 | Baseline / 基准帧数 | Second lighting / 第二光照帧数 |
|---|---:|---:|
| Mars | 9,879 | 9,879 |
| Moon | 10,821 | 10,821 |
| Cabin | 12,100 | 12,100 |

## Find the files / 查找文件

Open the [English download panel](https://wwwwws12.github.io/space-vla-benchmark/#dataset-downloads) or [中文下载区](https://wwwwws12.github.io/space-vla-benchmark/index.zh-CN.html#dataset-downloads). Each group lists the actual ZIP byte sizes, filenames and SHA256 values. A complete dataset manifest and SHA256SUMS file accompany the archives. The metadata list is [dataset-downloads.json](../site/dist/downloads/dataset-downloads.json).

The [dataset-v1.0 Release](https://github.com/wwwwws12/space-vla-benchmark/releases/tag/dataset-v1.0) contains all 29 ZIP archives plus `dataset_manifest.json` and `SHA256SUMS`. The public project page links to the same Release assets. No GitHub sign-in is required to download them.

全部29个ZIP分包、`dataset_manifest.json` 与 `SHA256SUMS` 已在 [dataset-v1.0 Release](https://github.com/wwwwws12/space-vla-benchmark/releases/tag/dataset-v1.0) 发布。中英文网页下载按钮指向这些同名附件，无需登录GitHub即可下载。

From the repository root / 在仓库根目录运行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\preview_site.ps1
```

## Download and extract / 下载与解压

1. Select the world and lighting you need. Download **every ZIP listed in that group**, plus `dataset_manifest.json` and `SHA256SUMS`.
2. Check each ZIP's SHA256 against the matching entry in `SHA256SUMS` before extracting it.
3. Extract every ZIP into the **same empty destination directory**. These are independent ZIP archives containing complete routes; do not concatenate their bytes. Download all six groups for the complete dataset.
4. Keep the manifest and checksum list with the extracted data. From the code repository, run `python -B scripts/verify_dataset_download.py PATH_TO_EXTRACTED/space-vla-dataset-v1`. Each extracted group also contains its own copy of `verify_dataset_download.py`. The downloadable container uses the dedicated `sfb.download.v1` format.

1. 选择世界和光照，下载该组列出的**全部 ZIP**、`dataset_manifest.json` 与 `SHA256SUMS`。
2. 先逐包比对 SHA256，再解压；文件大小仅供核对容量，不能代替 SHA256。
3. 全部解压到**同一个空目录**。每个 ZIP 包含完整路线，独立可解压，无需拼接文件；需要完整数据时下载全部六组。
4. 保留数据清单和校验清单。在代码仓库执行 `python -B scripts/verify_dataset_download.py 解压目录/space-vla-dataset-v1`；每组包内也附带同一校验器 `verify_dataset_download.py`。下载容器采用独立的 `sfb.download.v1` 数据格式。

Check one downloaded archive / 单包 SHA256 示例：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\YOUR_DOWNLOADED_FILE.zip'
```

Compare the returned hash with that filename's entry in `SHA256SUMS`. On systems with `sha256sum`, placing all downloaded files and `SHA256SUMS` in the same directory allows verification with `sha256sum -c SHA256SUMS`; downloading only selected groups will leave other entries missing.

将返回值与 `SHA256SUMS` 中同名文件的记录逐字比较。若使用 `sha256sum -c SHA256SUMS`，仅下载部分组时，其余文件会显示缺失，不能据此认定已下载文件损坏。

## Contents and use / 内容与用途

Packages include the complete RGB images, semantic IDs and labels, target masks, route/task metadata, frozen dev/test splits and evaluation-only truth. The source PNG and NPZ bytes are retained. Download metadata use portable paths and retain source hashes; private service records and internal history paths are excluded.

数据包保留完整 RGB、语义 ID 与标签、目标 mask、路线及任务元数据、冻结划分和仅供评测的真值。原 PNG、NPZ 字节保留；下载元数据使用可移植路径并记录来源哈希，不包含私有服务记录与内部历史路径。

Distance, visibility, masks and other evaluation truth must **not** be supplied to the visual Judger as model input. Follow the [protocol](PROTOCOL.md) and [dataset specification](DATASET.md). Third-party scene source assets, model weights and inference services are not included. Dataset attribution and distribution status are described in [DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md). The verifier checks transfer integrity; it does not repeat model evaluation or task-semantic acceptance.

距离、可见性、mask 等评测真值**不能传入模型**。使用时遵循[评测协议](PROTOCOL.md)与[数据说明](DATASET.md)。第三方场景源资产、模型权重和推理服务不包含在数据包内，素材署名及分发状态见 [DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md)。校验器检查文件传输完整性，不重新执行模型评测或任务语义验收。
