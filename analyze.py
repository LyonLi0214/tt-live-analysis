#!/usr/bin/env python3
"""TT 直播活动数据分析 CLI — 读取 Excel 模板，输出 Markdown 报告"""
import argparse
import sys
import os

# 确保能 import core 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.reader import read_activity_data, list_activities
from core.metrics_l1 import compute_l1
from core.metrics_l2 import compute_l2
from core.metrics_l3 import compute_l3
from core.metrics_l4 import compute_l4
from core.cache import (compute_hash, load_activity_cache, save_activity_cache,
                        load_baselines, save_baselines)
from core.report import generate_report


def main():
    parser = argparse.ArgumentParser(
        description="TT 直播活动数据分析 — 从 Excel 模板生成 Markdown 报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python3 analyze.py --file template.xlsx --activity "S3赛季BR直播"
  python3 analyze.py --file template.xlsx --list
""")
    parser.add_argument("--file", required=True, help="Excel 模板文件路径")
    parser.add_argument("--activity", help="要分析的活动名称（必须与①注册表和Sheet名一致）")
    parser.add_argument("--output", help="输出报告路径（默认：{活动名}_report.md）")
    parser.add_argument("--cache-dir", default="./cache", help="缓存目录（默认：./cache）")
    parser.add_argument("--no-cache", action="store_true", help="禁用缓存，强制重新计算")
    parser.add_argument("--list", action="store_true", help="列出所有已注册的活动")

    args = parser.parse_args()

    # 检查文件
    if not os.path.exists(args.file):
        print(f"错误：文件不存在 — {args.file}")
        sys.exit(1)

    # 列出活动模式
    if args.list:
        activities = list_activities(args.file)
        print("已注册的活动：")
        for i, name in enumerate(activities, 1):
            print(f"  {i}. {name}")
        sys.exit(0)

    # 分析模式
    if not args.activity:
        print("错误：请指定 --activity 参数，或使用 --list 查看可用活动")
        sys.exit(1)

    print(f"正在分析活动「{args.activity}」...")

    # Step 1: 读取数据（选择性读取）
    try:
        data = read_activity_data(args.file, args.activity)
    except ValueError as e:
        print(f"错误：{e}")
        sys.exit(1)

    print(f"  数据读取完成：{len(data['daily'])} 天日粒度数据")

    # Step 2: 检查缓存
    data_hash = compute_hash(data["daily"])
    cached = None
    if not args.no_cache:
        cached = load_activity_cache(args.cache_dir, args.activity)
        if cached and cached.get("data_hash") == data_hash:
            print("  命中缓存，跳过 L1-L3 计算")
            l1 = cached["l1"]
            l2 = cached["l2"]
        else:
            cached = None

    # Step 3: 计算指标
    if not cached:
        print("  计算一级指标 (L1)...")
        l1 = compute_l1(data["daily"], data["meta"])

        print("  计算二级指标 (L2)...")
        l2 = compute_l2(data["daily"], l1)

    print("  计算三级指标 (L3 时序分析)...")
    l3 = compute_l3(data["daily"], data["events_own"], data["events_competitor"])

    # L3 摘要（用于缓存，排除 DataFrame）
    l3_summary = {k: v for k, v in l3.items() if k not in ("daily_series", "events_timeline")}

    print("  计算四级指标 (L4 跨期对比)...")
    cache_bl = load_baselines(args.cache_dir) if not args.no_cache else None
    l1["_activity_name"] = args.activity
    l4 = compute_l4(l1, l2, data["historical"], cache_bl)

    # Step 4: 保存缓存
    if not args.no_cache:
        save_activity_cache(args.cache_dir, args.activity, data_hash, l1, l2, l3_summary)
        if l4.get("baselines") and not l4["baselines"].get("_insufficient"):
            save_baselines(args.cache_dir, l4["baselines"])
        print("  缓存已更新")

    # Step 5: 生成报告
    print("  生成 Markdown 报告...")
    report = generate_report(
        meta=data["meta"],
        l1=l1,
        l2=l2,
        l3=l3,
        l4=l4,
        creators=data["creators"],
        competitors=data["competitors"],
    )

    # Step 6: 写入文件
    output_path = args.output or f"{args.activity}_report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n报告已生成：{output_path}")
    print(f"  共 {len(report.splitlines())} 行，{len(report)} 字符")


if __name__ == "__main__":
    main()
