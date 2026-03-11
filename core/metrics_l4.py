"""四级指标：跨期对比与自建基准线"""
import numpy as np


def compute_l4(l1: dict, l2: dict, historical: dict, cache_baselines: dict = None) -> dict:
    """跨期对比 + 基准线计算。

    Args:
        l1: 当前活动的一级指标
        l2: 当前活动的二级指标
        historical: reader 返回的历史汇总数据
        cache_baselines: 缓存的基准线（可选）

    Returns:
        dict with comparison, baselines, positioning
    """
    hist_activities = historical.get("activities", [])
    existing_baselines = historical.get("baselines", {})

    # --- 找到上一期活动做环比 ---
    previous = _find_previous(l1["budget"], hist_activities, l1.get("_activity_name", ""))
    comparison = _compute_comparison(l1, previous) if previous else {}

    # --- 计算基准线 ---
    if cache_baselines:
        baselines = cache_baselines
    elif existing_baselines and all(existing_baselines.get(k) for k in ["P75", "P50", "P25"]):
        baselines = existing_baselines
    else:
        baselines = _compute_baselines(hist_activities)

    # --- 当前指标在基准线中的定位 ---
    positioning = _position_vs_baselines(l1, baselines)

    # --- 供给弹性 ---
    supply_elasticity = 0
    if previous and previous.get("budget") and previous["budget"] > 0:
        budget_change_pct = (l1["budget"] - previous["budget"]) / previous["budget"]
        uv_change_pct = (l1["total_watch_uv"] - previous.get("watch_uv", 0)) / previous.get("watch_uv", 1)
        supply_elasticity = (uv_change_pct / budget_change_pct) if budget_change_pct else 0

    return {
        "previous_name": previous.get("name", "无") if previous else "无",
        "comparison": comparison,
        "baselines": baselines,
        "positioning": positioning,
        "supply_elasticity": supply_elasticity,
        "has_enough_history": len(hist_activities) >= 3,
    }


def _find_previous(current_budget, hist_activities: list, current_name: str) -> dict:
    """在历史活动中找到最近的一期（排除当前）"""
    for act in hist_activities:
        if act["name"] != current_name:
            return act
    return None


def _compute_comparison(l1: dict, previous: dict) -> dict:
    """计算环比变化"""
    comparisons = {}
    metric_map = {
        "cpm": ("budget", "show_pv", lambda b, sp: b / sp * 1000 if sp else 0),
        "cpv": ("budget", "watch_pv", lambda b, wp: b / wp * 1000 if wp else 0),
        "ctr": ("watch_uv", "show_uv", lambda wu, su: wu / su if su else 0),
        "avg_watch_duration": ("watch_duration", "watch_uv", lambda wd, wu: wd / wu if wu else 0),
        "traffic_dividend": ("watch_uv", "go_live_uv", lambda wu, gl: wu / gl if gl else 0),
    }

    for metric, (num_key, den_key, formula) in metric_map.items():
        current_val = l1.get(metric, 0)
        prev_val = formula(previous.get(num_key, 0), previous.get(den_key, 0))
        if prev_val:
            change_pct = (current_val - prev_val) / prev_val
        else:
            change_pct = 0
        comparisons[metric] = {
            "current": current_val,
            "previous": prev_val,
            "change_pct": change_pct,
        }

    return comparisons


def _compute_baselines(hist_activities: list) -> dict:
    """从历史数据计算 P25/P50/P75 基准线"""
    if len(hist_activities) < 3:
        return {"_insufficient": True}

    metrics_to_baseline = {}
    for act in hist_activities:
        budget = act.get("budget", 0)
        sp = act.get("show_pv", 0)
        wp = act.get("watch_pv", 0)
        su = act.get("show_uv", 0)
        wu = act.get("watch_uv", 0)
        wd = act.get("watch_duration", 0)

        cpm = (budget / sp * 1000) if sp else 0
        cpv = (budget / wp * 1000) if wp else 0
        ctr = (wu / su) if su else 0
        avg_wd = (wd / wu) if wu else 0

        for k, v in [("cpm", cpm), ("cpv", cpv), ("ctr", ctr), ("avg_watch_duration", avg_wd)]:
            metrics_to_baseline.setdefault(k, []).append(v)

    baselines = {}
    for label, pct in [("P25", 25), ("P50", 50), ("P75", 75)]:
        baselines[label] = {}
        for metric, values in metrics_to_baseline.items():
            baselines[label][metric] = float(np.percentile(values, pct))

    return baselines


def _position_vs_baselines(l1: dict, baselines: dict) -> dict:
    """判断当前指标在基准线中的位置"""
    if baselines.get("_insufficient"):
        return {"_note": "历史数据不足3期，暂无基准线"}

    positioning = {}
    for metric in ["cpm", "cpv", "ctr", "avg_watch_duration"]:
        current = l1.get(metric, 0)
        p25 = baselines.get("P25", {}).get(metric, 0)
        p50 = baselines.get("P50", {}).get(metric, 0)
        p75 = baselines.get("P75", {}).get(metric, 0)

        # CPM/CPV 越低越好，CTR/时长 越高越好
        if metric in ["cpm", "cpv"]:
            if current <= p25:
                level = "优秀 (低于P25)"
            elif current <= p50:
                level = "良好 (P25-P50)"
            elif current <= p75:
                level = "一般 (P50-P75)"
            else:
                level = "预警 (高于P75)"
        else:
            if current >= p75:
                level = "优秀 (高于P75)"
            elif current >= p50:
                level = "良好 (P50-P75)"
            elif current >= p25:
                level = "一般 (P25-P50)"
            else:
                level = "预警 (低于P25)"

        positioning[metric] = {"value": current, "level": level, "p25": p25, "p50": p50, "p75": p75}

    return positioning
