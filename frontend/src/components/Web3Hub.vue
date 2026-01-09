<template>
  <div class="web3-hub">
    <!-- Tab 导航 -->
    <div class="web3-tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>

    <!-- 推荐保险面板 -->
    <div v-if="activeTab === 'nft'" class="tab-content nft-panel">
      <div class="panel-header">
        <h2>🏆 推荐保险记录</h2>
        <p class="panel-desc">您的保险推荐记录将永久保存到区块链，成为可信赖的推荐凭证</p>
      </div>

      <!-- 钱包连接 -->
      <div class="wallet-section">
        <div v-if="!walletConnected" class="wallet-connect">
          <button class="connect-btn" @click="connectWallet">
            🔗 连接钱包
          </button>
          <p class="wallet-hint">支持 MetaMask、WalletConnect 等主流钱包</p>
        </div>
        <div v-else class="wallet-info">
          <span class="wallet-address">{{ shortenAddress(walletAddress) }}</span>
          <span class="network-badge">{{ networkName }}</span>
          <button class="disconnect-btn" @click="disconnectWallet">断开</button>
        </div>
      </div>

      <!-- 推荐统计 -->
      <div class="nft-stats">
        <div class="stat-card">
          <span class="stat-value">{{ nftStats.minted }}</span>
          <span class="stat-label">已推荐</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ nftStats.totalValue }}</span>
          <span class="stat-label">总价值 (ETH)</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ nftStats.earnings }}</span>
          <span class="stat-label">推荐收益</span>
        </div>
      </div>

      <!-- NFT 列表 -->
      <div class="nft-grid">
        <div v-for="nft in nftList" :key="nft.tokenId" class="nft-card">
          <div class="nft-preview">
            <div class="nft-icon">{{ nft.icon || '📄' }}</div>
            <span class="nft-token-id">#{{ nft.tokenId }}</span>
          </div>
          <div class="nft-info">
            <h4 class="nft-title">{{ nft.title }}</h4>
            <p class="nft-question">{{ truncate(nft.question, 50) }}</p>
          </div>
          <div class="nft-meta">
            <span class="nft-date">{{ formatDate(nft.mintedAt) }}</span>
            <a :href="getExplorerUrl(nft.txHash || nft.tokenId)" target="_blank" class="nft-link">
              查看交易 ↗
            </a>
          </div>
        </div>
        
        <div v-if="nftList.length === 0" class="empty-state">
          <span class="empty-icon">🏆</span>
          <p>您还没有推荐任何保险</p>
          <p class="empty-hint">在保险合同解析中获得满意答案后，可以铸造为推荐保险记录</p>
        </div>
      </div>
    </div>

    <!-- 保险治理面板 -->
    <div v-if="activeTab === 'dao'" class="tab-content dao-panel">
      <div class="panel-header">
        <h2>🏛️ 保险治理</h2>
        <p class="panel-desc">参与保险产品推荐治理，投票决定优质保险推荐标准</p>
      </div>

      <!-- 治理统计 -->
      <div class="dao-stats">
        <div class="stat-card">
          <span class="stat-value">{{ daoStats.votingPower }}</span>
          <span class="stat-label">投票权</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ daoStats.activeProposals }}</span>
          <span class="stat-label">活跃提案</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ daoStats.participated }}</span>
          <span class="stat-label">已参与投票</span>
        </div>
      </div>

      <!-- 提案列表 -->
      <div class="proposals-list">
        <h3>📋 活跃提案</h3>
        <div v-for="proposal in proposals" :key="proposal.id" class="proposal-card">
          <div class="proposal-header">
            <span class="proposal-status" :class="proposal.status">
              {{ proposal.status === 'active' ? '🟢 投票中' : '⏳ 待执行' }}
            </span>
            <span class="proposal-id">#{{ proposal.id }}</span>
          </div>
          <h4 class="proposal-title">{{ proposal.title }}</h4>
          <p class="proposal-desc">{{ truncate(proposal.description, 100) }}</p>
          <div class="proposal-votes">
            <div class="vote-bar">
              <div class="vote-for" :style="{ width: getVotePercent(proposal, 'for') + '%' }"></div>
            </div>
            <div class="vote-labels">
              <span class="vote-for-label">赞成 {{ proposal.votesFor }}</span>
              <span class="vote-against-label">反对 {{ proposal.votesAgainst }}</span>
            </div>
          </div>
          <div class="proposal-actions">
            <button class="vote-btn for" @click="vote(proposal.id, 'for')">👍 赞成</button>
            <button class="vote-btn against" @click="vote(proposal.id, 'against')">👎 反对</button>
          </div>
        </div>

        <div v-if="proposals.length === 0" class="empty-state">
          <span class="empty-icon">📭</span>
          <p>暂无活跃提案</p>
        </div>
      </div>
    </div>

    <!-- 保险任务面板 -->
    <div v-if="activeTab === 'tasks'" class="tab-content tasks-panel">
      <div class="panel-header">
        <h2>📋 保险任务</h2>
        <p class="panel-desc">发布保险咨询任务、领取任务、赚取推荐奖励</p>
      </div>

      <!-- 任务统计 -->
      <div class="task-stats">
        <div class="stat-card">
          <span class="stat-value">{{ taskStats.available }}</span>
          <span class="stat-label">可领取任务</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ taskStats.inProgress }}</span>
          <span class="stat-label">进行中</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ taskStats.completed }}</span>
          <span class="stat-label">已完成</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ taskStats.totalRewards }} ETH</span>
          <span class="stat-label">累计奖励</span>
        </div>
      </div>

      <!-- 任务筛选 -->
      <div class="task-filters">
        <button 
          v-for="filter in taskFilters" 
          :key="filter.value"
          class="filter-btn"
          :class="{ active: taskFilter === filter.value }"
          @click="taskFilter = filter.value"
        >
          {{ filter.label }}
        </button>
      </div>

      <!-- 任务列表 -->
      <div class="tasks-grid">
        <div v-for="task in filteredTasks" :key="task.id" class="task-card">
          <div class="task-header">
            <span class="task-category">{{ task.category }}</span>
            <span class="task-reward">{{ task.reward }} ETH</span>
          </div>
          <h4 class="task-title">{{ task.title }}</h4>
          <p class="task-desc">{{ truncate(task.description, 80) }}</p>
          <div class="task-skills">
            <span v-for="skill in task.skills.slice(0, 3)" :key="skill" class="skill-tag">
              {{ skill }}
            </span>
          </div>
          <div class="task-footer">
            <span class="task-deadline">⏰ {{ formatDeadline(task.deadline) }}</span>
            <button 
              class="claim-btn" 
              :class="task.status"
              @click="claimTask(task.id)"
              :disabled="task.status !== 'OPEN'"
            >
              {{ getTaskButtonText(task.status) }}
            </button>
          </div>
        </div>

        <div v-if="filteredTasks.length === 0" class="empty-state">
          <span class="empty-icon">📝</span>
          <p>暂无任务</p>
        </div>
      </div>
    </div>

    <!-- Web3 状态提示 -->
    <div v-if="!web3Available" class="web3-notice">
      <div class="notice-content">
        <span class="notice-icon">ℹ️</span>
        <div class="notice-text">
          <p><strong>Web3 功能预览模式</strong></p>
          <p>完整功能需要部署智能合约并配置 Web3 环境</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// Props
const props = defineProps({
  userAddress: String,
  isLoggedIn: Boolean
})

// Emits
const emit = defineEmits(['mint-nft', 'connect-wallet'])

// 状态
const activeTab = ref('nft')
const walletConnected = ref(false)
const walletAddress = ref('')
const networkName = ref('Sepolia')
const web3Available = ref(false)
const taskFilter = ref('all')

// Tab 配置
const tabs = [
  { id: 'nft', icon: '🏆', label: '推荐保险' },
  { id: 'dao', icon: '🏛️', label: '保险治理' },
  { id: 'tasks', icon: '📋', label: '保险任务' }
]

// 任务筛选器
const taskFilters = [
  { value: 'all', label: '全部' },
  { value: 'OPEN', label: '可领取' },
  { value: 'mine', label: '我的任务' }
]

// 模拟数据
const nftStats = ref({
  minted: 0,
  totalValue: '0.00',
  earnings: '0.00'
})

const daoStats = ref({
  votingPower: 0,
  activeProposals: 2,
  participated: 0
})

const taskStats = ref({
  available: 4,
  inProgress: 0,
  completed: 0,
  totalRewards: '0.00'
})

const nftList = ref([])

// 加载铸造的 NFT（从 localStorage 和后端）
async function loadMintedNFTs() {
  // 从 localStorage 加载
  try {
    const stored = localStorage.getItem('mintedNFTs')
    if (stored) {
      const parsed = JSON.parse(stored)
      nftList.value = parsed.map((nft, index) => ({
        tokenId: nft.tokenId || index + 1,
        title: `推荐保险 #${nft.tokenId || index + 1}`,
        question: nft.question || '推荐的保险产品',
        icon: '🏆',
        mintedAt: nft.timestamp,
        txHash: nft.txHash,
        ipfsCID: nft.ipfsCID
      }))
      nftStats.value.minted = nftList.value.length
    }
  } catch (e) {
    console.log('Failed to load NFTs from localStorage:', e)
  }
  
  // 尝试从后端加载
  if (walletConnected.value && walletAddress.value) {
    try {
      const response = await fetch(`/v1/web3/nfts/${walletAddress.value}`)
      if (response.ok) {
        const data = await response.json()
        if (data.nfts && data.nfts.length > 0) {
          nftList.value = data.nfts.map(nft => ({
            tokenId: nft.token_id,
            title: `推荐保险 #${nft.token_id}`,
            question: nft.question,
            icon: '🏆',
            mintedAt: nft.created_at,
            txHash: nft.tx_hash,
            ipfsCID: nft.ipfs_cid
          }))
          nftStats.value.minted = nftList.value.length
        }
      }
    } catch (e) {
      console.log('Failed to load NFTs from backend:', e)
    }
  }
}

const proposals = ref([
  {
    id: 1,
    title: '增加保险推荐佣金分成比例',
    description: '提议将推荐人佣金从 5% 提高到 7.5%，激励更多高质量保险推荐',
    status: 'active',
    votesFor: 1254,
    votesAgainst: 342
  },
  {
    id: 2,
    title: '引入保险推荐质量评估机制',
    description: '建立去中心化的保险推荐质量评估系统，由社区投票决定推荐质量分数',
    status: 'active',
    votesFor: 892,
    votesAgainst: 156
  }
])

const tasks = ref([
  {
    id: 1,
    title: '解读AIA人寿保险条款',
    description: '需要保险专业人士解读AIA人寿保险条款的细节，包括保障范围和理赔条件',
    category: '条款解读',
    skills: ['保险', '条款分析', '理赔经验'],
    reward: 0.5,
    deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    status: 'OPEN'
  },
  {
    id: 2,
    title: '重疾险对比分析',
    description: '对比分析市场上主流重疾险产品，提供专业推荐建议',
    category: '产品对比',
    skills: ['重疾险', '产品分析', '保险顾问'],
    reward: 1.2,
    deadline: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000),
    status: 'OPEN'
  },
  {
    id: 3,
    title: '家庭保险配置方案',
    description: '为三口之家设计全面的保险配置方案',
    category: '方案设计',
    skills: ['保险规划', '家庭保障', '理财规划'],
    reward: 0.3,
    deadline: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
    status: 'OPEN'
  },
  {
    id: 4,
    title: '医疗险理赔指南',
    description: '编写医疗险理赔流程指南和常见问题解答',
    category: '理赔指南',
    skills: ['理赔经验', '医疗险'],
    reward: 0.2,
    deadline: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000),
    status: 'OPEN'
  }
])

// 计算属性
const filteredTasks = computed(() => {
  if (taskFilter.value === 'all') return tasks.value
  if (taskFilter.value === 'mine') return tasks.value.filter(t => t.claimer === walletAddress.value)
  return tasks.value.filter(t => t.status === taskFilter.value)
})

// 方法
async function connectWallet() {
  if (typeof window.ethereum !== 'undefined') {
    try {
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' })
      if (accounts.length > 0) {
        walletAddress.value = accounts[0]
        walletConnected.value = true
        const chainId = await window.ethereum.request({ method: 'eth_chainId' })
        networkName.value = getNetworkName(parseInt(chainId, 16))
      }
    } catch (e) {
      console.error('Wallet connection failed:', e)
    }
  } else {
    alert('请安装 MetaMask 钱包')
  }
}

function disconnectWallet() {
  walletConnected.value = false
  walletAddress.value = ''
}

function getNetworkName(chainId) {
  const networks = {
    1: 'Ethereum',
    11155111: 'Sepolia',
    80002: 'Polygon Amoy',
    84532: 'Base Sepolia'
  }
  return networks[chainId] || `Chain ${chainId}`
}

function shortenAddress(address) {
  if (!address) return ''
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

function truncate(text, length) {
  if (!text) return ''
  return text.length > length ? text.slice(0, length) + '...' : text
}

function formatDate(date) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

function formatDeadline(date) {
  if (!date) return ''
  const days = Math.ceil((new Date(date) - new Date()) / (1000 * 60 * 60 * 24))
  return days > 0 ? `${days} 天后截止` : '已截止'
}

function getExplorerUrl(tokenIdOrTxHash) {
  // 如果看起来像交易哈希（以0x开头且长度>42），显示交易页面
  if (tokenIdOrTxHash && typeof tokenIdOrTxHash === 'string' && tokenIdOrTxHash.startsWith('0x') && tokenIdOrTxHash.length > 42) {
    return `https://sepolia.etherscan.io/tx/${tokenIdOrTxHash}`
  }
  // 否则显示 token 页面
  return `https://sepolia.etherscan.io/token/0x921691b0478A9d08e1dbb152e2D6991729a6402A?a=${tokenIdOrTxHash}`
}

function getVotePercent(proposal, type) {
  const total = proposal.votesFor + proposal.votesAgainst
  if (total === 0) return 50
  return type === 'for' 
    ? (proposal.votesFor / total * 100) 
    : (proposal.votesAgainst / total * 100)
}

function vote(proposalId, choice) {
  if (!walletConnected.value) {
    alert('请先连接钱包')
    return
  }
  console.log(`Voting ${choice} on proposal ${proposalId}`)
  // TODO: 实际投票逻辑
}

function claimTask(taskId) {
  if (!walletConnected.value) {
    alert('请先连接钱包')
    return
  }
  console.log(`Claiming task ${taskId}`)
  // TODO: 实际领取逻辑
}

function getTaskButtonText(status) {
  const texts = {
    'OPEN': '领取任务',
    'CLAIMED': '进行中',
    'SUBMITTED': '待审核',
    'COMPLETED': '已完成'
  }
  return texts[status] || status
}

// 初始化
onMounted(async () => {
  // 检查 Web3 状态
  try {
    const response = await fetch('/v1/web3/status')
    if (response.ok) {
      const data = await response.json()
      web3Available.value = data.enabled
    }
  } catch (e) {
    console.log('Web3 not available')
  }
  
  // 检查钱包连接状态
  if (typeof window.ethereum !== 'undefined' && window.ethereum.selectedAddress) {
    walletAddress.value = window.ethereum.selectedAddress
    walletConnected.value = true
  }
  
  // 加载铸造的 NFT
  await loadMintedNFTs()
})
</script>

<style scoped>
.web3-hub {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* Tab 导航 */
.web3-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid var(--border-color, #e5e7eb);
  padding-bottom: 0.5rem;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-radius: 0.5rem 0.5rem 0 0;
  cursor: pointer;
  font-size: 1rem;
  color: var(--text-secondary, #6b7280);
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--hover-bg, #f3f4f6);
  color: var(--text-primary, #111827);
}

.tab-btn.active {
  background: var(--primary-color, #6366f1);
  color: white;
}

.tab-icon {
  font-size: 1.25rem;
}

/* 面板头部 */
.panel-header {
  margin-bottom: 2rem;
}

.panel-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.panel-desc {
  color: var(--text-secondary, #6b7280);
}

/* 钱包连接 */
.wallet-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--card-bg, #f9fafb);
  border-radius: 1rem;
}

.wallet-connect {
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

.connect-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.wallet-hint {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: var(--text-secondary, #6b7280);
}

.wallet-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.wallet-address {
  font-family: monospace;
  padding: 0.5rem 1rem;
  background: var(--bg-secondary, #e5e7eb);
  border-radius: 0.5rem;
}

.network-badge {
  padding: 0.25rem 0.75rem;
  background: #10b981;
  color: white;
  border-radius: 1rem;
  font-size: 0.75rem;
}

.disconnect-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 0.5rem;
  cursor: pointer;
}

/* 统计卡片 */
.nft-stats, .dao-stats, .task-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  padding: 1.5rem;
  background: var(--card-bg, white);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 1rem;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-color, #6366f1);
}

.stat-label {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-secondary, #6b7280);
}

/* NFT 网格 */
.nft-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.nft-card {
  background: var(--card-bg, white);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 1rem;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.nft-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.nft-preview {
  position: relative;
  padding: 2rem;
  background: linear-gradient(135deg, #f0f1ff, #e8e9ff);
  text-align: center;
}

.nft-icon {
  font-size: 3rem;
}

.nft-token-id {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.nft-info {
  padding: 1rem;
}

.nft-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.nft-question {
  font-size: 0.875rem;
  color: var(--text-secondary, #6b7280);
}

.nft-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border-color, #e5e7eb);
  font-size: 0.75rem;
}

.nft-link {
  color: var(--primary-color, #6366f1);
  text-decoration: none;
}

/* 提案列表 */
.proposals-list h3 {
  margin-bottom: 1rem;
}

.proposal-card {
  padding: 1.5rem;
  background: var(--card-bg, white);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 1rem;
  margin-bottom: 1rem;
}

.proposal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.proposal-status {
  font-size: 0.875rem;
}

.proposal-id {
  color: var(--text-secondary, #6b7280);
  font-size: 0.875rem;
}

.proposal-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.proposal-desc {
  color: var(--text-secondary, #6b7280);
  margin-bottom: 1rem;
}

.proposal-votes {
  margin-bottom: 1rem;
}

.vote-bar {
  height: 8px;
  background: #fee2e2;
  border-radius: 4px;
  overflow: hidden;
}

.vote-for {
  height: 100%;
  background: #10b981;
  border-radius: 4px;
}

.vote-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
}

.vote-for-label { color: #10b981; }
.vote-against-label { color: #ef4444; }

.proposal-actions {
  display: flex;
  gap: 0.5rem;
}

.vote-btn {
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: opacity 0.2s;
}

.vote-btn.for {
  background: #d1fae5;
  color: #059669;
}

.vote-btn.against {
  background: #fee2e2;
  color: #dc2626;
}

.vote-btn:hover {
  opacity: 0.8;
}

/* 任务筛选 */
.task-filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  background: var(--bg-secondary, #f3f4f6);
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn.active {
  background: var(--primary-color, #6366f1);
  color: white;
}

/* 任务网格 */
.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.task-card {
  padding: 1.5rem;
  background: var(--card-bg, white);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 1rem;
}

.task-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.task-category {
  padding: 0.25rem 0.75rem;
  background: var(--bg-secondary, #f3f4f6);
  border-radius: 1rem;
  font-size: 0.75rem;
}

.task-reward {
  font-weight: 600;
  color: #10b981;
}

.task-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.task-desc {
  font-size: 0.875rem;
  color: var(--text-secondary, #6b7280);
  margin-bottom: 1rem;
}

.task-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.skill-tag {
  padding: 0.25rem 0.5rem;
  background: #e0e7ff;
  color: #4f46e5;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-deadline {
  font-size: 0.75rem;
  color: var(--text-secondary, #6b7280);
}

.claim-btn {
  padding: 0.5rem 1rem;
  background: var(--primary-color, #6366f1);
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
}

.claim-btn:disabled {
  background: var(--bg-secondary, #e5e7eb);
  color: var(--text-secondary, #6b7280);
  cursor: not-allowed;
}

/* 空状态 */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary, #6b7280);
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.empty-hint {
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

/* Web3 提示 */
.web3-notice {
  margin-top: 2rem;
  padding: 1rem;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 0.75rem;
}

.notice-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.notice-icon {
  font-size: 1.5rem;
}

.notice-text p {
  margin: 0;
}

.notice-text p:first-child {
  font-weight: 600;
}

/* 深色模式 */
:root.dark .web3-hub,
.dark-mode .web3-hub {
  --card-bg: #1f2937;
  --bg-secondary: #374151;
  --border-color: #4b5563;
  --text-primary: #f9fafb;
  --text-secondary: #9ca3af;
}
</style>

