# Codex Food Master

家庭食物管理和一周食谱规划的本地 SQLite MVP。

第一版目标是跑通一个完整闭环：

1. 录入家庭食材库存
2. 基于库存和菜谱生成 7 天午餐、晚餐计划
3. 根据计划和库存生成采购清单
4. 记录实际用餐、食材消耗和菜谱评分
5. 生成一周总结，为下周计划提供反馈

## 快速开始

初始化数据库：

```bash
python3 scripts/init_db.py
```

录入一条库存：

```bash
python3 scripts/add_inventory.py "鸡胸肉" 600 g --category 肉类 --storage 冷藏 --expiry 2026-06-18 --location 冰箱
```

生成下周计划：

```bash
python3 scripts/generate_weekly_plan.py --week-start 2026-06-15
```

生成采购清单：

```bash
python3 scripts/generate_shopping_list.py --week-start 2026-06-15
```

记录一餐结果：

```bash
python3 scripts/record_meal_result.py --item-id 1 --rating 5 --comments "好吃，份量正好"
```

生成周总结：

```bash
python3 scripts/weekly_summary.py --week-start 2026-06-15
```

备份数据库：

```bash
python3 scripts/backup_database.py
```

## 目录

- `config/`：家庭人数、饮食喜好、份量和食谱生成规则
- `data/`：SQLite 数据库和导出文件
- `docs/`：数据库和流程说明
- `recipes/`：第一版样例菜谱和模板
- `scripts/`：可直接运行的 MVP 脚本
- `src/`：核心业务逻辑，未来网页和安卓 App 可复用

## 备份

源码和配置文件建议用 Git 管理。真实运行数据保存在 `data/food_master.sqlite`，这个文件已被 `.gitignore` 排除，需要单独备份。

手动备份数据库：

```bash
python3 scripts/backup_database.py
```

添加标签：

```bash
python3 scripts/backup_database.py --label before_big_import
```

默认保留最近 20 个备份，备份文件会放在 `backups/`。

## 家庭成员和份量

在 `config/household.md` 的“家庭成员”里填写每个人的性别和年龄后，系统会估算家庭总份量系数。比如成人男性约 1.1 人份、成人女性约 1.0 人份、6-12 岁儿童约 0.65 人份。

如果没有填写有效年龄信息，系统会继续使用“默认用餐人数”。
