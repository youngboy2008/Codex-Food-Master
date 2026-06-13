from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "food_master.sqlite"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'other',
    default_unit TEXT NOT NULL DEFAULT 'g',
    storage_type TEXT,
    shelf_life_days INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS inventory_items (
    id INTEGER PRIMARY KEY,
    ingredient_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    purchase_date DATE,
    expiry_date DATE,
    location TEXT,
    status TEXT NOT NULL DEFAULT 'available',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    meal_type TEXT NOT NULL DEFAULT 'either',
    cuisine_type TEXT,
    difficulty INTEGER NOT NULL DEFAULT 2,
    prep_minutes INTEGER NOT NULL DEFAULT 10,
    cook_minutes INTEGER NOT NULL DEFAULT 20,
    servings INTEGER NOT NULL DEFAULT 2,
    tags TEXT,
    instructions TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    quantity_per_serving REAL NOT NULL,
    unit TEXT NOT NULL,
    required INTEGER NOT NULL DEFAULT 1,
    substitute_group TEXT,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    UNIQUE (recipe_id, ingredient_id)
);

CREATE TABLE IF NOT EXISTS meal_plans (
    id INTEGER PRIMARY KEY,
    week_start_date DATE NOT NULL,
    plan_name TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    generated_by TEXT NOT NULL DEFAULT 'rule_based',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (week_start_date, plan_name)
);

CREATE TABLE IF NOT EXISTS meal_plan_items (
    id INTEGER PRIMARY KEY,
    meal_plan_id INTEGER NOT NULL,
    meal_date DATE NOT NULL,
    meal_slot TEXT NOT NULL,
    recipe_id INTEGER NOT NULL,
    planned_servings REAL NOT NULL,
    priority_reason TEXT,
    status TEXT NOT NULL DEFAULT 'planned',
    notes TEXT,
    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    UNIQUE (meal_plan_id, meal_date, meal_slot)
);

CREATE TABLE IF NOT EXISTS shopping_lists (
    id INTEGER PRIMARY KEY,
    meal_plan_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id),
    UNIQUE (meal_plan_id)
);

CREATE TABLE IF NOT EXISTS shopping_list_items (
    id INTEGER PRIMARY KEY,
    shopping_list_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    required_quantity REAL NOT NULL,
    inventory_quantity REAL NOT NULL,
    purchase_quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium',
    purchased INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id),
    UNIQUE (shopping_list_id, ingredient_id)
);

CREATE TABLE IF NOT EXISTS meal_results (
    id INTEGER PRIMARY KEY,
    meal_plan_item_id INTEGER NOT NULL,
    actual_recipe_id INTEGER NOT NULL,
    actual_servings REAL NOT NULL,
    rating INTEGER,
    liked INTEGER,
    leftovers TEXT,
    comments TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meal_plan_item_id) REFERENCES meal_plan_items(id),
    FOREIGN KEY (actual_recipe_id) REFERENCES recipes(id)
);

CREATE TABLE IF NOT EXISTS ingredient_usage_logs (
    id INTEGER PRIMARY KEY,
    meal_result_id INTEGER,
    inventory_item_id INTEGER,
    ingredient_id INTEGER NOT NULL,
    quantity_used REAL NOT NULL,
    unit TEXT NOT NULL,
    usage_type TEXT NOT NULL DEFAULT 'cooked',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meal_result_id) REFERENCES meal_results(id),
    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);

CREATE TABLE IF NOT EXISTS recipe_ratings_summary (
    recipe_id INTEGER PRIMARY KEY,
    avg_rating REAL,
    times_planned INTEGER NOT NULL DEFAULT 0,
    times_cooked INTEGER NOT NULL DEFAULT 0,
    times_skipped INTEGER NOT NULL DEFAULT 0,
    last_cooked_date DATE,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
);
"""


SAMPLE_INGREDIENTS = [
    ("鸡胸肉", "肉类", "g", "冷藏", 4),
    ("西兰花", "蔬菜", "g", "冷藏", 5),
    ("米饭", "主食", "g", "常温", 180),
    ("番茄", "蔬菜", "g", "冷藏", 5),
    ("鸡蛋", "蛋类", "个", "冷藏", 21),
    ("面条", "主食", "g", "常温", 180),
    ("牛肉", "肉类", "g", "冷藏", 4),
    ("胡萝卜", "蔬菜", "g", "冷藏", 14),
    ("豆腐", "豆制品", "g", "冷藏", 3),
    ("青菜", "蔬菜", "g", "冷藏", 4),
    ("三文鱼", "鱼虾", "g", "冷藏", 2),
]


SAMPLE_RECIPES = [
    {
        "name": "西兰花炒鸡胸肉",
        "meal_type": "either",
        "cuisine_type": "中式家常菜",
        "difficulty": 2,
        "prep_minutes": 10,
        "cook_minutes": 20,
        "servings": 2,
        "tags": "快手,高蛋白,适合带饭",
        "instructions": "鸡胸肉切片腌制，西兰花焯水后同炒，搭配米饭。",
        "ingredients": [("鸡胸肉", 150, "g"), ("西兰花", 250, "g"), ("米饭", 90, "g")],
    },
    {
        "name": "番茄鸡蛋面",
        "meal_type": "either",
        "cuisine_type": "中式家常菜",
        "difficulty": 1,
        "prep_minutes": 5,
        "cook_minutes": 15,
        "servings": 2,
        "tags": "快手,简化餐",
        "instructions": "番茄炒出汁，加入鸡蛋和面条煮熟。",
        "ingredients": [("番茄", 180, "g"), ("鸡蛋", 1, "个"), ("面条", 100, "g")],
    },
    {
        "name": "牛肉胡萝卜盖饭",
        "meal_type": "dinner",
        "cuisine_type": "中式家常菜",
        "difficulty": 2,
        "prep_minutes": 10,
        "cook_minutes": 25,
        "servings": 2,
        "tags": "高蛋白,适合带饭",
        "instructions": "牛肉和胡萝卜炖煮或快炒后盖在米饭上。",
        "ingredients": [("牛肉", 160, "g"), ("胡萝卜", 180, "g"), ("米饭", 90, "g")],
    },
    {
        "name": "豆腐青菜饭",
        "meal_type": "either",
        "cuisine_type": "中式家常菜",
        "difficulty": 1,
        "prep_minutes": 5,
        "cook_minutes": 15,
        "servings": 2,
        "tags": "清淡,快手",
        "instructions": "豆腐煎香，青菜快炒，搭配米饭。",
        "ingredients": [("豆腐", 180, "g"), ("青菜", 250, "g"), ("米饭", 90, "g")],
    },
    {
        "name": "三文鱼蔬菜饭",
        "meal_type": "dinner",
        "cuisine_type": "简单西式",
        "difficulty": 2,
        "prep_minutes": 10,
        "cook_minutes": 20,
        "servings": 2,
        "tags": "鱼类,高蛋白",
        "instructions": "三文鱼煎熟，西兰花焯水或烤制，搭配米饭。",
        "ingredients": [("三文鱼", 170, "g"), ("西兰花", 220, "g"), ("米饭", 90, "g")],
    },
]


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(seed: bool = True) -> None:
    with connect() as conn:
        conn.executescript(SCHEMA_SQL)
        if seed:
            seed_sample_data(conn)


def seed_sample_data(conn: sqlite3.Connection) -> None:
    for name, category, unit, storage, shelf_life in SAMPLE_INGREDIENTS:
        conn.execute(
            """
            INSERT OR IGNORE INTO ingredients
            (name, category, default_unit, storage_type, shelf_life_days)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, category, unit, storage, shelf_life),
        )

    for recipe in SAMPLE_RECIPES:
        conn.execute(
            """
            INSERT OR IGNORE INTO recipes
            (name, meal_type, cuisine_type, difficulty, prep_minutes, cook_minutes,
             servings, tags, instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipe["name"],
                recipe["meal_type"],
                recipe["cuisine_type"],
                recipe["difficulty"],
                recipe["prep_minutes"],
                recipe["cook_minutes"],
                recipe["servings"],
                recipe["tags"],
                recipe["instructions"],
            ),
        )
        recipe_id = conn.execute("SELECT id FROM recipes WHERE name = ?", (recipe["name"],)).fetchone()["id"]
        for ingredient_name, quantity, unit in recipe["ingredients"]:
            ingredient_id = conn.execute(
                "SELECT id FROM ingredients WHERE name = ?", (ingredient_name,)
            ).fetchone()["id"]
            conn.execute(
                """
                INSERT OR IGNORE INTO recipe_ingredients
                (recipe_id, ingredient_id, quantity_per_serving, unit, required)
                VALUES (?, ?, ?, ?, 1)
                """,
                (recipe_id, ingredient_id, quantity, unit),
            )


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]
