# RAG Platform 云平台部署指南

本指南介绍如何将 RAG Platform 部署到主流云平台。

---

## 📋 部署架构选择

| 方案 | 前端 | 后端 | 数据库 | 存储 | 月成本 |
|------|------|------|--------|------|--------|
| **方案 A** | Vercel | Railway | Railway MySQL | Cloudflare R2 | ~$15-30 |
| **方案 B** | Vercel | Render | Render PostgreSQL | AWS S3 | ~$20-40 |
| **方案 C** | Vercel | Fly.io | PlanetScale | Cloudflare R2 | ~$10-25 |
| **方案 D** | 阿里云 OSS | 阿里云 ECS | 阿里云 RDS | 阿里云 OSS | ~¥200-500 |

**推荐**: 方案 A (Vercel + Railway) - 最简单、性价比高

---

## 🚀 方案 A: Vercel + Railway (推荐)

### 架构图

```
┌─────────────────┐     ┌─────────────────┐
│     Vercel      │────▶│     Railway     │
│   (Frontend)    │     │    (Backend)    │
│   Vue + Vite    │     │    FastAPI      │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Railway  │ │ Railway  │ │ R2/S3    │
              │  MySQL   │ │  Redis   │ │ Storage  │
              └──────────┘ └──────────┘ └──────────┘
```

### 步骤 1: 部署后端到 Railway

1. **注册 Railway**
   - 访问 https://railway.app
   - 使用 GitHub 登录

2. **创建项目**
   ```bash
   # 安装 Railway CLI
   npm install -g @railway/cli
   
   # 登录
   railway login
   
   # 在项目目录初始化
   cd rag-platform-mvp/backend
   railway init
   ```

3. **添加数据库**
   - 在 Railway 控制台点击 "New" → "Database" → "MySQL"
   - 自动生成连接信息

4. **配置环境变量**
   
   在 Railway 控制台 → Settings → Variables 添加：
   
   ```
   DATABASE_TYPE=mysql
   MYSQL_HOST=${{MySQL.MYSQLHOST}}
   MYSQL_PORT=${{MySQL.MYSQLPORT}}
   MYSQL_USER=${{MySQL.MYSQLUSER}}
   MYSQL_PASSWORD=${{MySQL.MYSQLPASSWORD}}
   MYSQL_DATABASE=${{MySQL.MYSQLDATABASE}}
   
   JWT_SECRET_KEY=<生成一个32+字符的随机密钥>
   
   STORAGE_TYPE=s3
   S3_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
   S3_ACCESS_KEY=<your-r2-access-key>
   S3_SECRET_KEY=<your-r2-secret-key>
   S3_BUCKET=rag-platform
   
   ANTHROPIC_API_KEY=<your-api-key>
   ```

5. **部署**
   ```bash
   railway up
   ```

6. **获取后端 URL**
   - 部署完成后，Railway 会提供一个 URL
   - 例如: `https://rag-backend-production.up.railway.app`

### 步骤 2: 部署前端到 Vercel

1. **注册 Vercel**
   - 访问 https://vercel.com
   - 使用 GitHub 登录

2. **导入项目**
   - 点击 "New Project"
   - 选择你的 GitHub 仓库
   - 设置 Root Directory 为 `rag-platform-mvp/frontend`

3. **配置环境变量**
   
   在 Vercel 控制台 → Settings → Environment Variables 添加：
   
   ```
   VITE_API_URL=https://rag-backend-production.up.railway.app
   ```

4. **部署**
   - 点击 "Deploy"
   - 等待构建完成

5. **配置自定义域名 (可选)**
   - Settings → Domains → Add Domain
   - 添加你的域名并配置 DNS

### 步骤 3: 配置 Cloudflare R2 存储

1. **创建 R2 存储桶**
   - 登录 Cloudflare Dashboard
   - R2 → Create bucket → 命名为 `rag-platform`

2. **创建 API Token**
   - R2 → Manage R2 API Tokens
   - Create API Token → 选择 "Object Read & Write"
   - 保存 Access Key ID 和 Secret Access Key

3. **获取端点 URL**
   ```
   https://<account-id>.r2.cloudflarestorage.com
   ```

---

## 🌐 方案 B: Vercel + Render

### 步骤 1: 部署后端到 Render

1. **注册 Render**
   - 访问 https://render.com
   - 使用 GitHub 登录

2. **创建 Web Service**
   - New → Web Service
   - 连接 GitHub 仓库
   - Root Directory: `rag-platform-mvp/backend`
   - Build Command: `pip install -r requirements.prod.txt`
   - Start Command: `gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

3. **添加 PostgreSQL 数据库**
   - New → PostgreSQL
   - 选择免费计划或 Starter

4. **配置环境变量**
   ```
   DATABASE_TYPE=mysql  # 或改用 PostgreSQL
   DATABASE_URL=${{PostgreSQL.DATABASE_URL}}
   JWT_SECRET_KEY=<your-secret>
   ANTHROPIC_API_KEY=<your-api-key>
   STORAGE_TYPE=s3
   S3_ACCESS_KEY=<your-key>
   S3_SECRET_KEY=<your-secret>
   S3_BUCKET=rag-platform
   ```

5. **获取后端 URL**
   - 例如: `https://rag-platform-api.onrender.com`

### 步骤 2: 部署前端到 Vercel

(同方案 A)

---

## ✈️ 方案 C: Vercel + Fly.io

### 步骤 1: 部署后端到 Fly.io

1. **安装 Fly CLI**
   ```bash
   # macOS
   brew install flyctl
   
   # 或使用安装脚本
   curl -L https://fly.io/install.sh | sh
   ```

2. **登录并初始化**
   ```bash
   fly auth login
   cd rag-platform-mvp/backend
   fly launch
   ```

3. **创建 fly.toml 配置**
   ```toml
   app = "rag-platform-api"
   primary_region = "nrt"  # Tokyo
   
   [build]
     dockerfile = "Dockerfile.prod"
   
   [env]
     PORT = "8080"
     DATABASE_TYPE = "mysql"
   
   [http_service]
     internal_port = 8080
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 1
   
   [[services]]
     internal_port = 8080
     protocol = "tcp"
   
     [[services.ports]]
       handlers = ["http"]
       port = 80
   
     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   
     [[services.http_checks]]
       interval = "10s"
       timeout = "2s"
       path = "/health"
   ```

4. **设置 Secrets**
   ```bash
   fly secrets set JWT_SECRET_KEY="your-secret-key"
   fly secrets set ANTHROPIC_API_KEY="your-api-key"
   fly secrets set MYSQL_HOST="your-db-host"
   fly secrets set MYSQL_PASSWORD="your-db-password"
   ```

5. **部署**
   ```bash
   fly deploy
   ```

---

## 🇨🇳 方案 D: 阿里云部署

### 架构图

```
┌─────────────────┐
│   阿里云 CDN    │
└────────┬────────┘
         │
┌────────┴────────┐
│  阿里云 SLB     │
│  (负载均衡)     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ ECS-1 │ │ ECS-2 │
│Backend│ │Backend│
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│  RDS  │ │  OSS  │
│ MySQL │ │ 存储  │
└───────┘ └───────┘
```

### 步骤 1: 创建 ECS 服务器

```bash
# 使用阿里云 CLI
aliyun ecs CreateInstance \
  --RegionId cn-hangzhou \
  --InstanceType ecs.t6-c1m2.large \
  --ImageId ubuntu_22_04_x64 \
  --SecurityGroupId sg-xxx \
  --VSwitchId vsw-xxx
```

### 步骤 2: 创建 RDS MySQL

```bash
aliyun rds CreateDBInstance \
  --RegionId cn-hangzhou \
  --Engine MySQL \
  --EngineVersion 8.0 \
  --DBInstanceClass rds.mysql.s1.small \
  --DBInstanceStorage 20
```

### 步骤 3: 创建 OSS 存储桶

```bash
aliyun oss mb oss://rag-platform-prod --region cn-hangzhou
```

### 步骤 4: 部署应用

```bash
# SSH 到 ECS
ssh root@your-ecs-ip

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 克隆代码
git clone https://github.com/your-org/rag-platform.git
cd rag-platform

# 配置环境变量
cp deploy/env.prod.template .env.prod
nano .env.prod

# 部署
docker-compose -f docker-compose.prod.yml up -d
```

### 步骤 5: 配置 CDN

1. 登录阿里云 CDN 控制台
2. 添加域名
3. 配置源站为 ECS IP 或 SLB 地址
4. 开启 HTTPS

---

## 🔧 通用配置

### 环境变量速查

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_TYPE` | 数据库类型 | `mysql` |
| `MYSQL_HOST` | 数据库主机 | `db.railway.app` |
| `MYSQL_PASSWORD` | 数据库密码 | `***` |
| `JWT_SECRET_KEY` | JWT 密钥 (32+字符) | `abc123...` |
| `STORAGE_TYPE` | 存储类型 | `s3`, `oss`, `local` |
| `S3_ENDPOINT` | S3 端点 | `https://xxx.r2.cloudflarestorage.com` |
| `S3_ACCESS_KEY` | S3 访问密钥 | `***` |
| `S3_SECRET_KEY` | S3 密钥 | `***` |
| `ANTHROPIC_API_KEY` | Claude API 密钥 | `sk-ant-...` |

### 生成 JWT 密钥

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📊 成本对比

| 平台 | 免费额度 | 入门成本 | 生产成本 |
|------|---------|---------|---------|
| **Vercel** | 100GB 带宽/月 | $0 | $20/月 |
| **Railway** | $5 额度/月 | $5-10 | $20-50/月 |
| **Render** | 750 小时/月 | $0 | $25-75/月 |
| **Fly.io** | 3 shared VMs | $0 | $10-30/月 |
| **Cloudflare R2** | 10GB 存储 | $0 | $0.015/GB |
| **阿里云** | 无 | ~¥50 | ¥200-500/月 |

---

## ✅ 部署检查清单

- [ ] 后端 API 可访问 (`/health` 返回 200)
- [ ] 前端可访问并能调用 API
- [ ] 数据库连接正常
- [ ] 文件上传功能正常
- [ ] LLM 响应正常
- [ ] HTTPS 已启用
- [ ] 自定义域名已配置

---

## 🆘 常见问题

### Q: Vercel 部署失败 "Build Error"

```bash
# 检查 Node 版本
node --version  # 需要 18+

# 本地测试构建
cd frontend
npm run build
```

### Q: Railway 数据库连接失败

确保使用 Railway 提供的变量引用：
```
MYSQL_HOST=${{MySQL.MYSQLHOST}}
```

### Q: CORS 错误

在后端 `main.py` 中添加前端域名：
```python
origins = [
    "https://your-app.vercel.app",
    "https://your-domain.com"
]
```

---

## 📚 相关链接

- [Vercel 文档](https://vercel.com/docs)
- [Railway 文档](https://docs.railway.app)
- [Render 文档](https://render.com/docs)
- [Fly.io 文档](https://fly.io/docs)
- [Cloudflare R2](https://developers.cloudflare.com/r2)

