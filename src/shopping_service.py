from __future__ import annotations

import sqlite3
from collections import defaultdict

from .inventory_service import available_inventory_by_ingredient


def generate_shopping_list(conn: sqlite3.Connection, meal_plan_id: int) -> int:
    existing = conn.execute(
        "SELECT id FROM shopping_lists WHERE meal_plan_id = ?", (meal_plan_id,)
    ).fetchone()
    if existing:
        shopping_list_id = int(existing["id"])
        conn.execute("DELETE FROM shopping_list_items WHERE shopping_list_id = ?", (shopping_list_id,))
    else:
        conn.execute(
            "INSERT INTO shopping_lists (meal_plan_id, status) VALUES (?, 'draft')",
            (meal_plan_id,),
        )
        shopping_list_id = int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])

    required: dict[int, dict] = defaultdict(lambda: {"quantity": 0.0, "unit": "g", "required": 0})
    rows = conn.execute(
        """
        SELECT ri.ingredient_id, ri.quantity_per_serving, ri.unit, ri.required,
               mpi.planned_servings
        FROM meal_plan_items mpi
        JOIN recipe_ingredients ri ON ri.recipe_id = mpi.recipe_id
        WHERE mpi.meal_plan_id = ?
        """,
        (meal_plan_id,),
    ).fetchall()
    for row in rows:
        ingredient_id = int(row["ingredient_id"])
        required[ingredient_id]["quantity"] += float(row["quantity_per_serving"]) * float(row["planned_servings"])
        required[ingredient_id]["unit"] = row["unit"]
        required[ingredient_id]["required"] = max(required[ingredient_id]["required"], int(row["required"]))

    inventory = available_inventory_by_ingredient(conn)
    for ingredient_id, item in required.items():
        required_quantity = item["quantity"]
        inventory_quantity = inventory.get(ingredient_id, 0.0)
        purchase_quantity = max(0.0, required_quantity - inventory_quantity)
        if purchase_quantity <= 0:
            continue
        priority = "high" if item["required"] else "medium"
        conn.execute(
            """
            INSERT INTO shopping_list_items
            (shopping_list_id, ingredient_id, required_quantity, inventory_quantity,
             purchase_quantity, unit, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                shopping_list_id,
                ingredient_id,
                required_quantity,
                inventory_quantity,
                purchase_quantity,
                item["unit"],
                priority,
            ),
        )
    return shopping_list_id


def shopping_rows(conn: sqlite3.Connection, shopping_list_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT sli.id, i.name, sli.required_quantity, sli.inventory_quantity,
               sli.purchase_quantity, sli.unit, sli.priority, sli.purchased
        FROM shopping_list_items sli
        JOIN ingredients i ON i.id = sli.ingredient_id
        WHERE sli.shopping_list_id = ?
        ORDER BY CASE sli.priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, i.name
        """,
        (shopping_list_id,),
    ).fetchall()
