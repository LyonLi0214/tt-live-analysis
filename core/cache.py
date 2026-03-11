"""缓存层：存储计算结果避免重复计算"""
import json
import hashlib
from pathlib import Path
from typing import Optional
import pandas as pd


def compute_hash(daily: pd.DataFrame) -> str:
    """计算日粒度数据的哈希值，用于缓存校验"""
    data_str = daily.to_csv(index=False)
    return hashlib.md5(data_str.encode()).hexdigest()


def load_activity_cache(cache_dir: str, activity_name: str) -> Optional[dict]:
    """加载指定活动的缓存结果"""
    path = Path(cache_dir) / f"{activity_name}_metrics.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_activity_cache(cache_dir: str, activity_name: str, data_hash: str,
                        l1: dict, l2: dict, l3_summary: dict):
    """保存活动计算结果到缓存"""
    path = Path(cache_dir) / f"{activity_name}_metrics.json"
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    cache = {
        "version": "1.0",
        "data_hash": data_hash,
        "l1": l1,
        "l2": l2,
        "l3_summary": l3_summary,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def load_baselines(cache_dir: str) -> Optional[dict]:
    """加载基准线缓存"""
    path = Path(cache_dir) / "baselines.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_baselines(cache_dir: str, baselines: dict):
    """保存基准线到缓存"""
    path = Path(cache_dir) / "baselines.json"
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(baselines, f, ensure_ascii=False, indent=2)
