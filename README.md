# AskData

[![CI](https://github.com/AikingChoice/askdata-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/AikingChoice/askdata-agent/actions/workflows/ci.yml)

AskData 是一个 Text-to-SQL 数据问数 Agent：自然语言问题经过语义路由、schema 检索、SQL 生成、安全校验和只读执行，返回表格或图表。缺少口径时会追问，遇到敏感数据或写操作会拒答。

## 功能

- 语义路由：`sql` / `clarify` / `refuse` 三种出口
- Schema 检索：BM25 + 外键图
- SQL 生成：DeepSeek `deepseek-flash`，OpenAI 兼容接口
- SQL 安全：SQLGlot AST、单条 SELECT、表白名单、禁注释、强制 LIMIT
- 只读执行：SQLite `mode=ro` + `query_only` + 超时
- 修复循环：闸门或执行失败后回灌错误，最多 3 次
- 评估：40 条 golden，结果集对比
- 前端：聊天、表格、图表、SQL 展示
- 可观测：JSONL trace，PII 拒答脱敏

## 架构

```mermaid
flowchart LR
    U[用户] --> UI[前端]
    UI --> API[FastAPI /api/ask]
    API --> G[LangGraph]
    G --> A[analyze: 指标/时间/维度/拒答]
    A -->|sql| R[BM25 + FK 选表]
    A -->|clarify/refuse| E[直接返回]
    R --> S[生成 SQL]
    S --> Q[SQLGlot 闸门]
    Q -->|通过| X[只读执行]
    Q -->|失败| P[修复]
    X -->|成功| T[表格/图表]
    X -->|失败| P
    P --> S
    T --> UI
```

## 快速开始

```bash
uv sync --extra dev
python scripts/load_db.py --fresh
uv run uvicorn app.main:app --reload --port 8000
```

打开 `http://127.0.0.1:8000`。如果 8000 被占用，改成 `--port 8012`。

配置模型：

```bash
cp .env.example .env
# LLM_MODE=deepseek
# DEEPSEEK_API_KEY=...
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# DEEPSEEK_MODEL=deepseek-flash
```

没有 key 时会退回 Mock 模式，适合跑测试和看追问/拒答流程。

## API

```bash
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"上月 GMV 是多少？"}'
```

返回字段：

- `route`：`sql` / `clarify` / `refuse`
- `answer`：追问/拒答文本
- `sql`、`raw_sql`：执行 SQL 与模型原始 SQL
- `columns`、`rows`、`row_count`
- `analysis`：metric、time_range、dimensions、reason
- `attempts`、`trace`、`latency_ms`、`error`

其他接口：`GET /api/health`、`GET /api/schema`、`GET /docs`。

## 安全边界

1. 只允许单条 `SELECT` / `WITH...SELECT`。
2. 拒绝 DDL/DML、多语句、注释、限定表名和未知表。
3. 强制 `LIMIT 1000`；已有更小 LIMIT 保留。
4. SQLite 只读连接，并设置查询超时。
5. 写操作、PII、数据源不支持的主题在生成 SQL 前拒答。
6. 生产版本还需要登录、租户隔离、RLS、限流和人工审批。

## 数据

`data/` 下是确定性合成数据：

- 日期维 730 天，12 个区域，5 个渠道，20 个商品，60 个客户，6 个活动，14 个销售
- 438 个订单，1,014 条明细，58 条退款
- 含区域别名、空渠道、空退款原因、部分退款、复购偏置等脏数据

数据字典见 [docs/data_dictionary.md](docs/data_dictionary.md)。

## 评估

```bash
python scripts/build_golden.py
python scripts/run_eval.py
```

最新结果（40 条，真实 DeepSeek）：

| 指标 | 结果 |
|---|---:|
| 路由准确率 | 100.0% |
| Valid SQL Rate | 97.2% |
| Execution Accuracy | 91.7% |
| 追问/拒答正确率 | 100.0% |
| simple EX | 100.0% |
| moderate EX | 87.5% |
| challenging EX | 87.5% |
| p95 延迟 | 8.9s |

EX 使用结果集多重集比较，浮点保留 2 位；排名题只比较对象列，增长率题只比较增长列，额外证据列不惩罚。

完整报告见 [docs/eval_report.md](docs/eval_report.md)。目前还有 3 条失败：Q018 品类毛利率分摊、Q022 区域占比分组、Q036 连续 3 月毛利率下降时模型返回空 SQL。

## 演示

```bash
python scripts/demo.py          # 真实 DeepSeek
python scripts/demo.py --mock   # 不调用外部模型
```

覆盖 GMV、品类 Top 3、渠道退款率、追问和 PII 拒答。

## Docker

```bash
docker compose up --build
```

镜像构建时会执行 `scripts/load_db.py --fresh` 生成演示库。`.env` 可选，不提供时走 Mock。

## 可观测

每次 `POST /api/ask` 会追加一条 JSONL trace 到 `data/traces.jsonl`，记录 trace_id、路由、选中表、SQL、attempts、延迟和错误。PII 拒答时问题会写成 `[redacted]`。写文件失败不会影响请求。

## 部署

部署说明见 [docs/DEPLOY.md](docs/DEPLOY.md)。目前只跑了本地和 Docker，公网部署尚未执行。

## 目录

```text
app/
  main.py              FastAPI + 静态页面
  pipeline.py          LangGraph 状态图
  semantic.py          语义路由/追问/拒答
  schema_retrieval.py  BM25 + 外键图
  sql_guard.py         SQL 闸门
  executor.py          只读执行
  llm.py               DeepSeek / Mock
  static/index.html    前端
  observability.py     JSONL trace
data/
  schema.sql           10 表 DDL
  seed.sql             种子数据
  metrics.yml          指标/维度/歧义
  golden.jsonl         40 条评估集
docs/
  PLAN.md              方案
  data_dictionary.md   数据字典
  eval_report.md       评估报告
  DEPLOY.md            部署说明
scripts/
  load_db.py           灌库
  demo.py              5 问演示
  build_golden.py      构建/校验 gold SQL
  run_eval.py          真实评估
```

## 已知限制

- 合成数据，不代表真实业务分布；91.7% 是这 40 条用例上的结果，不是线上准确率。
- 只支持 SQLite demo；生产需要 Postgres、只读角色、RLS 和审计。
- 没有登录、权限和限流，当前是单用户 demo。
- 没有公网部署；没有外部 tracing 后端。
- 40 条评估集偏小，challenging 还有 3 条失败。
