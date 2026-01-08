# 🚀 光源 NFT 智能合约部署完整指南

## 目录
1. [前置准备](#1-前置准备)
2. [在 Remix 部署合约](#2-在-remix-部署合约)
3. [配置后端环境变量](#3-配置后端环境变量)
4. [测试完整流程](#4-测试完整流程)

---

## 1. 前置准备

### 1.1 安装 MetaMask
1. 浏览器打开 https://metamask.io
2. 安装浏览器扩展
3. 创建钱包，**保存好助记词**

### 1.2 切换到 Sepolia 测试网
1. 点击 MetaMask 顶部的网络下拉
2. 选择 "Sepolia test network"
3. 如果没有，点击 "Show test networks" 开启

### 1.3 获取测试币
访问以下任一水龙头，输入你的钱包地址：
- https://sepoliafaucet.com
- https://www.alchemy.com/faucets/ethereum-sepolia
- https://sepolia-faucet.pk910.de

等待几分钟，确保账户有 0.1+ ETH

### 1.4 获取签名者私钥（重要！）
1. 在 MetaMask 中创建一个**新账户**专门用于签名
2. 点击账户旁边的三个点 → "账户详情" → "显示私钥"
3. 输入密码，复制私钥（以 0x 开头的 64 位十六进制）
4. **⚠️ 这个私钥只用于测试，不要放入主网资金！**

---

## 2. 在 Remix 部署合约

### 2.1 打开 Remix
浏览器访问：https://remix.ethereum.org

### 2.2 创建合约文件

**步骤：**
1. 左侧 File Explorer → 点击 📄 图标创建新文件
2. 文件名：`SparkKnowledgeNFT.sol`
3. 复制 `contracts/SparkKnowledgeNFT.sol` 的完整内容粘贴进去

**同样创建：**
- `UtilityToken.sol`（从 five_smart_contracts_B.sol 中提取前 96 行）

### 2.3 编译合约

1. 左侧点击 "Solidity Compiler" 图标 (第三个)
2. Compiler 版本选择：`0.8.19`
3. 勾选 "Auto compile"
4. 点击 "Compile SparkKnowledgeNFT.sol"
5. 看到绿色 ✓ 表示编译成功

### 2.4 连接 MetaMask

1. 左侧点击 "Deploy & Run Transactions" 图标 (第四个)
2. **ENVIRONMENT** 下拉选择：`Injected Provider - MetaMask`
3. MetaMask 弹窗 → 点击 "连接"
4. 确认顶部显示你的钱包地址

### 2.5 部署 UtilityToken（第一步）

```
CONTRACT 选择: UtilityToken
参数: 无
```

1. 在 CONTRACT 下拉选择 `UtilityToken`
2. 点击橙色 **Deploy** 按钮
3. MetaMask 弹窗确认交易
4. 等待交易完成

**📝 记录地址：**
在 "Deployed Contracts" 区域展开 UtilityToken，复制地址：
```
UTIL_ADDR = 0x________________________（你的地址）
```

### 2.6 部署 SparkKnowledgeNFT（第二步）

```
CONTRACT 选择: SparkKnowledgeNFT
```

**填写构造参数（从上到下）：**

| 参数 | 填写内容 | 说明 |
|------|---------|------|
| `_utilityToken` | `0x...` | 上一步的 UTIL_ADDR |
| `_platform` | `0x...` | 你的钱包地址（收平台费） |
| `_dao` | `0x0000000000000000000000000000000000000000` | 暂不启用 DAO |
| `_trustedSigner` | `0x...` | 签名账户地址（1.4步创建的） |
| `_chainId` | `11155111` | Sepolia 链 ID |

**操作：**
1. 在每个参数框中依次填入对应值
2. 点击橙色 **Deploy** 按钮
3. MetaMask 确认交易
4. 等待部署完成

**📝 记录地址：**
```
NFT_ADDR = 0x________________________（合约地址）
```

### 2.7 给自己铸造一些测试代币

1. 在 Deployed Contracts 展开 `UtilityToken`
2. 找到 `mint` 函数
3. 填写参数：
   - `to`: 你的钱包地址
   - `value`: `1000000000000000000000` (1000 个代币)
4. 点击 **transact**
5. 确认交易

---

## 3. 配置后端环境变量

### 3.1 创建 .env 文件

在项目根目录创建文件：`rag-platform-mvp/backend/.env`

```bash
# ============ Web3 NFT 配置 ============

# 签名者私钥（1.4步获取的，以0x开头）
NFT_SIGNER_PRIVATE_KEY=0x你的私钥在这里

# Sepolia RPC URL（可用 Alchemy 免费创建）
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/你的API_KEY

# 部署的 SparkKnowledgeNFT 合约地址
SPARK_NFT_CONTRACT=0x你部署的NFT合约地址

# ============ 其他配置 ============
OLLAMA_URL=http://localhost:11434
```

### 3.2 获取 Alchemy RPC URL

1. 访问 https://www.alchemy.com
2. 注册账号
3. 创建新 App，选择 "Ethereum" + "Sepolia"
4. 复制 API Key 填入上面

### 3.3 安装 Python 依赖

```bash
cd rag-platform-mvp/backend
pip install web3 eth-account
```

### 3.4 重启后端

```bash
# 停止旧进程
pkill -f "uvicorn main:app"

# 启动
cd rag-platform-mvp/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 4. 测试完整流程

### 4.1 测试签名 API

```bash
# 获取登录 token
TOKEN="你的JWT_TOKEN"

# 测试配置
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/web3/config
```

应该返回：
```json
{
  "success": true,
  "data": {
    "signer_configured": true,
    "signer_address": "0x...",
    "contract_configured": true,
    "contract_address": "0x..."
  }
}
```

### 4.2 完整铸造流程

1. **用户对话获得光源值 ≥70**
2. **前端请求签名：**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "你的对话ID",
    "wallet_address": "用户的钱包地址",
    "price": 1000000000000000000
  }' \
  http://localhost:8000/v1/web3/mint-signature
```

3. **用户在 Remix 调用合约铸造：**
   - 展开 SparkKnowledgeNFT
   - 找到 `mintSparkNFT` 函数
   - 填入返回的 mint_data 和 signature
   - 点击 transact

4. **确认铸造成功：**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token_id": 0, "tx_hash": "0x..."}' \
  http://localhost:8000/v1/web3/confirm-mint/你的对话ID
```

---

## 📋 地址汇总表

部署完成后填写此表：

| 名称 | 地址 | 用途 |
|------|------|------|
| UtilityToken | `0x________________` | 平台代币 |
| SparkKnowledgeNFT | `0x________________` | NFT 合约 |
| Platform | `0x________________` | 平台收款地址 |
| TrustedSigner | `0x________________` | 后端签名地址 |

---

## ❓ 常见问题

### Q: 交易失败 "gas too low"
增加 Gas Limit，Remix 默认可能不够

### Q: "invalid signature"
检查后端 .env 中的私钥是否正确，是否与合约中 _trustedSigner 地址对应

### Q: "spark value too low"
只有光源值 ≥70 的对话才能铸造 NFT

### Q: 合约验证失败
确保 Remix 编译器版本与代码中 `pragma solidity ^0.8.19;` 一致

---

## 🔒 安全提醒

1. **私钥安全**：测试私钥不要放入任何主网资金
2. **主网部署前**：进行完整安全审计
3. **备份**：保存所有合约地址和私钥

