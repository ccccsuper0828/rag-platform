# RAG Platform 生产部署指南

## 📋 目录

1. [架构概览](#架构概览)
2. [部署选项](#部署选项)
3. [快速部署](#快速部署)
4. [云平台部署](#云平台部署)
5. [配置说明](#配置说明)
6. [监控与运维](#监控与运维)

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                         负载均衡 / CDN                           │
│                    (Cloudflare / AWS ALB)                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Nginx 反向代理                            │
│                    (SSL 终止 / 路由分发)                         │
└─────────────────────────────────────────────────────────────────┘
                    │                       │
                    ▼                       ▼
        ┌───────────────────┐   ┌───────────────────────┐
        │  Frontend (Vue)   │   │   Backend (FastAPI)   │
        │    静态资源        │   │      API 服务         │
        │   Port: 80        │   │     Port: 8000        │
        └───────────────────┘   └───────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
        ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
        │      MySQL        │ │      Redis        │ │   对象存储         │
        │    用户数据        │ │   缓存/会话       │ │  (S3/OSS/MinIO)   │
        │   Port: 3306      │ │   Port: 6379      │ │   文件存储         │
        └───────────────────┘ └───────────────────┘ └───────────────────┘
                                          │
                                          ▼
                              ┌───────────────────┐
                              │    LLM 服务       │
                              │  (Claude/GPT/     │
                              │   Ollama)         │
                              └───────────────────┘
```

### 多租户数据隔离

| 数据类型 | 隔离方式 | 存储位置 |
|---------|---------|---------|
| 用户账户 | user_id 主键 | MySQL `users` |
| RAG 文档 | user_id 外键 | MySQL `rags` + 对象存储 |
| 记忆库 | user_id 外键 | MySQL `memories` |
| 光源数据 | user_id 外键 | MySQL `spark_*` |
| NFT 记录 | user_id 外键 | MySQL `nfts` |
| 文件 | 路径隔离 | `users/{user_id}/uploads/` |

---

## 🚀 部署选项

### 选项 1: Docker Compose (推荐入门)

适合：小型团队、快速验证、单机部署

```bash
# 一键部署
./deploy/scripts/deploy.sh
```

### 选项 2: Kubernetes (推荐生产)

适合：大规模、高可用、弹性伸缩

```bash
# 使用 Helm Chart
helm install rag-platform ./deploy/helm
```

### 选项 3: 云托管服务

适合：最小运维、快速上线

| 服务 | AWS | 阿里云 | 腾讯云 |
|------|-----|-------|-------|
| 计算 | ECS/Fargate | ECS | CVM/TKE |
| 数据库 | RDS MySQL | RDS | CDB |
| 存储 | S3 | OSS | COS |
| CDN | CloudFront | CDN | CDN |

---

## ⚡ 快速部署

### 1. 准备环境

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 克隆项目

```bash
git clone https://github.com/your-org/rag-platform.git
cd rag-platform
```

### 3. 配置环境

```bash
# 复制配置模板
cp deploy/env.prod.template .env.prod

# 编辑配置 (必须修改以下项)
nano .env.prod
```

**必须修改的配置：**

```bash
# 数据库密码
MYSQL_ROOT_PASSWORD=<生成强密码>
MYSQL_PASSWORD=<生成强密码>

# Redis 密码
REDIS_PASSWORD=<生成强密码>

# JWT 密钥
JWT_SECRET_KEY=<生成 32+ 字符的随机密钥>

# LLM API 密钥 (选择一个)
ANTHROPIC_API_KEY=sk-ant-...
# 或
OPENAI_API_KEY=sk-...
```

生成强密码的方法：

```bash
# 生成随机密码
openssl rand -base64 32

# 生成 JWT 密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. 部署

```bash
# 构建并启动
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 5. 验证

```bash
# 健康检查
curl http://localhost/health

# 测试 API
curl http://localhost/api/v1/auth/me
```

---

## ☁️ 云平台部署

### AWS 部署

#### 1. 创建基础设施

```bash
# 使用 Terraform (推荐)
cd deploy/terraform/aws
terraform init
terraform plan
terraform apply
```

或手动创建：

1. **RDS MySQL**
   - 实例类型: db.t3.medium
   - 存储: 100GB SSD
   - 开启自动备份

2. **ElastiCache Redis**
   - 节点类型: cache.t3.micro
   - 集群模式: 关闭

3. **S3 存储桶**
   - 开启版本控制
   - 配置生命周期策略

4. **ECS Fargate**
   - 任务定义: 2 vCPU, 4GB RAM
   - 服务: 最小 2 个任务

#### 2. 配置 CI/CD

```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push
        run: |
          docker build -t $ECR_REGISTRY/rag-backend:${{ github.sha }} ./backend
          docker push $ECR_REGISTRY/rag-backend:${{ github.sha }}

      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster rag-cluster --service rag-backend --force-new-deployment
```

### 阿里云部署

#### 1. 创建资源

```bash
# 使用阿里云 CLI
aliyun ecs CreateInstance ...
aliyun rds CreateDBInstance ...
aliyun oss mb oss://rag-platform-prod
```

#### 2. 配置存储

```bash
# .env.prod
STORAGE_TYPE=oss
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY=your_access_key
OSS_SECRET_KEY=your_secret_key
OSS_BUCKET=rag-platform-prod
```

---

## ⚙️ 配置说明

### 存储配置

#### 本地存储 (开发)

```bash
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=user_data
```

#### AWS S3

```bash
STORAGE_TYPE=s3
S3_ACCESS_KEY=AKIAXXXXXXXXX
S3_SECRET_KEY=xxxxxxxxxxxxxxx
S3_BUCKET=rag-platform-prod
S3_REGION=us-east-1
```

#### MinIO (自托管 S3)

```bash
STORAGE_TYPE=s3
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin123
S3_BUCKET=rag-platform
```

#### 阿里云 OSS

```bash
STORAGE_TYPE=oss
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY=your_access_key
OSS_SECRET_KEY=your_secret_key
OSS_BUCKET=rag-platform-prod
```

### LLM 配置

#### Claude (推荐)

```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

#### OpenAI

```bash
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o
```

#### Ollama (自托管)

```bash
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3:70b
```

### SSL 配置

#### 使用 Let's Encrypt

```bash
# 安装 certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

#### 配置 Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # ... 其他配置
}
```

---

## 📊 监控与运维

### 健康检查

```bash
# 检查所有服务
./deploy/scripts/deploy.sh status

# 检查 API
curl -s http://localhost/health | jq

# 检查数据库连接
docker exec rag_mysql mysqladmin ping -h localhost
```

### 日志查看

```bash
# 查看所有日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务
docker-compose -f docker-compose.prod.yml logs -f backend

# 导出日志
docker-compose -f docker-compose.prod.yml logs --no-color > logs.txt
```

### 备份

```bash
# 备份 MySQL
docker exec rag_mysql mysqldump -u root -p rag_platform > backup_$(date +%Y%m%d).sql

# 备份到 S3
aws s3 cp backup_$(date +%Y%m%d).sql s3://rag-platform-backups/
```

### 扩容

```bash
# 水平扩展 Backend
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并部署
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 零停机更新 (rolling update)
docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend
```

---

## 🔒 安全检查清单

- [ ] 所有密码使用强随机生成
- [ ] JWT 密钥至少 32 字符
- [ ] 数据库禁止外网访问
- [ ] 开启 HTTPS
- [ ] 配置防火墙规则
- [ ] 启用日志监控
- [ ] 定期备份数据
- [ ] 限制 API 访问频率

---

## 📞 常见问题

### Q: 数据库连接失败

```bash
# 检查 MySQL 状态
docker logs rag_mysql

# 检查网络
docker network inspect rag-platform-mvp_rag_network
```

### Q: 文件上传失败

```bash
# 检查存储配置
docker exec rag_backend env | grep STORAGE

# 检查 MinIO 状态
curl http://localhost:9000/minio/health/live
```

### Q: LLM 响应超时

```bash
# 检查 LLM 配置
docker exec rag_backend env | grep -E "(ANTHROPIC|OPENAI|OLLAMA)"

# 测试 Ollama
curl http://localhost:11434/api/generate -d '{"model":"llama3","prompt":"Hi"}'
```

---

## 📚 相关文档

- [多租户指南](./MULTI_TENANT_GUIDE.md)
- [API 文档](./docs/api.md)
- [架构概览](./COMPLETE_ARCHITECTURE.md)

