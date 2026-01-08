# RAG Platform 免费托管部署（Claude 付费）

## 🎯 方案概览

| 组件 | 服务 | 费用 |
|------|------|------|
| 前端 | **Vercel** | 免费 |
| 后端 + Runner | **Railway** | 免费 $5/月额度 |
| 数据库 | **Neon** (PostgreSQL) | 免费 |
| LLM | **Claude API** | 按量付费 |

**总托管成本: $0/月**（Claude API 另计）

---

## 🚀 部署步骤

### Step 1: 注册免费服务（5分钟）

1. **Vercel**: https://vercel.com → GitHub 登录
2. **Railway**: https://railway.app → GitHub 登录  
3. **Neon**: https://neon.tech → 创建免费 PostgreSQL

### Step 2: 获取 Claude API Key

1. 访问 https://console.anthropic.com
2. 注册/登录
3. 创建 API Key: `sk-ant-api03-xxx`
4. 充值（按需）

### Step 3: 创建 Neon 数据库

1. 登录 https://console.neon.tech
2. Create Project → 选择区域
3. 复制 Connection String:
   ```
   postgresql://user:pass@xxx.neon.tech/neondb?sslmode=require
   ```

### Step 4: 部署后端到 Railway

```bash
# 1. 安装 Railway CLI
npm install -g @railway/cli

# 2. 登录
railway login

# 3. 进入后端目录
cd "/Users/chaowang/rag platform/rag-platform-mvp/backend"

# 4. 初始化项目
railway init
# 选择: Create new project → 输入项目名

# 5. 设置环境变量
railway variables set ANTHROPIC_API_KEY=sk-ant-api03-你的key
railway variables set JWT_SECRET=$(openssl rand -hex 32)
railway variables set DATABASE_URL=你的Neon连接字符串
railway variables set AI_PARTNER_RUNNER_URL=http://localhost:9001

# 6. 部署
railway up

# 7. 获取后端 URL
railway open
# 记下 URL，如: https://xxx.up.railway.app
```

### Step 5: 部署 AI Partner Runner 到 Railway

```bash
# 在同一个 Railway 项目中添加新服务
cd "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_runner"

# 创建新服务
railway service create runner

# 设置环境变量
railway variables set ANTHROPIC_API_KEY=sk-ant-api03-你的key
railway variables set AI_PARTNER_WORKSPACES_DIR=/app/workspaces

# 部署
railway up
```

### Step 6: 部署前端到 Vercel

```bash
# 1. 安装 Vercel CLI
npm install -g vercel

# 2. 进入前端目录
cd "/Users/chaowang/rag platform/rag-platform-mvp/frontend"

# 3. 部署
vercel

# 4. 设置环境变量（Railway 后端 URL）
vercel env add VITE_API_BASE_URL
# 输入: https://你的railway后端.up.railway.app

# 5. 重新部署生产版本
vercel --prod
```

---

## 📋 环境变量汇总

### Railway 后端

| 变量 | 值 |
|------|-----|
| `ANTHROPIC_API_KEY` | sk-ant-api03-xxx |
| `JWT_SECRET` | 随机字符串 |
| `DATABASE_URL` | postgresql://... (Neon) |
| `AI_PARTNER_RUNNER_URL` | Runner 服务内部 URL |

### Railway Runner

| 变量 | 值 |
|------|-----|
| `ANTHROPIC_API_KEY` | sk-ant-api03-xxx |
| `AI_PARTNER_WORKSPACES_DIR` | /app/workspaces |

### Vercel 前端

| 变量 | 值 |
|------|-----|
| `VITE_API_BASE_URL` | https://后端.up.railway.app |

---

## 🔧 Railway 配置文件

创建 `backend/railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.prod"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

创建 `ai_partner_runner/railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.prod"
  },
  "deploy": {
    "startCommand": "uvicorn app:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

## 🔄 简化版：只用 Railway

Railway 可以一站式托管所有服务：

```bash
cd "/Users/chaowang/rag platform/rag-platform-mvp"

# 部署整个项目
railway init
railway up

# Railway 会自动检测 docker-compose.yml 并部署所有服务
```

### Railway 环境变量（一次性设置）

在 Railway Dashboard 设置：

```
ANTHROPIC_API_KEY=sk-ant-api03-xxx
JWT_SECRET=xxx
MYSQL_ROOT_PASSWORD=xxx
```

---

## 💰 费用估算

### 托管费用: $0

| 服务 | 免费额度 |
|------|---------|
| Vercel | 无限静态托管 |
| Railway | $5/月（足够运行 2 服务） |
| Neon | 0.5GB 免费 |

### Claude API 费用

| 模型 | 输入 | 输出 |
|------|------|------|
| Claude Sonnet | $3/M tokens | $15/M tokens |
| Claude Haiku | $0.25/M tokens | $1.25/M tokens |

**估算**（100用户/天，每人10次对话）：
- Sonnet: ~$15-30/月
- Haiku: ~$3-5/月

---

## ✅ 部署检查清单

- [ ] Vercel 账号已创建
- [ ] Railway 账号已创建
- [ ] Neon 数据库已创建
- [ ] Claude API Key 已获取
- [ ] 后端已部署到 Railway
- [ ] Runner 已部署到 Railway
- [ ] 前端已部署到 Vercel
- [ ] 环境变量已配置
- [ ] 网站可正常访问

---

## 🌐 最终访问地址

部署完成后：

- **前端**: `https://你的项目.vercel.app`
- **后端 API**: `https://你的项目.up.railway.app`

如需自定义域名，Vercel 和 Railway 都支持免费绑定。

---

## ⚠️ Railway 免费层限制

- $5 免费额度/月
- 约 500 小时运行时间
- 超出后服务暂停到下月

**解决方案**：
1. 升级到 Hobby 计划 ($5/月)
2. 或使用 Render（750小时/月免费）

---

## 🆘 常见问题

### Q: Railway 部署失败

```bash
# 查看日志
railway logs

# 常见原因：Dockerfile 路径问题
# 确保 Dockerfile.prod 存在
```

### Q: 前后端无法通信

检查 Vercel 环境变量：
```
VITE_API_BASE_URL=https://完整的railway后端URL
```

### Q: Claude API 报错

1. 检查 API Key 是否正确
2. 检查账户余额
3. 查看 Railway 日志

