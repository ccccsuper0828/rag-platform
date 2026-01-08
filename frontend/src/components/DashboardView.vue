<template>
  <div class="dashboard-container">
    <!-- 顶部统计概览 -->
    <div class="stats-overview">
      <div class="stat-card primary">
        <div class="stat-icon">💬</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_conversations }}</div>
          <div class="stat-label">总对话数</div>
        </div>
      </div>
      
      <div class="stat-card success">
        <div class="stat-icon">📄</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_documents }}</div>
          <div class="stat-label">已上传文档</div>
        </div>
      </div>
      
      <div class="stat-card info">
        <div class="stat-icon">🧠</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_memories }}</div>
          <div class="stat-label">记忆条目</div>
        </div>
      </div>
      
      <div class="stat-card warning">
        <div class="stat-icon">🔬</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.research_count }}</div>
          <div class="stat-label">深度研究</div>
        </div>
      </div>
      
      <div class="stat-card accent">
        <div class="stat-icon">🕸️</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.graph_nodes }}</div>
          <div class="stat-label">知识图谱节点</div>
        </div>
      </div>
      
      <div class="stat-card secondary">
        <div class="stat-icon">🔗</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.graph_edges }}</div>
          <div class="stat-label">图谱关系</div>
        </div>
      </div>
    </div>
    
    <!-- 主内容网格 -->
    <div class="dashboard-grid">
      <!-- 用户画像卡片 -->
      <div class="grid-item persona-card">
        <div class="card-header">
          <h3>👤 用户画像</h3>
          <button class="refresh-btn" @click="loadPersona">🔄</button>
        </div>
        <div class="card-body">
          <div v-if="userPersona" class="persona-content">
            <div class="persona-avatar">
              {{ userPersona.name?.charAt(0) || '用' }}
            </div>
            <div class="persona-info">
              <h4>{{ userPersona.name || '未设置名称' }}</h4>
              <p class="persona-role">{{ userPersona.role || '用户' }}</p>
              <div class="persona-tags">
                <span 
                  v-for="tag in (userPersona.tags || []).slice(0, 5)" 
                  :key="tag"
                  class="tag"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="empty-persona">
            <p>暂无用户画像</p>
            <p class="hint">与 AI 对话后会自动生成</p>
          </div>
        </div>
      </div>
      
      <!-- 知识库使用统计 -->
      <div class="grid-item usage-card">
        <div class="card-header">
          <h3>📊 使用统计</h3>
        </div>
        <div class="card-body">
          <div class="usage-chart">
            <div class="usage-bar-container">
              <div class="usage-bar">
                <div 
                  class="usage-fill chat" 
                  :style="{ width: getUsagePercent('chat') + '%' }"
                ></div>
              </div>
              <div class="usage-legend">
                <span class="legend-dot chat"></span>
                <span>AI 问答</span>
                <span class="legend-value">{{ usageData.chat || 0 }}</span>
              </div>
            </div>
            <div class="usage-bar-container">
              <div class="usage-bar">
                <div 
                  class="usage-fill research" 
                  :style="{ width: getUsagePercent('research') + '%' }"
                ></div>
              </div>
              <div class="usage-legend">
                <span class="legend-dot research"></span>
                <span>深度研究</span>
                <span class="legend-value">{{ usageData.research || 0 }}</span>
              </div>
            </div>
            <div class="usage-bar-container">
              <div class="usage-bar">
                <div 
                  class="usage-fill discussion" 
                  :style="{ width: getUsagePercent('discussion') + '%' }"
                ></div>
              </div>
              <div class="usage-legend">
                <span class="legend-dot discussion"></span>
                <span>讨论参与</span>
                <span class="legend-value">{{ usageData.discussion || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 知识库列表 -->
      <div class="grid-item kb-card">
        <div class="card-header">
          <h3>📚 我的知识库</h3>
          <button class="add-btn" @click="$emit('upload')">➕ 添加</button>
        </div>
        <div class="card-body">
          <div v-if="ragList.length > 0" class="kb-list">
            <div 
              v-for="rag in ragList.slice(0, 5)" 
              :key="rag.rag_id"
              class="kb-item"
              @click="$emit('select-rag', rag)"
            >
              <span class="kb-icon">{{ getFileIcon(rag.file_path) }}</span>
              <div class="kb-info">
                <span class="kb-name">{{ getFileName(rag.file_path) }}</span>
                <span class="kb-meta">{{ formatDate(rag.created_at) }}</span>
              </div>
              <span class="kb-status" :class="{ active: rag.active !== false }">
                {{ rag.active !== false ? '●' : '○' }}
              </span>
            </div>
          </div>
          <div v-else class="empty-kb">
            <p>暂无知识库</p>
            <button class="create-btn" @click="$emit('upload')">创建第一个</button>
          </div>
        </div>
      </div>
      
      <!-- 最近对话 -->
      <div class="grid-item conversations-card">
        <div class="card-header">
          <h3>💬 最近对话</h3>
          <button class="view-all-btn" @click="$emit('view-chat')">查看全部 →</button>
        </div>
        <div class="card-body">
          <div v-if="recentConversations.length > 0" class="conversation-list">
            <div 
              v-for="conv in recentConversations" 
              :key="conv.id"
              class="conversation-item"
            >
              <div class="conv-icon">🗨️</div>
              <div class="conv-info">
                <span class="conv-title">{{ conv.title || '未命名对话' }}</span>
                <span class="conv-preview">{{ conv.preview }}</span>
              </div>
              <span class="conv-time">{{ formatTime(conv.time) }}</span>
            </div>
          </div>
          <div v-else class="empty-conversations">
            <p>暂无对话记录</p>
            <p class="hint">开始提问创建您的第一个对话</p>
          </div>
        </div>
      </div>
      
      <!-- 快捷操作 -->
      <div class="grid-item actions-card">
        <div class="card-header">
          <h3>⚡ 快捷操作</h3>
        </div>
        <div class="card-body">
          <div class="action-grid">
            <button class="action-btn" @click="$emit('view-chat')">
              <span class="action-icon">🤖</span>
              <span class="action-text">AI 问答</span>
            </button>
            <button class="action-btn" @click="$emit('view-research')">
              <span class="action-icon">🔬</span>
              <span class="action-text">深度研究</span>
            </button>
            <button class="action-btn" @click="$emit('view-memory')">
              <span class="action-icon">🧠</span>
              <span class="action-text">记忆库</span>
            </button>
            <button class="action-btn" @click="$emit('view-graph')">
              <span class="action-icon">🕸️</span>
              <span class="action-text">知识图谱</span>
            </button>
            <button class="action-btn" @click="$emit('upload')">
              <span class="action-icon">📤</span>
              <span class="action-text">上传文档</span>
            </button>
            <button class="action-btn" @click="$emit('view-discussion')">
              <span class="action-icon">💬</span>
              <span class="action-text">讨论大厅</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  ragList: {
    type: Array,
    default: () => []
  },
  authToken: {
    type: String,
    default: ''
  },
  apiBase: {
    type: String,
    default: 'http://localhost:8000'
  }
})

const emit = defineEmits([
  'upload', 
  'select-rag', 
  'view-chat', 
  'view-research', 
  'view-memory', 
  'view-graph',
  'view-discussion'
])

// 状态
const stats = ref({
  total_conversations: 0,
  total_documents: 0,
  total_memories: 0,
  research_count: 0,
  graph_nodes: 0,
  graph_edges: 0
})

const userPersona = ref(null)
const usageData = ref({
  chat: 0,
  research: 0,
  discussion: 0
})
const recentConversations = ref([])

// 计算
const totalUsage = computed(() => {
  return (usageData.value.chat || 0) + 
         (usageData.value.research || 0) + 
         (usageData.value.discussion || 0) || 1
})

// 方法
const getUsagePercent = (type) => {
  return Math.round((usageData.value[type] || 0) / totalUsage.value * 100)
}

const getFileIcon = (filePath) => {
  if (!filePath) return '📄'
  const ext = filePath.split('.').pop()?.toLowerCase()
  const icons = { pdf: '📕', txt: '📝', md: '📘', docx: '📗', pptx: '📙' }
  return icons[ext] || '📄'
}

const getFileName = (filePath) => {
  if (!filePath) return '未知文件'
  return filePath.split('/').pop() || filePath
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const loadStats = async () => {
  try {
    const response = await fetch(`${props.apiBase}/v1/dashboard/stats`, {
      headers: {
        'Authorization': `Bearer ${props.authToken}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      stats.value = data
    }
  } catch (e) {
    console.error('Failed to load dashboard stats:', e)
  }
}

const loadPersona = async () => {
  try {
    const response = await fetch(`${props.apiBase}/v1/dashboard/persona`, {
      headers: {
        'Authorization': `Bearer ${props.authToken}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      userPersona.value = data
    }
  } catch (e) {
    console.error('Failed to load persona:', e)
  }
}

const loadUsage = async () => {
  try {
    const response = await fetch(`${props.apiBase}/v1/dashboard/usage`, {
      headers: {
        'Authorization': `Bearer ${props.authToken}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      usageData.value = data
    }
  } catch (e) {
    console.error('Failed to load usage:', e)
  }
}

const loadRecentConversations = async () => {
  try {
    const response = await fetch(`${props.apiBase}/v1/dashboard/conversations?limit=5`, {
      headers: {
        'Authorization': `Bearer ${props.authToken}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      recentConversations.value = data.conversations || []
    }
  } catch (e) {
    console.error('Failed to load conversations:', e)
  }
}

// 更新统计 (基于本地数据)
const updateLocalStats = () => {
  stats.value.total_documents = props.ragList.length
}

onMounted(() => {
  updateLocalStats()
  loadStats()
  loadPersona()
  loadUsage()
  loadRecentConversations()
})

// 暴露刷新方法
defineExpose({
  refresh: () => {
    updateLocalStats()
    loadStats()
    loadPersona()
    loadUsage()
    loadRecentConversations()
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100%;
}

/* 统计概览 */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.stat-card.primary .stat-icon { background: #dbeafe; }
.stat-card.success .stat-icon { background: #d1fae5; }
.stat-card.info .stat-icon { background: #e0e7ff; }
.stat-card.warning .stat-icon { background: #fef3c7; }
.stat-card.accent .stat-icon { background: #fce7f3; }
.stat-card.secondary .stat-icon { background: #f3e8ff; }

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

/* 主内容网格 */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.grid-item {
  background: white;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: all 0.2s ease;
}

.grid-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f3f4f6;
}

.card-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.refresh-btn, .add-btn, .view-all-btn {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover, .add-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.view-all-btn {
  border: none;
  color: #f97316;
  font-weight: 500;
}

.view-all-btn:hover {
  color: #ea580c;
}

.card-body {
  padding: 20px;
}

/* 用户画像 */
.persona-content {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.persona-avatar {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f97316, #fb923c);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  flex-shrink: 0;
}

.persona-info {
  flex: 1;
}

.persona-info h4 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.persona-role {
  margin: 0 0 12px;
  font-size: 13px;
  color: #6b7280;
}

.persona-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 4px 10px;
  background: #f3f4f6;
  border-radius: 12px;
  font-size: 12px;
  color: #374151;
}

.empty-persona, .empty-kb, .empty-conversations {
  text-align: center;
  padding: 24px;
  color: #9ca3af;
}

.empty-persona p, .empty-kb p, .empty-conversations p {
  margin: 0 0 8px;
}

.hint {
  font-size: 12px;
  color: #d1d5db;
}

/* 使用统计 */
.usage-chart {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.usage-bar-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.usage-bar {
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.usage-fill.chat { background: linear-gradient(90deg, #f97316, #fb923c); }
.usage-fill.research { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.usage-fill.discussion { background: linear-gradient(90deg, #3b82f6, #60a5fa); }

.usage-legend {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.chat { background: #f97316; }
.legend-dot.research { background: #8b5cf6; }
.legend-dot.discussion { background: #3b82f6; }

.legend-value {
  margin-left: auto;
  font-weight: 600;
  color: #374151;
}

/* 知识库列表 */
.kb-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kb-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.kb-item:hover {
  background: #f3f4f6;
}

.kb-icon {
  font-size: 20px;
}

.kb-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.kb-name {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
}

.kb-meta {
  font-size: 12px;
  color: #9ca3af;
}

.kb-status {
  font-size: 12px;
  color: #9ca3af;
}

.kb-status.active {
  color: #10b981;
}

.create-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #f97316, #fb923c);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.create-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

/* 对话列表 */
.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 10px;
}

.conv-icon {
  font-size: 18px;
}

.conv-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.conv-title {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
}

.conv-preview {
  font-size: 12px;
  color: #9ca3af;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.conv-time {
  font-size: 12px;
  color: #9ca3af;
}

/* 快捷操作 */
.action-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: white;
  border-color: #f97316;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.1);
}

.action-icon {
  font-size: 24px;
}

.action-text {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

/* 网格布局调整 */
.persona-card { grid-column: 1 / 2; }
.usage-card { grid-column: 2 / 3; }
.kb-card { grid-column: 3 / 4; }
.conversations-card { grid-column: 1 / 3; }
.actions-card { grid-column: 3 / 4; }

/* 响应式 */
@media (max-width: 1200px) {
  .stats-overview {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .persona-card { grid-column: 1 / 2; }
  .usage-card { grid-column: 2 / 3; }
  .kb-card { grid-column: 1 / 2; }
  .conversations-card { grid-column: 2 / 3; }
  .actions-card { grid-column: 1 / 3; }
}

@media (max-width: 768px) {
  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .persona-card,
  .usage-card,
  .kb-card,
  .conversations-card,
  .actions-card {
    grid-column: 1 / 2;
  }
  
  .action-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

