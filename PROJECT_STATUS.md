# Anthropic Blog Monitor - 项目现状

**更新时间**: 2026-02-24  
**状态**: 🟡 基础功能已部署，部分功能待完善

---

## 📦 项目概述

Anthropic 官方博客监控服务，自动抓取最新文章并生成中文摘要。

**项目位置**: `/Users/huangyifei/.openclaw/workspace/anthropic-blog-monitor`

---

## ✅ 已完成功能

### 1. Docker 部署
- [x] PostgreSQL 15 数据库容器
- [x] FastAPI 后端容器
- [x] Next.js 前端容器
- [x] docker-compose 编排

### 2. 后端 API
- [x] FastAPI 框架搭建
- [x] PostgreSQL 数据库连接
- [x] 文章数据模型 (Article)
- [x] RESTful API 接口
  - `GET /articles` - 获取文章列表
  - `GET /articles/:id` - 获取单篇文章
  - `POST /scrape` - 手动触发爬取
  - `GET /status` - 服务状态

### 3. 爬虫功能
- [x] Anthropic Engineering 博客爬取
- [x] Anthropic News 页面爬取
- [x] 文章标题、URL 提取
- [x] 网页内容提取（基础版）

### 4. 大模型集成
- [x] 读取 OpenClaw 配置文件 (`~/.openclaw/openclaw.json`)
- [x] 自动获取 Dashscope API Key
- [x] 使用 qwen3.5-plus 模型
- [x] 摘要生成接口

### 5. 定时任务
- [x] APScheduler 调度器
- [x] 每日 9:00 自动检查更新
- [x] 新文章自动处理

### 6. 前端展示
- [x] Next.js 14 框架
- [x] 文章列表页面
- [x] 响应式设计
- [x] 自动刷新（每分钟）

---

## 🚧 待完善功能

### 高优先级

| 问题 | 描述 | 解决方案 |
|------|------|----------|
| **内容提取不完整** | 爬虫无法获取文章正文内容 | 需要优化爬虫逻辑，处理 Next.js SSR 渲染 |
| **摘要未生成** | 文章摘要字段为空 | 内容提取完成后，摘要 API 会自动调用 |
| **飞书推送未配置** | 缺少 Webhook URL | 创建 `.env` 文件配置 `FEISHU_WEBHOOK` |

### 中优先级

- [ ] 文章详情页
- [ ] 搜索功能
- [ ] 标签分类
- [ ] 阅读统计

### 低优先级

- [ ] 用户订阅功能
- [ ] 邮件推送
- [ ] RSS 输出
- [ ] 多语言支持

---

## 🔧 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端** | Python + FastAPI | 3.11 + 0.133.0 |
| **前端** | Next.js + React | 14.1.0 + 18.2.0 |
| **数据库** | PostgreSQL | 15-alpine |
| **ORM** | SQLAlchemy | 2.0.25 |
| **调度器** | APScheduler | 3.10.4 |
| **大模型** | Dashscope qwen3.5-plus | - |
| **部署** | Docker Compose | 3.8 |

---

## 📁 项目结构

```
anthropic-blog-monitor/
├── backend/
│   ├── main.py           # FastAPI 主应用
│   ├── scraper.py        # 爬虫模块
│   ├── summarizer.py     # 摘要生成
│   ├── scheduler.py      # 定时任务
│   ├── database.py       # 数据库连接
│   ├── models.py         # 数据模型
│   ├── config.py         # 配置读取
│   ├── notifier.py       # 飞书推送
│   └── requirements.txt  # Python 依赖
├── frontend/
│   ├── app/
│   │   ├── page.tsx      # 首页
│   │   ├── layout.tsx    # 布局
│   │   └── globals.css   # 全局样式
│   ├── package.json
│   └── next.config.js
├── docker-compose.yml    # Docker 编排
├── README.md             # 项目说明
└── PROJECT_STATUS.md     # 本文档
```

---

## 🚀 快速启动

### 1. 启动服务
```bash
cd /Users/huangyifei/.openclaw/workspace/anthropic-blog-monitor
docker-compose up -d
```

### 2. 访问服务
- 前端：http://localhost:3002
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 3. 手动触发爬取
```bash
curl -X POST http://localhost:8000/scrape
```

### 4. 查看日志
```bash
# 后端日志
docker logs -f anthropic-blog-backend

# 前端日志
docker logs -f anthropic-blog-frontend

# 数据库日志
docker logs -f anthropic-blog-db
```

### 5. 停止服务
```bash
docker-compose down
```

---

## 📊 当前运行状态

```bash
# 检查容器状态
docker-compose ps

# 输出示例：
NAME                      STATUS                    PORTS
anthropic-blog-backend    Up 5 minutes              0.0.0.0:8000->8000/tcp
anthropic-blog-db         Up 10 minutes (healthy)   0.0.0.0:5432->5432/tcp
anthropic-blog-frontend   Up 9 minutes              0.0.0.0:3002->3000/tcp
```

---

## 🔐 配置说明

### 环境变量（可选）

创建 `.env` 文件配置以下内容：

```bash
# 飞书推送 Webhook
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx

# 数据库配置（默认值）
POSTGRES_USER=anthropic_blog
POSTGRES_PASSWORD=anthropic_blog_pass
POSTGRES_DB=anthropic_blog
```

### 大模型配置

自动从 `~/.openclaw/openclaw.json` 读取：
- API Key: `sk-sp-0b0126cd996d4aa2887a115f0a50f9d7`
- Base URL: `https://coding.dashscope.aliyuncs.com/v1`
- Model: `qwen3.5-plus`

---

## 🐛 已知问题

### 1. 爬虫内容提取问题
**现象**: 文章内容为空，导致摘要无法生成

**原因**: Anthropic 网站使用 Next.js SSR，内容在 JSON 数据中

**解决方案**: 
- 优化 `scraper.py` 中的 `scrape_article_content()` 方法
- 从 HTML 的 `<script>` 标签中提取 JSON 数据
- 或使用 Playwright 等工具渲染 JavaScript

### 2. 端口冲突
**现象**: 前端启动失败，提示端口被占用

**原因**: 3000 端口被 docker-project-manager 占用

**解决方案**: 前端改用 3002 端口

---

## 📈 下一步计划

### 本周
- [ ] 修复爬虫内容提取
- [ ] 测试摘要生成功能
- [ ] 配置飞书推送

### 下周
- [ ] 添加文章详情页
- [ ] 优化 UI/UX
- [ ] 添加搜索功能

### 长期
- [ ] 支持更多博客源
- [ ] 用户订阅系统
- [ ] 数据分析面板

---

## 📝 开发记录

### 2026-02-24
- ✅ 项目初始化
- ✅ Docker 部署完成
- ✅ 后端 API 开发
- ✅ 前端页面开发
- ✅ OpenClaw 配置集成
- ⚠️ 爬虫内容提取待优化
- ⚠️ 摘要生成待测试

---

## 📞 联系方式

**项目负责人**: 大尾巴猫 🐱  
**开发时间**: 2026-02-24  
**Git 仓库**: `/Users/huangyifei/.openclaw/workspace/anthropic-blog-monitor`

---

*最后更新：2026-02-24 21:20*
