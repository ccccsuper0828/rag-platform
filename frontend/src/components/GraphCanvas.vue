<template>
  <div class="graph-canvas-container" ref="rootEl">
    <div v-show="graphData.nodes.length > 0" class="graph-canvas" ref="container"></div>
    
    <!-- 顶部操作区 -->
    <div class="graph-overlay top" v-if="showControls">
      <div class="graph-controls">
        <input 
          v-model="searchKeyword" 
          type="text" 
          class="search-input"
          placeholder="搜索节点... (* 显示全部)"
          @keydown.enter="handleSearch"
        />
        <button class="control-btn" @click="handleSearch">
          🔍 搜索
        </button>
        <button class="control-btn" @click="handleRefresh">
          🔄 刷新
        </button>
        <button class="control-btn" @click="handleFitView">
          📐 适应
        </button>
      </div>
    </div>
    
    <!-- 统计信息面板 -->
    <div class="graph-stats-panel" v-if="graphData.nodes.length > 0">
      <div class="stat-item">
        <span class="stat-label">节点</span>
        <span class="stat-value">{{ graphData.nodes.length }}</span>
        <span v-if="graphInfo?.total_nodes" class="stat-total">/ {{ graphInfo.total_nodes }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">边</span>
        <span class="stat-value">{{ graphData.edges.length }}</span>
        <span v-if="graphInfo?.total_edges" class="stat-total">/ {{ graphInfo.total_edges }}</span>
      </div>
    </div>
    
    <!-- 图例 -->
    <div class="graph-legend" v-if="entityTypes.length > 0">
      <div class="legend-title">实体类型</div>
      <div class="legend-items">
        <div 
          v-for="(item, index) in entityTypes" 
          :key="item.type"
          class="legend-item"
        >
          <span class="legend-color" :style="{ backgroundColor: getTypeColor(item.type, index) }"></span>
          <span class="legend-text">{{ item.type }}</span>
          <span class="legend-count">({{ item.count }})</span>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-show="graphData.nodes.length === 0" class="graph-empty">
      <div class="empty-icon">🕸️</div>
      <div class="empty-text">暂无图谱数据</div>
      <div class="empty-hint">上传文档后会自动生成知识图谱</div>
    </div>
  </div>
</template>

<script setup>
import { Graph } from '@antv/g6'
import { onMounted, onUnmounted, ref, watch, computed } from 'vue'

const props = defineProps({
  graphData: {
    type: Object,
    required: true,
    default: () => ({ nodes: [], edges: [] })
  },
  graphInfo: {
    type: Object,
    default: () => ({})
  },
  showControls: {
    type: Boolean,
    default: true
  },
  labelField: { 
    type: String, 
    default: 'name' 
  },
  autoFit: { 
    type: Boolean, 
    default: true 
  },
  sizeByDegree: { 
    type: Boolean, 
    default: true 
  },
})

const emit = defineEmits(['ready', 'node-click', 'edge-click', 'canvas-click', 'search'])

const container = ref(null)
const rootEl = ref(null)
const searchKeyword = ref('*')

let graphInstance = null
let resizeObserver = null
let renderTimeout = null

// 颜色方案
const typeColors = {
  'person': '#60a5fa',
  'organization': '#34d399',
  'technology': '#f59e0b',
  'concept': '#a78bfa',
  'location': '#f472b6',
}

const defaultColors = [
  '#60a5fa', '#34d399', '#f59e0b', '#f472b6', '#22d3ee',
  '#a78bfa', '#f97316', '#4ade80', '#f43f5e', '#2dd4bf',
]

// 计算实体类型统计
const entityTypes = computed(() => {
  const types = {}
  for (const node of props.graphData.nodes) {
    const type = node.type || 'unknown'
    types[type] = (types[type] || 0) + 1
  }
  return Object.entries(types)
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count)
})

function getTypeColor(type, index = 0) {
  return typeColors[type] || defaultColors[index % defaultColors.length]
}

// 力导向布局配置 - 优化分散效果
const defaultLayout = {
  type: 'd3-force',
  preventOverlap: true,
  alphaDecay: 0.05,
  alphaMin: 0.001,
  velocityDecay: 0.4,
  iterations: 300,
  force: {
    center: { x: 0.5, y: 0.5, strength: 0.05 },
    charge: { strength: -1200, distanceMin: 50, distanceMax: 1000 },
    link: { distance: 180, strength: 0.3 },
  },
  collide: { radius: 60, strength: 1, iterations: 5 },
}

function formatData() {
  const data = props.graphData || { nodes: [], edges: [] }
  const degrees = new Map()

  for (const n of data.nodes) {
    degrees.set(String(n.id), 0)
  }
  for (const e of data.edges) {
    const s = String(e.source_id)
    const t = String(e.target_id)
    degrees.set(s, (degrees.get(s) || 0) + 1)
    degrees.set(t, (degrees.get(t) || 0) + 1)
  }

  const nodes = (data.nodes || []).map((n, idx) => ({
    id: String(n.id),
    data: {
      label: n[props.labelField] ?? n.name ?? String(n.id),
      degree: degrees.get(String(n.id)) || 0,
      type: n.type || 'unknown',
      typeIndex: entityTypes.value.findIndex(t => t.type === n.type),
      original: n
    },
  }))

  const edges = (data.edges || []).map((e, idx) => ({
    id: e.id ? String(e.id) : `edge-${idx}`,
    source: String(e.source_id),
    target: String(e.target_id),
    data: {
      label: e.type ?? '',
      original: e
    },
  }))

  return { nodes, edges }
}

function initGraph() {
  if (!container.value) return

  const width = container.value.offsetWidth
  const height = container.value.offsetHeight

  if (width === 0 && height === 0) {
    clearTimeout(renderTimeout)
    renderTimeout = setTimeout(initGraph, 200)
    return
  }

  container.value.innerHTML = ''

  if (graphInstance) {
    try { graphInstance.destroy() } catch (e) {}
    graphInstance = null
  }

  graphInstance = new Graph({
    container: container.value,
    width,
    height,
    autoFit: props.autoFit,
    autoResize: true,
    layout: defaultLayout,
    node: {
      type: 'circle',
      style: {
        labelText: (d) => d.data.label,
        labelFill: '#374151',
        labelWordWrap: true,
        labelMaxWidth: '200%',
        size: (d) => {
          if (!props.sizeByDegree) return 24
          const deg = d.data.degree || 0
          return Math.min(18 + deg * 4, 50)
        },
        fill: (d) => {
          const type = d.data.type
          const idx = d.data.typeIndex >= 0 ? d.data.typeIndex : 0
          return getTypeColor(type, idx)
        },
        opacity: 0.9,
        stroke: '#fff',
        lineWidth: 2,
        shadowColor: 'rgba(0,0,0,0.2)',
        shadowBlur: 6,
      },
    },
    edge: {
      type: 'quadratic',
      style: {
        labelText: (d) => d.data.label,
        labelFill: '#6b7280',
        labelBackground: true,
        labelBackgroundFill: '#f3f4f6',
        labelBackgroundRadius: 4,
        stroke: '#9ca3af',
        opacity: 0.7,
        lineWidth: 1.5,
        endArrow: true,
      },
    },
    behaviors: [
      'drag-element',
      'zoom-canvas',
      'drag-canvas',
      'hover-activate',
      {
        type: 'click-select',
        degree: 1,
        state: 'selected',
        neighborState: 'active',
        unselectedState: 'inactive',
        multiple: true,
        trigger: ['shift'],
      }
    ],
  })

  // 绑定事件
  graphInstance.on('node:click', (evt) => {
    const { target } = evt
    const nodeId = target.id
    const nodeData = graphInstance.getNodeData(nodeId)
    emit('node-click', nodeData)
  })

  graphInstance.on('edge:click', (evt) => {
    const { target } = evt
    const edgeId = target.id
    const edgeData = graphInstance.getEdgeData(edgeId)
    emit('edge-click', edgeData)
  })

  graphInstance.on('canvas:click', (evt) => {
    if (!evt.target) {
      emit('canvas-click')
    }
  })

  emit('ready', graphInstance)
}

function setGraphData() {
  if (!graphInstance) initGraph()
  if (!graphInstance) return
  
  const data = formatData()
  graphInstance.setData(data)
  graphInstance.render()

  // 触发布局
  setTimeout(() => {
    try {
      if (graphInstance && graphInstance.layout) {
        graphInstance.layout()
      }
    } catch (error) {
      console.warn('布局失败:', error)
    }
  }, 10)
}

function handleSearch() {
  emit('search', searchKeyword.value)
}

function handleRefresh() {
  refreshGraph()
}

function handleFitView() {
  if (graphInstance) {
    try { graphInstance.fitView() } catch (_) {}
  }
}

function refreshGraph() {
  if (graphInstance) {
    try { graphInstance.destroy() } catch (e) {}
    graphInstance = null
  }
  if (container.value) container.value.innerHTML = ''
  clearTimeout(renderTimeout)
  renderTimeout = setTimeout(() => { initGraph(); setGraphData() }, 300)
}

watch(() => props.graphData, () => {
  clearTimeout(renderTimeout)
  renderTimeout = setTimeout(() => setGraphData(), 50)
}, { deep: true })

onMounted(() => {
  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      if (!container.value || !graphInstance) return
      const width = container.value.offsetWidth
      const height = container.value.offsetHeight
      if (width > 0 && height > 0) {
        graphInstance.changeSize(width, height)
      }
    })
    if (container.value) resizeObserver.observe(container.value)
  }

  clearTimeout(renderTimeout)
  renderTimeout = setTimeout(() => { initGraph(); setGraphData() }, 300)
})

onUnmounted(() => {
  if (resizeObserver && container.value) resizeObserver.unobserve(container.value)
  clearTimeout(renderTimeout)
  try { graphInstance?.destroy() } catch (e) {}
  graphInstance = null
})

defineExpose({
  refreshGraph,
  fitView: handleFitView,
  getInstance: () => graphInstance,
})
</script>

<style scoped>
.graph-canvas-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  overflow: hidden;
}

.graph-canvas {
  width: 100%;
  height: 100%;
}

.graph-overlay {
  position: absolute;
  z-index: 10;
  pointer-events: auto;
}

.graph-overlay.top {
  top: 12px;
  left: 12px;
  right: 12px;
}

.graph-controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 150px;
  max-width: 250px;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  background: white;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.control-btn {
  padding: 8px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.graph-stats-panel {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: flex;
  gap: 16px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  font-size: 13px;
  backdrop-filter: blur(4px);
  z-index: 10;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-label {
  color: #6b7280;
  font-weight: 500;
}

.stat-value {
  color: #111827;
  font-weight: 600;
}

.stat-total {
  color: #9ca3af;
  font-size: 11px;
}

.graph-legend {
  position: absolute;
  bottom: 16px;
  right: 16px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(4px);
  z-index: 10;
  max-width: 180px;
}

.legend-title {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-text {
  color: #374151;
  flex: 1;
}

.legend-count {
  color: #9ca3af;
  font-size: 11px;
}

.graph-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #9ca3af;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 6px;
}

.empty-hint {
  font-size: 13px;
  color: #9ca3af;
}
</style>

