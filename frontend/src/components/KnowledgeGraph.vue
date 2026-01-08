<template>
  <div class="knowledge-graph-container">
    <!-- 头部控制栏 -->
    <div class="kg-header">
      <div class="kg-title">
        <span class="kg-icon">🧠</span>
        <h2>知识图谱</h2>
        <span class="kg-status" :class="{ active: isLoading }">
          {{ isLoading ? '构建中...' : `${stats.nodeCount} 节点 · ${stats.edgeCount} 边` }}
        </span>
      </div>
      <div class="kg-actions">
        <button class="action-btn build" @click="buildGraph" :disabled="isLoading">
          <span>🔨</span> 构建图谱
        </button>
        <button class="action-btn refresh" @click="loadGraph" :disabled="isLoading">
          <span>🔄</span> 刷新
        </button>
        <button class="action-btn search" @click="showSearch = !showSearch">
          <span>🔍</span> 搜索
        </button>
      </div>
    </div>

    <!-- 搜索面板 -->
    <div v-if="showSearch" class="search-panel">
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="搜索实体或关系..."
        @keyup.enter="searchGraph"
      />
      <button @click="searchGraph" :disabled="!searchQuery || isSearching">
        {{ isSearching ? '搜索中...' : '搜索' }}
      </button>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <span>找到 {{ searchResults.length }} 条结果</span>
        <button class="close-btn" @click="searchResults = []">✕</button>
      </div>
      <div class="results-list">
        <div 
          v-for="(result, index) in searchResults" 
          :key="index" 
          class="result-item"
          @click="highlightNode(result)"
        >
          <span class="result-fact">{{ result.fact }}</span>
        </div>
      </div>
    </div>

    <!-- 图谱可视化区域 -->
    <div class="graph-viewport" ref="graphContainer">
      <!-- SVG 图谱 -->
      <svg ref="graphSvg" class="graph-svg">
        <!-- 边 -->
        <g class="edges">
          <line
            v-for="edge in visibleEdges"
            :key="edge.id"
            :x1="getNodePosition(edge.source).x"
            :y1="getNodePosition(edge.source).y"
            :x2="getNodePosition(edge.target).x"
            :y2="getNodePosition(edge.target).y"
            class="edge-line"
            :class="{ highlighted: edge.highlighted }"
          />
        </g>
        <!-- 节点 -->
        <g class="nodes">
          <g
            v-for="node in visibleNodes"
            :key="node.id"
            class="node-group"
            :class="{ highlighted: node.highlighted }"
            :transform="`translate(${node.x}, ${node.y})`"
            @click="selectNode(node)"
            @mouseenter="hoverNode = node"
            @mouseleave="hoverNode = null"
          >
            <circle
              :r="getNodeSize(node)"
              :fill="getNodeColor(node.group)"
              class="node-circle"
            />
            <text
              :dy="getNodeSize(node) + 15"
              class="node-label"
            >
              {{ truncate(node.name, 12) }}
            </text>
          </g>
        </g>
      </svg>

      <!-- 空状态 -->
      <div v-if="!isLoading && nodes.length === 0" class="empty-state">
        <span class="empty-icon">🌐</span>
        <p>尚未构建知识图谱</p>
        <p class="empty-hint">点击"构建图谱"按钮从 RAG 文档中提取实体和关系</p>
        <button class="build-btn" @click="buildGraph">
          🔨 开始构建
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>正在构建知识图谱...</p>
        <p class="loading-hint">这可能需要一些时间，取决于文档大小</p>
      </div>
    </div>

    <!-- 节点详情面板 -->
    <div v-if="selectedNode" class="node-detail-panel">
      <div class="panel-header">
        <h3>{{ selectedNode.name }}</h3>
        <button class="close-btn" @click="selectedNode = null">✕</button>
      </div>
      <div class="panel-content">
        <div class="detail-item">
          <label>类型</label>
          <span class="node-type" :style="{ background: getNodeColor(selectedNode.group) }">
            {{ selectedNode.group }}
          </span>
        </div>
        <div class="detail-item" v-if="selectedNode.summary">
          <label>摘要</label>
          <p>{{ selectedNode.summary }}</p>
        </div>
        <div class="detail-item">
          <label>相关边</label>
          <div class="related-edges">
            <div 
              v-for="edge in getRelatedEdges(selectedNode.id)" 
              :key="edge.id"
              class="edge-item"
            >
              {{ edge.fact || edge.type }}
            </div>
            <p v-if="getRelatedEdges(selectedNode.id).length === 0" class="no-edges">
              暂无相关连接
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="graph-legend">
      <div 
        v-for="(color, type) in nodeColors" 
        :key="type" 
        class="legend-item"
      >
        <span class="legend-dot" :style="{ background: color }"></span>
        <span class="legend-label">{{ type }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'

const props = defineProps({
  ragId: {
    type: String,
    required: true
  }
})

// 状态
const isLoading = ref(false)
const isSearching = ref(false)
const showSearch = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const selectedNode = ref(null)
const hoverNode = ref(null)
const graphContainer = ref(null)
const graphSvg = ref(null)

// 图数据
const nodes = ref([])
const edges = ref([])

// 统计
const stats = computed(() => ({
  nodeCount: nodes.value.length,
  edgeCount: edges.value.length
}))

// 节点颜色映射
const nodeColors = {
  'Person': '#FF6B6B',
  'Organization': '#4ECDC4',
  'Technology': '#45B7D1',
  'Location': '#96CEB4',
  'Concept': '#FECA57',
  'Entity': '#9B59B6',
  'default': '#A8A8A8'
}

// 可见节点和边
const visibleNodes = computed(() => nodes.value)
const visibleEdges = computed(() => edges.value)

// 方法
async function loadGraph() {
  if (!props.ragId) return
  
  isLoading.value = true
  try {
    const response = await fetch(`/v1/knowledge-graph/${props.ragId}/graph`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success && result.data) {
        nodes.value = result.data.nodes || []
        edges.value = result.data.links || []
        
        // 布局计算
        await nextTick()
        layoutGraph()
      }
    }
  } catch (e) {
    console.error('Failed to load graph:', e)
  } finally {
    isLoading.value = false
  }
}

async function buildGraph() {
  if (!props.ragId) return
  
  isLoading.value = true
  try {
    const response = await fetch(`/v1/knowledge-graph/${props.ragId}/build`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      // 构建完成后刷新图谱
      await loadGraph()
    } else {
      console.error('Build failed:', await response.text())
    }
  } catch (e) {
    console.error('Failed to build graph:', e)
  } finally {
    isLoading.value = false
  }
}

async function searchGraph() {
  if (!searchQuery.value || !props.ragId) return
  
  isSearching.value = true
  try {
    const response = await fetch(`/v1/knowledge-graph/${props.ragId}/search`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: searchQuery.value,
        limit: 20
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      searchResults.value = result.results || []
    }
  } catch (e) {
    console.error('Search failed:', e)
  } finally {
    isSearching.value = false
  }
}

function layoutGraph() {
  if (!graphContainer.value || nodes.value.length === 0) return
  
  const width = graphContainer.value.clientWidth
  const height = graphContainer.value.clientHeight
  const centerX = width / 2
  const centerY = height / 2
  
  // 按类型分组节点，使用螺旋布局
  const nodesByType = {}
  nodes.value.forEach(node => {
    const type = node.type || node.group || 'default'
    if (!nodesByType[type]) nodesByType[type] = []
    nodesByType[type].push(node)
  })
  
  const types = Object.keys(nodesByType)
  const typeCount = types.length || 1
  
  // 每种类型占据一个扇区
  types.forEach((type, typeIdx) => {
    const typeNodes = nodesByType[type]
    const sectorAngle = (2 * Math.PI) / typeCount
    const sectorStart = typeIdx * sectorAngle
    
    // 在扇区内使用多层圆形布局
    typeNodes.forEach((node, nodeIdx) => {
      const layer = Math.floor(nodeIdx / 8) // 每层8个节点
      const posInLayer = nodeIdx % 8
      const layerCount = Math.ceil(typeNodes.length / 8)
      
      // 计算半径（越外层越大）
      const minRadius = Math.min(width, height) * 0.15
      const maxRadius = Math.min(width, height) * 0.42
      const radius = minRadius + (maxRadius - minRadius) * (layer / Math.max(layerCount - 1, 1))
      
      // 在扇区内均匀分布
      const nodesInThisLayer = Math.min(8, typeNodes.length - layer * 8)
      const angleStep = sectorAngle * 0.8 / Math.max(nodesInThisLayer, 1)
      const angle = sectorStart + sectorAngle * 0.1 + posInLayer * angleStep
      
      node.x = centerX + radius * Math.cos(angle)
      node.y = centerY + radius * Math.sin(angle)
    })
  })
}

function getNodePosition(nodeId) {
  const node = nodes.value.find(n => n.id === nodeId)
  return node ? { x: node.x || 0, y: node.y || 0 } : { x: 0, y: 0 }
}

function getNodeSize(node) {
  // 根据连接数计算大小
  const connections = edges.value.filter(
    e => e.source === node.id || e.target === node.id
  ).length
  return Math.max(8, Math.min(25, 8 + connections * 2))
}

function getNodeColor(group) {
  return nodeColors[group] || nodeColors.default
}

function selectNode(node) {
  selectedNode.value = node === selectedNode.value ? null : node
}

function highlightNode(result) {
  // 高亮相关节点
  nodes.value.forEach(n => {
    n.highlighted = n.id === result.source_node || n.id === result.target_node
  })
}

function getRelatedEdges(nodeId) {
  return edges.value.filter(e => e.source === nodeId || e.target === nodeId)
}

function truncate(text, length) {
  if (!text) return ''
  return text.length > length ? text.slice(0, length) + '...' : text
}

// 监听 ragId 变化
watch(() => props.ragId, (newId) => {
  if (newId) {
    loadGraph()
  }
}, { immediate: true })

// 窗口大小变化时重新布局
onMounted(() => {
  window.addEventListener('resize', layoutGraph)
})
</script>

<style scoped>
.knowledge-graph-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 600px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 1rem;
  overflow: hidden;
  position: relative;
}

/* 头部 */
.kg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.kg-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.kg-icon {
  font-size: 1.5rem;
}

.kg-title h2 {
  margin: 0;
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
}

.kg-status {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  padding: 0.25rem 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
}

.kg-status.active {
  color: #45B7D1;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.kg-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.5rem;
  color: white;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.build {
  background: linear-gradient(135deg, #45B7D1, #4ECDC4);
  border: none;
}

/* 搜索面板 */
.search-panel {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  background: rgba(0, 0, 0, 0.2);
}

.search-panel input {
  flex: 1;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.5rem;
  color: white;
  font-size: 0.875rem;
}

.search-panel input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.search-panel button {
  padding: 0.75rem 1.5rem;
  background: #45B7D1;
  border: none;
  border-radius: 0.5rem;
  color: white;
  font-weight: 500;
  cursor: pointer;
}

.search-panel button:disabled {
  opacity: 0.5;
}

/* 搜索结果 */
.search-results {
  position: absolute;
  top: 120px;
  left: 1.5rem;
  width: 300px;
  max-height: 300px;
  background: rgba(26, 26, 46, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  z-index: 100;
  overflow: hidden;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.75rem;
}

.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: 1rem;
}

.results-list {
  max-height: 250px;
  overflow-y: auto;
}

.result-item {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: background 0.2s;
}

.result-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.result-fact {
  color: white;
  font-size: 0.875rem;
}

/* 图谱视口 */
.graph-viewport {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: 100%;
}

/* 边 */
.edge-line {
  stroke: rgba(255, 255, 255, 0.2);
  stroke-width: 1;
  transition: stroke 0.2s, stroke-width 0.2s;
}

.edge-line.highlighted {
  stroke: #45B7D1;
  stroke-width: 2;
}

/* 节点 */
.node-group {
  cursor: pointer;
  transition: transform 0.2s;
}

.node-group:hover {
  transform: scale(1.1);
}

.node-group.highlighted .node-circle {
  stroke: #FFD700;
  stroke-width: 3;
}

.node-circle {
  stroke: rgba(255, 255, 255, 0.3);
  stroke-width: 2;
  transition: all 0.2s;
}

.node-label {
  fill: white;
  font-size: 10px;
  text-anchor: middle;
  pointer-events: none;
}

/* 空状态 */
.empty-state, .loading-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: white;
}

.empty-icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 1rem;
}

.empty-state p {
  margin: 0.5rem 0;
}

.empty-hint {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
}

.build-btn {
  margin-top: 1.5rem;
  padding: 0.75rem 2rem;
  background: linear-gradient(135deg, #45B7D1, #4ECDC4);
  border: none;
  border-radius: 0.75rem;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.build-btn:hover {
  transform: scale(1.05);
}

/* 加载状态 */
.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: #45B7D1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-hint {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
}

/* 节点详情面板 */
.node-detail-panel {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  width: 280px;
  background: rgba(26, 26, 46, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  overflow: hidden;
  z-index: 100;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
}

.panel-header h3 {
  margin: 0;
  color: white;
  font-size: 1rem;
}

.panel-content {
  padding: 1rem;
}

.detail-item {
  margin-bottom: 1rem;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-item label {
  display: block;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
}

.node-type {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  color: white;
  font-size: 0.75rem;
}

.detail-item p {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.875rem;
  line-height: 1.5;
}

.related-edges {
  max-height: 150px;
  overflow-y: auto;
}

.edge-item {
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.25rem;
  margin-bottom: 0.25rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.75rem;
}

.no-edges {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.75rem;
  font-style: italic;
}

/* 图例 */
.graph-legend {
  position: absolute;
  bottom: 1.5rem;
  left: 1.5rem;
  display: flex;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(26, 26, 46, 0.9);
  border-radius: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
}
</style>

