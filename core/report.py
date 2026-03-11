"""Markdown 报告生成器 — 面线点框架 9个模块"""


def generate_report(meta: dict, l1: dict, l2: dict, l3: dict, l4: dict,
                    creators, competitors: list) -> str:
    """生成完整的 Markdown 分析报告。"""
    sections = [
        _section_header(meta),
        _section_a_summary(meta, l1, l3, l4),
        _section_b_dashboard(l1, l2),
        _section_c_daily_trend(l3),
        _section_d_quadrant(l1, l4),
        _section_e_attribution(l3),
        _section_f_creators(creators),
        _section_g_comparison(l4),
        _section_h_recommendations(l1, l2, l3, l4),
        _section_i_scheduling(l3, meta),
        _section_footer(meta),
    ]
    return "\n\n".join(sections)


def _section_header(meta):
    return f"""# TT 直播活动分析报告 —「{meta['name']}」

> 活动周期：{meta['start_date']} ~ {meta['end_date']} ({meta['days']}天) | 地区：{meta['region']} | 预算：${meta['budget']:,.0f}
> 分析框架：面(现状) → 线(归因) → 点(行动)"""


def _section_a_summary(meta, l1, l3, l4):
    """A. 3句话老板摘要"""
    # 第1句：大盘概览
    s1 = (f"活动「{meta['name']}」在 {l1['days']} 天内实现 "
          f"{_fmt_num(l1['total_show_uv'])} 独立用户曝光、"
          f"{_fmt_num(l1['total_watch_uv'])} 用户看播，"
          f"CTR 为 {l1['ctr']*100:.2f}%，CPV ${l1['cpv']:.4f}。")

    # 第2句：核心发现
    if l3["uv_decay_slope"] < 0:
        s2 = (f"用户看播量以每天 {_fmt_num(abs(l3['uv_decay_slope']))} 的速度衰减，"
              f"首尾比为 {l3['head_tail_ratio']:.2f}，")
        if l3["inflection_day"]:
            s2 += f"关键拐点出现在第 {l3['inflection_day']} 天。"
        else:
            s2 += "衰减较为均匀。"
    else:
        s2 = f"用户看播量呈上升趋势，日均增长 {_fmt_num(l3['uv_decay_slope'])}，活动势能持续积累。"

    # 第3句：环比定位
    comp = l4.get("comparison", {})
    if comp:
        ctr_info = comp.get("ctr", {})
        if ctr_info.get("change_pct"):
            direction = "提升" if ctr_info["change_pct"] > 0 else "下降"
            s3 = f"对比上期「{l4['previous_name']}」，CTR {direction} {abs(ctr_info['change_pct'])*100:.1f}%。"
        else:
            s3 = f"对比基期为「{l4['previous_name']}」。"
    else:
        s3 = "暂无历史对比数据。"

    return f"""---

## 面（Surface）— 现状与结果

### A. 老板摘要（3句话）

1. {s1}
2. {s2}
3. {s3}"""


def _section_b_dashboard(l1, l2):
    """B. 大盘水位表"""
    rows = [
        ("**一级指标**", "", ""),
        ("总曝光人次 (Show PV)", _fmt_num(l1["total_show_pv"]), "规模"),
        ("总曝光人数 (Show UV)", _fmt_num(l1["total_show_uv"]), "规模"),
        ("总看播人次 (Watch PV)", _fmt_num(l1["total_watch_pv"]), "规模"),
        ("总看播人数 (Watch UV)", _fmt_num(l1["total_watch_uv"]), "规模"),
        ("总看播时长 (min)", _fmt_num(l1["total_watch_duration"]), "规模"),
        ("开播人数 (Go LIVE UV)", _fmt_num(l1["total_go_live_uv"]), "供给"),
        ("总开播时长 (min)", _fmt_num(l1["total_live_duration"]), "供给"),
        ("日均看播人数", _fmt_num(l1["daily_watch_uv"]), "效率"),
        ("千次曝光成本 CPM", f"${l1['cpm']:.4f}", "成本"),
        ("千次看播成本 CPV", f"${l1['cpv']:.4f}", "成本"),
        ("曝光点击转化率 CTR", f"{l1['ctr']*100:.2f}%", "效率"),
        ("人均看播时长 (min)", f"{l1['avg_watch_duration']:.2f}", "留存"),
        ("人均进房频次", f"{l1['view_frequency']:.2f}", "行为"),
        ("人均曝光频次", f"{l1['impression_frequency']:.2f}", "行为"),
        ("单主播获客红利", _fmt_num(l1["traffic_dividend"]), "供给效率"),
        ("人均开播时长 (min)", f"{l1['avg_live_duration']:.2f}", "供给"),
        ("", "", ""),
        ("**二级指标**", "", ""),
        ("供给消化率", f"{l2['supply_consumption_rate']:.2f}", "供需"),
        ("流量利用率", f"{l2['flow_utilization_rate']:.4f}", "效率"),
        ("主播时长密度 (min/人/天)", f"{l2['streamer_time_density']:.2f}", "供给"),
        ("观众时长密度 (min/人/天)", f"{l2['viewer_time_density']:.2f}", "留存"),
        ("PV/UV 离散度", f"{l2['pv_uv_dispersion']:.2f}", "行为"),
        ("供需比", f"{l2['supply_demand_ratio']:.4f}", "供需"),
    ]

    table = "| 指标 | 数值 | 维度 |\n| :--- | :--- | :--- |\n"
    for name, value, dim in rows:
        if name == "":
            continue
        table += f"| {name} | {value} | {dim} |\n"

    return f"""### B. 大盘水位表

{table}"""


def _section_c_daily_trend(l3):
    """C. 逐日趋势 + 事件标注"""
    daily = l3.get("daily_series")
    timeline = l3.get("events_timeline", [])
    inflection_day = l3.get("inflection_day", 0)

    if daily is None or daily.empty:
        return "### C. 逐日趋势\n\n暂无逐日数据。"

    # 日期到事件的映射
    date_events = {}
    for ev in timeline:
        d = str(ev["date"])
        date_events.setdefault(d, []).append(f"[{ev['source']}] {ev['name']}")

    table = "| Day | 日期 | Watch UV | CTR | Go LIVE UV | 事件 | 备注 |\n"
    table += "| :---: | :--- | ---: | ---: | ---: | :--- | :--- |\n"

    for _, row in daily.iterrows():
        day = int(row["day"])
        date = str(row["date"])
        uv = _fmt_num(row["watch_uv"])
        ctr = f"{row.get('daily_ctr', 0)*100:.2f}%" if "daily_ctr" in row else "-"
        live = _fmt_num(row["go_live_uv"])
        events_str = " / ".join(date_events.get(date, ["-"]))
        note = "**<< 拐点**" if day == inflection_day else ""
        table += f"| {day} | {date} | {uv} | {ctr} | {live} | {events_str} | {note} |\n"

    return f"""---

## 线（Line）— 归因与洞察

### C. 逐日趋势 + 事件标注

{table}

**时序指标**：
- UV 衰减斜率：{l3['uv_decay_slope']:+,.0f}/天 (R²={l3['uv_decay_r2']:.2f})
- CTR 疲劳速度：{l3['ctr_fatigue_slope']*100:+.4f}%/天 (R²={l3['ctr_fatigue_r2']:.2f})
- 供给稳定性 (CV)：{l3['supply_cv']:.3f} {'(稳定)' if l3['supply_cv'] < 0.15 else '(波动较大)' if l3['supply_cv'] > 0.3 else '(正常)'}
- 峰值日/均值比：{l3['peak_avg_ratio']:.2f} (峰值在第 {l3['peak_day']} 天)
- 周末效应系数：{l3['weekend_coefficient']:.2f}
- 首尾比：{l3['head_tail_ratio']:.2f} {'(虎头蛇尾)' if l3['head_tail_ratio'] > 1.5 else '(势能上升)' if l3['head_tail_ratio'] < 0.8 else '(相对均衡)'}"""


def _section_d_quadrant(l1, l4):
    """D. 效率-规模象限定位"""
    positioning = l4.get("positioning", {})
    if positioning.get("_note"):
        return f"""### D. 效率-规模象限定位

{positioning['_note']}

当前数据点：
- 规模 (Watch UV)：{_fmt_num(l1['total_watch_uv'])}
- 效率 (CPV)：${l1['cpv']:.4f}
- CTR：{l1['ctr']*100:.2f}%"""

    ctr_pos = positioning.get("ctr", {}).get("level", "未知")
    cpv_pos = positioning.get("cpv", {}).get("level", "未知")

    # 判定象限
    high_scale = l1["total_watch_uv"] > 0  # 简化判断
    high_eff = "优秀" in cpv_pos or "良好" in cpv_pos

    if high_scale and high_eff:
        quadrant = "理想状态（高规模 + 高效率）"
    elif high_scale:
        quadrant = "粗放增长（高规模 + 低效率）"
    elif high_eff:
        quadrant = "精准小众（低规模 + 高效率）"
    else:
        quadrant = "需警惕（低规模 + 低效率）"

    return f"""### D. 效率-规模象限定位

**当前象限**：{quadrant}

| 指标 | 当前值 | 基准线定位 |
| :--- | :--- | :--- |
| CTR | {l1['ctr']*100:.2f}% | {ctr_pos} |
| CPV | ${l1['cpv']:.4f} | {cpv_pos} |"""


def _section_e_attribution(l3):
    """E. 因果链归因"""
    timeline = l3.get("events_timeline", [])
    daily = l3.get("daily_series")
    inflection_day = l3.get("inflection_day", 0)
    inflection_date = l3.get("inflection_date", "")

    if not timeline:
        return "### E. 因果链归因\n\n暂无排期事件数据，无法进行归因分析。"

    # 找出与拐点日相关的事件
    related_events = []
    for ev in timeline:
        if ev["day"] and inflection_day:
            if abs(ev["day"] - inflection_day) <= 1:
                related_events.append(ev)

    lines = ["### E. 因果链归因\n"]

    if inflection_day and related_events:
        lines.append(f"**拐点分析**：第 {inflection_day} 天 ({inflection_date})，"
                     f"Watch UV 变化 {l3['inflection_change']:+,.0f}\n")
        lines.append("可能关联事件：")
        for ev in related_events:
            lines.append(f"- [{ev['source']}] {ev['name']} ({ev['type']}) — 预期影响：{ev['impact']}")
    elif inflection_day:
        lines.append(f"**拐点分析**：第 {inflection_day} 天 ({inflection_date})，"
                     f"Watch UV 变化 {l3['inflection_change']:+,.0f}，"
                     f"但未找到对应事件，可能为自然衰减或未记录的外部因素。")

    lines.append("\n**完整事件时间线**：\n")
    lines.append("| 日期 | Day | 事件 | 来源 | 类型 | 预期影响 |")
    lines.append("| :--- | :---: | :--- | :--- | :--- | :--- |")
    for ev in timeline:
        day_str = str(ev["day"]) if ev["day"] else "活动外"
        lines.append(f"| {ev['date']} | {day_str} | {ev['name']} | {ev['source']} | {ev['type']} | {ev['impact']} |")

    return "\n".join(lines)


def _section_f_creators(creators):
    """F. 创作者生态概览"""
    import pandas as pd
    if creators is None or (isinstance(creators, pd.DataFrame) and creators.empty):
        return "### F. 创作者生态概览\n\n暂无创作者数据。"

    total = len(creators)

    # 分层统计
    tier_counts = creators["tier"].value_counts().to_dict() if "tier" in creators.columns else {}
    vert_counts = creators["vertical"].value_counts().to_dict() if "vertical" in creators.columns else {}

    lines = [f"### F. 创作者生态概览\n"]
    lines.append(f"本期活动 Top 创作者共 **{total}** 位。\n")

    if tier_counts:
        lines.append("**体量分层**：\n")
        lines.append("| 分层 | 数量 | 占比 |")
        lines.append("| :--- | :---: | :---: |")
        for tier, count in tier_counts.items():
            if tier:
                lines.append(f"| {tier} | {count} | {count/total*100:.1f}% |")

    if vert_counts:
        lines.append("\n**垂直度分布**：\n")
        lines.append("| 类型 | 数量 | 占比 |")
        lines.append("| :--- | :---: | :---: |")
        for vert, count in vert_counts.items():
            if vert:
                lines.append(f"| {vert} | {count} | {count/total*100:.1f}% |")

    # 泛化风险
    non_game = sum(v for k, v in vert_counts.items() if k and "游戏" not in k and "电竞" not in k)
    if total and non_game / total > 0.5:
        lines.append(f"\n> 泛用户创作者占比 {non_game/total*100:.1f}%，存在 **泛化稀释风险**，可能拉低 CTR。")

    return "\n".join(lines)


def _section_g_comparison(l4):
    """G. 跨期对比"""
    comp = l4.get("comparison", {})
    prev_name = l4.get("previous_name", "无")

    if not comp:
        return "### G. 跨期对比\n\n暂无历史对比数据。建议在⑤历史汇总中追加数据后重新分析。"

    lines = [f"### G. 跨期对比（vs {prev_name}）\n"]
    lines.append("| 指标 | 本期 | 上期 | 变化 | 趋势 |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")

    metric_names = {
        "cpm": ("CPM", "$", 4),
        "cpv": ("CPV", "$", 4),
        "ctr": ("CTR", "%", 2),
        "avg_watch_duration": ("人均看播时长", "min", 2),
        "traffic_dividend": ("单主播获客红利", "", 0),
    }

    for key, (name, unit, decimals) in metric_names.items():
        data = comp.get(key, {})
        current = data.get("current", 0)
        previous = data.get("previous", 0)
        change = data.get("change_pct", 0)

        if unit == "$":
            cur_str = f"${current:.{decimals}f}"
            prev_str = f"${previous:.{decimals}f}"
        elif unit == "%":
            cur_str = f"{current*100:.{decimals}f}%"
            prev_str = f"{previous*100:.{decimals}f}%"
        elif unit == "min":
            cur_str = f"{current:.{decimals}f}"
            prev_str = f"{previous:.{decimals}f}"
        else:
            cur_str = f"{current:,.0f}"
            prev_str = f"{previous:,.0f}"

        trend = "↑" if change > 0.05 else "↓" if change < -0.05 else "→"
        change_str = f"{change*100:+.1f}%"

        lines.append(f"| {name} | {cur_str} | {prev_str} | {change_str} | {trend} |")

    # 基准线
    if l4.get("has_enough_history"):
        lines.append("\n**基准线定位**：\n")
        pos = l4.get("positioning", {})
        for metric, info in pos.items():
            if isinstance(info, dict) and "level" in info:
                lines.append(f"- {metric}: {info['level']}")
    else:
        lines.append("\n> 历史数据不足 3 期，基准线（P25/P50/P75）将在积累更多数据后自动生成。")

    return "\n".join(lines)


def _section_h_recommendations(l1, l2, l3, l4):
    """H. 行动建议表（规则驱动）"""
    recs = []

    # 规则1: CTR 过低
    if l1["ctr"] < 0.05:
        recs.append(("应该优化", f"CTR 仅 {l1['ctr']*100:.2f}%，低于 5% 基准",
                      "建议优化推流人群包和直播间封面设计，提高曝光-进房转化", "P0"))

    # 规则2: 衰减过快
    if l3["head_tail_ratio"] > 2.0:
        recs.append(("应该调整", f"首尾比 {l3['head_tail_ratio']:.2f}，活动后半段严重衰减",
                      "建议在活动中期（第 5-7 天）增加脉冲机制（加码奖励/KOL 团播）", "P0"))

    # 规则3: 供给波动大
    if l3["supply_cv"] > 0.3:
        recs.append(("应该稳定", f"供给稳定性 CV={l3['supply_cv']:.3f}，开播人数波动大",
                      "建议设定每日开播门槛激励，减少间歇性参与", "P1"))

    # 规则4: 单主播红利高但开播时长低
    if l1["avg_live_duration"] < 120 and l1["traffic_dividend"] > 3000:
        recs.append(("应该提门槛", f"单主播红利 {l1['traffic_dividend']:,.0f} 但人均开播仅 {l1['avg_live_duration']:.0f}min",
                      "建议将 Premium 开播门槛提升至日均 150 分钟", "P0"))

    # 规则5: 周末效应不足
    if l3["weekend_coefficient"] < 0.8:
        recs.append(("可以优化", f"周末效应系数 {l3['weekend_coefficient']:.2f}，周末看播低于工作日",
                      "建议增加周末专属排期或周末特别激励", "P2"))

    # 规则6: 供给消化率异常
    if l2["supply_consumption_rate"] < 50:
        recs.append(("需关注", f"供给消化率 {l2['supply_consumption_rate']:.1f}，大量开播时长无人观看",
                      "建议优化推流匹配机制或减少低质量开播", "P1"))

    # 规则7: PV/UV 离散度过高（封面疲劳）
    if l2["pv_uv_dispersion"] > 3.0:
        recs.append(("应该优化", f"PV/UV 离散度 {l2['pv_uv_dispersion']:.2f}，用户多次看到封面但不点击",
                      "建议更新封面素材或调整推流策略，减少无效曝光", "P1"))

    # 默认建议
    if not recs:
        recs.append(("持续追踪", "各项指标处于正常范围",
                      "建议继续保持当前策略，关注下期数据变化", "P2"))

    lines = ["""---

## 点（Point）— 启示与行动

### H. 行动建议\n"""]
    lines.append("| 建议类型 | 数据发现 | 建议行动 | 优先级 |")
    lines.append("| :--- | :--- | :--- | :---: |")
    for rec_type, finding, action, priority in recs:
        lines.append(f"| {rec_type} | {finding} | {action} | **{priority}** |")

    return "\n".join(lines)


def _section_i_scheduling(l3, meta):
    """I. 下期排期建议"""
    lines = ["### I. 下期排期建议\n"]

    inflection = l3.get("inflection_day", 0)
    head_tail = l3.get("head_tail_ratio", 1)
    weekend = l3.get("weekend_coefficient", 1)

    if inflection and head_tail > 1.5:
        lines.append(f"- 本期从第 **{inflection}** 天开始出现明显拐点，"
                     f"建议下期在第 {max(1, inflection-1)} 天安排中期刺激事件（如 KOL 团播/奖励加码）")

    if weekend < 0.9:
        lines.append("- 周末看播量低于工作日，建议下期增加周末专属活动或增加周末投放预算")
    elif weekend > 1.2:
        lines.append("- 周末看播量显著高于工作日，建议下期将重点资源集中在周末")

    if l3.get("supply_cv", 0) > 0.2:
        lines.append("- 开播人数波动较大，建议下期设置每日开播打卡激励，稳定供给侧")

    lines.append(f"\n**建议活动周期**：基于本期 {meta['days']} 天数据，"
                 f"有效活跃期约 {min(inflection + 2, meta['days']) if inflection else meta['days']} 天，"
                 f"建议下期活动周期控制在 {min(inflection + 3, 14) if inflection else 10}-"
                 f"{min(inflection + 5, 21) if inflection else 14} 天。")

    return "\n".join(lines)


def _section_footer(meta):
    return f"""---

> 报告由 tt-live-analysis 自动生成 | 活动：{meta['name']} | 数据框架：面-线-点
> 数据来源：TT 直播数据分析模板 v4.0"""


def _fmt_num(n):
    """格式化大数字"""
    if n is None:
        return "0"
    n = float(n)
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}亿"
    elif n >= 10_000_000:
        return f"{n/10_000:.0f}万"
    elif n >= 10_000:
        return f"{n/10_000:.1f}万"
    else:
        return f"{n:,.0f}"
