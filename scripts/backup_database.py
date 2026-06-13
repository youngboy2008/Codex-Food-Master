#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "food_master.sqlite"
BACKUP_DIR = ROOT / "backups"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="备份本地 SQLite 数据库")
    parser.add_argument(
        "--keep",
        type=int,
        default=20,
        help="保留最近多少个备份，默认 20。设为 0 表示不自动清理。",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="可选标签，例如 before_big_import，会加入备份文件名。",
    )
    return parser.parse_args()


def backup_database(label: str | None = None) -> Path:
    if not DB_PATH.exists():
        raise FileNotFoundError("还没有找到 data/food_master.sqlite，请先运行 scripts/init_db.py")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_label = ""
    if label:
        safe_label = "_" + "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in label)
    backup_path = BACKUP_DIR / f"food_master_{timestamp}{safe_label}.sqlite"

    source = sqlite3.connect(DB_PATH)
    try:
        target = sqlite3.connect(backup_path)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()

    return backup_path


def prune_old_backups(keep: int) -> list[Path]:
    if keep <= 0 or not BACKUP_DIR.exists():
        return []
    backups = sorted(
        BACKUP_DIR.glob("food_master_*.sqlite"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    removed: list[Path] = []
    for path in backups[keep:]:
        path.unlink()
        removed.append(path)
    return removed


def main() -> None:
    args = parse_args()
    backup_path = backup_database(args.label)
    removed = prune_old_backups(args.keep)
    print(f"已备份数据库：{backup_path}")
    if removed:
        print(f"已清理旧备份：{len(removed)} 个")


if __name__ == "__main__":
    main()

