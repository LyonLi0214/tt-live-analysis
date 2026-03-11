# TT Live Streaming Activity Analyzer

TikTok 直播活动数据分析工具 — 从 Excel 模板自动计算四级指标并生成结构化报告。

## Quick Start

```bash
# 安装依赖
pip3 install -r requirements.txt

# 查看可用活动
python3 analyze.py --file template.xlsx --list

# 分析指定活动
python3 analyze.py --file template.xlsx --activity "S3赛季BR直播"
```

## Features

- **选择性读取**：只加载目标活动数据，不浪费资源
- **四级指标体系**：基础比值 → 交叉字段 → 时序分析 → 跨期对比
- **缓存机制**：历史指标和基准线缓存为 JSON，避免重复计算
- **面-线-点报告**：自动生成 9 模块结构化 Markdown 报告
- **事件归因**：日粒度数据 × 排期事件交叉验证

## Indicator System

| Level | Indicators |
| :--- | :--- |
| L1 Basic | CPM, CPV, CTR, Avg Watch Duration, View Frequency, Traffic Dividend |
| L2 Cross-field | Supply Consumption Rate, Flow Utilization, PV/UV Dispersion |
| L3 Time-series | UV Decay Slope, CTR Fatigue, Supply CV, Inflection Point, Weekend Effect |
| L4 Cross-period | Period-over-Period Change, Supply Elasticity, P25/P50/P75 Baselines |

## Template

Requires the v4.0 Excel template with sheets: Activity Registry, Daily Data (per activity), Schedule, Creators, Historical Summary, Competitor Monitor.
