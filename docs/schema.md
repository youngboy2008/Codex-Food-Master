# SQLite 数据库表设计

数据库文件：`data/food_master.sqlite`

## ingredients

食材基础表。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 食材 ID |
| name | TEXT | 食材名称 |
| category | TEXT | 分类 |
| default_unit | TEXT | 默认单位 |
| storage_type | TEXT | 储藏方式 |
| shelf_life_days | INTEGER | 默认保质天数 |
| notes | TEXT | 备注 |

## inventory_items

当前库存表，按购买批次记录。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 库存记录 ID |
| ingredient_id | INTEGER FK | 食材 ID |
| quantity | REAL | 当前数量 |
| unit | TEXT | 单位 |
| purchase_date | DATE | 购买日期 |
| expiry_date | DATE | 过期日期 |
| location | TEXT | 存放位置 |
| status | TEXT | available / used_up / expired / discarded |
| notes | TEXT | 备注 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

## recipes

菜谱主表。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 菜谱 ID |
| name | TEXT | 菜名 |
| meal_type | TEXT | lunch / dinner / either |
| cuisine_type | TEXT | 菜系 |
| difficulty | INTEGER | 难度 1-5 |
| prep_minutes | INTEGER | 准备时间 |
| cook_minutes | INTEGER | 烹饪时间 |
| servings | INTEGER | 默认份数 |
| tags | TEXT | 标签 |
| instructions | TEXT | 做法 |
| active | INTEGER | 是否启用 |
| created_at | TEXT | 创建时间 |

## recipe_ingredients

菜谱食材表。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 记录 ID |
| recipe_id | INTEGER FK | 菜谱 ID |
| ingredient_id | INTEGER FK | 食材 ID |
| quantity_per_serving | REAL | 每人份用量 |
| unit | TEXT | 单位 |
| required | INTEGER | 是否必须 |
| substitute_group | TEXT | 替换组 |

## meal_plans

一周饭菜计划主表。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 计划 ID |
| week_start_date | DATE | 周开始日期 |
| plan_name | TEXT | 计划名称 |
| status | TEXT | draft / confirmed / completed |
| generated_by | TEXT | manual / rule_based / future_ai |
| notes | TEXT | 备注 |
| created_at | TEXT | 创建时间 |

## meal_plan_items

具体每餐安排。

`planned_servings` 使用份量系数，不一定是整数。例如两个成人加一个 8 岁儿童可能是 2.65 份。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 记录 ID |
| meal_plan_id | INTEGER FK | 所属计划 |
| meal_date | DATE | 日期 |
| meal_slot | TEXT | lunch / dinner |
| recipe_id | INTEGER FK | 菜谱 ID |
| planned_servings | REAL | 计划份量系数，例如 4.0 表示约 4 个标准成人份 |
| priority_reason | TEXT | 推荐原因 |
| status | TEXT | planned / cooked / skipped / replaced |
| notes | TEXT | 备注 |

## shopping_lists

采购计划主表。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 采购清单 ID |
| meal_plan_id | INTEGER FK | 饭菜计划 ID |
| status | TEXT | draft / purchased / cancelled |
| created_at | TEXT | 创建时间 |
| notes | TEXT | 备注 |

## shopping_list_items

采购清单明细。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 明细 ID |
| shopping_list_id | INTEGER FK | 所属采购清单 |
| ingredient_id | INTEGER FK | 食材 ID |
| required_quantity | REAL | 计划需要数量 |
| inventory_quantity | REAL | 当前库存数量 |
| purchase_quantity | REAL | 建议购买数量 |
| unit | TEXT | 单位 |
| priority | TEXT | high / medium / low |
| purchased | INTEGER | 是否已购买 |
| notes | TEXT | 备注 |

## meal_results

实际用餐反馈。

`actual_servings` 使用实际份量系数，方便记录“今天少做一点”或“多做一份留饭”。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 反馈 ID |
| meal_plan_item_id | INTEGER FK | 对应某一餐 |
| actual_recipe_id | INTEGER FK | 实际菜谱 |
| actual_servings | REAL | 实际份量系数 |
| rating | INTEGER | 评分 1-5 |
| liked | INTEGER | 是否喜欢 |
| leftovers | TEXT | 剩菜情况 |
| comments | TEXT | 评价 |
| created_at | TEXT | 创建时间 |

## ingredient_usage_logs

食材消耗记录。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 消耗记录 ID |
| meal_result_id | INTEGER FK | 用餐反馈 ID |
| inventory_item_id | INTEGER FK | 库存批次 ID |
| ingredient_id | INTEGER FK | 食材 ID |
| quantity_used | REAL | 实际消耗数量 |
| unit | TEXT | 单位 |
| usage_type | TEXT | cooked / wasted / expired / discarded |
| notes | TEXT | 备注 |
| created_at | TEXT | 创建时间 |

## recipe_ratings_summary

菜谱评分汇总。

| 字段 | 类型 | 说明 |
|---|---|---|
| recipe_id | INTEGER PK | 菜谱 ID |
| avg_rating | REAL | 平均评分 |
| times_planned | INTEGER | 被计划次数 |
| times_cooked | INTEGER | 实际烹饪次数 |
| times_skipped | INTEGER | 跳过次数 |
| last_cooked_date | DATE | 最近烹饪日期 |
| updated_at | TEXT | 更新时间 |
