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


def next_monday() -> str:
    today = date.today()
    days = (7 - today.weekday()) % 7
    if days == 0:
        days = 7
    return (today + timedelta(days=days)).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成一周总结")
    parser.add_argument("--week-start", default=next_monday(), help="周开始日期 YYYY-MM-DD")
    return parser.parse_args()


def main() -> None:
    init_db(seed=True)
    args = parse_args()
    with connect() as conn:
        plan = find_plan_by_week(conn, args.week_start)
        if plan is None:
            raise SystemExit("没有找到这一周的饭菜计划。")
        plan_id = int(plan["id"])
        stats = conn.execute(
            """
            SELECT
                COUNT(*) AS planned,
                SUM(CASE WHEN status = 'cooked' THEN 1 ELSE 0 END) AS cooked,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) AS skipped
            FROM meal_plan_items
            WHERE meal_plan_id = ?
            """,
            (plan_id,),
        ).fetchone()
        top_recipes = conn.execute(
            """
            SELECT r.name, AVG(mr.rating) AS avg_rating, COUNT(*) AS times_cooked
            FROM meal_results mr
            JOIN meal_plan_items mpi ON mpi.id = mr.meal_plan_item_id
            JOIN recipes r ON r.id = mr.actual_recipe_id
            WHERE mpi.meal_plan_id = ? AND mr.rating IS NOT NULL
            GROUP BY r.id
            ORDER BY avg_rating DESC, times_cooked DESC
            LIMIT 5
            """,
            (plan_id,),
        ).fetchall()
        used_ingredients = conn.execute(
            """
            SELECT i.name, SUM(iul.quantity_used) AS quantity_used, iul.unit
            FROM ingredient_usage_logs iul
            JOIN meal_results mr ON mr.id = iul.meal_result_id
            JOIN meal_plan_items mpi ON mpi.id = mr.meal_plan_item_id
            JOIN ingredients i ON i.id = iul.ingredient_id
            WHERE mpi.meal_plan_id = ?
            GROUP BY i.id, iul.unit
            ORDER BY quantity_used DESC
            LIMIT 10
            """,
            (plan_id,),
        ).fetchall()

        lines = [f"# 一周总结：{args.week_start}", ""]
        lines.append(f"- 计划餐数：{stats['planned'] or 0}")
        lines.append(f"- 已完成餐数：{stats['cooked'] or 0}")
        lines.append(f"- 跳过餐数：{stats['skipped'] or 0}")
        lines.extend(["", "## 评分较高的菜"])
        if top_recipes:
            for row in top_recipes:
                lines.append(f"- {row['name']}：平均 {row['avg_rating']:.1f} 分，做过 {row['times_cooked']} 次")
        else:
            lines.append("- 暂无评分记录")
        lines.extend(["", "## 食材消耗最多"])
        if used_ingredients:
            for row in used_ingredients:
                lines.append(f"- {row['name']}：{row['quantity_used']:g}{row['unit']}")
        else:
            lines.append("- 暂无消耗记录")
        lines.extend(["", "## 下周建议"])
        lines.append("- 高评分菜可以保留在候选池。")
        lines.append("- 经常剩菜的菜下次减少份量。")
        lines.append("- 采购前先查看临期库存，优先安排消耗。")

        path = write_markdown("weekly_summary.md", "\n".join(lines).strip() + "\n")
        print(f"已生成一周总结，并导出到：{path}")
        print("\n".join(lines))


if __name__ == "__main__":
    main()

