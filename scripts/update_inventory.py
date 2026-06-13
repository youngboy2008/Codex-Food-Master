#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db import connect, init_db
from src.inventory_service import inventory_report, refresh_inventory_status


def main() -> None:
    init_db(seed=True)
    with connect() as conn:
        refresh_inventory_status(conn)
        print("库存状态已刷新。")
        for row in inventory_report(conn):
            expiry = row["expiry_date"] or "未记录"
            location = row["location"] or "-"
            print(f"- #{row['id']} {row['name']}：{row['quantity']:g}{row['unit']}，过期：{expiry}，位置：{location}，状态：{row['status']}")


if __name__ == "__main__":
    main()

