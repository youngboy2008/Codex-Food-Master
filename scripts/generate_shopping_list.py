#!/usr/bin/env python3
import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db import connect, init_db
from src.exporters import write_markdown
from src.meal_plan_service import find_plan_by_week
from src.shopping_service import generate_shopping_list, shopping_rows


def next_monday() -> str:
    today = date.today()
    days = (7 - today.weekday()) % 7
    if days == 0:
        days = 7
    return (today + timedelta(days=days)).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据饭菜计划生成采购清单")
    parser.add_argument("--week-start", default=next_monday(), help="周开始日期 YYYY-MM-DD")
    return parser.parse_args()


def main() -> None:
    init_db(seed=True)
    args = parse_args()
    with connect() as conn:
        plan = find_plan_by_week(conn, args.week_start)
        if plan is None:
            raise SystemExit("没有找到这一周的饭菜计划，请先运行 generate_weekly_plan.py")
        shopping_list_id = generate_shopping_list(conn, int(plan["id"]))
        rows = shopping_rows(conn, shopping_list_id)
        lines = [f"# 采购清单：{args.week_start}", ""]
        if not rows:
            lines.append("当前库存已经覆盖计划食材，暂不需要采购。")
        for row in rows:
            lines.append(
                f"- {row['name']}：建议购买 {row['purchase_quantity']:g}{row['unit']} "
                f"(计划需要 {row['required_quantity']:g}{row['unit']}，库存 {row['inventory_quantity']:g}{row['unit']}，优先级 {row['priority']})"
            )
        path = write_markdown("shopping_list.md", "\n".join(lines).strip() + "\n")
        print(f"已生成采购清单 #{shopping_list_id}，并导出到：{path}")
        if rows:
            for row in rows:
                print(f"- {row['name']}：买 {row['purchase_quantity']:g}{row['unit']} ({row['priority']})")
        else:
            print("不需要额外采购。")


if __name__ == "__main__":
    main()

