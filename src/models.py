from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IngredientNeed:
    ingredient_id: int
    name: str
    quantity: float
    unit: str


@dataclass(frozen=True)
class PlannedMeal:
    id: int
    meal_date: str
    meal_slot: str
    recipe_name: str
    servings: float
    reason: str | None = None
