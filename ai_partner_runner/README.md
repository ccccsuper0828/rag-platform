# AI Partner Runner (Host Service)

这个服务负责把 **Claude Code + Skills（ai-partner-chat）** 融入到 `rag-platform-mvp`：
- 每个 `rag_id` 对应一个隔离 workspace
- workspace 内自动准备 `.claude/skills/ai-partner-chat/`
- 通过 PTY 启动 `claude` CLI 并流式读取输出

> 重要：Claude Code 是 **macOS/Windows/Linux 的本机 CLI**，不能在 Linux Docker 容器里直接运行（Mac 二进制不能在容器内跑）。  
> 所以 Runner **必须在宿主机运行**，MVP 后端容器通过 `host.docker.internal` 调它。

## 1) 前置条件：安装 Claude Code

请先在宿主机安装 Claude Code（安装后确保终端里能执行 `claude --version`）。

### 方式 A：npm 全局安装（macOS / Linux 常用）

如果你不想用 `sudo` 全局安装，可以创建一个专用的 npm 全局目录：

```bash
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

安装 Claude Code：

```bash
npm install -g @anthropic-ai/claude-code
```

验证：

```bash
claude --version
which claude
```

> 如果 `claude --version` 还是提示找不到：
> - 重新开一个新终端窗口（让 PATH 生效）
> - 或检查你用的是不是 zsh：`echo $SHELL`
> - 如果是 bash，把 PATH 写到 `~/.bashrc` 或 `~/.bash_profile`

安装成功后再继续下面步骤。

## 2) 放置 ai-partner-chat skill

你已经下载在：
- `/Users/chaowang/rag platform/ai-partner-chat`

Runner 会把它复制到每个 workspace 的：
- `<workspace>/.claude/skills/ai-partner-chat/`

## 3) 启动 Runner

```bash
cd "/Users/chaowang/rag platform/rag-platform-mvp/ai_partner_runner"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 推荐：使用 `.env`（更省事）
# 1) 复制 `env.example` → `.env`
# 2) 在 `.env` 里把 ANTHROPIC_AUTH_TOKEN 替换成你的 Moonshot API Key
# 3) 启动时会自动读取 `.env`

uvicorn app:app --host 0.0.0.0 --port 9001 --reload
```

健康检查：
- `GET http://localhost:9001/health`

> 如果调用时报错 `Invalid API key · Please run /login`：
> - 说明 Claude Code 没拿到可用的 `ANTHROPIC_AUTH_TOKEN`（或没配置 Kimi 的 base url）
> - 请检查 `.env` 中 `ANTHROPIC_AUTH_TOKEN` 是否正确，然后重启 Runner 再试

## 4) MVP 后端如何连 Runner

在 `docker-compose.yml` 里设置：
- `AI_PARTNER_RUNNER_URL=http://host.docker.internal:9001`

然后前端选择 `aipartner` 即可（我们会在 MVP 里加这个架构选项）。


