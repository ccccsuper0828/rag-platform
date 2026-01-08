# Web3 功能配置指南

## 🚀 快速开始

### 1. 配置 IPFS（必需）

首先需要配置 Pinata 来存储 NFT 内容：

1. 访问 [Pinata](https://app.pinata.cloud/) 注册账号
2. 创建 API Key，获取 JWT Token
3. 在后端 `.env` 文件中添加：

```bash
IPFS_ENABLED=true
PINATA_JWT=your_jwt_token_here
```

### 2. 配置区块链网络（可选）

如果要将内容铸造为链上 NFT：

```bash
WEB3_ENABLED=true
WEB3_NETWORK=sepolia
WEB3_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
WEB3_CHAIN_ID=11155111
```

获取 RPC URL：
- [Infura](https://infura.io/) - 免费额度足够测试
- [Alchemy](https://alchemy.com/) - 免费额度更多

### 3. 部署智能合约（可选）

```bash
cd contracts
npm install
npx hardhat compile

# 设置私钥并部署
PRIVATE_KEY=0x... npx hardhat run scripts/deploy.js --network sepolia
```

部署后，将合约地址添加到 `.env`：

```bash
RAG_NFT_CONTRACT=0x你的合约地址
```

### 4. 获取测试币

- Sepolia: https://sepoliafaucet.com/
- Polygon Amoy: https://faucet.polygon.technology/

---

## 📋 完整配置示例

```bash
# ===== Web3 功能 =====
WEB3_ENABLED=true
WEB3_NETWORK=sepolia
WEB3_RPC_URL=https://sepolia.infura.io/v3/abc123
WEB3_CHAIN_ID=11155111

# ===== 合约地址 =====
RAG_NFT_CONTRACT=0x1234567890abcdef...

# ===== IPFS =====
IPFS_ENABLED=true
PINATA_JWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🎨 功能说明

### 无需合约也能使用
即使不部署合约，只需配置 IPFS，用户也可以：
- ✅ 将 RAG 答案上传到 IPFS
- ✅ 获得永久存储的内容 CID
- ✅ 通过 IPFS 网关访问内容

### 部署合约后
- ✅ 将内容铸造为 ERC-721 NFT
- ✅ 链上验证内容真实性
- ✅ 支持版税收益

---

## 🔗 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/web3/status` | GET | 获取 Web3 功能状态 |
| `/v1/web3/network` | GET | 获取网络信息 |
| `/v1/web3/nft/prepare` | POST | 准备 NFT 铸造（上传到 IPFS） |
| `/v1/web3/ipfs/upload` | POST | 直接上传到 IPFS |
| `/v1/web3/ipfs/{cid}` | GET | 从 IPFS 获取内容 |
| `/v1/web3/nft/{token_id}` | GET | 获取 NFT 元数据 |

---

## 📱 前端使用

1. 进入 AI 问答界面
2. 与 AI 对话获得回答
3. 点击回答下方的 **"🎨 铸造 NFT"** 按钮
4. 连接 MetaMask 钱包
5. 确认交易即可铸造

---

## 🔧 智能合约

合约位于 `contracts/src/RAGKnowledgeNFT.sol`，功能包括：
- ERC-721 标准 NFT
- 链上存储内容哈希
- 支持版税（5%）
- 防止重复铸造相同内容

