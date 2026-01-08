/**
 * Web3 集成 Hook
 * 
 * 提供钱包连接和合约交互功能
 * 独立模块，不影响现有 RAG 功能
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'

// 状态
const isConnected = ref(false)
const account = ref(null)
const chainId = ref(null)
const provider = ref(null)
const signer = ref(null)
const error = ref(null)

// Web3 配置（从后端获取）
const web3Config = ref({
  enabled: false,
  contractAddress: null,
  network: null,
  chainId: null
})

// 支持的网络
const SUPPORTED_NETWORKS = {
  11155111: {
    name: 'Sepolia',
    rpcUrl: 'https://sepolia.infura.io/v3/YOUR_KEY',
    explorer: 'https://sepolia.etherscan.io'
  },
  80002: {
    name: 'Polygon Amoy',
    rpcUrl: 'https://rpc-amoy.polygon.technology',
    explorer: 'https://amoy.polygonscan.com'
  },
  84532: {
    name: 'Base Sepolia',
    rpcUrl: 'https://sepolia.base.org',
    explorer: 'https://sepolia.basescan.org'
  }
}

/**
 * 初始化 Web3 配置
 */
async function initWeb3Config() {
  try {
    const response = await fetch('/v1/web3/status')
    if (response.ok) {
      const data = await response.json()
      web3Config.value = data
    }
  } catch (e) {
    console.log('Web3 integration not available:', e.message)
  }
}

/**
 * 连接钱包
 */
async function connectWallet() {
  error.value = null
  
  if (typeof window.ethereum === 'undefined') {
    error.value = '请安装 MetaMask 钱包'
    return false
  }
  
  try {
    // 请求账户访问
    const accounts = await window.ethereum.request({
      method: 'eth_requestAccounts'
    })
    
    if (accounts.length === 0) {
      error.value = '请选择一个钱包账户'
      return false
    }
    
    account.value = accounts[0]
    chainId.value = parseInt(await window.ethereum.request({ method: 'eth_chainId' }), 16)
    isConnected.value = true
    
    // 监听账户变化
    window.ethereum.on('accountsChanged', handleAccountsChanged)
    window.ethereum.on('chainChanged', handleChainChanged)
    
    return true
  } catch (e) {
    error.value = e.message
    return false
  }
}

/**
 * 断开钱包
 */
function disconnectWallet() {
  isConnected.value = false
  account.value = null
  chainId.value = null
  
  if (window.ethereum) {
    window.ethereum.removeListener('accountsChanged', handleAccountsChanged)
    window.ethereum.removeListener('chainChanged', handleChainChanged)
  }
}

/**
 * 处理账户变化
 */
function handleAccountsChanged(accounts) {
  if (accounts.length === 0) {
    disconnectWallet()
  } else {
    account.value = accounts[0]
  }
}

/**
 * 处理网络变化
 */
function handleChainChanged(newChainId) {
  chainId.value = parseInt(newChainId, 16)
}

/**
 * 切换网络
 */
async function switchNetwork(targetChainId) {
  if (!window.ethereum) {
    error.value = '请安装 MetaMask'
    return false
  }
  
  const chainIdHex = '0x' + targetChainId.toString(16)
  
  try {
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: chainIdHex }]
    })
    return true
  } catch (switchError) {
    // 网络未添加，尝试添加
    if (switchError.code === 4902) {
      const network = SUPPORTED_NETWORKS[targetChainId]
      if (network) {
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [{
              chainId: chainIdHex,
              chainName: network.name,
              rpcUrls: [network.rpcUrl],
              blockExplorerUrls: [network.explorer]
            }]
          })
          return true
        } catch (addError) {
          error.value = addError.message
          return false
        }
      }
    }
    error.value = switchError.message
    return false
  }
}

/**
 * 获取当前网络名称
 */
const networkName = computed(() => {
  if (!chainId.value) return '未连接'
  return SUPPORTED_NETWORKS[chainId.value]?.name || `Chain ${chainId.value}`
})

/**
 * 缩短地址显示
 */
function shortenAddress(address) {
  if (!address) return ''
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

/**
 * 导出 Hook
 */
export function useWeb3() {
  onMounted(() => {
    initWeb3Config()
    
    // 检查是否已连接
    if (window.ethereum && window.ethereum.selectedAddress) {
      account.value = window.ethereum.selectedAddress
      isConnected.value = true
      window.ethereum.request({ method: 'eth_chainId' }).then(id => {
        chainId.value = parseInt(id, 16)
      })
    }
  })
  
  onUnmounted(() => {
    if (window.ethereum) {
      window.ethereum.removeListener('accountsChanged', handleAccountsChanged)
      window.ethereum.removeListener('chainChanged', handleChainChanged)
    }
  })
  
  return {
    // 状态
    isConnected,
    account,
    chainId,
    networkName,
    error,
    web3Config,
    
    // 方法
    connectWallet,
    disconnectWallet,
    switchNetwork,
    shortenAddress,
    
    // 常量
    SUPPORTED_NETWORKS
  }
}

export default useWeb3

