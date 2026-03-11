"""三级指标：时序分析"""
import numpy as np
import pandas as pd
from datetime import datetime


def compute_l3(daily: pd.DataFrame, events_own: list, events_comp: list) -> dict:
    """从日粒度数据计算时序指标，并对齐事件标注。"""
    n = len(daily)
    if n < 2:
        return _minimal_result(daily, events_own, events_comp)

    days = daily["day"].values.astype(float)
    watch_uv = daily["watch_uv"].values.astype(float)
    show_pv = daily["show_pv"].values.astype(float)
    show_uv = daily["show_uv"].values.astype(float)
    watch_pv = daily["watch_pv"].values.astype(float)
    go_live_uv = daily["go_live_uv"].values.astype(float)

    # 逐日 CTR
    daily_ctr = np.where(show_uv > 0, watch_pv / show_uv, 0)

    # UV 衰减斜率 (线性回归)
    uv_slope, uv_intercept = np.polyfit(days, watch_uv, 1)
    uv_r2 = _r_squared(days, watch_uv, uv_slope, uv_intercept)

    # CTR 疲劳速度
    ctr_slope, ctr_intercept = np.polyfit(days, daily_ctr, 1)
    ctr_r2 = _r_squared(days, daily_ctr, ctr_slope, ctr_intercept)

    # 供给稳定性 (变异系数)
    supply_mean = np.mean(go_live_uv)
    supply_std = np.std(go_live_uv)
    supply_cv = (supply_std / supply_mean) if supply_mean else 0

    # 峰值日/均值比
    peak_avg_ratio = (np.max(watch_uv) / np.mean(watch_uv)) if np.mean(watch_uv) else 0
    peak_day = int(daily.iloc[np.argmax(watch_uv)]["day"])

    # 拐点日 (最大逐日变化)
    if n >= 3:
        diff = np.abs(np.diff(watch_uv))
        inflection_idx = int(np.argmax(diff)) + 1  # +1 因为 diff 比原数组短1
        inflection_day = int(daily.iloc[inflection_idx]["day"])
        inflection_date = daily.iloc[inflection_idx]["date"]
        inflection_change = float(np.diff(watch_uv)[inflection_idx - 1])
    else:
        inflection_day = 0
        inflection_date = ""
        inflection_change = 0

    # 周末效应系数
    weekend_uv, weekday_uv = _weekend_effect(daily)
    weekend_coefficient = (weekend_uv / weekday_uv) if weekday_uv else 1.0

    # 首尾比
    head_days = min(3, n)
    tail_days = min(3, n)
    head_avg = np.mean(watch_uv[:head_days])
    tail_avg = np.mean(watch_uv[-tail_days:])
    head_tail_ratio = (head_avg / tail_avg) if tail_avg else 0

    # 事件时间线标注
    events_timeline = _build_timeline(daily, events_own, events_comp)

    # 逐日明细（供报告使用）
    daily_series = daily.copy()
    daily_series["daily_ctr"] = daily_ctr

    return {
        "uv_decay_slope": float(uv_slope),
        "uv_decay_r2": float(uv_r2),
        "ctr_fatigue_slope": float(ctr_slope),
        "ctr_fatigue_r2": float(ctr_r2),
        "supply_cv": float(supply_cv),
        "peak_avg_ratio": float(peak_avg_ratio),
        "peak_day": peak_day,
        "inflection_day": inflection_day,
        "inflection_date": str(inflection_date),
        "inflection_change": float(inflection_change),
        "weekend_coefficient": float(weekend_coefficient),
        "head_tail_ratio": float(head_tail_ratio),
        "events_timeline": events_timeline,
        "daily_series": daily_series,
    }


def _r_squared(x, y, slope, intercept):
    predicted = slope * x + intercept
    ss_res = np.sum((y - predicted) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return 1 - (ss_res / ss_tot) if ss_tot else 0


def _weekend_effect(daily: pd.DataFrame):
    weekend_uv = []
    weekday_uv = []
    for _, row in daily.iterrows():
        date_str = str(row["date"])
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt.weekday() >= 5:
                weekend_uv.append(row["watch_uv"])
            else:
                weekday_uv.append(row["watch_uv"])
        except ValueError:
            weekday_uv.append(row["watch_uv"])

    avg_weekend = np.mean(weekend_uv) if weekend_uv else 0
    avg_weekday = np.mean(weekday_uv) if weekday_uv else 0
    return float(avg_weekend), float(avg_weekday)


def _build_timeline(daily: pd.DataFrame, events_own: list, events_comp: list) -> list:
    """将事件按日期对齐到日粒度时间线"""
    date_to_day = {}
    for _, row in daily.iterrows():
        date_to_day[str(row["date"])] = int(row["day"])

    timeline = []
    for event in events_own:
        day = date_to_day.get(str(event["date"]))
        timeline.append({
            "day": day,
            "date": str(event["date"]),
            "name": event["name"],
            "type": event["type"],
            "impact": event["impact"],
            "source": "我方",
        })

    for event in events_comp:
        day = date_to_day.get(str(event["date"]))
        timeline.append({
            "day": day,
            "date": str(event["date"]),
            "name": event["name"],
            "type": event["type"],
            "impact": event["impact"],
            "source": "竞品/外部",
        })

    return sorted(timeline, key=lambda x: str(x["date"]))


def _minimal_result(daily, events_own, events_comp):
    """数据不足时返回最小结果"""
    return {
        "uv_decay_slope": 0, "uv_decay_r2": 0,
        "ctr_fatigue_slope": 0, "ctr_fatigue_r2": 0,
        "supply_cv": 0, "peak_avg_ratio": 0, "peak_day": 0,
        "inflection_day": 0, "inflection_date": "", "inflection_change": 0,
        "weekend_coefficient": 1.0, "head_tail_ratio": 1.0,
        "events_timeline": _build_timeline(daily, events_own, events_comp),
        "daily_series": daily.copy(),
    }
