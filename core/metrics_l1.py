"""一级指标：基础比值计算"""
import pandas as pd


def compute_l1(daily: pd.DataFrame, meta: dict) -> dict:
    """从日粒度数据计算一级基础指标。

    Args:
        daily: 日粒度 DataFrame
        meta: 活动元信息（含 budget）

    Returns:
        dict of metric_name -> value
    """
    total = daily[["show_pv", "show_uv", "watch_pv", "watch_uv",
                    "watch_duration", "go_live_uv", "live_duration"]].sum()

    budget = meta.get("budget", 0)
    days = len(daily)

    results = {
        # 汇总值
        "total_show_pv": total["show_pv"],
        "total_show_uv": total["show_uv"],
        "total_watch_pv": total["watch_pv"],
        "total_watch_uv": total["watch_uv"],
        "total_watch_duration": total["watch_duration"],
        "total_go_live_uv": total["go_live_uv"],
        "total_live_duration": total["live_duration"],
        "days": days,
        "budget": budget,

        # 日均值
        "daily_show_uv": total["show_uv"] / days if days else 0,
        "daily_watch_uv": total["watch_uv"] / days if days else 0,
        "daily_go_live_uv": total["go_live_uv"] / days if days else 0,

        # 一级指标
        "cpm": (budget / total["show_pv"] * 1000) if total["show_pv"] else 0,
        "cpv": (budget / total["watch_pv"] * 1000) if total["watch_pv"] else 0,
        "ctr": (total["watch_uv"] / total["show_uv"]) if total["show_uv"] else 0,
        "avg_watch_duration": (total["watch_duration"] / total["watch_uv"]) if total["watch_uv"] else 0,
        "view_frequency": (total["watch_pv"] / total["watch_uv"]) if total["watch_uv"] else 0,
        "impression_frequency": (total["show_pv"] / total["show_uv"]) if total["show_uv"] else 0,
        "traffic_dividend": (total["watch_uv"] / total["go_live_uv"]) if total["go_live_uv"] else 0,
        "avg_live_duration": (total["live_duration"] / total["go_live_uv"]) if total["go_live_uv"] else 0,
    }

    return results
