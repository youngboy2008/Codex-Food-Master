from __future__ import annotations

import sqlite3


def record_meal_result(
    conn: sqlite3.Connection,
    meal_plan_item_id: int,
    rating: int | None = None,
    actual_servings: float | None = None,
    leftovers: str | None = None,
    comments: str | None = None,
    mark_status: str = "cooked",
) -> int:
    item = conn.execute(
        "SELECT * FROM meal_plan_items WHERE id = ?", (meal_plan_item_id,)
    ).fetchone()
    if item is None:
        raise ValueError(f"Meal plan item not found: {meal_plan_item_id}")
    actual_recipe_id = int(item["recipe_id"])
    servings = actual_servings if actual_servings is not None else float(item["planned_servings"])
    liked = None if rating is None else int(rating >= 4)

    conn.execute(
        """
        INSERT INTO meal_results
        (meal_plan_item_id, actual_recipe_id, actual_servings, rating, liked, leftovers, comments)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (meal_plan_item_id, actual_recipe_id, servings, rating, liked, leftovers, comments),
    )
    meal_result_id = int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])
    consume_recipe_ingredients(conn, meal_result_id, actual_recipe_id, servings)
    conn.execute(
        "UPDATE meal_plan_items SET status = ? WHERE id = ?",
        (mark_status, meal_plan_item_id),
    )
    update_recipe_summary(conn, actual_recipe_id)
    return meal_result_id


def consume_recipe_ingredients(
    conn: sqlite3.Connection,
    meal_result_id: int,
    recipe_id: int,
    servings: float,
) -> None:
    ingredients = conn.execute(
        """
        SELECT ingredient_id, quantity_per_serving, unit
        FROM recipe_ingredients
        WHERE recipe_id = ?
        """,
        (recipe_id,),
    ).fetchall()
    for ingredient in ingredients:
        remaining = float(ingredient["quantity_per_serving"]) * servings
        ingredient_id = int(ingredient["ingredient_id"])
        batches = conn.execute(
            """
            SELECT *
            FROM inventory_items
            WHERE ingredient_id = ? AND status = 'available' AND quantity > 0
            ORDER BY expiry_date IS NULL, expiry_date, purchase_date
            """,
            (ingredient_id,),
        ).fetchall()
        for batch in batches:
            if remaining <= 0:
                break
            batch_quantity = float(batch["quantity"])
            used = min(batch_quantity, remaining)
            remaining -= used
            new_quantity = batch_quantity - used
            status = "used_up" if new_quantity <= 0 else "available"
            conn.execute(
                """
                UPDATE inventory_items
                SET quantity = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_quantity, status, batch["id"]),
            )
            conn.execute(
                """
                INSERT INTO ingredient_usage_logs
                (meal_result_id, inventory_item_id, ingredient_id, quantity_used, unit, usage_type)
                VALUES (?, ?, ?, ?, ?, 'cooked')
                """,
                (meal_result_id, batch["id"], ingredient_id, used, ingredient["unit"]),
            )
        if remaining > 0:
            conn.execute(
                """
                INSERT INTO ingredient_usage_logs
                (meal_result_id, inventory_item_id, ingredient_id, quantity_used, unit, usage_type, notes)
                VALUES (?, NULL, ?, ?, ?, 'cooked', '库存不足，记录为计划外补足或未扣库存')
                """,
                (meal_result_id, ingredient_id, remaining, ingredient["unit"]),
            )


def update_recipe_summary(conn: sqlite3.Connection, recipe_id: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO recipe_ratings_summary (recipe_id) VALUES (?)",
        (recipe_id,),
    )
    conn.execute(
        """
        UPDATE recipe_ratings_summary
        SET avg_rating = (
            SELECT AVG(rating)
            FROM meal_results
            WHERE actual_recipe_id = ? AND rating IS NOT NULL
        ),
        times_cooked = (
            SELECT COUNT(*)
            FROM meal_results
            WHERE actual_recipe_id = ?
        ),
        last_cooked_date = (
            SELECT MAX(mpi.meal_date)
            FROM meal_results mr
            JOIN meal_plan_items mpi ON mpi.id = mr.meal_plan_item_id
            WHERE mr.actual_recipe_id = ?
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE recipe_id = ?
        """,
        (recipe_id, recipe_id, recipe_id, recipe_id),
    )
