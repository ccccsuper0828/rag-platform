# RAG Knowledge NFT 智能合约部署指南

## 📋 概述

本指南介绍如何将 RAG Knowledge NFT 合约部署到测试网。

## 🔧 前置要求

1. **Node.js 18+**
2. **测试网 ETH**（用于支付 Gas）
3. **Infura/Alchemy API Key**（可选，用于 RPC）

## 📦 安装依赖

```bash
cd contracts
npm install
```

## 🔑 配置环境变量

创建 `.env` 文件：

```bash
# 部署者私钥（从 MetaMask 导出，不要使用主网资金的账户！）
PRIVATE_KEY=0x...

# RPC URL（选择一个测试网）
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
POLYGON_AMOY_RPC_URL=https://rpc-amoy.polygon.technology
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org

# Etherscan API Key（用于验证合约）
ETHERSCAN_API_KEY=YOUR_KEY
```

## 💧 获取测试网 ETH

### Sepolia
- https://sepoliafaucet.com
- https://www.alchemy.com/faucets/ethereum-sepolia

### Polygon Amoy
- https://faucet.polygon.technology

### Base Sepolia
- https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet

## 🚀 部署流程

### 1. 编译合约

```bash
npm run compile
```

### 2. 本地测试

```bash
# 运行测试
npm run test

# 启动本地节点
npm run node

# 在另一个终端部署到本地
npm run deploy:local
```

### 3. 部署到测试网

```bash
# 部署到 Sepolia
npm run deploy:sepolia

# 部署到 Polygon Amoy
npm run deploy:polygon

# 部署到 Base Sepolia
npm run deploy:base
```

### 4. 验证合约

```bash
# 自动验证（部署脚本会尝试）
# 或手动验证
npx hardhat verify --network sepolia CONTRACT_ADDRESS
```

## 📝 部署后配置

部署成功后，将合约地址添加到后端 `.env`：

```bash
# Web3 配置
WEB3_ENABLED=true
WEB3_NETWORK=sepolia
WEB3_CHAIN_ID=11155111
RAG_NFT_CONTRACT=0x...部署的合约地址
```

## 📁 部署产物

部署后会生成以下文件：

```
contracts/deployments/
├── sepolia.json          # 部署信息
└── frontend-config.json  # 前端配置（含 ABI）
```

将 `frontend-config.json` 复制到前端项目。

## 🔍 验证部署

### 1. 查看合约

- Sepolia: https://sepolia.etherscan.io/address/YOUR_CONTRACT
- Polygon Amoy: https://amoy.polygonscan.com/address/YOUR_CONTRACT
- Base Sepolia: https://sepolia.basescan.org/address/YOUR_CONTRACT

### 2. 测试铸造

```javascript
// 使用 ethers.js 测试
const contract = new ethers.Contract(address, abi, signer)
const tx = await contract.mintKnowledgeNFT(
  "Test question",
  ethers.keccak256(ethers.toUtf8Bytes("Test answer")),
  "QmTestCID",
  { value: ethers.parseEther("0.001") }
)
await tx.wait()
console.log("Minted!")
```

## 🛠️ 常见问题

### Q: Gas 不足
```
确保账户有足够的测试网 ETH
```

### Q: 部署失败 "nonce too low"
```bash
# 重置 MetaMask 账户 nonce
# 设置 -> 高级 -> 清除活动和 Nonce 数据
```

### Q: 验证失败
```bash
# 手动验证
npx hardhat verify --network sepolia --constructor-args arguments.js CONTRACT_ADDRESS
```

## 📚 相关资源

- [Hardhat 文档](https://hardhat.org/docs)
- [OpenZeppelin 文档](https://docs.openzeppelin.com)
- [Etherscan 验证](https://docs.etherscan.io/tutorials/verifying-contracts-programmatically)

