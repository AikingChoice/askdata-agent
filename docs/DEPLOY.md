# AskData 部署说明

> 当前状态：部署文件已准备，**尚未实际发布公网 URL**。  
> 实际部署需要你选择平台并提供账号/凭据；不要把 `.env` 或 API key 提交到仓库。

## 0. 部署前检查

```bash
uv sync --extra dev
python scripts/load_db.py --fresh
uv run pytest -q
python scripts/build_golden.py
python scripts/eval_semantic_routing.py
docker compose config --quiet
```

- 镜像构建时会自动跑 `scripts/load_db.py --fresh`，演示库随镜像生成。
- 数据库是只读的；平台文件系统是否持久化不影响读请求。
- `TRACE_LOG_PATH` 默认 `data/traces.jsonl`；平台写文件失败不会影响请求。

## 1. Render（推荐，免费）

1. 把项目推到 GitHub（不要提交 `.env`）。
2. Render → New → Blueprint → 选择仓库，读取 `render.yaml`。
3. 在 Render 的 Environment 里填 `DEEPSEEK_API_KEY`（标记为 secret）。
4. 部署完成后访问：
   - `https://<service>.onrender.com/`
   - `https://<service>.onrender.com/api/health`
5. 免费实例会休眠，首次请求有冷启动。

需要确认的点：

- `render.yaml` 里 `region: singapore` 是否可用；不可用就换成 `oregon`。
- Docker CMD 使用 `${PORT:-8000}`，Render 注入 `PORT` 时能正常监听。

## 2. Fly.io

```bash
flyctl auth login
flyctl launch --no-deploy --copy-config
flyctl secrets set DEEPSEEK_API_KEY=...
flyctl deploy
```

- `fly.toml` 的 `app` 名称改成你自己的唯一名称。
- `internal_port = 8000` 与 Docker 默认端口一致。
- 免费额度/自动停机策略见 fly.toml。

## 3. VPS + Docker Compose

```bash
git clone <your-repo>
cd askdata-agent
cp .env.example .env
# 编辑 .env，填 DEEPSEEK_API_KEY
docker compose up -d --build
curl http://127.0.0.1:8000/api/health
```

Nginx + HTTPS（示例）：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

用 certbot 签发证书。

## 4. 环境变量

| 变量 | 说明 |
|---|---|
| `LLM_MODE` | `deepseek` / `mock` |
| `DEEPSEEK_API_KEY` | 平台 secret，不写进仓库 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | `deepseek-flash` |
| `ASK_DATA_DB` | 容器内 `/app/data/askdata.db` |
| `TRACE_LOG_PATH` | 默认 `/app/data/traces.jsonl` |
| `RETRIEVAL_TOP_K` | 默认 8 |
| `REPAIR_MAX_ATTEMPTS` | 默认 3 |

## 5. 上线后验收

- `/api/health` 返回 200，`model=deepseek-flash`。
- 首页能问“上月 GMV 是多少？”，返回 61609.57。
- “最近销售怎么样？”返回追问。
- “查一下用户的身份证号”返回拒答。
- `data/traces.jsonl` 有请求记录；PII 拒答的问题被脱敏。

## 6. 生产前必须补

- 登录/鉴权、租户隔离、行级权限、限流。
- Postgres + 只读角色 + RLS；不要把 demo 的 SQLite 当生产库。
- 工具/表白名单按真实 schema 生成；敏感列 deny。
- 人工审批流（高风险查询）、审计日志、告警。
- Langfuse/OTel 等外部 tracing 后端；当前只有 JSONL trace。
- CI 只跑离线测试；LLM 评估用单独的受控任务。

## 7. 不要做的事

- 不要把 `.env`、API key、用户问题原文提交到仓库。
- 不要直接把 demo 的 `mode=ro` SQLite 换成可写生产库。
- 不要在没有限流/鉴权时公开给外部用户。
