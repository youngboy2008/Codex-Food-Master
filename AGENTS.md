# AGENTS.md

## 项目目标

这是一个本地家庭食物管理和一周食谱规划 MVP。

核心流程：

1. 管理家庭食材库存
2. 生成 7 天午餐和晚餐计划
3. 根据计划生成采购清单
4. 记录实际食材消耗和菜谱评分
5. 生成一周总结并影响未来推荐

## 技术方向

- 使用 SQLite 作为本地数据库
- 第一版不做网页界面
- 第一版不接真实 AI API
- Markdown 保存家庭偏好、份量规则、食谱生成规则
- Python 脚本负责本地流程
- `src/` 中的业务逻辑需要方便未来网页和安卓 App 复用

## 重要目录

- `config/`：家庭成员、饮食偏好、份量规则、生成规则
- `data/`：SQLite 数据库和导出文件
- `docs/`：schema、流程和未来扩展说明
- `recipes/`：样例菜谱和模板
- `scripts/`：命令行入口
- `src/`：核心业务逻辑
- `backups/`：SQLite 数据库备份目录，只提交 `.gitkeep`

## 开发原则

- 不要把业务逻辑写死在脚本里，优先放到 `src/`
- 脚本只作为命令行入口
- 不要提交 `data/food_master.sqlite`
- 不要提交 `data/exports/*.md`
- 不要提交 `backups/*.sqlite`
- 修改数据库结构时，同步更新 `docs/schema.md`
- 修改流程时，同步更新 `docs/workflow.md`
- 家庭成员份量计算需要兼容小数份量
- 菜品的备菜使用上尽量用库存里的整份或者整袋食材，多用一些是可以的
- 如果家庭成员没有有效年龄信息，使用默认用餐人数
- 重要数据录入或批量修改前，建议先运行 `scripts/backup_database.py`

## MVP 脚本

常用命令：

```bash
python3 scripts/init_db.py
python3 scripts/add_inventory.py
python3 scripts/generate_weekly_plan.py
python3 scripts/generate_shopping_list.py
python3 scripts/record_meal_result.py
python3 scripts/weekly_summary.py
python3 scripts/backup_database.py
```

## 未来预留

- 网页端应复用 `src/` 里的业务逻辑
- 安卓端优先考虑调用本地 API，而不是重复实现所有规则
- AI 未来只负责生成候选计划，最终仍写入 SQLite
