#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.db import DB_PATH, init_db


def main() -> None:
    init_db(seed=True)
    print(f"数据库已初始化：{DB_PATH}")
    print("已写入样例食材和样例菜谱。")


if __name__ == "__main__":
    main()

