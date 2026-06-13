from __future__ import annotations

import sqlite3
from collections import Counter
from datetime import date, timedelta

from .config_reader import disliked_terms, household_portion_units
from .inventory_service import available_inventory_by_ingredient


def _recipe_rows(conn: sqlite3.Connection, meal_slot: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT r.*,
               COALESCE(s.avg_rating, 3) AS avg_rating,
               COALESCE(s.times_cooked, 0) AS times_cooked
        FROM recipes r
        LEFT JOIN recipe_ratings_summary s ON s.recipe_id = r.id
        WHERE r.active = 1 AND (r.meal_type = 'either' OR r.meal_type = ?)
        ORDER BY r.name
        """,
        (meal_slot,),
    ).fetchall()


def _recipe_ingredients(conn: sqlite3.Connection, recipe_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT ri.*, i.name, i.category
        FROM recipe_ingredients ri
        JOIN ingredients i ON i.id = ri.ingredient_id
        WHERE ri.recipe_id = ?
        """,
        (recipe_id,),
    ).fetchall()


def _score_recipe(
    conn: sqlite3.Connection,
    recipe: sqlite3.Row,
    servings: float,
    inventory: dict[int, float],
    used_counts: Counter[int],
) -> tuple[float, str]:
    ingredients = _recipe_ingredients(conn, int(recipe["id"]))
    disliked = disliked_terms()
    if any(any(term and term in row["name"] for term in disliked) for row in ingredients):
        return (-999, "命中不喜欢或忌口食材")

    inventory_hits = 0
    expiring_hits = 0
    today = date.today()
    for item in ingredients:
        need = float(item["quantity_per_serving"]) * servings
        have = inventory.get(int(item["ingredient_id"]), 0)
        if have >= min(need, 1):
            inventory_hits += 1
        expiring = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM inventory_items
            WHERE ingredient_id = ?
              AND status = 'available'
              AND quantity > 0
              AND expiry_date IS NOT NULL
              AND expiry_date <= ?
            """,
            (item["ingredient_id"], (today + timedelta(days=3)).isoformat()),
        ).fetchone()["n"]
        if expiring:
            expiring_hits += 1

    base_rating = float(recipe["avg_rating"] or 3)
    score = base_rating
    score += inventory_hits * 2
    score += expiring_hits * 3
    score -= used_counts[int(recipe["id"])] * 4
    reason = f"库存匹配 {inventory_hits} 项，临期优先 {expiring_hits} 项，历史评分 {base_rating:.1f}，综合分 {score:.1f}"
    return (score, reason)


def _whole_package_servings_for_dinner(
    conn: sqlite3.Connection,
    recipe_id: int,
    base_servings: float,
) -> tuple[float, str | None]:
    best: tuple[float, float, str] | None = None
    ingredients = _recipe_ingredients(conn, recipe_id)
    protein_rows = [
        row
        for row in ingredients
        if row["required"] and row["category"] in {"肉类", "鱼虾"}
    ]
    for ingredient in protein_rows:
        quantity_per_serving = float(ingredient["quantity_per_serving"])
        if quantity_per_serving <= 0:
            continue
        base_needed = quantity_per_serving * base_servings
        batches = conn.execute(
            """
            SELECT quantity, unit
            FROM inventory_items
            WHERE ingredient_id = ?
              AND status = 'available'
              AND quantity > 0
              AND unit = ?
            ORDER BY expiry_date IS NULL, expiry_date, purchase_date
            """,
            (ingredient["ingredient_id"], ingredient["unit"]),
        ).fetchall()
        if not batches:
            continue

        quantities = [float(batch["quantity"]) for batch in batches]
        candidates = quantities + [sum(quantities)]
        for candidate_quantity in candidates:
            if candidate_quantity <= 0:
                continue
            adjusted_servings = round(candidate_quantity / quantity_per_serving, 2)
            if adjusted_servings < base_servings * 0.75:
                continue
            if adjusted_servings > base_servings * 2.25:
                continue

            # Prefer enough food, then the closest whole-package match.
            under_penalty = base_needed * 0.5 if candidate_quantity < base_needed * 0.9 else 0
            all_batches_bonus = -base_needed * 0.08 if candidate_quantity == sum(quantities) and len(quantities) > 1 else 0
            distance = abs(candidate_quantity - base_needed) + under_penalty + all_batches_bonus
            reason = (
                f"晚餐整份食材：{ingredient['name']} 按 {candidate_quantity:g}{ingredient['unit']} "
                f"调整为 {adjusted_servings:g} 人份"
            )
            if best is None or distance < best[0]:
                best = (distance, adjusted_servings, reason)

    if best is None:
        return base_servings, None
    return best[1], best[2]


def _planned_servings_for_recipe(
    conn: sqlite3.Connection,
    recipe_id: int,
    meal_slot: str,
    base_servings: float,
) -> tuple[float, str | None]:
    if meal_slot != "dinner":
        return base_servings, None
    return _whole_package_servings_for_dinner(conn, recipe_id, base_servings)


def generate_weekly_plan(conn: sqlite3.Connection, week_start: str) -> int:
    servings = household_portion_units()
    plan_name = "default"
    existing = conn.execute(
        "SELECT id FROM meal_plans WHERE week_start_date = ? AND plan_name = ?",
        (week_start, plan_name),
    ).fetchone()
    if existing:
        plan_id = int(existing["id"])
        conn.execute("DELETE FROM meal_plan_items WHERE meal_plan_id = ?", (plan_id,))
    else:
        conn.execute(
            """
            INSERT INTO meal_plans (week_start_date, plan_name, status, generated_by)
            VALUES (?, ?, 'draft', 'rule_based')
            """,
            (week_start, plan_name),
        )
        plan_id = int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])

    inventory = available_inventory_by_ingredient(conn)
    used_counts: Counter[int] = Counter()
    start = date.fromisoformat(week_start)
    slots = ["lunch", "dinner"]

    for offset in range(7):
        meal_date = (start + timedelta(days=offset)).isoformat()
        for slot in slots:
            candidates = []
            for recipe in _recipe_rows(conn, slot):
                score, reason = _score_recipe(conn, recipe, servings, inventory, used_counts)
                candidates.append((score, reason, recipe))
            candidates.sort(key=lambda item: (item[0], -used_counts[int(item[2]["id"])]), reverse=True)
            best_score, reason, recipe = candidates[0]
            recipe_id = int(recipe["id"])
            used_counts[recipe_id] += 1
            if best_score < -100:
                reason = "没有完全符合偏好的菜谱，暂用最低风险候选"
            planned_servings, servings_reason = _planned_servings_for_recipe(
                conn, recipe_id, slot, servings
            )
            if servings_reason:
                reason = f"{reason}；{servings_reason}"
            conn.execute(
                """
                INSERT INTO meal_plan_items
                (meal_plan_id, meal_date, meal_slot, recipe_id, planned_servings, priority_reason)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (plan_id, meal_date, slot, recipe_id, planned_servings, reason),
            )

    update_times_planned(conn)
    return plan_id


def update_times_planned(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO recipe_ratings_summary (recipe_id)
        SELECT id FROM recipes
        """
    )
    conn.execute(
        """
        UPDATE recipe_ratings_summary
        SET times_planned = (
            SELECT COUNT(*)
            FROM meal_plan_items mpi
            WHERE mpi.recipe_id = recipe_ratings_summary.recipe_id
        ),
        updated_at = CURRENT_TIMESTAMP
        """
    )


def plan_rows(conn: sqlite3.Connection, meal_plan_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT mpi.id, mpi.meal_date, mpi.meal_slot, r.name AS recipe_name,
               mpi.planned_servings, mpi.priority_reason, mpi.status
        FROM meal_plan_items mpi
        JOIN recipes r ON r.id = mpi.recipe_id
        WHERE mpi.meal_plan_id = ?
        ORDER BY mpi.meal_date, CASE mpi.meal_slot WHEN 'lunch' THEN 1 ELSE 2 END
        """,
        (meal_plan_id,),
    ).fetchall()


def find_plan_by_week(conn: sqlite3.Connection, week_start: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT * FROM meal_plans
        WHERE week_start_date = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (week_start,),
    ).fetchone()
