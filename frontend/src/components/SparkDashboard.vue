<template>
  <div class="spark-dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <h2 class="dashboard-title">
        <span class="title-icon">✨</span>
        光源中心
      </h2>
      <p class="dashboard-subtitle">追踪您的知识贡献价值</p>
    </div>

    <!-- User Profile Card -->
    <div class="profile-card" v-if="profile">
      <div class="profile-header">
        <div class="profile-avatar">
          <span class="avatar-icon">👤</span>
          <span class="reputation-badge" :class="'level-' + profile.reputation_level">
            Lv.{{ profile.reputation_level }}
          </span>
        </div>
        <div class="profile-info">
          <h3 class="profile-name">我的光源档案</h3>
          <div class="profile-stats-row">
            <div class="stat-item">
              <span class="stat-value">{{ profile.total_spark.toFixed(1) }}</span>
              <span class="stat-label">累计光源</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ profile.total_conversations }}</span>
              <span class="stat-label">对话总数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ profile.high_spark_conversations }}</span>
              <span class="stat-label">高光对话</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Progress to Next Level -->
      <div class="level-progress">
        <div class="progress-header">
          <span>声誉等级 {{ profile.reputation_level }} → {{ profile.reputation_level + 1 }}</span>
          <span class="progress-text">
            {{ profile.total_spark.toFixed(0) }} / {{ nextLevelThreshold }}
          </span>
        </div>
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: levelProgress + '%' }"
          ></div>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="quick-stats">
        <div class="stat-box">
          <span class="stat-icon">🏆</span>
          <span class="stat-number">{{ profile.nft_count }}</span>
          <span class="stat-desc">NFT</span>
        </div>
        <div class="stat-box">
          <span class="stat-icon">📊</span>
          <span class="stat-number">{{ profile.average_spark.toFixed(1) }}</span>
          <span class="stat-desc">平均光源</span>
        </div>
        <div class="stat-box">
          <span class="stat-icon">💰</span>
          <span class="stat-number">{{ profile.rewards_earned.toFixed(2) }}</span>
          <span class="stat-desc">累计奖励</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="dashboard-tabs">
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'my' }"
        @click="activeTab = 'my'"
      >
        📝 我的对话
      </button>
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'leaderboard' }"
        @click="activeTab = 'leaderboard'"
      >
        🏆 排行榜
      </button>
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'nft' }"
        @click="activeTab = 'nft'"
      >
        🎨 NFT
      </button>
    </div>

    <!-- My Conversations -->
    <div v-if="activeTab === 'my'" class="tab-content">
      <div v-if="loading" class="loading-state">
        <span class="spinner">⏳</span> 加载中...
      </div>
      <div v-else-if="conversations.length === 0" class="empty-state">
        <span class="empty-icon">💬</span>
        <p>暂无对话记录</p>
        <p class="empty-hint">开始与文档对话，积累您的光源值！</p>
      </div>
      <div v-else class="conversation-list">
        <div 
          v-for="conv in conversations" 
          :key="conv.conversation_id"
          class="conversation-card"
          :class="{ 'nft-eligible': conv.nft_eligible }"
        >
          <div class="conv-header">
            <div 
              class="spark-badge" 
              :class="getSparkClass(conv.spark_value)"
            >
              ✨ {{ conv.spark_value.toFixed(1) }}
            </div>
            <span v-if="conv.nft_eligible && !conv.nft_minted" class="nft-ready">
              🎨 可铸造 NFT
            </span>
            <span v-if="conv.nft_minted" class="nft-minted">
              ✅ 已铸造
            </span>
          </div>
          <div class="conv-question">{{ conv.question }}</div>
          <div class="conv-meta">
            <span>📎 {{ conv.citations_count }} 引用</span>
            <span>❤️ {{ conv.like_count }}</span>
            <span>⭐ {{ conv.save_count }}</span>
            <span class="conv-time">{{ formatTime(conv.created_at) }}</span>
          </div>
          <div class="conv-scores">
            <div class="mini-score" title="基础质量">📝 {{ conv.base_score.toFixed(1) }}</div>
            <div class="mini-score" title="引用关系">🔗 {{ conv.citation_score.toFixed(1) }}</div>
            <div class="mini-score" title="知识激活">💡 {{ conv.activation_score.toFixed(1) }}</div>
            <div class="mini-score" title="用户行为">👥 {{ conv.behavior_score.toFixed(1) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Leaderboard -->
    <div v-if="activeTab === 'leaderboard'" class="tab-content">
      <div class="leaderboard-section">
        <h3 class="section-title">🏆 用户排行榜</h3>
        <div v-if="userLeaderboard.length === 0" class="empty-state">
          <span class="empty-icon">📊</span>
          <p>暂无排行数据</p>
        </div>
        <div v-else class="leaderboard-list">
          <div 
            v-for="user in userLeaderboard" 
            :key="user.user_id"
            class="leaderboard-item"
            :class="{ 'top-3': user.rank <= 3 }"
          >
            <div class="rank-badge" :class="'rank-' + Math.min(user.rank, 4)">
              {{ user.rank <= 3 ? ['🥇', '🥈', '🥉'][user.rank - 1] : '#' + user.rank }}
            </div>
            <div class="user-info">
              <span class="user-name">用户 {{ user.user_id.slice(0, 8) }}</span>
              <span class="user-level">Lv.{{ user.reputation_level || 1 }}</span>
            </div>
            <div class="user-spark">
              ✨ {{ (user.total_spark || 0).toFixed(1) }}
            </div>
          </div>
        </div>
      </div>

      <div class="leaderboard-section">
        <h3 class="section-title">🔥 高光对话榜</h3>
        <div v-if="convLeaderboard.length === 0" class="empty-state">
          <span class="empty-icon">💬</span>
          <p>暂无高光对话</p>
        </div>
        <div v-else class="leaderboard-list">
          <div 
            v-for="conv in convLeaderboard" 
            :key="conv.conversation_id"
            class="leaderboard-item conversation"
          >
            <div class="rank-badge" :class="'rank-' + Math.min(conv.rank, 4)">
              {{ conv.rank <= 3 ? ['🥇', '🥈', '🥉'][conv.rank - 1] : '#' + conv.rank }}
            </div>
            <div class="conv-preview">
              <span class="conv-text">{{ conv.question }}</span>
              <span class="conv-user">by {{ conv.user_id.slice(0, 8) }}</span>
            </div>
            <div class="conv-spark" :class="{ 'nft-ready': conv.nft_eligible }">
              ✨ {{ conv.spark_value.toFixed(1) }}
              <span v-if="conv.nft_minted" class="minted-icon">🎨</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- NFT Section -->
    <div v-if="activeTab === 'nft'" class="tab-content">
      <div class="nft-section">
        <h3 class="section-title">🎨 NFT 铸造中心</h3>
        
        <div class="nft-eligible-list" v-if="nftEligible.length > 0">
          <p class="nft-intro">以下对话已达到 NFT 铸造资格（光源值 ≥ 70）：</p>
          <div 
            v-for="conv in nftEligible" 
            :key="conv.conversation_id"
            class="nft-eligible-card"
          >
            <div class="nft-preview">
              <div class="nft-spark">✨ {{ conv.spark_value.toFixed(1) }}</div>
              <div class="nft-question">{{ conv.question }}</div>
            </div>
            <button class="mint-btn" @click="mintNFT(conv.conversation_id)">
              🎨 铸造 NFT
            </button>
          </div>
        </div>
        <div v-else class="empty-state">
          <span class="empty-icon">🎨</span>
          <p>暂无可铸造的 NFT</p>
          <p class="empty-hint">当对话光源值达到 70 分以上时，即可铸造为 NFT</p>
        </div>

        <!-- NFT Stats -->
        <div class="nft-stats" v-if="profile">
          <div class="nft-stat-card">
            <span class="nft-stat-icon">🎨</span>
            <span class="nft-stat-value">{{ profile.nft_count }}</span>
            <span class="nft-stat-label">已铸造 NFT</span>
          </div>
          <div class="nft-stat-card">
            <span class="nft-stat-icon">💎</span>
            <span class="nft-stat-value">{{ profile.nft_total_value.toFixed(2) }}</span>
            <span class="nft-stat-label">NFT 总价值</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const API_BASE = ''

// State
const activeTab = ref('my')
const loading = ref(false)
const profile = ref(null)
const conversations = ref([])
const userLeaderboard = ref([])
const convLeaderboard = ref([])
const nftEligible = ref([])

// Computed
const nextLevelThreshold = computed(() => {
  const thresholds = { 1: 100, 2: 300, 3: 600, 4: 1000, 5: 2000, 6: 4000, 7: 8000, 8: 15000, 9: 30000, 10: 50000 }
  return thresholds[profile.value?.reputation_level + 1] || 100
})

const levelProgress = computed(() => {
  if (!profile.value) return 0
  const current = profile.value.total_spark
  const threshold = nextLevelThreshold.value
  const prevThreshold = { 1: 0, 2: 100, 3: 300, 4: 600, 5: 1000, 6: 2000, 7: 4000, 8: 8000, 9: 15000, 10: 30000 }[profile.value.reputation_level] || 0
  return Math.min(((current - prevThreshold) / (threshold - prevThreshold)) * 100, 100)
})

// Methods
const getToken = () => localStorage.getItem('token')

const fetchProfile = async () => {
  try {
    const response = await fetch(`${API_BASE}/v1/spark/profile`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (response.ok) {
      const result = await response.json()
      profile.value = result.data
    }
  } catch (error) {
    console.error('Fetch profile error:', error)
  }
}

const fetchConversations = async () => {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/v1/spark/conversations?limit=50`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (response.ok) {
      const result = await response.json()
      conversations.value = result.data
    }
  } catch (error) {
    console.error('Fetch conversations error:', error)
  } finally {
    loading.value = false
  }
}

const fetchLeaderboards = async () => {
  try {
    const [userRes, convRes] = await Promise.all([
      fetch(`${API_BASE}/v1/spark/leaderboard/users?limit=10`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      }),
      fetch(`${API_BASE}/v1/spark/leaderboard/conversations?limit=10`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      })
    ])
    
    if (userRes.ok) {
      const result = await userRes.json()
      userLeaderboard.value = result.data
    }
    if (convRes.ok) {
      const result = await convRes.json()
      convLeaderboard.value = result.data
    }
  } catch (error) {
    console.error('Fetch leaderboards error:', error)
  }
}

const fetchNFTEligible = async () => {
  try {
    const response = await fetch(`${API_BASE}/v1/spark/nft/eligible`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (response.ok) {
      const result = await response.json()
      nftEligible.value = result.data
    }
  } catch (error) {
    console.error('Fetch NFT eligible error:', error)
  }
}

const mintNFT = async (conversationId) => {
  alert(`NFT 铸造功能开发中...\n对话 ID: ${conversationId}`)
  // TODO: Implement actual NFT minting
}

const getSparkClass = (value) => {
  if (value >= 80) return 'spark-legendary'
  if (value >= 70) return 'spark-epic'
  if (value >= 50) return 'spark-rare'
  if (value >= 30) return 'spark-common'
  return 'spark-basic'
}

const formatTime = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleDateString('zh-CN', { 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  fetchProfile()
  fetchConversations()
  fetchLeaderboards()
  fetchNFTEligible()
})
</script>

<style scoped>
.spark-dashboard {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Header */
.dashboard-header {
  text-align: center;
  margin-bottom: 32px;
}

.dashboard-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary, #1a1a2e);
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.title-icon {
  font-size: 32px;
}

.dashboard-subtitle {
  color: var(--text-secondary, #666);
  margin: 0;
}

/* Profile Card */
.profile-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.profile-header {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.profile-avatar {
  position: relative;
  width: 64px;
  height: 64px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  font-size: 32px;
}

.reputation-badge {
  position: absolute;
  bottom: -4px;
  right: -4px;
  background: #ffc107;
  color: #333;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 8px;
}

.profile-info {
  flex: 1;
}

.profile-name {
  font-size: 18px;
  margin: 0 0 12px 0;
}

.profile-stats-row {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

/* Level Progress */
.level-progress {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 8px;
}

.progress-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ffc107 0%, #ff9800 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* Quick Stats */
.quick-stats {
  display: flex;
  gap: 12px;
}

.stat-box {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-icon {
  font-size: 20px;
}

.stat-number {
  font-size: 18px;
  font-weight: 700;
}

.stat-desc {
  font-size: 11px;
  opacity: 0.8;
}

/* Tabs */
.dashboard-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  background: var(--bg-secondary, #f5f5f5);
  padding: 4px;
  border-radius: 12px;
}

.tab-btn {
  flex: 1;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-secondary, #666);
}

.tab-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.tab-btn.active {
  background: white;
  color: var(--accent-color, #667eea);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Tab Content */
.tab-content {
  min-height: 300px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-secondary, #666);
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.empty-hint {
  font-size: 13px;
  opacity: 0.7;
}

.spinner {
  animation: spin 1s linear infinite;
  display: inline-block;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Conversation List */
.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.conversation-card {
  background: var(--bg-primary, white);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;
}

.conversation-card:hover {
  border-color: var(--accent-color, #667eea);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.conversation-card.nft-eligible {
  border-color: #ffc107;
  background: linear-gradient(135deg, #fffde7 0%, #fff8e1 100%);
}

.conv-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.spark-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.spark-basic { background: linear-gradient(135deg, #6c757d 0%, #495057 100%); }
.spark-common { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); }
.spark-rare { background: linear-gradient(135deg, #007bff 0%, #6610f2 100%); }
.spark-epic { background: linear-gradient(135deg, #fd7e14 0%, #ffc107 100%); }
.spark-legendary { background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%); }

.nft-ready {
  font-size: 11px;
  color: #e65100;
  font-weight: 600;
}

.nft-minted {
  font-size: 11px;
  color: #388e3c;
  font-weight: 600;
}

.conv-question {
  font-size: 14px;
  color: var(--text-primary, #1a1a2e);
  margin-bottom: 8px;
  line-height: 1.5;
}

.conv-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-tertiary, #999);
}

.conv-time {
  margin-left: auto;
}

.conv-scores {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-color, #e0e0e0);
}

.mini-score {
  font-size: 11px;
  color: var(--text-secondary, #666);
  background: var(--bg-secondary, #f5f5f5);
  padding: 4px 8px;
  border-radius: 6px;
}

/* Leaderboard */
.leaderboard-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: var(--text-primary, #1a1a2e);
}

.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.leaderboard-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-primary, white);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.leaderboard-item:hover {
  transform: translateX(4px);
  border-color: var(--accent-color, #667eea);
}

.leaderboard-item.top-3 {
  background: linear-gradient(135deg, #fff8e1 0%, #fffde7 100%);
  border-color: #ffc107;
}

.rank-badge {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  border-radius: 8px;
  background: var(--bg-secondary, #f5f5f5);
}

.rank-1 { background: linear-gradient(135deg, #ffd700 0%, #ffb300 100%); }
.rank-2 { background: linear-gradient(135deg, #e0e0e0 0%, #bdbdbd 100%); }
.rank-3 { background: linear-gradient(135deg, #cd7f32 0%, #a05a2c 100%); color: white; }

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
}

.user-level {
  font-size: 11px;
  color: var(--text-tertiary, #999);
}

.user-spark,
.conv-spark {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent-color, #667eea);
}

.conv-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.conv-text {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-user {
  font-size: 11px;
  color: var(--text-tertiary, #999);
}

.conv-spark.nft-ready {
  color: #e65100;
}

.minted-icon {
  margin-left: 4px;
}

/* NFT Section */
.nft-section {
  margin-bottom: 24px;
}

.nft-intro {
  font-size: 14px;
  color: var(--text-secondary, #666);
  margin-bottom: 16px;
}

.nft-eligible-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.nft-eligible-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #fff8e1 0%, #fffde7 100%);
  border: 2px solid #ffc107;
  border-radius: 12px;
}

.nft-preview {
  flex: 1;
}

.nft-spark {
  font-size: 16px;
  font-weight: 700;
  color: #e65100;
  margin-bottom: 4px;
}

.nft-question {
  font-size: 13px;
  color: var(--text-primary, #1a1a2e);
}

.mint-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mint-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.nft-stats {
  display: flex;
  gap: 16px;
  margin-top: 24px;
}

.nft-stat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: var(--bg-secondary, #f5f5f5);
  border-radius: 12px;
}

.nft-stat-icon {
  font-size: 28px;
}

.nft-stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #1a1a2e);
}

.nft-stat-label {
  font-size: 12px;
  color: var(--text-secondary, #666);
}
</style>

