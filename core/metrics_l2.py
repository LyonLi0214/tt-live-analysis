"""二级指标：交叉字段计算"""
import pandas as pd


def compute_l2(daily: pd.DataFrame, l1: dict) -> dict:
    """从日粒度数据和L1结果计算二级交叉指标。"""
    total = daily[["show_pv", "show_uv", "watch_pv", "watch_uv",
                    "watch_duration", "go_live_uv", "live_duration"]].sum()
    days = len(daily)

    # 供给消化率: 每分钟开播被观看了多少分钟
    supply_consumption = (total["watch_duration"] / total["live_duration"]) if total["live_duration"] else 0

    # 流量利用率: CTR × 消化率
    flow_utilization = l1["ctr"] * supply_consumption if supply_consumption else 0

    # 主播时长密度: 每个主播每天平均播多久
    streamer_time_density = (
        total["live_duration"] / (total["go_live_uv"] * days)
        if total["go_live_uv"] and days else 0
    )

    # 观众时长密度: 每个观众每天平均看多久
    viewer_time_density = (
        total["watch_duration"] / (total["watch_uv"] * days)
        if total["watch_uv"] and days else 0
    )

    # PV/UV 离散度
    show_freq = total["show_pv"] / total["show_uv"] if total["show_uv"] else 0
    watch_freq = total["watch_pv"] / total["watch_uv"] if total["watch_uv"] else 0
    pv_uv_dispersion = (show_freq / watch_freq) if watch_freq else 0

    # 供需比 (标准化)
    avg_watch = l1["avg_watch_duration"]
    avg_live = l1["avg_live_duration"]
    if total["watch_uv"] and avg_watch and total["go_live_uv"] and avg_live:
        supply_demand_ratio = (total["go_live_uv"] * avg_live) / (total["watch_uv"] * avg_watch)
    else:
        supply_demand_ratio = 0

    return {
        "supply_consumption_rate": supply_consumption,
        "flow_utilization_rate": flow_utilization,
        "streamer_time_density": streamer_time_density,
        "viewer_time_density": viewer_time_density,
        "pv_uv_dispersion": pv_uv_dispersion,
        "supply_demand_ratio": supply_demand_ratio,
    }
