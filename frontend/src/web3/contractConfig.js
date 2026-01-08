/**
 * RAG NFT 合约配置
 * 部署合约后更新此文件
 */

// 合约 ABI - 只包含需要的函数
export const RAG_NFT_ABI = [
  // 铸造函数
  {
    "inputs": [
      { "internalType": "string", "name": "question", "type": "string" },
      { "internalType": "bytes32", "name": "answerHash", "type": "bytes32" },
      { "internalType": "string", "name": "ipfsCID", "type": "string" }
    ],
    "name": "mintKnowledgeNFT",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "payable",
    "type": "function"
  },
  // 获取铸造费用
  {
    "inputs": [],
    "name": "mintFee",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  },
  // 获取用户的 NFT 列表
  {
    "inputs": [{ "internalType": "address", "name": "user", "type": "address" }],
    "name": "getUserTokens",
    "outputs": [{ "internalType": "uint256[]", "name": "", "type": "uint256[]" }],
    "stateMutability": "view",
    "type": "function"
  },
  // 获取 NFT 内容详情
  {
    "inputs": [{ "internalType": "uint256", "name": "tokenId", "type": "uint256" }],
    "name": "getContentDetails",
    "outputs": [
      { "internalType": "string", "name": "question", "type": "string" },
      { "internalType": "bytes32", "name": "answerHash", "type": "bytes32" },
      { "internalType": "string", "name": "ipfsCID", "type": "string" },
      { "internalType": "uint256", "name": "createdAt", "type": "uint256" },
      { "internalType": "address", "name": "creator", "type": "address" },
      { "internalType": "bool", "name": "verified", "type": "bool" }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  // 检查哈希是否已铸造
  {
    "inputs": [{ "internalType": "bytes32", "name": "answerHash", "type": "bytes32" }],
    "name": "isHashMinted",
    "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
    "stateMutability": "view",
    "type": "function"
  },
  // 获取总供应量
  {
    "inputs": [],
    "name": "totalSupply",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  },
  // 铸造事件
  {
    "anonymous": false,
    "inputs": [
      { "indexed": true, "internalType": "uint256", "name": "tokenId", "type": "uint256" },
      { "indexed": true, "internalType": "address", "name": "creator", "type": "address" },
      { "indexed": false, "internalType": "string", "name": "question", "type": "string" },
      { "indexed": false, "internalType": "bytes32", "name": "answerHash", "type": "bytes32" },
      { "indexed": false, "internalType": "string", "name": "ipfsCID", "type": "string" }
    ],
    "name": "KnowledgeNFTMinted",
    "type": "event"
  }
]

// 支持的网络配置
export const SUPPORTED_NETWORKS = {
  // Sepolia 测试网
  11155111: {
    name: 'Sepolia',
    contractAddress: '', // 部署后填写
    rpcUrl: 'https://sepolia.infura.io/v3/',
    explorerUrl: 'https://sepolia.etherscan.io',
    currency: 'ETH',
    faucet: 'https://sepoliafaucet.com'
  },
  // Polygon Amoy 测试网
  80002: {
    name: 'Polygon Amoy',
    contractAddress: '', // 部署后填写
    rpcUrl: 'https://rpc-amoy.polygon.technology',
    explorerUrl: 'https://amoy.polygonscan.com',
    currency: 'MATIC',
    faucet: 'https://faucet.polygon.technology'
  },
  // Base Sepolia 测试网
  84532: {
    name: 'Base Sepolia',
    contractAddress: '', // 部署后填写
    rpcUrl: 'https://sepolia.base.org',
    explorerUrl: 'https://sepolia.basescan.org',
    currency: 'ETH',
    faucet: 'https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet'
  },
  // 本地开发网络
  31337: {
    name: 'Localhost',
    contractAddress: '', // 本地部署后填写
    rpcUrl: 'http://127.0.0.1:8545',
    explorerUrl: '',
    currency: 'ETH',
    faucet: ''
  }
}

// 获取当前网络配置
export function getNetworkConfig(chainId) {
  return SUPPORTED_NETWORKS[chainId] || null
}

// 检查网络是否支持
export function isNetworkSupported(chainId) {
  return chainId in SUPPORTED_NETWORKS && SUPPORTED_NETWORKS[chainId].contractAddress !== ''
}

// 获取合约地址
export function getContractAddress(chainId) {
  const network = SUPPORTED_NETWORKS[chainId]
  return network ? network.contractAddress : null
}

// 获取区块链浏览器 NFT 链接
export function getNFTExplorerUrl(chainId, tokenId) {
  const network = SUPPORTED_NETWORKS[chainId]
  if (!network || !network.explorerUrl || !network.contractAddress) return null
  return `${network.explorerUrl}/token/${network.contractAddress}?a=${tokenId}`
}

// 获取交易链接
export function getTxExplorerUrl(chainId, txHash) {
  const network = SUPPORTED_NETWORKS[chainId]
  if (!network || !network.explorerUrl) return null
  return `${network.explorerUrl}/tx/${txHash}`
}

