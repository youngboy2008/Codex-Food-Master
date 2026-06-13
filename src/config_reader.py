from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT_DIR / "config"


@dataclass(frozen=True)
class HouseholdMember:
    name: str
    gender: str | None
    age: int
    portion_factor: float


def read_markdown(name: str) -> str:
    path = CONFIG_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def household_default_servings() -> int:
    text = read_markdown("household.md")
    match = re.search(r"默认用餐人数：\s*(\d+)", text)
    return int(match.group(1)) if match else 2


def estimate_portion_factor(age: int, gender: str | None = None) -> float:
    if age <= 5:
        return 0.4
    if age <= 12:
        return 0.65
    if age <= 17:
        return 0.85
    if age >= 65:
        return 0.9
    if gender == "男":
        return 1.1
    return 1.0


def household_members() -> list[HouseholdMember]:
    text = read_markdown("household.md")
    members: list[HouseholdMember] = []
    capture = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            capture = line == "## 家庭成员"
            continue
        if not capture or not line.startswith("- ") or "年龄" not in line:
            continue
        content = line[2:].strip()
        name = content.split("：", 1)[0].strip() if "：" in content else "未命名成员"
        gender_match = re.search(r"性别\s*([男女]|其他)", content)
        age_match = re.search(r"年龄\s*(\d+)", content)
        factor_match = re.search(r"份量系数\s*([0-9]+(?:\.[0-9]+)?)", content)
        if not age_match:
            continue
        age = int(age_match.group(1))
        gender = gender_match.group(1) if gender_match else None
        factor = float(factor_match.group(1)) if factor_match else estimate_portion_factor(age, gender)
        members.append(HouseholdMember(name=name, gender=gender, age=age, portion_factor=factor))
    return members


def household_portion_units() -> float:
    members = household_members()
    if not members:
        return float(household_default_servings())
    return round(sum(member.portion_factor for member in members), 2)


def disliked_terms() -> set[str]:
    text = read_markdown("food_preferences.md")
    terms: set[str] = set()
    capture = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            capture = "不喜欢" in line or "忌口" in line
            continue
        if capture and line.startswith("- "):
            terms.add(line[2:].strip())
    return terms
