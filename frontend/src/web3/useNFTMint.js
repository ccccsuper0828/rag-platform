/**
 * NFT 铸造 Hook
 * 
 * 提供将 RAG 答案铸造为 NFT 的功能
 */

import { ref, computed } from 'vue'
import { useWeb3 } from './useWeb3'

// 铸造状态
const mintStatus = ref('idle') // idle, preparing, uploading, minting, success, error
const mintError = ref(null)
const mintResult = ref(null)
const txHash = ref(null)

// 合约 ABI (简化版)
const RAG_NFT_ABI = [
  {
    inputs: [
      { name: 'question', type: 'string' },
      { name: 'answerHash', type: 'bytes32' },
      { name: 'ipfsCID', type: 'string' }
    ],
    name: 'mintKnowledgeNFT',
    outputs: [{ name: 'tokenId', type: 'uint256' }],
    stateMutability: 'payable',
    type: 'function'
  }
]

/**
 * NFT 铸造 Hook
 */
export function useNFTMint() {
  const { isConnected, account, chainId } = useWeb3()
  
  /**
   * 准备铸造（上传到 IPFS）
   */
  async function prepareMint(question, answer, sources = []) {
    if (!isConnected.value || !account.value) {
      mintError.value = '请先连接钱包'
      return null
    }
    
    mintStatus.value = 'preparing'
    mintError.value = null
    
    try {
      const response = await fetch('/v1/web3/nft/prepare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          question,
          answer,
          sources,
          user_address: account.value,
          metadata: {
            minted_from: 'rag-platform',
            chain_id: chainId.value
          }
        })
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Preparation failed')
      }
      
      const result = await response.json()
      mintResult.value = result
      mintStatus.value = 'ready'
      
      return result
    } catch (e) {
      mintError.value = e.message
      mintStatus.value = 'error'
      return null
    }
  }
  
  /**
   * 执行铸造
   */
  async function executeMint(prepareResult) {
    if (!prepareResult || !prepareResult.transaction_params) {
      mintError.value = '请先准备铸造'
      return null
    }
    
    if (!window.ethereum) {
      mintError.value = '请安装 MetaMask'
      return null
    }
    
    mintStatus.value = 'minting'
    mintError.value = null
    
    try {
      const { ethers } = await import('ethers')
      
      const provider = new ethers.BrowserProvider(window.ethereum)
      const signer = await provider.getSigner()
      
      const params = prepareResult.transaction_params
      const contract = new ethers.Contract(
        params.contract_address,
        params.abi,
        signer
      )
      
      // 发送铸造交易
      const tx = await contract.mintKnowledgeNFT(
        params.params.question,
        params.params.answerHash,
        params.params.ipfsCID,
        { value: ethers.parseEther(params.value) }
      )
      
      txHash.value = tx.hash
      
      // 等待交易确认
      const receipt = await tx.wait()
      
      // 解析事件获取 tokenId
      const event = receipt.logs.find(log => {
        try {
          const parsed = contract.interface.parseLog(log)
          return parsed.name === 'KnowledgeNFTMinted'
        } catch {
          return false
        }
      })
      
      let tokenId = null
      if (event) {
        const parsed = contract.interface.parseLog(event)
        tokenId = parsed.args.tokenId.toString()
      }
      
      mintResult.value = {
        ...mintResult.value,
        tokenId,
        txHash: tx.hash,
        blockNumber: receipt.blockNumber
      }
      
      mintStatus.value = 'success'
      
      return mintResult.value
    } catch (e) {
      mintError.value = e.message
      mintStatus.value = 'error'
      return null
    }
  }
  
  /**
   * 一键铸造（准备 + 执行）
   */
  async function mintNFT(question, answer, sources = []) {
    const prepareResult = await prepareMint(question, answer, sources)
    if (!prepareResult) return null
    
    return await executeMint(prepareResult)
  }
  
  /**
   * 重置状态
   */
  function resetMint() {
    mintStatus.value = 'idle'
    mintError.value = null
    mintResult.value = null
    txHash.value = null
  }
  
  /**
   * 获取铸造进度百分比
   */
  const mintProgress = computed(() => {
    switch (mintStatus.value) {
      case 'idle': return 0
      case 'preparing': return 25
      case 'uploading': return 50
      case 'ready': return 60
      case 'minting': return 80
      case 'success': return 100
      case 'error': return 0
      default: return 0
    }
  })
  
  /**
   * 获取状态描述
   */
  const mintStatusText = computed(() => {
    switch (mintStatus.value) {
      case 'idle': return '准备就绪'
      case 'preparing': return '准备中...'
      case 'uploading': return '上传到 IPFS...'
      case 'ready': return '等待铸造'
      case 'minting': return '铸造中，请在钱包中确认...'
      case 'success': return '铸造成功！'
      case 'error': return '铸造失败'
      default: return ''
    }
  })
  
  return {
    // 状态
    mintStatus,
    mintError,
    mintResult,
    txHash,
    mintProgress,
    mintStatusText,
    
    // 方法
    prepareMint,
    executeMint,
    mintNFT,
    resetMint
  }
}

export default useNFTMint

