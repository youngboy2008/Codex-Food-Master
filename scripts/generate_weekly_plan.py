#!/usr/bin/env python3
import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db import connect, init_db
from src.exporters import write_markdown
from src.inventory_service import refresh_inventory_status
from src.meal_plan_service import generate_weekly_plan, plan_rows


def next_monday() -> str:
    today = date.today()
    days = (7 - today.weekday()) % 7
    if days == 0:
        days = 7
    return (today + timedelta(days=days)).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 7 天午餐和晚餐计划")
    parser.add_argument("--week-start", default=next_monday(), help="周开始日期 YYYY-MM-DD，默认下周一")
    return parser.parse_args()


def slot_label(slot: str) -> str:
    return "午餐" if slot == "lunch" else "晚餐"


def main() -> None:
    init_db(seed=True)
    args = parse_args()
    with connect() as conn:
        refresh_inventory_status(conn)
        plan_id = generate_weekly_plan(conn, args.week_start)
        rows = plan_rows(conn, plan_id)
        lines = [f"# 一周饭菜计划：{args.week_start}", ""]
        current_date = None
        for row in rows:
            if row["meal_date"] != current_date:
                current_date = row["meal_date"]
                lines.extend(["", f"## {current_date}"])
            lines.append(
                f"- {slot_label(row['meal_slot'])}：{row['recipe_name']} "
                f"({float(row['planned_servings']):g} 人份) - {row['priority_reason']}"
            )
        path = write_markdown("weekly_plan.md", "\n".join(lines).strip() + "\n")
        print(f"已生成饭菜计划 #{plan_id}，并导出到：{path}")
        for row in rows:
            print(f"- #{row['id']} {row['meal_date']} {slot_label(row['meal_slot'])}：{row['recipe_name']}")


if __name__ == "__main__":
    main()
