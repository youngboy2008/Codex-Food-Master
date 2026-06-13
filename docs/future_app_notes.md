# 后续网页和安卓 App 预留

## 数据库预留

- 主表统一使用 `id INTEGER PRIMARY KEY`。
- 业务表保留 `created_at` 和 `updated_at`。
- 状态字段使用稳定枚举值，例如 `draft`、`confirmed`、`completed`。
- SQLite 继续作为本地单机数据源。

## 业务逻辑预留

核心逻辑放在 `src/`，脚本只负责命令行输入输出。未来可以让网页后端或安卓同步逻辑复用同一套服务。

## 网页方向

未来可以增加：

```text
web/
├── backend/
│   └── api.py
└── frontend/
```

建议 API：

- `GET /inventory`
- `POST /inventory`
- `POST /meal-plans/generate`
- `GET /shopping-lists/{id}`
- `POST /meal-results`
- `GET /weekly-summary`

## 安卓方向

优先建议安卓 App 调用本地服务 API。这样业务逻辑集中在 Python 服务层，安卓只负责界面。

如果后续需要完全离线安卓，可以把 SQLite schema 和规则迁移到安卓本地实现。

## AI 接入预留

当前不接真实 AI API。未来 AI 可以读取：

- Markdown 偏好配置
- 当前库存
- 历史评分
- 最近吃过什么
- 采购限制

AI 只负责生成候选计划，最终仍写入现有 SQLite 表。

