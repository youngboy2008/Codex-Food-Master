from __future__ import annotations

import sqlite3
from datetime import date, timedelta


def get_or_create_ingredient(
    conn: sqlite3.Connection,
    name: str,
    category: str = "other",
    unit: str = "g",
    storage: str | None = None,
    shelf_life_days: int | None = None,
) -> int:
    row = conn.execute("SELECT id FROM ingredients WHERE name = ?", (name,)).fetchone()
    if row:
        return int(row["id"])
    conn.execute(
        """
        INSERT INTO ingredients (name, category, default_unit, storage_type, shelf_life_days)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, category, unit, storage, shelf_life_days),
    )
    return int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def add_inventory_item(
    conn: sqlite3.Connection,
    ingredient_name: str,
    quantity: float,
    unit: str,
    category: str = "other",
    storage: str | None = None,
    purchase_date: str | None = None,
    expiry_date: str | None = None,
    location: str | None = None,
    notes: str | None = None,
) -> int:
    ingredient_id = get_or_create_ingredient(conn, ingredient_name, category, unit, storage)
    if purchase_date is None:
        purchase_date = date.today().isoformat()
    if expiry_date is None:
        shelf_life = conn.execute(
            "SELECT shelf_life_days FROM ingredients WHERE id = ?", (ingredient_id,)
        ).fetchone()["shelf_life_days"]
        if shelf_life:
            expiry_date = (date.fromisoformat(purchase_date) + timedelta(days=int(shelf_life))).isoformat()
    conn.execute(
        """
        INSERT INTO inventory_items
        (ingredient_id, quantity, unit, purchase_date, expiry_date, location, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, 'available', ?)
        """,
        (ingredient_id, quantity, unit, purchase_date, expiry_date, location, notes),
    )
    return int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def available_inventory_by_ingredient(conn: sqlite3.Connection) -> dict[int, float]:
    rows = conn.execute(
        """
        SELECT ingredient_id, SUM(quantity) AS quantity
        FROM inventory_items
        WHERE status = 'available' AND quantity > 0
        GROUP BY ingredient_id
        """
    ).fetchall()
    return {int(row["ingredient_id"]): float(row["quantity"] or 0) for row in rows}


def inventory_report(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT ii.id, i.name, ii.quantity, ii.unit, ii.expiry_date, ii.location, ii.status
        FROM inventory_items ii
        JOIN ingredients i ON i.id = ii.ingredient_id
        ORDER BY ii.status, ii.expiry_date IS NULL, ii.expiry_date, i.name
        """
    ).fetchall()


def refresh_inventory_status(conn: sqlite3.Connection) -> None:
    today = date.today().isoformat()
    conn.execute(
        """
        UPDATE inventory_items
        SET status = 'used_up', updated_at = CURRENT_TIMESTAMP
        WHERE quantity <= 0 AND status = 'available'
        """
    )
    conn.execute(
        """
        UPDATE inventory_items
        SET status = 'expired', updated_at = CURRENT_TIMESTAMP
        WHERE expiry_date IS NOT NULL AND expiry_date < ? AND status = 'available'
        """,
        (today,),
    )

