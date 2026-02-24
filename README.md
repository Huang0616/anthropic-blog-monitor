# Anthropic Blog Monitor 📰

Anthropic 官方博客监控服务，自动抓取最新文章并生成中文摘要。

## 功能特性

- ✅ 自动爬取 Anthropic Engineering 和 News 博客
- ✅ 使用本地大模型（qwen-3.5）生成中文摘要
- ✅ 每日上午 9 点定时检查更新
- ✅ 飞书消息推送新文章
- ✅ 简洁的 Web UI 展示
- ✅ 智能重试机制（网络波动自动重试）
- ✅ 速率限制（避免触发反爬）

## 技术栈

- **后端**: FastAPI + SQLAlchemy + APScheduler
- **前端**: Next.js + Tailwind CSS
- **数据库**: PostgreSQL 15
- **部署**: Docker Compose

## 快速开始

### 1. 配置环境变量（可选）

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件配置飞书 Webhook（可选）：

```bash
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
```

### 2. 启动服务

```bash
cd /Users/huangyifei/.openclaw/workspace/anthropic-blog-monitor
docker-compose up -d
```

### 3. 访问服务

- **前端 UI**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 4. 查看日志

```bash
# 查看后端日志
docker logs -f anthropic-blog-backend

# 查看前端日志
docker logs -f anthropic-blog-frontend

# 首次启动后手动触发爬取
curl -X POST http://localhost:8000/scrape
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/status` | GET | 服务状态 |
| `/articles` | GET | 获取文章列表 |
| `/articles/:id` | GET | 获取单篇文章 |
| `/scrape` | POST | 手动触发爬取 |

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FEISHU_WEBHOOK` | 飞书推送 Webhook | 无 |
| `POSTGRES_USER` | 数据库用户名 | `anthropic_blog` |
| `POSTGRES_PASSWORD` | 数据库密码 | `anthropic_blog_pass` |
| `POSTGRES_DB` | 数据库名 | `anthropic_blog` |

### 大模型配置

服务会自动读取 `~/.openclaw/config.json` 和 `~/.openclaw/models.json` 获取 qwen 模型 API 配置。

## 停止服务

```bash
docker-compose down
```

## 数据持久化

数据库数据存储在 Docker volume `postgres_data` 中，删除容器不会丢失数据。

如需完全清空数据：

```bash
docker-compose down -v
```

## 开发说明

### 后端开发

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 集成到 docker-project-manager

服务使用标准 docker-compose.yml 配置，docker-project-manager 会自动发现并管理。

访问 docker-project-manager UI 即可看到 `anthropic-blog-monitor` 服务。

---

**享受 Anthropic 的高质量技术文章！** 🚀
