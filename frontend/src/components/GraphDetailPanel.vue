<template>
  <transition name="slide-fade">
    <div class="detail-panel" v-if="visible">
      <div class="panel-header">
        <span class="panel-title">{{ title }}</span>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      
      <div class="panel-content">
        <template v-if="item">
          <!-- 节点详情 -->
          <template v-if="type === 'node'">
            <div class="detail-section">
              <div class="detail-row main-info">
                <span class="detail-icon" :style="{ backgroundColor: getTypeColor(item.data?.type) }">
                  {{ getTypeIcon(item.data?.type) }}
                </span>
                <div class="detail-main">
                  <div class="detail-name">{{ item.data?.label || item.id }}</div>
                  <div class="detail-type">{{ item.data?.type || '未知类型' }}</div>
                </div>
              </div>
            </div>
            
            <div class="detail-section" v-if="item.data?.original?.properties">
              <div class="section-title">属性信息</div>
              <div class="properties-list">
                <div 
                  v-for="(value, key) in filteredProperties" 
                  :key="key"
                  class="property-item"
                >
                  <span class="property-key">{{ key }}</span>
                  <span class="property-value">{{ formatValue(value) }}</span>
                </div>
              </div>
            </div>
            
            <div class="detail-section" v-if="relatedFiles.length > 0">
              <div class="section-title">来源文件</div>
              <div class="files-list">
                <div 
                  v-for="file in relatedFiles" 
                  :key="file"
                  class="file-item"
                >
                  📄 {{ file }}
                </div>
              </div>
            </div>
          </template>
          
          <!-- 边详情 -->
          <template v-else-if="type === 'edge'">
            <div class="detail-section">
              <div class="detail-row edge-info">
                <div class="edge-label">{{ item.data?.label || '关联' }}</div>
                <div class="edge-direction">
                  <span class="edge-node">{{ getSourceLabel() }}</span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-node">{{ getTargetLabel() }}</span>
                </div>
              </div>
            </div>
            
            <div class="detail-section" v-if="item.data?.original?.properties">
              <div class="section-title">关系属性</div>
              <div class="properties-list">
                <div 
                  v-for="(value, key) in filteredEdgeProperties" 
                  :key="key"
                  class="property-item"
                >
                  <span class="property-key">{{ key }}</span>
                  <span class="property-value">{{ formatValue(value) }}</span>
                </div>
              </div>
            </div>
          </template>
        </template>
        
        <div v-else class="no-selection">
          <div class="no-selection-icon">👆</div>
          <div class="no-selection-text">点击节点或边查看详情</div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: Boolean,
  item: Object,
  type: String, // 'node' | 'edge'
  graphData: {
    type: Object,
    default: () => ({ nodes: [], edges: [] })
  }
})

defineEmits(['close'])

// 类型颜色映射
const typeColors = {
  'person': '#60a5fa',
  'organization': '#34d399',
  'technology': '#f59e0b',
  'concept': '#a78bfa',
  'location': '#f472b6',
}

// 类型图标映射
const typeIcons = {
  'person': '👤',
  'organization': '🏢',
  'technology': '⚙️',
  'concept': '💡',
  'location': '📍',
}

const title = computed(() => {
  return props.type === 'node' ? '节点详情' : '关系详情'
})

function getTypeColor(type) {
  return typeColors[type] || '#9ca3af'
}

function getTypeIcon(type) {
  return typeIcons[type] || '📎'
}

// 过滤节点属性
const filteredProperties = computed(() => {
  if (!props.item?.data?.original?.properties) return {}
  
  const properties = props.item.data.original.properties
  const hidden = ['id', 'label', 'type', 'files', 'embedding']
  const result = {}
  
  Object.keys(properties).forEach(key => {
    if (!hidden.includes(key)) {
      result[key] = properties[key]
    }
  })
  
  return result
})

// 过滤边属性
const filteredEdgeProperties = computed(() => {
  if (!props.item?.data?.original?.properties) return {}
  
  const properties = props.item.data.original.properties
  const hidden = ['source_id', 'target_id', '_id', 'id']
  const result = {}
  
  Object.keys(properties).forEach(key => {
    if (!hidden.includes(key)) {
      result[key] = properties[key]
    }
  })
  
  return result
})

// 相关文件
const relatedFiles = computed(() => {
  const files = props.item?.data?.original?.properties?.files
  if (Array.isArray(files)) return files
  return []
})

function formatValue(value) {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

function getSourceLabel() {
  if (!props.item) return '?'
  const sourceId = props.item.source
  const node = props.graphData.nodes?.find(n => n.id === sourceId)
  return node?.name || node?.data?.label || sourceId
}

function getTargetLabel() {
  if (!props.item) return '?'
  const targetId = props.item.target
  const node = props.graphData.nodes?.find(n => n.id === targetId)
  return node?.name || node?.data?.label || targetId
}
</script>

<style scoped>
.detail-panel {
  position: absolute;
  top: 60px;
  right: 16px;
  width: 280px;
  max-height: calc(100% - 80px);
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  z-index: 100;
  backdrop-filter: blur(8px);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid #f3f4f6;
  background: #f9fafb;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.close-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.panel-content {
  padding: 12px;
  overflow-y: auto;
  max-height: 400px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.main-info {
  padding: 8px;
  background: #f9fafb;
  border-radius: 8px;
}

.detail-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.detail-main {
  flex: 1;
  min-width: 0;
}

.detail-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  word-break: break-word;
}

.detail-type {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.properties-list {
  background: #f9fafb;
  border-radius: 8px;
  padding: 8px;
}

.property-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 12px;
}

.property-item:last-child {
  border-bottom: none;
}

.property-key {
  color: #6b7280;
  font-weight: 500;
}

.property-value {
  color: #111827;
  text-align: right;
  max-width: 60%;
  word-break: break-word;
}

.files-list {
  background: #f9fafb;
  border-radius: 8px;
  padding: 8px;
}

.file-item {
  font-size: 12px;
  color: #374151;
  padding: 4px 0;
}

.edge-info {
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  background: #f9fafb;
  border-radius: 8px;
}

.edge-label {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.edge-direction {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.edge-node {
  padding: 4px 8px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  color: #374151;
}

.edge-arrow {
  color: #9ca3af;
  font-weight: bold;
}

.no-selection {
  text-align: center;
  padding: 24px;
  color: #9ca3af;
}

.no-selection-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.no-selection-text {
  font-size: 13px;
}

/* 动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>

