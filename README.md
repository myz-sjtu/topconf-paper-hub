# TopConf Paper Hub

TopConf Paper Hub 是一个面向 **计算机网络、计算机体系结构、人工智能** 顶会论文的元数据采集与分类后端。

项目采用 **Conference Registry First** 方案：先维护可审核的顶会白名单，再按会议、年份和来源生成采集任务。第一版默认只保存论文元数据、DOI、官方页面和开放 PDF 链接，不做全网盲爬，也不绕过登录、付费墙或访问控制。

## Features

- 顶会白名单：SIGCOMM、NSDI、ISCA、MICRO、NeurIPS、ICML、CVPR、ACL 等。
- 按会议名称和会议届次年份归档，例如 `SIGCOMM 2025`、`NeurIPS 2024`。
- 来源适配器：DBLP、OpenAlex、OpenReview、CVF Open Access、USENIX。
- 入库流水线：标准化、去重、来源溯源、关键词子领域分类。
- FastAPI 接口：会议、届次、论文查询、采集预览、采集任务运行。
- 本地 SQLite 开发，PostgreSQL/Redis 可用于部署。
- APScheduler 支持每日增量任务，默认关闭。

## Quick Start

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env
.venv/bin/topconf init-db
.venv/bin/uvicorn app.main:app --reload
```

Open:

- Web dashboard: <http://127.0.0.1:8000/>
- Health: <http://127.0.0.1:8000/health>
- Swagger: <http://127.0.0.1:8000/docs>
- Conferences: <http://127.0.0.1:8000/api/v1/conferences>

## CLI Examples

```bash
# Preview SIGCOMM DBLP tasks for the default recent 5-year window
.venv/bin/topconf preview --conference SIGCOMM --source dblp

# Run a metadata crawl for SIGCOMM 2025 from DBLP
.venv/bin/topconf crawl --conference SIGCOMM --year 2025 --source dblp
```

## API Examples

```bash
curl "http://127.0.0.1:8000/api/v1/conferences?domain=ai"

curl -X POST "http://127.0.0.1:8000/api/v1/crawl/preview" \
  -H "Content-Type: application/json" \
  -d '{"conferences":["SIGCOMM"],"years":[2025],"sources":["dblp"]}'

curl "http://127.0.0.1:8000/api/v1/papers?conference=SIGCOMM&year=2025"
```

## Development

```bash
.venv/bin/pytest -q
.venv/bin/ruff check app tests
```

## Compliance

- 保存元数据、DOI、官方 landing page 和开放 PDF 链接。
- 不批量缓存受版权限制的 PDF。
- 不绕过登录、付费墙、robots 限制或访问控制。
- ACM/IEEE 等来源优先保存 DOI/landing page。
