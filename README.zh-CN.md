# 太空 VLA Benchmark

**在太空仿真环境的固定轨迹上，评测视觉目标识别与语义停止策略。**

[GitHub](https://github.com/wwwwws12/space-vla-benchmark) · [项目介绍页（本地）](site/dist/index.zh-CN.html) · [English](README.md) · [评测协议](docs/PROTOCOL.md) · [数据说明](docs/DATASET.md) · [完整结果](results/summary.json)

> 当前为私有仓库中的发布候选包。作者和许可证待确认，公开发布及GitHub Pages部署尚未进行；第三方素材权利分别处理。见[发布状态](RELEASE_STATUS.md)。

| 火星 | 月球C配对光照 | 太空舱 |
|---|---|---|
| ![火星](site/dist/assets/mars_baseline.png) | ![月球](site/dist/assets/moon_second.png) | ![太空舱](site/dist/assets/cabin_baseline.png) |

以上为已有dev路线的真实仿真图像，保留原PNG字节。[图片来源](docs/ASSETS.md)。

## 项目研究什么？

模型判断“看到了目标”，是否就能让机器人在合适的位置停止？本项目采用Mars、Moon、Cabin各三个场景的脚本T轨，比较Qwen2.5-VL-3B、Lance_3B和Nova Lite 1.0在两种光照下的目标可见性判断，以及TRACE、delay-only、可见性Oracle的停止表现。

Isaac Sim负责渲染，模型只接收当前图像和目标短语。距离、坐标、mask和前次回答不进入模型输入。项目依据制作流程文档独立开发；当前实验是固定轨迹上的感知与停止分析，没有开展自主导航器或真机验证。

## 数据与划分

- 3世界、9场景、900条独立路线，两种光照分别32,800帧，共65,600帧。
- 每场景100条＝20 dev＋80 test；每世界60 dev＋240 test。
- 三模型基准dev等权共同选参，冻结Mars K3/q3、Moon K2/q3、Cabin K3/q3；test不调参。
- 第二光照保持路线、目标、相机和划分不变，直接沿用冻结参数。
- Mars太阳高度角35°→**8°**；Moon A/B改变太阳方位，C为人工solar-on对照；Cabin灯强60000→12000。旧Mars15°结果已退出主表。

## 主结果

主TRACE，每个单元格均为240条test路线：

| 世界 | 模型 | 基准 SR | 第二光照 SR | 差值（pp） |
|---|---|---:|---:|---:|
| Mars | Qwen2.5-VL-3B | 89/240 · 37.08% | 79/240 · 32.92% | -4.17 |
| Mars | Lance_3B | 130/240 · 54.17% | 133/240 · 55.42% | +1.25 |
| Mars | Nova Lite 1.0 | 85/240 · 35.42% | 97/240 · 40.42% | +5.00 |
| Moon | Qwen2.5-VL-3B | 67/240 · 27.92% | 53/240 · 22.08% | -5.83 |
| Moon | Lance_3B | 73/240 · 30.42% | 63/240 · 26.25% | -4.17 |
| Moon | Nova Lite 1.0 | 53/240 · 22.08% | 45/240 · 18.75% | -3.33 |
| Cabin | Qwen2.5-VL-3B | 69/240 · 28.75% | 52/240 · 21.67% | -7.08 |
| Cabin | Lance_3B | 68/240 · 28.33% | 37/240 · 15.42% | -12.92 |
| Cabin | Nova Lite 1.0 | 99/240 · 41.25% | 95/240 · 39.58% | -1.67 |

![双光照对比](site/dist/assets/01_trace_sr_paired.png)

2160个模型×路线对的主TRACE成功率由**33.94%降至30.28%**。9组中7组下降、2组上升。基准9/9、第二光照8/9组TRACE低于delay-only，保留负结果，不宣称普遍改善或统计显著。

网页可切换四种策略查看SR/SPL；结果文件还包含全部九格。Oracle用可见性真值替代模型回答，不是距离成功率的理论上界。

## 本地使用

使用Python3.12+即可汇总已有数值结果，无需安装依赖、启动模型或Isaac：

```powershell
python -B analysis/summarize_results.py
python -B analysis/summarize_results.py --method delay_only
python -B analysis/summarize_results.py --method oracle_visibility
python -B analysis/summarize_results.py --all-grid
```

上述命令重新聚合已保存的120960行回放指标，**不是重新推理或从图像重建成绩**。完整图像数据、第三方场景资产和模型权重尚未随候选包分发。

介绍页双击`site/dist/index.zh-CN.html`即可打开；也可执行：

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory site/dist
```

然后访问`http://127.0.0.1:8765/index.zh-CN.html`。无需Node、前端构建工具或外部CDN。

## 文件导航

| 目录 | 内容 |
|---|---|
| `sfb/` | 从当前工程原样提取的18个核心模块 |
| `results/` | 主表、全部九格、路线划分、数据清单与SHA来源 |
| `analysis/` | 离线汇总入口 |
| `site/dist/` | 中英文介绍页、真实双光照示例、交互结果表 |
| `protocols/`、`configs/` | 评测约定、数据格式与相机/动作配置 |
| `docs/` | 使用、复现边界、已知限制与发布说明 |

## 如实披露的边界

Qwen基准180条dev在线确认完成，动作/位姿前缀与同回答回放180/180一致，停止帧164/180一致。Cabin原光照与在线重拍83/1086组PSNR低于40dB；未发现采集关联/标注错误，但跨进程重复性尚未完全解决。采集1.273192秒/帧与含HTTP在线循环1.840710秒的计时口径不同。

Nova云端权重和全部变换不能独立观测，保留`campaign_match_verified=false`。原错误、UNKNOWN和显式补测证据保存在原开发工程；公开结果是脱敏后的数值投影，不包含完整逐请求审计。详见[限制](docs/LIMITATIONS.md)。

当前包可以用于本地审阅。正式公开前填写作者/单位，确定代码和数据许可证，并处理图片/第三方素材发布范围；不直接套用统一CC0。发布步骤见[维护者说明](docs/PUBLISHING.md)。
