---
name: tt-live-analysis
description: 读取 TT 直播数据分析模板 Excel，按活动名称自动计算四级指标体系并生成面-线-点结构化 Markdown 分析报告。
---
# TT 直播活动数据分析 Skill

当此 Skill 激活时，Agent 按以下步骤操作：

## 前置条件

- Python 3.9+
- 依赖：`pip3 install -r requirements.txt`（openpyxl, pandas, numpy）
- 用户需提供符合 v4.0 模板格式的 Excel 文件

## 使用方式

脚本路径：`/Users/lyon/my-app/tt-live-analysis/analyze.py`

### 1. 查看可用活动
```bash
python3 /Users/lyon/my-app/tt-live-analysis/analyze.py --file <excel_path> --list
```

### 2. 分析指定活动
```bash
python3 /Users/lyon/my-app/tt-live-analysis/analyze.py --file <excel_path> --activity "<活动名称>"
```

### 3. 自定义输出路径
```bash
python3 /Users/lyon/my-app/tt-live-analysis/analyze.py --file <excel_path> --activity "<活动名称>" --output report.md
```

### 4. 强制跳过缓存重新计算
```bash
python3 /Users/lyon/my-app/tt-live-analysis/analyze.py --file <excel_path> --activity "<活动名称>" --no-cache
```

## 输出内容

脚本会生成一份 Markdown 报告，包含 9 个模块（面-线-点框架）：

- **A. 老板摘要**：3 句话概括活动表现
- **B. 大盘水位表**：一二级指标全量（CPM/CPV/CTR/留存/供需等）
- **C. 逐日趋势**：日粒度数据 + 事件标注 + 拐点标记
- **D. 象限定位**：效率-规模四象限定位
- **E. 因果链归因**：数据异常 × 事件排期交叉验证
- **F. 创作者生态**：体量分层、垂直度分布、泛化风险
- **G. 跨期对比**：环比变化 + 历史分位数基准线
- **H. 行动建议**：规则驱动的优先级排序建议
- **I. 排期建议**：下期活动周期和关键节点建议

## 数据模板要求

Excel 文件必须包含以下 Sheet（名称必须精确匹配）：

| Sheet 名 | 内容 |
| :--- | :--- |
| ① 活动注册表 | 活动主表（名称=主键） |
| {活动名称} | 对应活动的日粒度 8 字段数据 |
| ③ 我方产品排期 | 排期事件（白区=我方，蓝区=竞品/外部） |
| ④ Top200 创作者 | 创作者列表 |
| ⑤ 历史汇总 | 历次活动汇总（用于跨期对比） |
| ⑥ 竞品监控 | 竞品清单 |

## Token 效率设计

- 只读取目标活动对应的 Sheet，其他活动数据不会被加载
- 排期和创作者按活动名筛选，只返回匹配行
- 计算结果缓存为 JSON，二次运行自动跳过已算指标
- Agent 只需读取输出的 Markdown 报告，无需接触原始 Excel
