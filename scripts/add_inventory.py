#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db import connect, init_db
from src.inventory_service import add_inventory_item, inventory_report, refresh_inventory_status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="录入家庭食材库存")
    parser.add_argument("name", help="食材名称，例如 鸡胸肉")
    parser.add_argument("quantity", type=float, help="数量")
    parser.add_argument("unit", help="单位，例如 g、kg、个、ml")
    parser.add_argument("--category", default="other", help="分类，例如 肉类、蔬菜、主食")
    parser.add_argument("--storage", default=None, help="储藏方式，例如 冷藏、冷冻、常温")
    parser.add_argument("--purchase-date", default=None, help="购买日期 YYYY-MM-DD，默认今天")
    parser.add_argument("--expiry", default=None, help="过期日期 YYYY-MM-DD")
    parser.add_argument("--location", default=None, help="存放位置")
    parser.add_argument("--notes", default=None, help="备注")
    return parser.parse_args()


def main() -> None:
    init_db(seed=True)
    args = parse_args()
    with connect() as conn:
        item_id = add_inventory_item(
            conn,
            args.name,
            args.quantity,
            args.unit,
            category=args.category,
            storage=args.storage,
            purchase_date=args.purchase_date,
            expiry_date=args.expiry,
            location=args.location,
            notes=args.notes,
        )
        refresh_inventory_status(conn)
        print(f"已添加库存 #{item_id}：{args.name} {args.quantity:g}{args.unit}")
        print("\n当前库存：")
        for row in inventory_report(conn):
            expiry = row["expiry_date"] or "未记录"
            location = row["location"] or "-"
            print(f"- #{row['id']} {row['name']}：{row['quantity']:g}{row['unit']}，过期：{expiry}，位置：{location}，状态：{row['status']}")


if __name__ == "__main__":
    main()

