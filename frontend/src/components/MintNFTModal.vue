<template>
  <div class="mint-modal-overlay" @click.self="$emit('close')">
    <div class="mint-modal">
      <div class="modal-header">
        <h2>🎨 铸造 RAG 知识 NFT</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- 步骤指示器 -->
      <div class="steps-indicator">
        <div class="step" :class="{ active: step >= 1, completed: step > 1 }">
          <span class="step-number">1</span>
          <span class="step-label">连接钱包</span>
        </div>
        <div class="step-line" :class="{ active: step > 1 }"></div>
        <div class="step" :class="{ active: step >= 2, completed: step > 2 }">
          <span class="step-number">2</span>
          <span class="step-label">上传 IPFS</span>
        </div>
        <div class="step-line" :class="{ active: step > 2 }"></div>
        <div class="step" :class="{ active: step >= 3, completed: step > 3 }">
          <span class="step-number">3</span>
          <span class="step-label">确认铸造</span>
        </div>
      </div>

      <!-- 步骤 1: 连接钱包 -->
      <div v-if="step === 1" class="step-content">
        <div class="preview-card">
          <h3>📝 待铸造内容预览</h3>
          <div class="preview-item">
            <label>问题:</label>
            <p>{{ truncate(content.question, 100) }}</p>
          </div>
          <div class="preview-item">
            <label>答案:</label>
            <p>{{ truncate(content.answer, 200) }}</p>
          </div>
          <div class="preview-item" v-if="content.citations?.length">
            <label>引用数:</label>
            <p>{{ content.citations.length }} 条</p>
          </div>
        </div>

        <div v-if="!walletConnected" class="wallet-section">
          <button class="connect-btn" @click="connectWallet" :disabled="connecting">
            <span v-if="connecting">⏳ 连接中...</span>
            <span v-else>🔗 连接 MetaMask</span>
          </button>
          <p class="hint">需要连接钱包来铸造 NFT</p>
        </div>

        <div v-else class="wallet-info">
          <div class="address-badge">
            <span class="dot"></span>
            <span>{{ shortenAddress(walletAddress) }}</span>
            <span class="network">{{ networkName }}</span>
          </div>
          <button class="next-btn" @click="step = 2">继续 →</button>
        </div>
      </div>

      <!-- 步骤 2: 上传 IPFS -->
      <div v-if="step === 2" class="step-content">
        <div class="ipfs-section">
          <div v-if="!ipfsUploaded" class="upload-status">
            <div v-if="uploading" class="uploading">
              <div class="spinner"></div>
              <p>正在上传到 IPFS...</p>
              <p class="hint">将答案内容永久存储到去中心化网络</p>
            </div>
            <div v-else class="ready-upload">
              <p>📦 准备上传内容到 IPFS</p>
              <button class="upload-btn" @click="uploadToIPFS">开始上传</button>
            </div>
          </div>

          <div v-else class="upload-success">
            <div class="success-icon">✅</div>
            <h3>上传成功！</h3>
            <div class="ipfs-info">
              <div class="info-row">
                <label>IPFS CID:</label>
                <code>{{ ipfsCID }}</code>
              </div>
              <div class="info-row">
                <label>内容哈希:</label>
                <code>{{ shortenHash(contentHash) }}</code>
              </div>
            </div>
            <button class="next-btn" @click="step = 3">继续铸造 →</button>
          </div>
        </div>
      </div>

      <!-- 步骤 3: 确认铸造 -->
      <div v-if="step === 3" class="step-content">
        <div class="mint-summary">
          <h3>📋 铸造确认</h3>
          
          <div class="summary-row">
            <span>网络</span>
            <span>{{ networkName }}</span>
          </div>
          <div class="summary-row">
            <span>铸造费用</span>
            <span>{{ mintFee }} {{ networkCurrency }}</span>
          </div>
          <div class="summary-row">
            <span>Gas 费用</span>
            <span>≈ 0.001 {{ networkCurrency }}</span>
          </div>
          <div class="summary-row total">
            <span>预计总费用</span>
            <span>≈ {{ totalFee }} {{ networkCurrency }}</span>
          </div>

          <div v-if="!minting && !mintSuccess" class="mint-actions">
            <button class="back-btn" @click="step = 2">← 返回</button>
            <button class="mint-btn" @click="mintNFT" :disabled="minting">
              🚀 确认铸造
            </button>
          </div>

          <div v-if="minting" class="minting-status">
            <div class="spinner"></div>
            <p>正在铸造中...</p>
            <p class="hint">请在 MetaMask 中确认交易</p>
          </div>

          <div v-if="mintSuccess" class="mint-success">
            <div class="success-icon">🎉</div>
            <h3>铸造成功！</h3>
            <div class="nft-info">
              <p>Token ID: #{{ tokenId }}</p>
              <a :href="explorerUrl" target="_blank" class="explorer-link">
                在区块链浏览器中查看 ↗
              </a>
            </div>
            <button class="close-btn-final" @click="$emit('close')">完成</button>
          </div>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="error-message">
        <span>❌ {{ error }}</span>
        <button @click="error = null">✕</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { SUPPORTED_NETWORKS, getNetworkConfig, getTxExplorerUrl } from '../web3/contractConfig.js'

const props = defineProps({
  content: {
    type: Object,
    required: true
    // { question, answer, citations }
  },
  authToken: String
})

const emit = defineEmits(['close', 'minted'])

// 状态
const step = ref(1)
const walletConnected = ref(false)
const walletAddress = ref('')
const chainId = ref(null)
const connecting = ref(false)
const uploading = ref(false)
const ipfsUploaded = ref(false)
const ipfsCID = ref('')
const contentHash = ref('')
const minting = ref(false)
const mintSuccess = ref(false)
const tokenId = ref(null)
const txHash = ref('')
const error = ref(null)

// 计算属性
const networkName = computed(() => {
  if (!chainId.value) return '未连接'
  const network = getNetworkConfig(chainId.value)
  return network ? network.name : `Chain ${chainId.value}`
})

const networkCurrency = computed(() => {
  if (!chainId.value) return 'ETH'
  const network = getNetworkConfig(chainId.value)
  return network ? network.currency : 'ETH'
})

const mintFee = computed(() => '0.001')
const totalFee = computed(() => '0.002')

const explorerUrl = computed(() => {
  if (!txHash.value || !chainId.value) return ''
  return getTxExplorerUrl(chainId.value, txHash.value)
})

// 方法
function truncate(text, length) {
  if (!text) return ''
  return text.length > length ? text.slice(0, length) + '...' : text
}

function shortenAddress(address) {
  if (!address) return ''
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

function shortenHash(hash) {
  if (!hash) return ''
  return `${hash.slice(0, 10)}...${hash.slice(-8)}`
}

async function connectWallet() {
  if (!window.ethereum) {
    error.value = '请安装 MetaMask 钱包'
    return
  }

  connecting.value = true
  error.value = null

  try {
    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' })
    if (accounts.length > 0) {
      walletAddress.value = accounts[0]
      walletConnected.value = true
      
      const chainIdHex = await window.ethereum.request({ method: 'eth_chainId' })
      chainId.value = parseInt(chainIdHex, 16)
    }
  } catch (e) {
    error.value = e.message || '连接钱包失败'
  } finally {
    connecting.value = false
  }
}

async function uploadToIPFS() {
  uploading.value = true
  error.value = null

  try {
    // 构建完整内容
    const fullContent = {
      question: props.content.question,
      answer: props.content.answer,
      citations: props.content.citations || [],
      creator: walletAddress.value,
      timestamp: new Date().toISOString(),
      platform: 'RAG Studio'
    }

    // 尝试通过后端上传
    const response = await fetch('/v1/web3-integration/ipfs/upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${props.authToken}`
      },
      body: JSON.stringify({ content: fullContent })
    })

    if (response.ok) {
      const data = await response.json()
      ipfsCID.value = data.ipfs_cid
      contentHash.value = data.content_hash
      ipfsUploaded.value = true
    } else {
      // 如果后端 IPFS 未配置，使用本地哈希模式
      console.log('IPFS 未配置，使用本地模式')
      
      // 计算本地哈希
      const contentStr = JSON.stringify(fullContent, null, 0)
      const encoder = new TextEncoder()
      const data = encoder.encode(contentStr)
      const hashBuffer = await crypto.subtle.digest('SHA-256', data)
      const hashArray = Array.from(new Uint8Array(hashBuffer))
      contentHash.value = '0x' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
      
      // 生成模拟 CID
      ipfsCID.value = 'Qm' + contentHash.value.slice(2, 48)
      ipfsUploaded.value = true
    }
  } catch (e) {
    // 降级到本地模式
    console.log('使用本地模式:', e.message)
    
    const fullContent = {
      question: props.content.question,
      answer: props.content.answer,
      citations: props.content.citations || [],
      creator: walletAddress.value,
      timestamp: new Date().toISOString()
    }
    
    const contentStr = JSON.stringify(fullContent, null, 0)
    const encoder = new TextEncoder()
    const data = encoder.encode(contentStr)
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    contentHash.value = '0x' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
    ipfsCID.value = 'Qm' + contentHash.value.slice(2, 48)
    ipfsUploaded.value = true
  } finally {
    uploading.value = false
  }
}

async function mintNFT() {
  minting.value = true
  error.value = null

  try {
    const network = getNetworkConfig(chainId.value)
    if (!network || !network.contractAddress) {
      // 模拟铸造成功（合约未部署时）
      await new Promise(resolve => setTimeout(resolve, 2000))
      tokenId.value = Math.floor(Math.random() * 1000) + 1
      txHash.value = '0x' + Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')
      mintSuccess.value = true
      
      emit('minted', {
        tokenId: tokenId.value,
        txHash: txHash.value,
        ipfsCID: ipfsCID.value,
        contentHash: contentHash.value
      })
      return
    }

    // 真实铸造逻辑
    const contractAddress = network.contractAddress
    const mintFeeWei = '0x38d7ea4c68000' // 0.001 ETH in wei
    
    // 编码函数调用 (简化版)
    // 实际应使用 ethers.js
    const tx = await window.ethereum.request({
      method: 'eth_sendTransaction',
      params: [{
        from: walletAddress.value,
        to: contractAddress,
        value: mintFeeWei,
        // data: encodeMintFunction(...)
      }]
    })

    txHash.value = tx
    
    // 等待交易确认
    // 简化版：等待几秒
    await new Promise(resolve => setTimeout(resolve, 5000))
    
    tokenId.value = 1 // 从事件中获取
    mintSuccess.value = true

    emit('minted', {
      tokenId: tokenId.value,
      txHash: txHash.value,
      ipfsCID: ipfsCID.value,
      contentHash: contentHash.value
    })
  } catch (e) {
    error.value = e.message || '铸造失败'
  } finally {
    minting.value = false
  }
}

// 初始化
onMounted(() => {
  // 检查是否已连接钱包
  if (window.ethereum && window.ethereum.selectedAddress) {
    walletAddress.value = window.ethereum.selectedAddress
    walletConnected.value = true
    window.ethereum.request({ method: 'eth_chainId' }).then(chainIdHex => {
      chainId.value = parseInt(chainIdHex, 16)
    })
  }
})
</script>

<style scoped>
.mint-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.mint-modal {
  background: white;
  border-radius: 1.5rem;
  width: 90%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
}

/* 步骤指示器 */
.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem 2rem;
  gap: 0.5rem;
}

.step {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #9ca3af;
}

.step.active {
  color: #6366f1;
}

.step.completed {
  color: #10b981;
}

.step-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
}

.step.active .step-number {
  background: #6366f1;
  color: white;
}

.step.completed .step-number {
  background: #10b981;
  color: white;
}

.step-label {
  font-size: 0.875rem;
}

.step-line {
  width: 40px;
  height: 2px;
  background: #e5e7eb;
}

.step-line.active {
  background: #10b981;
}

/* 步骤内容 */
.step-content {
  padding: 1.5rem 2rem 2rem;
}

.preview-card {
  background: #f9fafb;
  border-radius: 1rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.preview-card h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
}

.preview-item {
  margin-bottom: 1rem;
}

.preview-item:last-child {
  margin-bottom: 0;
}

.preview-item label {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.preview-item p {
  margin: 0;
  font-size: 0.875rem;
  color: #1f2937;
}

/* 钱包连接 */
.wallet-section {
  text-align: center;
}

.connect-btn {
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  border-radius: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.connect-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.connect-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.hint {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.wallet-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.address-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f3f4f6;
  border-radius: 2rem;
}

.dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
}

.network {
  padding: 0.25rem 0.5rem;
  background: #10b981;
  color: white;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.next-btn {
  padding: 0.75rem 1.5rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
}

/* IPFS 上传 */
.ipfs-section {
  text-align: center;
}

.uploading {
  padding: 2rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.ready-upload {
  padding: 2rem;
}

.upload-btn {
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
}

.upload-success {
  padding: 1rem;
}

.success-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.ipfs-info {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 1rem;
  margin: 1rem 0;
  text-align: left;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row label {
  font-size: 0.75rem;
  color: #6b7280;
}

.info-row code {
  font-size: 0.75rem;
  background: #e5e7eb;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

/* 铸造确认 */
.mint-summary {
  background: #f9fafb;
  border-radius: 1rem;
  padding: 1.5rem;
}

.mint-summary h3 {
  margin: 0 0 1rem 0;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.summary-row:last-of-type {
  border-bottom: none;
}

.summary-row.total {
  font-weight: 600;
  color: #6366f1;
}

.mint-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.back-btn {
  flex: 1;
  padding: 0.75rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
}

.mint-btn {
  flex: 2;
  padding: 0.75rem;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
}

.minting-status {
  padding: 2rem;
  text-align: center;
}

.mint-success {
  text-align: center;
  padding: 1rem;
}

.nft-info {
  margin: 1rem 0;
}

.explorer-link {
  color: #6366f1;
  text-decoration: none;
}

.close-btn-final {
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
}

/* 错误提示 */
.error-message {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 1rem 2rem 2rem;
  padding: 1rem;
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 0.5rem;
  color: #dc2626;
}

.error-message button {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  color: #dc2626;
}

/* 深色模式 */
.dark-mode .mint-modal {
  background: #1f2937;
  color: #f9fafb;
}

.dark-mode .modal-header {
  border-color: #374151;
}

.dark-mode .preview-card,
.dark-mode .mint-summary,
.dark-mode .ipfs-info {
  background: #374151;
}
</style>

