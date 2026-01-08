/**
 * Web3 模块导出
 * 
 * 独立的 Web3 功能模块
 * 不影响现有 RAG 功能
 */

export { useWeb3 } from './useWeb3'
export { useNFTMint } from './useNFTMint'

// 检查 Web3 是否可用
export function isWeb3Available() {
  return typeof window !== 'undefined' && typeof window.ethereum !== 'undefined'
}

// 获取 Web3 状态
export async function getWeb3Status() {
  try {
    const response = await fetch('/v1/web3/status')
    if (response.ok) {
      return await response.json()
    }
    return { enabled: false }
  } catch {
    return { enabled: false }
  }
}

