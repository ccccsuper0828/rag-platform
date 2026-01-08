<template>
  <div class="pdf-parallel-container">
    <!-- Left: PDF Viewer -->
    <div class="pdf-panel" :style="{ width: splitPosition + '%' }">
      <div class="pdf-toolbar">
        <div class="toolbar-left">
          <button class="tool-btn" @click="zoomOut" title="缩小">
            <span>➖</span>
          </button>
          <span class="zoom-level">{{ Math.round(scale * 100) }}%</span>
          <button class="tool-btn" @click="zoomIn" title="放大">
            <span>➕</span>
          </button>
          <button class="tool-btn" @click="fitToWidth" title="适应宽度">
            <span>↔️</span>
          </button>
        </div>
        <div class="toolbar-center">
          <button class="tool-btn" @click="prevPage" :disabled="currentPage <= 1">
            <span>◀</span>
          </button>
          <span class="page-info">
            <input 
              type="number" 
              v-model.number="pageInput" 
              @change="goToPage"
              class="page-input"
              min="1"
              :max="totalPages"
            />
            / {{ totalPages }}
          </span>
          <button class="tool-btn" @click="nextPage" :disabled="currentPage >= totalPages">
            <span>▶</span>
          </button>
        </div>
        <div class="toolbar-right">
          <div class="search-box">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="搜索文档..."
              @keyup.enter="searchInPdf"
              class="search-input"
            />
            <button class="tool-btn" @click="searchInPdf" title="搜索">
              <span>🔍</span>
            </button>
          </div>
        </div>
      </div>
      
      <div class="pdf-content" ref="pdfContainer" @scroll="onScroll">
        <!-- PDF View -->
        <div v-if="isPdf" class="pdf-pages">
          <div 
            v-for="pageNum in totalPages" 
            :key="pageNum"
            class="pdf-page-wrapper"
            :ref="el => pageRefs[pageNum] = el"
          >
            <canvas 
              :ref="el => canvasRefs[pageNum] = el"
              class="pdf-canvas"
            ></canvas>
            <!-- Highlight overlays -->
            <div 
              v-for="highlight in getPageHighlights(pageNum)" 
              :key="highlight.id"
              class="highlight-overlay"
              :class="highlight.type"
              :style="getHighlightStyle(highlight)"
              @click="onHighlightClick(highlight)"
            >
              <span v-if="highlight.citation" class="citation-badge">
                [^{{ highlight.citation }}]
              </span>
            </div>
            <!-- Search result highlights -->
            <div 
              v-for="(result, idx) in getPageSearchResults(pageNum)" 
              :key="'search-' + idx"
              class="search-highlight"
              :style="result.style"
            ></div>
          </div>
        </div>
        
        <!-- Text Document View -->
        <div v-else class="text-document-view">
          <div class="document-header">
            <h3>{{ documentName || '文档内容' }}</h3>
          </div>
          <div 
            class="document-content" 
            ref="textContentRef"
            @mouseup="handleTextSelection"
          >
            <pre v-if="documentType === 'text'" class="text-content">{{ documentContent }}</pre>
            <div v-else class="markdown-content" v-html="renderedMarkdown"></div>
          </div>
        </div>
      </div>
      
      <!-- Minimap / Thumbnail -->
      <div class="pdf-minimap" v-if="showMinimap">
        <div 
          v-for="pageNum in totalPages" 
          :key="'thumb-' + pageNum"
          class="minimap-page"
          :class="{ active: currentPage === pageNum }"
          @click="goToPageDirect(pageNum)"
        >
          {{ pageNum }}
        </div>
      </div>
    </div>
    
    <!-- Resizer -->
    <div 
      class="panel-resizer" 
      @mousedown="startResize"
    ></div>
    
    <!-- Right: AI Chat -->
    <div class="chat-panel" :style="{ width: (100 - splitPosition) + '%' }">
      <div class="chat-header">
        <h3>🤖 AI 研究助手</h3>
        <div class="chat-options">
          <div class="response-mode-selector">
            <button 
              v-for="mode in responseModes" 
              :key="mode.value"
              class="mode-btn"
              :class="{ active: responseMode === mode.value }"
              @click="responseMode = mode.value"
              :title="mode.description"
            >
              {{ mode.icon }} {{ mode.label }}
            </button>
          </div>
          <label class="web-search-toggle" :title="enableWebSearch ? '点击关闭网络搜索' : '点击开启网络搜索'">
            <input type="checkbox" v-model="enableWebSearch" />
            <span class="toggle-label">🌐 网络搜索</span>
          </label>
        </div>
      </div>
      
      <div class="chat-messages" ref="chatContainer">
        <div 
          v-for="(msg, idx) in messages" 
          :key="idx"
          class="message"
          :class="msg.role"
        >
          <div class="message-avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div 
              v-html="renderMessageContent(msg.content, msg.citations)"
              @click="handleCitationClick($event, msg)"
            ></div>
            <!-- Evidence section -->
            <div v-if="msg.citations && msg.citations.length > 0" class="evidence-section">
              <div class="evidence-header" @click="toggleEvidence(idx)">
                <span>📚 引用来源 ({{ msg.citations.length }})</span>
                <span class="toggle-icon">{{ expandedEvidence[idx] ? '▼' : '▶' }}</span>
              </div>
              <div v-if="expandedEvidence[idx]" class="evidence-list">
                <div 
                  v-for="citation in msg.citations" 
                  :key="citation.key"
                  class="evidence-item"
                  @click="scrollToCitation(citation)"
                >
                  <span class="cite-key">[^{{ citation.key }}]</span>
                  <span class="cite-text">"{{ citation.reference }}"</span>
                  <span v-if="citation.page" class="cite-page">p.{{ citation.page }}</span>
                </div>
              </div>
            </div>
            
            <!-- Spark (光源值) Display -->
            <div v-if="msg.spark && msg.role === 'assistant'" class="spark-badge-container">
              <div 
                class="spark-badge" 
                :class="getSparkClass(msg.spark.spark_value)"
                @click="toggleSparkDetail(idx)"
                :title="`光源值: ${msg.spark.spark_value}`"
              >
                <span class="spark-icon">✨</span>
                <span class="spark-value">{{ msg.spark.spark_value.toFixed(1) }}</span>
                <span v-if="msg.spark.nft_eligible" class="nft-badge">NFT</span>
              </div>
              
              <!-- Spark Detail Popup -->
              <div v-if="expandedSpark[idx]" class="spark-detail-popup">
                <div class="spark-detail-header">
                  <span class="spark-detail-title">🔥 光源详情</span>
                  <button class="close-btn" @click.stop="toggleSparkDetail(idx)">×</button>
                </div>
                <div class="spark-detail-body">
                  <div class="spark-score-item">
                    <span class="score-label">📝 基础质量</span>
                    <div class="score-bar">
                      <div class="score-fill" :style="{ width: (msg.spark.scores.base / 30 * 100) + '%' }"></div>
                    </div>
                    <span class="score-value">{{ msg.spark.scores.base.toFixed(1) }}/30</span>
                  </div>
                  <div class="spark-score-item">
                    <span class="score-label">🔗 引用关系</span>
                    <div class="score-bar">
                      <div class="score-fill" :style="{ width: (msg.spark.scores.citation / 25 * 100) + '%' }"></div>
                    </div>
                    <span class="score-value">{{ msg.spark.scores.citation.toFixed(1) }}/25</span>
                  </div>
                  <div class="spark-score-item">
                    <span class="score-label">💡 知识激活</span>
                    <div class="score-bar">
                      <div class="score-fill" :style="{ width: (msg.spark.scores.activation / 20 * 100) + '%' }"></div>
                    </div>
                    <span class="score-value">{{ msg.spark.scores.activation.toFixed(1) }}/20</span>
                  </div>
                  <div class="spark-score-item">
                    <span class="score-label">👥 用户行为</span>
                    <div class="score-bar">
                      <div class="score-fill" :style="{ width: (msg.spark.scores.behavior / 25 * 100) + '%' }"></div>
                    </div>
                    <span class="score-value">{{ msg.spark.scores.behavior.toFixed(1) }}/25</span>
                  </div>
                </div>
                <div v-if="msg.spark.nft_eligible" class="nft-eligible-banner">
                  🎉 恭喜！此对话已达到 NFT 铸造资格
                </div>
                
                <!-- Action Buttons in Popup -->
                <div class="spark-actions">
                  <button 
                    class="spark-action-btn like-btn"
                    :class="{ active: msg.liked }"
                    @click.stop="handleLike(idx, msg.spark.conversation_id)"
                  >
                    <span>{{ msg.liked ? '❤️' : '🤍' }}</span>
                    <span class="action-count">{{ msg.likeCount || 0 }}</span>
                  </button>
                  <button 
                    class="spark-action-btn save-btn"
                    :class="{ active: msg.saved }"
                    @click.stop="handleSave(idx, msg.spark.conversation_id)"
                  >
                    <span>{{ msg.saved ? '⭐' : '☆' }}</span>
                    <span class="action-count">{{ msg.saveCount || 0 }}</span>
                  </button>
                  <button 
                    class="spark-action-btn share-btn"
                    @click.stop="handleShare(idx, msg.spark.conversation_id)"
                  >
                    <span>📤</span>
                    <span class="action-count">{{ msg.shareCount || 0 }}</span>
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Quick Action Bar (visible without popup) -->
            <div v-if="msg.spark && msg.role === 'assistant'" class="quick-action-bar">
              <button 
                class="quick-action like"
                :class="{ active: msg.liked }"
                @click="handleLike(idx, msg.spark.conversation_id)"
                :title="msg.liked ? '已点赞' : '点赞'"
              >
                {{ msg.liked ? '❤️' : '🤍' }} {{ msg.likeCount || 0 }}
              </button>
              <button 
                class="quick-action save"
                :class="{ active: msg.saved }"
                @click="handleSave(idx, msg.spark.conversation_id)"
                :title="msg.saved ? '已收藏' : '收藏'"
              >
                {{ msg.saved ? '⭐' : '☆' }} {{ msg.saveCount || 0 }}
              </button>
              <button 
                class="quick-action share"
                @click="handleShare(idx, msg.spark.conversation_id)"
                title="分享"
              >
                📤 {{ msg.shareCount || 0 }}
              </button>
            </div>
          </div>
        </div>
        
        <!-- Streaming message -->
        <div v-if="isStreaming" class="message assistant streaming">
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div v-html="renderMessageContent(streamingContent, [])"></div>
            <span class="typing-indicator">●●●</span>
          </div>
        </div>
        
        <!-- Status message -->
        <div v-if="statusMessage" class="status-message">
          <span class="status-icon">⏳</span>
          {{ statusMessage }}
        </div>
      </div>
      
      <div class="chat-input-area">
        <div class="input-actions">
          <button 
            class="action-btn"
            @click="addSelectedTextAsContext"
            :disabled="!selectedText"
            title="添加选中文本作为上下文"
          >
            📝 引用选中
          </button>
        </div>
        <div class="input-wrapper">
          <textarea 
            v-model="userInput"
            @keydown.enter.exact.prevent="sendMessage"
            placeholder="输入问题，AI 将基于文档回答并提供引用..."
            rows="3"
            class="chat-input"
          ></textarea>
          <button 
            class="send-btn"
            @click="sendMessage"
            :disabled="!userInput.trim() || isStreaming"
          >
            {{ isStreaming ? '⏳' : '📤' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick, shallowRef, toRaw } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'

// Props
const props = defineProps({
  pdfUrl: { type: String, default: '' },
  documentContent: { type: String, default: '' },
  documentType: { type: String, default: 'text' }, // 'pdf', 'text', 'markdown'
  documentName: { type: String, default: '' },
  ragId: { type: String, required: true },
  authToken: { type: String, required: true },
  isOwner: { type: Boolean, default: false }
})

// Computed
const isPdf = computed(() => props.documentType === 'pdf' && props.pdfUrl)
const isTextDocument = computed(() => !isPdf.value)

const emit = defineEmits(['citation-click', 'highlight-added'])

// Text Document State
const textContentRef = ref(null)
const renderedMarkdown = computed(() => {
  if (props.documentType === 'markdown' && props.documentContent) {
    // Simple markdown rendering (can be enhanced with a library)
    return props.documentContent
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>')
  }
  return ''
})

const handleTextSelection = () => {
  const selection = window.getSelection()
  if (selection && selection.toString().trim()) {
    selectedText.value = selection.toString().trim()
  }
}

// PDF State
const pdfContainer = ref(null)
const canvasRefs = ref({})
const pageRefs = ref({})
// Use shallowRef to avoid Vue's deep reactive proxy interfering with pdfjs internal objects
const pdfDoc = shallowRef(null)
const currentPage = ref(1)
const pageInput = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)
const showMinimap = ref(true)
const searchQuery = ref('')
const searchResults = ref([])
const highlights = ref([])
const selectedText = ref('')

// Chat State
const chatContainer = ref(null)
const messages = ref([])
const userInput = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const statusMessage = ref('')
const expandedEvidence = ref({})

// Spark (光源) State
const currentSpark = ref(null)  // 当前对话的光源值
const showSparkDetail = ref(false)  // 是否显示光源详情
const expandedSpark = ref({})  // 展开的光源详情索引

// Response Mode
const responseMode = ref('normal')
const responseModes = [
  { value: 'concise', label: '简洁', icon: '⚡', description: '简短直接的回答' },
  { value: 'normal', label: '标准', icon: '📝', description: '平衡的回答风格' },
  { value: 'detailed', label: '详细', icon: '📚', description: '深入全面的分析' }
]

// Web Search Toggle
const enableWebSearch = ref(false)
const webSearchResults = ref([])

// Layout State
const splitPosition = ref(55)
const isResizing = ref(false)

// API Base
const API_BASE = ''

// Initialize based on document type
onMounted(async () => {
  if (isPdf.value) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.mjs'
    await loadPdf()
  }
  // Text documents don't need special initialization
})

// Load PDF
const loadPdf = async () => {
  try {
    console.log('Loading PDF from:', props.pdfUrl)
    
    // Fetch PDF with Authorization header
    const response = await fetch(props.pdfUrl, {
      headers: {
        'Authorization': `Bearer ${props.authToken}`
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    // Get ArrayBuffer and convert to typed array
    const arrayBuffer = await response.arrayBuffer()
    const typedArray = new Uint8Array(arrayBuffer)
    
    console.log('PDF data size:', typedArray.length, 'bytes')
    
    // Load PDF with typed array directly (more compatible)
    const loadingTask = pdfjsLib.getDocument({
      data: typedArray,
      cMapUrl: '/cmaps/',
      cMapPacked: true
    })
    
    pdfDoc.value = await loadingTask.promise
    totalPages.value = pdfDoc.value.numPages
    pageInput.value = 1
    
    console.log(`PDF loaded: ${totalPages.value} pages`)
    
    // Wait for Vue to render the canvas elements
    await nextTick()
    
    // Render all pages
    for (let i = 1; i <= totalPages.value; i++) {
      await renderPage(i)
    }
    console.log(`PDF rendered successfully: ${totalPages.value} pages`)
  } catch (error) {
    console.error('Failed to load PDF:', error)
  }
}

// Render single page
const renderPage = async (pageNum) => {
  if (!pdfDoc.value) return
  
  const page = await pdfDoc.value.getPage(pageNum)
  const canvas = canvasRefs.value[pageNum]
  if (!canvas) return
  
  const viewport = page.getViewport({ scale: scale.value })
  canvas.width = viewport.width
  canvas.height = viewport.height
  
  const context = canvas.getContext('2d')
  await page.render({
    canvasContext: context,
    viewport: viewport
  }).promise
}

// Re-render all pages when scale changes
watch(scale, async () => {
  for (let i = 1; i <= totalPages.value; i++) {
    await renderPage(i)
  }
})

// Navigation
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    pageInput.value = currentPage.value
    scrollToPage(currentPage.value)
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    pageInput.value = currentPage.value
    scrollToPage(currentPage.value)
  }
}

const goToPage = () => {
  const page = Math.max(1, Math.min(pageInput.value, totalPages.value))
  currentPage.value = page
  pageInput.value = page
  scrollToPage(page)
}

const goToPageDirect = (page) => {
  currentPage.value = page
  pageInput.value = page
  scrollToPage(page)
}

const scrollToPage = (pageNum) => {
  const pageEl = pageRefs.value[pageNum]
  if (pageEl) {
    pageEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// Zoom controls
const zoomIn = () => { scale.value = Math.min(scale.value + 0.25, 3.0) }
const zoomOut = () => { scale.value = Math.max(scale.value - 0.25, 0.5) }
const fitToWidth = () => {
  if (pdfContainer.value) {
    const containerWidth = pdfContainer.value.clientWidth - 40
    // Estimate based on typical PDF width
    scale.value = containerWidth / 612 // Letter size width in points
  }
}

// Search in PDF
const searchInPdf = async () => {
  if (!searchQuery.value.trim() || !pdfDoc.value) return
  
  searchResults.value = []
  const query = searchQuery.value.toLowerCase()
  
  for (let i = 1; i <= totalPages.value; i++) {
    const page = await pdfDoc.value.getPage(i)
    const textContent = await page.getTextContent()
    
    textContent.items.forEach((item, idx) => {
      if (item.str.toLowerCase().includes(query)) {
        searchResults.value.push({
          page: i,
          text: item.str,
          transform: item.transform,
          width: item.width,
          height: item.height
        })
      }
    })
  }
  
  // Jump to first result
  if (searchResults.value.length > 0) {
    goToPageDirect(searchResults.value[0].page)
  }
}

// Get highlights for specific page
const getPageHighlights = (pageNum) => {
  return highlights.value.filter(h => h.page === pageNum)
}

const getPageSearchResults = (pageNum) => {
  return searchResults.value
    .filter(r => r.page === pageNum)
    .map(r => ({
      style: {
        left: r.transform[4] * scale.value + 'px',
        top: (r.transform[5] - r.height) * scale.value + 'px',
        width: r.width * scale.value + 'px',
        height: r.height * scale.value + 'px'
      }
    }))
}

const getHighlightStyle = (highlight) => {
  return {
    left: highlight.x + '%',
    top: highlight.y + '%',
    width: highlight.width + '%',
    height: highlight.height + '%'
  }
}

// Handle scroll to detect current page
const onScroll = () => {
  if (!pdfContainer.value) return
  
  const containerTop = pdfContainer.value.scrollTop
  const containerHeight = pdfContainer.value.clientHeight
  
  for (let i = 1; i <= totalPages.value; i++) {
    const pageEl = pageRefs.value[i]
    if (pageEl) {
      const rect = pageEl.getBoundingClientRect()
      const containerRect = pdfContainer.value.getBoundingClientRect()
      
      if (rect.top <= containerRect.top + containerHeight / 2 && rect.bottom >= containerRect.top) {
        if (currentPage.value !== i) {
          currentPage.value = i
          pageInput.value = i
        }
        break
      }
    }
  }
}

// Panel resizing
const startResize = (e) => {
  isResizing.value = true
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
}

const onResize = (e) => {
  if (!isResizing.value) return
  const container = document.querySelector('.pdf-parallel-container')
  if (!container) return
  
  const rect = container.getBoundingClientRect()
  const newPosition = ((e.clientX - rect.left) / rect.width) * 100
  splitPosition.value = Math.max(30, Math.min(70, newPosition))
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

// Chat functionality
const sendMessage = async () => {
  if (!userInput.value.trim() || isStreaming.value) return
  
  const question = userInput.value.trim()
  userInput.value = ''
  
  // Add user message
  messages.value.push({
    role: 'user',
    content: question,
    citations: []
  })
  
  // Scroll to bottom
  await nextTick()
  scrollChatToBottom()
  
  // Start streaming response
  isStreaming.value = true
  streamingContent.value = ''
  statusMessage.value = '正在分析文档...'
  
  try {
    const response = await fetch(`${API_BASE}/v1/rag/${props.ragId}/chat-with-citations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${props.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question: question,
        response_mode: responseMode.value,
        include_citations: true,
        enable_web_search: enableWebSearch.value
      })
    })
    
    if (!response.ok) {
      throw new Error('Chat request failed')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''
    let citations = []
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          
          try {
            const parsed = JSON.parse(data)
            if (parsed.type === 'content') {
              fullContent += parsed.text
              streamingContent.value = fullContent
            } else if (parsed.type === 'citation') {
              citations.push(parsed.citation)
            } else if (parsed.type === 'web_source') {
              webSearchResults.value.push(parsed.source)
            } else if (parsed.type === 'status') {
              statusMessage.value = parsed.message
            } else if (parsed.type === 'error') {
              console.error('Server error:', parsed.message)
            } else if (parsed.type === 'spark') {
              // 处理光源值事件
              currentSpark.value = parsed.data
            }
          } catch (e) {
            // Plain text chunk
            fullContent += data
            streamingContent.value = fullContent
          }
        }
      }
    }
    
    // Finalize message
    messages.value.push({
      role: 'assistant',
      content: fullContent,
      citations: citations,
      spark: currentSpark.value  // 保存光源值到消息
    })
    
    // Add highlights for citations
    addCitationHighlights(citations)
    
  } catch (error) {
    console.error('Chat error:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，处理您的问题时出现错误。请重试。',
      citations: []
    })
  } finally {
    isStreaming.value = false
    streamingContent.value = ''
    statusMessage.value = ''
    currentSpark.value = null  // 重置光源值
    await nextTick()
    scrollChatToBottom()
  }
}

// Add highlights based on citations
const addCitationHighlights = (citations) => {
  citations.forEach(citation => {
    if (citation.page && citation.position) {
      highlights.value.push({
        id: `cite-${citation.key}`,
        page: citation.page,
        x: citation.position.x || 10,
        y: citation.position.y || 10,
        width: citation.position.width || 80,
        height: citation.position.height || 5,
        citation: citation.key,
        type: 'citation',
        reference: citation.reference
      })
    }
  })
}

// Render message with clickable citations
const renderMessageContent = (content, citations) => {
  if (!content) return ''
  
  // Replace [^n] with clickable links
  let rendered = content.replace(/\[\^(\d+)\]/g, (match, key) => {
    return `<a href="#" class="citation-link" data-citation="${key}">[^${key}]</a>`
  })
  
  // Basic markdown rendering
  rendered = rendered
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
  
  return rendered
}

// Handle citation click
const handleCitationClick = (event, msg) => {
  const link = event.target.closest('.citation-link')
  if (!link) return
  
  event.preventDefault()
  const key = link.dataset.citation
  const citation = msg.citations?.find(c => String(c.key) === key)
  
  if (citation) {
    scrollToCitation(citation)
  }
}

// Scroll to citation in PDF
const scrollToCitation = (citation) => {
  if (citation.page) {
    goToPageDirect(citation.page)
    
    // Highlight the citation temporarily
    const existingHighlight = highlights.value.find(h => h.citation === citation.key)
    if (existingHighlight) {
      existingHighlight.flash = true
      setTimeout(() => {
        existingHighlight.flash = false
      }, 2000)
    }
  }
  
  emit('citation-click', citation)
}

// Toggle evidence section
const toggleEvidence = (msgIdx) => {
  expandedEvidence.value[msgIdx] = !expandedEvidence.value[msgIdx]
}

// Toggle spark detail popup
const toggleSparkDetail = (msgIdx) => {
  expandedSpark.value[msgIdx] = !expandedSpark.value[msgIdx]
}

// Get spark badge class based on value
const getSparkClass = (value) => {
  if (value >= 80) return 'spark-legendary'    // 紫色 - 传说级
  if (value >= 70) return 'spark-epic'         // 金色 - 史诗级 (NFT eligible)
  if (value >= 50) return 'spark-rare'         // 蓝色 - 稀有级
  if (value >= 30) return 'spark-common'       // 绿色 - 普通级
  return 'spark-basic'                          // 灰色 - 基础级
}

// Handle like action
const handleLike = async (msgIdx, conversationId) => {
  if (!conversationId) return
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE}/v1/spark/conversation/${conversationId}/like`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      // Update message state
      const msg = messages.value[msgIdx]
      if (msg) {
        msg.liked = true
        msg.likeCount = result.like_count
        // Update spark value
        if (msg.spark) {
          msg.spark.spark_value = result.new_spark_value
          msg.spark.nft_eligible = result.nft_eligible
        }
      }
    }
  } catch (error) {
    console.error('Like error:', error)
  }
}

// Handle save/bookmark action
const handleSave = async (msgIdx, conversationId) => {
  if (!conversationId) return
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE}/v1/spark/conversation/${conversationId}/save`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      const msg = messages.value[msgIdx]
      if (msg) {
        msg.saved = true
        msg.saveCount = result.save_count
        if (msg.spark) {
          msg.spark.spark_value = result.new_spark_value
          msg.spark.nft_eligible = result.nft_eligible
        }
      }
    }
  } catch (error) {
    console.error('Save error:', error)
  }
}

// Handle share action
const handleShare = async (msgIdx, conversationId) => {
  if (!conversationId) return
  
  try {
    const token = localStorage.getItem('token')
    
    // Copy share link to clipboard
    const shareUrl = `${window.location.origin}/conversation/${conversationId}`
    await navigator.clipboard.writeText(shareUrl)
    
    // Call share API
    const response = await fetch(`${API_BASE}/v1/spark/conversation/${conversationId}/share`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      const msg = messages.value[msgIdx]
      if (msg) {
        msg.shareCount = result.share_count
        if (msg.spark) {
          msg.spark.spark_value = result.new_spark_value
          msg.spark.nft_eligible = result.nft_eligible
        }
      }
      // Show success notification
      alert('分享链接已复制到剪贴板！')
    }
  } catch (error) {
    console.error('Share error:', error)
  }
}

// Add selected text as context
const addSelectedTextAsContext = () => {
  if (selectedText.value) {
    userInput.value += `\n\n[引用内容]:\n"${selectedText.value}"\n\n`
    selectedText.value = ''
  }
}

// Scroll chat to bottom
const scrollChatToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// Handle highlight click
const onHighlightClick = (highlight) => {
  if (highlight.citation) {
    // Find the message with this citation
    for (const msg of messages.value) {
      const citation = msg.citations?.find(c => c.key === highlight.citation)
      if (citation) {
        // Scroll to the message in chat
        break
      }
    }
  }
}

// Cleanup
onUnmounted(() => {
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style scoped>
.pdf-parallel-container {
  display: flex;
  height: 100%;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

/* PDF Panel */
.pdf-panel {
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
}

.pdf-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
}

.toolbar-left, .toolbar-center, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.tool-btn:hover:not(:disabled) {
  background: var(--accent-light);
  border-color: var(--accent-color);
}

.tool-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.zoom-level {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 45px;
  text-align: center;
}

.page-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-primary);
}

.page-input {
  width: 50px;
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  text-align: center;
  font-size: 13px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 4px;
}

.search-input {
  width: 150px;
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

/* PDF Content */
.pdf-content {
  flex: 1;
  overflow: auto;
  padding: 16px;
  background: #525659;
}

.pdf-pages {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* Text Document View */
.text-document-view {
  background: white;
  border-radius: 8px;
  margin: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.document-header {
  padding: 16px 20px;
  background: var(--bg-secondary, #f5f5f5);
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.document-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.document-content {
  padding: 20px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.text-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  margin: 0;
  background: transparent;
}

.markdown-content {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}

.markdown-content h1 {
  font-size: 24px;
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.markdown-content h2 {
  font-size: 20px;
  margin: 20px 0 12px;
}

.markdown-content h3 {
  font-size: 16px;
  margin: 16px 0 8px;
}

.markdown-content code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.pdf-page-wrapper {
  position: relative;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.pdf-canvas {
  display: block;
}

/* Highlight overlays */
.highlight-overlay {
  position: absolute;
  cursor: pointer;
  transition: all 0.2s;
}

.highlight-overlay.citation {
  background: rgba(255, 235, 59, 0.4);
  border: 2px solid #ffc107;
  border-radius: 2px;
}

.highlight-overlay:hover {
  background: rgba(255, 235, 59, 0.6);
}

.citation-badge {
  position: absolute;
  top: -20px;
  left: 0;
  background: #ffc107;
  color: #000;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.search-highlight {
  position: absolute;
  background: rgba(255, 152, 0, 0.4);
  border: 1px solid #ff9800;
  pointer-events: none;
}

/* Minimap */
.pdf-minimap {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 8px;
  background: var(--bg-tertiary);
  border-top: 1px solid var(--border-color);
  max-height: 80px;
  overflow-y: auto;
}

.minimap-page {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.minimap-page.active {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}

.minimap-page:hover:not(.active) {
  background: var(--accent-light);
}

/* Panel Resizer */
.panel-resizer {
  width: 6px;
  background: var(--bg-tertiary);
  cursor: col-resize;
  transition: background 0.2s;
}

.panel-resizer:hover {
  background: var(--accent-color);
}

/* Chat Panel */
.chat-panel {
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.response-mode-selector {
  display: flex;
  gap: 4px;
  background: var(--bg-tertiary);
  padding: 4px;
  border-radius: var(--radius-md);
}

.mode-btn {
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.mode-btn.active {
  background: var(--bg-secondary);
  color: var(--accent-color);
  font-weight: 600;
}

.mode-btn:hover:not(.active) {
  background: var(--bg-primary);
}

.chat-options {
  display: flex;
  align-items: center;
  gap: 12px;
}

.web-search-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  transition: all 0.2s;
}

.web-search-toggle:hover {
  background: var(--bg-primary);
}

.web-search-toggle input[type="checkbox"] {
  accent-color: var(--accent-color);
  width: 14px;
  height: 14px;
  cursor: pointer;
}

.web-search-toggle .toggle-label {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.web-search-toggle:has(input:checked) .toggle-label {
  color: var(--accent-color);
  font-weight: 600;
}

/* Chat Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 90%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: var(--accent-color);
}

.message-content {
  background: var(--bg-secondary);
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.message.user .message-content {
  background: var(--accent-color);
  color: white;
}

.message-content :deep(.citation-link) {
  color: var(--accent-color);
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
}

.message-content :deep(.citation-link:hover) {
  text-decoration: underline;
}

.message.user .message-content :deep(.citation-link) {
  color: #fff3e0;
}

/* Evidence Section */
.evidence-section {
  margin-top: 12px;
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
}

.evidence-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.toggle-icon {
  font-size: 10px;
}

.evidence-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.evidence-item {
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
}

.evidence-item:hover {
  background: var(--accent-light);
}

.cite-key {
  color: var(--accent-color);
  font-weight: 600;
  margin-right: 8px;
}

.cite-text {
  color: var(--text-secondary);
  font-style: italic;
}

.cite-page {
  color: var(--text-tertiary);
  font-size: 11px;
  margin-left: 8px;
}

/* Spark (光源值) Styles */
.spark-badge-container {
  position: relative;
  display: inline-block;
  margin-top: 12px;
}

.spark-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.spark-badge:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.spark-icon {
  font-size: 14px;
}

.spark-value {
  font-family: 'JetBrains Mono', monospace;
}

.nft-badge {
  background: linear-gradient(135deg, #ff6b6b 0%, #ffc107 100%);
  color: white;
  font-size: 9px;
  padding: 2px 5px;
  border-radius: 4px;
  margin-left: 4px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* Spark Level Colors */
.spark-basic {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
}

.spark-common {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
}

.spark-rare {
  background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
  color: white;
}

.spark-epic {
  background: linear-gradient(135deg, #fd7e14 0%, #ffc107 100%);
  color: white;
  animation: sparkGlow 2s ease-in-out infinite;
}

.spark-legendary {
  background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%);
  color: white;
  animation: sparkGlow 1.5s ease-in-out infinite;
}

@keyframes sparkGlow {
  0%, 100% { box-shadow: 0 0 8px rgba(255, 193, 7, 0.4); }
  50% { box-shadow: 0 0 16px rgba(255, 193, 7, 0.8); }
}

/* Spark Detail Popup */
.spark-detail-popup {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 8px;
  width: 280px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  z-index: 100;
  overflow: hidden;
}

.spark-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-secondary) 100%);
  color: white;
}

.spark-detail-title {
  font-weight: 600;
  font-size: 14px;
}

.spark-detail-header .close-btn {
  background: transparent;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  opacity: 0.8;
}

.spark-detail-header .close-btn:hover {
  opacity: 1;
}

.spark-detail-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.spark-score-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-label {
  flex: 0 0 80px;
  font-size: 12px;
  color: var(--text-secondary);
}

.score-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-color) 0%, var(--accent-secondary) 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.score-value {
  flex: 0 0 50px;
  font-size: 11px;
  color: var(--text-tertiary);
  text-align: right;
  font-family: 'JetBrains Mono', monospace;
}

.nft-eligible-banner {
  margin-top: 8px;
  padding: 12px;
  background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
  color: #e65100;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

/* Spark Action Buttons */
.spark-actions {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.spark-action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.spark-action-btn:hover {
  background: var(--accent-light);
  border-color: var(--accent-color);
}

.spark-action-btn.active {
  background: var(--accent-light);
  border-color: var(--accent-color);
}

.spark-action-btn .action-count {
  font-weight: 600;
  color: var(--text-secondary);
}

/* Quick Action Bar (below message) */
.quick-action-bar {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border-color);
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: transparent;
  border: none;
  font-size: 12px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: var(--radius-sm);
}

.quick-action:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.quick-action.active {
  color: var(--accent-color);
}

.quick-action.like:hover,
.quick-action.like.active {
  color: #e91e63;
}

.quick-action.save:hover,
.quick-action.save.active {
  color: #ffc107;
}

.quick-action.share:hover {
  color: #2196f3;
}

/* Streaming */
.message.streaming .typing-indicator {
  display: inline-block;
  margin-left: 8px;
  animation: pulse 1.5s ease-in-out infinite;
  color: var(--accent-color);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.status-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--accent-light);
  border-radius: var(--radius-md);
  color: var(--accent-color);
  font-size: 13px;
  animation: fadeIn 0.3s ease;
}

.status-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Chat Input */
.chat-input-area {
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.input-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.action-btn {
  padding: 6px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: var(--accent-light);
  border-color: var(--accent-color);
  color: var(--accent-color);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-wrapper {
  display: flex;
  gap: 8px;
}

.chat-input {
  flex: 1;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  resize: none;
  font-family: inherit;
}

.chat-input:focus {
  outline: none;
  border-color: var(--accent-color);
}

.send-btn {
  width: 48px;
  height: 48px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 20px;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

