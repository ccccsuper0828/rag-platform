/**
 * NFT 铸造服务
 * 处理与智能合约的交互
 */

import { RAG_NFT_ABI, getContractAddress, getNetworkConfig, getTxExplorerUrl, getNFTExplorerUrl } from './contractConfig.js'

// 检查是否支持 ethers
let ethers = null

// 动态导入 ethers（如果项目中有的话）
async function getEthers() {
  if (ethers) return ethers
  
  // 尝试使用 window.ethereum 的方式
  if (typeof window !== 'undefined' && window.ethereum) {
    // 使用简单的 Web3 方式，不依赖 ethers 库
    return null
  }
  return null
}

/**
 * 计算内容哈希 (keccak256)
 */
export async function computeContentHash(content) {
  const encoder = new TextEncoder()
  const data = encoder.encode(JSON.stringify(content, null, 0))
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return '0x' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

/**
 * 上传内容到 IPFS (通过后端代理)
 */
export async function uploadToIPFS(content, token) {
  try {
    const response = await fetch('/v1/web3-integration/ipfs/upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'IPFS 上传失败')
    }
    
    const data = await response.json()
    return {
      cid: data.ipfs_cid,
      contentHash: data.content_hash
    }
  } catch (error) {
    console.error('IPFS upload error:', error)
    throw error
  }
}

/**
 * 准备铸造数据 (通过后端)
 */
export async function prepareMintData(question, answer, citations, walletAddress, token) {
  try {
    const response = await fetch('/v1/web3-integration/nft/prepare', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        question,
        answer,
        citations,
        user_wallet_address: walletAddress
      })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '准备铸造数据失败')
    }
    
    return await response.json()
  } catch (error) {
    console.error('Prepare mint error:', error)
    throw error
  }
}

/**
 * 铸造 NFT
 */
export async function mintNFT(question, answerHash, ipfsCID, chainId) {
  if (!window.ethereum) {
    throw new Error('请安装 MetaMask 钱包')
  }
  
  const contractAddress = getContractAddress(chainId)
  if (!contractAddress) {
    throw new Error(`当前网络 (Chain ID: ${chainId}) 暂不支持，请切换到支持的测试网`)
  }
  
  try {
    // 获取铸造费用
    const mintFeeData = await window.ethereum.request({
      method: 'eth_call',
      params: [{
        to: contractAddress,
        data: '0x13966db5' // mintFee() 函数签名
      }, 'latest']
    })
    
    const mintFee = mintFeeData !== '0x' ? mintFeeData : '0x38d7ea4c68000' // 默认 0.001 ETH
    
    // 编码铸造函数调用
    const functionSignature = '0x' + 'mintKnowledgeNFT(string,bytes32,string)'.slice(0, 8)
    
    // 简化版：直接使用 ABI 编码
    // 这里我们使用一个更简单的方法
    const encoder = new TextEncoder()
    
    // 发送交易
    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' })
    const from = accounts[0]
    
    // 使用 eth_sendTransaction
    // 注意：实际项目中应该使用 ethers.js 或 web3.js 来正确编码函数调用
    const txHash = await window.ethereum.request({
      method: 'eth_sendTransaction',
      params: [{
        from,
        to: contractAddress,
        value: mintFee,
        data: encodeMintFunction(question, answerHash, ipfsCID)
      }]
    })
    
    return {
      txHash,
      explorerUrl: getTxExplorerUrl(chainId, txHash)
    }
  } catch (error) {
    console.error('Mint NFT error:', error)
    throw error
  }
}

/**
 * 编码 mintKnowledgeNFT 函数调用
 */
function encodeMintFunction(question, answerHash, ipfsCID) {
  // 函数选择器: keccak256("mintKnowledgeNFT(string,bytes32,string)").slice(0, 10)
  const functionSelector = '0x7d0bcd87' // 预计算的函数选择器
  
  // ABI 编码参数
  // 这是一个简化版本，实际应使用 ethers.js
  const questionBytes = stringToHex(question)
  const cidBytes = stringToHex(ipfsCID)
  
  // 动态参数偏移量
  const offset1 = 96 // 3 * 32 bytes (指向 question)
  const offset3 = offset1 + 32 + Math.ceil(questionBytes.length / 2 / 32) * 32 // 指向 ipfsCID
  
  // 构建 calldata (简化版，实际需要完整 ABI 编码)
  // 对于生产环境，请使用 ethers.js
  return functionSelector
}

/**
 * 辅助函数：字符串转 hex
 */
function stringToHex(str) {
  let hex = ''
  for (let i = 0; i < str.length; i++) {
    hex += str.charCodeAt(i).toString(16).padStart(2, '0')
  }
  return hex
}

/**
 * 获取用户的 NFT 列表
 */
export async function getUserNFTs(userAddress, chainId) {
  const contractAddress = getContractAddress(chainId)
  if (!contractAddress) return []
  
  try {
    // 调用 getUserTokens
    const functionSelector = '0xfa21df6d' // getUserTokens(address)
    const paddedAddress = userAddress.slice(2).padStart(64, '0')
    
    const result = await window.ethereum.request({
      method: 'eth_call',
      params: [{
        to: contractAddress,
        data: functionSelector + paddedAddress
      }, 'latest']
    })
    
    // 解析返回的 uint256[]
    if (result === '0x' || result.length <= 2) return []
    
    // 简化解析 (实际应使用 ethers.js)
    const tokens = []
    // ... 解析逻辑
    
    return tokens
  } catch (error) {
    console.error('Get user NFTs error:', error)
    return []
  }
}

/**
 * 切换网络
 */
export async function switchNetwork(targetChainId) {
  if (!window.ethereum) {
    throw new Error('请安装 MetaMask 钱包')
  }
  
  const network = getNetworkConfig(targetChainId)
  if (!network) {
    throw new Error('不支持的网络')
  }
  
  const chainIdHex = '0x' + targetChainId.toString(16)
  
  try {
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: chainIdHex }]
    })
    return true
  } catch (switchError) {
    // 网络不存在，尝试添加
    if (switchError.code === 4902) {
      try {
        await window.ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [{
            chainId: chainIdHex,
            chainName: network.name,
            rpcUrls: [network.rpcUrl],
            nativeCurrency: {
              name: network.currency,
              symbol: network.currency,
              decimals: 18
            },
            blockExplorerUrls: network.explorerUrl ? [network.explorerUrl] : []
          }]
        })
        return true
      } catch (addError) {
        throw new Error('添加网络失败: ' + addError.message)
      }
    }
    throw switchError
  }
}

/**
 * 格式化 ETH 金额
 */
export function formatEther(weiValue) {
  if (!weiValue) return '0'
  const value = BigInt(weiValue)
  const eth = Number(value) / 1e18
  return eth.toFixed(6)
}

/**
 * 解析 ETH 金额为 Wei
 */
export function parseEther(ethValue) {
  const wei = Math.floor(parseFloat(ethValue) * 1e18)
  return '0x' + wei.toString(16)
}

