# RAG Platform 生产环境部署指南

## 🎯 部署目标

将 RAG Platform 部署到公网服务器，让所有用户通过 `https://your-domain.com` 访问。

---

## 📋 部署方式对比

| 方式 | 成本 | 难度 | 推荐场景 |
|------|-----|------|---------|
| **云服务器 + Docker** | $20-100/月 | ⭐⭐ | 个人/小团队 |
| **Serverless** | 按量付费 | ⭐⭐⭐ | 流量波动大 |
| **Kubernetes** | $100+/月 | ⭐⭐⭐⭐ | 企业级 |

**推荐**: 云服务器 + Docker Compose（最简单、成本可控）

---

## 🚀 方案一：云服务器部署（推荐）

### Step 1: 购买云服务器

**推荐配置**（50-100 并发用户）：
- **CPU**: 4 核
- **内存**: 8GB
- **存储**: 100GB SSD
- **带宽**: 5Mbps+
- **系统**: Ubuntu 22.04 LTS

**云服务商推荐**：
- 国内：阿里云、腾讯云（约 ¥200-400/月）
- 海外：AWS EC2、DigitalOcean、Vultr（约 $40-80/月）

### Step 2: 域名与 SSL

```bash
# 1. 购买域名（阿里云/腾讯云/Cloudflare）
# 例如: rag-platform.com

# 2. 解析到服务器 IP
# A 记录: @ -> 你的服务器IP
# A 记录: api -> 你的服务器IP

# 3. SSL 证书（免费）
# 使用 Let's Encrypt，后面会配置
```

### Step 3: 服务器初始化

```bash
# SSH 登录服务器
ssh root@your-server-ip

# 更新系统
apt update && apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# 安装 Docker Compose
apt install docker-compose-plugin -y

# 安装 Node.js（for Claude CLI）
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 安装 Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
docker --version
```

### Step 4: 上传代码

```bash
# 方式1: Git Clone（推荐）
cd /opt
git clone https://github.com/your-username/rag-platform.git
cd rag-platform

# 方式2: 从本地上传
# 在本地执行：
rsync -avz --exclude 'node_modules' --exclude '__pycache__' \
  "/Users/chaowang/rag platform/rag-platform-mvp/" \
  root@your-server-ip:/opt/rag-platform/
```

### Step 5: 配置生产环境

创建生产环境配置 `/opt/rag-platform/.env.production`:

```env
# ========== Claude API（核心） ==========
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxx

# ========== 数据库 ==========
MYSQL_ROOT_PASSWORD=your-secure-password-here
MYSQL_DATABASE=rag_platform

# ========== 安全 ==========
JWT_SECRET=your-very-long-random-string-for-jwt-signing

# ========== 域名 ==========
DOMAIN=rag-platform.com
API_DOMAIN=api.rag-platform.com

# ========== 可选：NFT 功能 ==========
# WEB3_ENABLED=true
# SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/xxx
# RAG_NFT_CONTRACT=0x...
```

### Step 6: Docker Compose 生产配置

创建 `/opt/rag-platform/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # ========== 数据库 ==========
  mysql:
    image: mysql:8.0
    container_name: rag-mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - rag-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ========== AI Partner Runner ==========
  runner:
    build:
      context: ./ai_partner_runner
      dockerfile: Dockerfile.prod
    container_name: rag-runner
    restart: always
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLAUDE_BIN=/usr/local/bin/claude
      - AI_PARTNER_WORKSPACES_DIR=/app/workspaces
      - AI_PARTNER_SKILL_SRC=/app/skill
    volumes:
      - workspaces_data:/app/workspaces
      - ./ai-partner-chat:/app/skill:ro
    networks:
      - rag-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========== 后端 API ==========
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: rag-backend
    restart: always
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=root
      - MYSQL_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DB=${MYSQL_DATABASE}
      - AI_PARTNER_RUNNER_URL=http://runner:9001
      - JWT_SECRET=${JWT_SECRET}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - workspaces_data:/app/ai_partner_workspaces
    depends_on:
      mysql:
        condition: service_healthy
      runner:
        condition: service_healthy
    networks:
      - rag-network

  # ========== 前端 ==========
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        - VITE_API_BASE_URL=https://${API_DOMAIN}
    container_name: rag-frontend
    restart: always
    networks:
      - rag-network

  # ========== Nginx 反向代理 ==========
  nginx:
    image: nginx:alpine
    container_name: rag-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - certbot_data:/var/www/certbot:ro
    depends_on:
      - frontend
      - backend
    networks:
      - rag-network

  # ========== SSL 证书自动续期 ==========
  certbot:
    image: certbot/certbot
    container_name: rag-certbot
    volumes:
      - certbot_data:/var/www/certbot
      - ./nginx/ssl:/etc/letsencrypt
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

networks:
  rag-network:
    driver: bridge

volumes:
  mysql_data:
  workspaces_data:
  certbot_data:
```

### Step 7: 创建 Dockerfile

**`ai_partner_runner/Dockerfile.prod`**:

```dockerfile
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 安装 Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# 创建工作目录
WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建工作区目录
RUN mkdir -p /app/workspaces

# 暴露端口
EXPOSE 9001

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9001"]
```

**`backend/Dockerfile.prod`**:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/ai_partner_workspaces

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`frontend/Dockerfile.prod`**:

```dockerfile
# 构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# 生产阶段
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

### Step 8: Nginx 配置

创建 `/opt/rag-platform/nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # 上传文件大小限制
    client_max_body_size 50M;

    # 前端
    server {
        listen 80;
        server_name rag-platform.com www.rag-platform.com;

        # Let's Encrypt 验证
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # 重定向到 HTTPS
        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl http2;
        server_name rag-platform.com www.rag-platform.com;

        ssl_certificate /etc/nginx/ssl/live/rag-platform.com/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/live/rag-platform.com/privkey.pem;

        location / {
            proxy_pass http://frontend:80;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }

    # API
    server {
        listen 80;
        server_name api.rag-platform.com;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl http2;
        server_name api.rag-platform.com;

        ssl_certificate /etc/nginx/ssl/live/rag-platform.com/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/live/rag-platform.com/privkey.pem;

        location / {
            proxy_pass http://backend:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket 支持（流式响应）
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 300s;
        }
    }
}
```

### Step 9: 获取 SSL 证书

```bash
cd /opt/rag-platform

# 首次获取证书（先启动 nginx 不带 SSL）
docker compose -f docker-compose.prod.yml up -d nginx

# 获取证书
docker run -it --rm \
  -v ./nginx/ssl:/etc/letsencrypt \
  -v certbot_data:/var/www/certbot \
  certbot/certbot certonly \
  --webroot -w /var/www/certbot \
  -d rag-platform.com \
  -d www.rag-platform.com \
  -d api.rag-platform.com \
  --email your-email@example.com \
  --agree-tos
```

### Step 10: 启动生产环境

```bash
cd /opt/rag-platform

# 加载环境变量
export $(cat .env.production | xargs)

# 构建并启动所有服务
docker compose -f docker-compose.prod.yml up -d --build

# 查看状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

---

## 🔧 方案二：Serverless 部署（Vercel + Railway）

适合快速上线、流量不稳定的场景。

### 前端 → Vercel

```bash
cd frontend

# 安装 Vercel CLI
npm i -g vercel

# 部署
vercel --prod

# 设置环境变量
vercel env add VITE_API_BASE_URL
# 输入: https://your-api.railway.app
```

### 后端 → Railway

1. 访问 https://railway.app
2. 新建项目 → 从 GitHub 导入
3. 添加 MySQL 服务
4. 配置环境变量:
   - `ANTHROPIC_API_KEY`
   - `JWT_SECRET`
   - `MYSQL_*`（Railway 自动提供）
5. 部署

### AI Partner Runner → Railway

同样方式部署，注意 Claude CLI 需要在 Dockerfile 中安装。

---

## 💰 成本估算

### 云服务器方案（月费）

| 项目 | 费用 |
|------|-----|
| 云服务器 (4核8G) | ¥200-400 |
| 域名 | ¥50/年 |
| Anthropic API | 按量 ~$0.003/1K tokens |
| **总计** | **¥200-500/月** + API 费用 |

### API 费用估算

| 模型 | 输入价格 | 输出价格 |
|------|---------|---------|
| Claude Sonnet | $3/M tokens | $15/M tokens |
| Claude Haiku | $0.25/M tokens | $1.25/M tokens |

**示例**: 100 用户 × 10 次对话/天 × 1000 tokens/次 = 1M tokens/天
- Sonnet: ~$18/天 = $540/月
- Haiku: ~$1.5/天 = $45/月

---

## 🔐 安全加固

### 1. 防火墙

```bash
# 只开放必要端口
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw enable
```

### 2. API 限流

在 `backend/main.py` 添加:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/v1/chat/stream")
@limiter.limit("10/minute")  # 每分钟最多 10 次
async def chat_stream(...):
    ...
```

### 3. 监控

```bash
# 使用 Uptime Kuma 监控
docker run -d \
  --name uptime-kuma \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:1
```

---

## 📊 扩展建议

### 水平扩展

当用户量增长时：

1. **数据库**: 升级到云数据库（RDS/Cloud SQL）
2. **Runner**: 多实例 + 负载均衡
3. **缓存**: 添加 Redis 缓存热门查询
4. **CDN**: 前端静态资源上 CDN

### 高可用架构

```
                    ┌─────────────┐
                    │   CDN       │
                    │ (Cloudflare)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   负载均衡   │
                    │  (Nginx/ALB) │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
    │ Backend │       │ Backend │       │ Backend │
    │   #1    │       │   #2    │       │   #3    │
    └────┬────┘       └────┬────┘       └────┬────┘
         │                 │                 │
         └────────────┬────┴────────────────┘
                      │
              ┌───────▼───────┐
              │ MySQL 主从    │
              │ + Redis 集群  │
              └───────────────┘
```

---

## ✅ 部署检查清单

- [ ] 服务器已购买并初始化
- [ ] 域名已购买并解析
- [ ] SSL 证书已配置
- [ ] `.env.production` 已配置
- [ ] Docker 镜像构建成功
- [ ] 所有服务健康运行
- [ ] HTTPS 访问正常
- [ ] 用户注册/登录正常
- [ ] 文件上传正常
- [ ] 聊天功能正常
- [ ] 防火墙已配置
- [ ] 监控已设置
- [ ] 备份策略已制定

---

## 🆘 常见问题

### Q: Claude CLI 在 Docker 中无法认证

确保在 Dockerfile 中正确设置 API Key:
```dockerfile
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

或在 docker-compose 中传递:
```yaml
environment:
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

### Q: 数据库连接失败

等待 MySQL 完全启动:
```yaml
depends_on:
  mysql:
    condition: service_healthy
```

### Q: 上传大文件失败

调整 Nginx 配置:
```nginx
client_max_body_size 100M;
```

---

## 📞 技术支持

部署遇到问题？检查：
1. `docker compose logs -f` 查看错误
2. 确认所有环境变量正确设置
3. 确认 Anthropic API Key 有效且有余额

