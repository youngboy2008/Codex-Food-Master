#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db import connect, init_db
from src.feedback_service import record_meal_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="记录一餐实际结果、评分，并扣减库存")
    parser.add_argument("--item-id", type=int, required=True, help="meal_plan_items 的 ID")
    parser.add_argument("--rating", type=int, choices=range(1, 6), default=None, help="评分 1-5")
    parser.add_argument("--servings", type=float, default=None, help="实际份量系数，默认等于计划份量")
    parser.add_argument("--leftovers", default=None, help="剩菜情况")
    parser.add_argument("--comments", default=None, help="备注或评价")
    return parser.parse_args()


def main() -> None:
    init_db(seed=True)
    args = parse_args()
    with connect() as conn:
        result_id = record_meal_result(
            conn,
            args.item_id,
            rating=args.rating,
            actual_servings=args.servings,
            leftovers=args.leftovers,
            comments=args.comments,
        )
        print(f"已记录用餐结果 #{result_id}，库存已按菜谱用量扣减。")


if __name__ == "__main__":
    main()
