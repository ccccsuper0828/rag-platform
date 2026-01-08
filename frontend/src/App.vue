<template>
  <div class="app-container" :class="{ 'dark-mode': isDarkMode }">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo-container" @click="goHome">
          <div class="logo-icon">🧠</div>
          <span v-if="!sidebarCollapsed" class="logo-text">RAG Studio</span>
        </div>
        <button class="sidebar-toggle" @click="toggleSidebar">
          <span v-if="sidebarCollapsed">→</span>
          <span v-else>←</span>
        </button>
                </div>
      
      <nav class="sidebar-nav">
        <button 
          class="nav-item" 
          :class="{ active: currentView === 'ragHall' }"
          @click="currentView = 'ragHall'; loadRagHall()"
        >
          <span class="nav-icon">🏛️</span>
          <span v-if="!sidebarCollapsed" class="nav-label">RAG 大厅</span>
        </button>
        <button 
          class="nav-item" 
          :class="{ active: currentView === 'discussionHall' }"
          @click="currentView = 'discussionHall'; loadDiscussionRooms()"
        >
          <span class="nav-icon">💬</span>
          <span v-if="!sidebarCollapsed" class="nav-label">讨论大厅</span>
        </button>
        
        <div class="nav-divider"></div>
        
        <button 
          class="nav-item" 
          :class="{ active: currentView === 'chat', 'requires-login': !isLoggedIn }"
          @click="isLoggedIn ? (hasRags ? currentView = 'chat' : showUploadPanel = true) : showAuthModal = true"
          :disabled="!isLoggedIn || !hasRags"
          :title="!isLoggedIn ? '请先登录' : (!hasRags ? '请先上传文件' : '')"
        >
          <span class="nav-icon">🤖</span>
          <span v-if="!sidebarCollapsed" class="nav-label">AI 问答</span>
          <span v-if="!isLoggedIn && !sidebarCollapsed" class="nav-lock">🔒</span>
        </button>
        <button 
          class="nav-item" 
          :class="{ active: currentView === 'pdfChat', 'requires-login': !isLoggedIn }"
          @click="isLoggedIn ? (hasRags ? (currentView = 'pdfChat', loadDocumentForParallelView()) : null) : showAuthModal = true"
          :disabled="!isLoggedIn || !hasRags"
          :title="!isLoggedIn ? '请先登录' : (!hasRags ? '请先上传文件' : '')"
        >
          <span class="nav-icon">📖</span>
          <span v-if="!sidebarCollapsed" class="nav-label">文档研读</span>
          <span v-if="!isLoggedIn && !sidebarCollapsed" class="nav-lock">🔒</span>
        </button>
        <button 
          class="nav-item" 
          :class="{ active: currentView === 'research', 'requires-login': !isLoggedIn }"
          @click="isLoggedIn ? currentView = 'research' : showAuthModal = true"
          :disabled="!isLoggedIn || !hasRags"
          :title="!isLoggedIn ? '请先登录' : (!hasRags ? '请先上传文件' : '')"
        >
          <span class="nav-icon">🔬</span>
          <span v-if="!sidebarCollapsed" class="nav-label">深度研究</span>
          <span v-if="!isLoggedIn && !sidebarCollapsed" class="nav-lock">🔒</span>
        </button>
        <button 
          class="nav-item" 
          :class="{ active: currentView === 'memory', 'requires-login': !isLoggedIn }"
          @click="isLoggedIn ? (currentView = 'memory', loadMemories()) : showAuthModal = true"
          :disabled="!isLoggedIn"
          :title="!isLoggedIn ? '请先登录' : ''"
        >
          <span class="nav-icon">🧠</span>
          <span v-if="!sidebarCollapsed" class="nav-label">记忆库</span>
          <span v-if="!isLoggedIn && !sidebarCollapsed" class="nav-lock">🔒</span>
        </button>
        <button 
          class="nav-item" 
          :class="{ active: currentView === 'dashboard' }"
          @click="currentView = 'dashboard'; loadDashboard()"
        >
          <span class="nav-icon">📊</span>
          <span v-if="!sidebarCollapsed" class="nav-label">个人仪表盘</span>
        </button>
        <button 
          class="nav-item" 
          :class="{ active: currentView === 'spark', 'requires-login': !isLoggedIn }"
          @click="isLoggedIn ? currentView = 'spark' : showAuthModal = true"
          :disabled="!isLoggedIn"
          :title="!isLoggedIn ? '请先登录' : ''"
        >
          <span class="nav-icon">✨</span>
          <span v-if="!sidebarCollapsed" class="nav-label">光源中心</span>
          <span v-if="!isLoggedIn && !sidebarCollapsed" class="nav-lock">🔒</span>
        </button>
        <button 
          class="nav-item" 
          :class="{ active: currentView === 'web3', 'requires-login': !isLoggedIn }"
          @click="isLoggedIn ? currentView = 'web3' : showAuthModal = true"
          :disabled="!isLoggedIn"
          :title="!isLoggedIn ? '请先登录' : ''"
        >
          <span class="nav-icon">🔗</span>
          <span v-if="!sidebarCollapsed" class="nav-label">Web3 中心</span>
          <span v-if="!isLoggedIn && !sidebarCollapsed" class="nav-lock">🔒</span>
        </button>
        
        <!-- RAG 列表 -->
        <div v-if="!sidebarCollapsed && ragList.length > 0" class="rag-list-section">
          <div class="rag-list-header">
            <span>📚 我的知识库</span>
                  </div>
          <div 
            v-for="rag in ragList" 
            :key="rag.rag_id"
            class="rag-list-item"
            :class="{ active: currentRagId === rag.rag_id, inactive: rag.active === false }"
            @click="selectRag(rag)"
          >
            <span class="rag-item-icon">{{ rag.active === false ? '💤' : '📄' }}</span>
            <span class="rag-item-name">{{ getFileName(rag.file_path) }}</span>
                    </div>
              </div>
      </nav>
      
      <div class="sidebar-footer">
        <button class="theme-toggle" @click="toggleTheme">
          <span v-if="isDarkMode">☀️</span>
          <span v-else>🌙</span>
        </button>
        <div v-if="isLoggedIn && !sidebarCollapsed" class="user-info">
          <div class="user-badge">
            <span class="user-avatar">👤</span>
            <span class="user-name">{{ currentUser }}</span>
                  </div>
          <button class="logout-btn" @click="logout" title="退出登录">
            🚪
          </button>
                </div>
        <button v-if="!isLoggedIn && !sidebarCollapsed" class="login-btn" @click="showAuthModal = true">
          🔑 登录 / 注册
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Header with Upload Toggle -->
      <header class="main-header">
        <div class="header-left">
          <h1 class="page-title">
            {{ currentView === 'ragHall' ? 'RAG 知识库大厅' : 
               currentView === 'discussionHall' ? '讨论大厅' :
               currentView === 'discussion' ? '实时讨论' :
               currentView === 'chat' ? 'AI 智能问答' : 
               currentView === 'pdfChat' ? '文档研读模式' :
               currentView === 'research' ? '深度研究模式' : 
               currentView === 'memory' ? '记忆库' : 
               currentView === 'dashboard' ? '个人仪表盘' :
               currentView === 'spark' ? '光源中心' :
               currentView === 'web3' ? 'Web3 中心' : '创建知识库' }}
          </h1>
        </div>
        <div class="header-right">
          <!-- 当前 RAG 选择器 (在 chat 和 pdfChat 视图都显示) -->
          <div v-if="hasRags && (currentView === 'chat' || currentView === 'pdfChat' || currentView === 'research')" class="rag-selector">
            <select v-model="currentRagId" class="rag-select" @change="onRagChange">
              <option v-for="rag in ragList" :key="rag.rag_id" :value="rag.rag_id">
                {{ getFileName(rag.file_path) }}
              </option>
            </select>
              </div>

          <!-- 上传新文件按钮（仅登录用户可见） -->
          <button 
            v-if="isLoggedIn && hasRags" 
            class="upload-toggle-btn"
            @click="showUploadPanel = !showUploadPanel"
          >
            <span>{{ showUploadPanel ? '✕ 关闭' : '➕ 上传新文件' }}</span>
          </button>
          
          <!-- 登录按钮（未登录用户显示） -->
          <button 
            v-if="!isLoggedIn" 
            class="header-login-btn"
            @click="showAuthModal = true"
          >
            <span>🔑 登录 / 注册</span>
          </button>
          
          <div v-if="currentRagId" class="rag-badge">
            <span class="badge-dot"></span>
            <span class="badge-text">已连接</span>
          </div>
        </div>
      </header>
      
      <!-- 上传面板（可折叠，仅登录用户可见，不在 web3/dashboard/spark 等独立视图显示） -->
      <div v-if="isLoggedIn && (showUploadPanel || !hasRags) && !['web3', 'dashboard', 'spark', 'memory'].includes(currentView)" class="upload-panel" :class="{ 'is-overlay': hasRags }">
        <div class="upload-panel-content">
          <div v-if="hasRags" class="upload-panel-header">
            <h3>📤 上传新文件</h3>
            <p>添加更多文档到您的知识库</p>
          </div>
          
          <div v-else class="welcome-header">
            <h2 class="hero-title">
              <span class="gradient-text">欢迎回来！</span>
            </h2>
            <p class="hero-subtitle">
              上传您的第一个文档，开始与 AI 对话
            </p>
          </div>
          
          <!-- Upload Card -->
          <div class="upload-card" :class="{ 'is-dragging': isDragging, 'compact': hasRags }">
            <div 
              class="upload-dropzone"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="handleDrop"
              @click="triggerFileInput"
            >
              <input 
                ref="fileInput"
                type="file" 
                class="hidden-input"
                @change="handleFileSelect"
                accept=".pdf,.txt,.md,.docx,.pptx"
              >
              <div class="upload-icon">
                <div class="upload-icon-circle" :class="{ 'small': hasRags }">
                  <span v-if="!isUploading">📄</span>
                  <div v-else class="upload-spinner"></div>
                </div>
              </div>
              <div class="upload-text">
                <span v-if="!isUploading" class="upload-primary">
                  拖拽文件到这里 或 <span class="upload-link">点击选择</span>
                </span>
                <span v-else class="upload-primary uploading">
                  正在构建知识库...
                </span>
                <span class="upload-secondary">
                  支持 PDF、TXT、Markdown、Word、PowerPoint
                </span>
              </div>
            </div>
            
            <!-- Upload Progress -->
            <div v-if="isUploading" class="upload-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
              </div>
              <span class="progress-text">{{ uploadStatus }}</span>
            </div>
            
            <!-- Duplicate File Warning -->
            <div v-if="duplicateFileInfo.show" class="duplicate-warning">
              <div class="warning-icon">⚠️</div>
              <div class="warning-content">
                <h4>文件内容已存在</h4>
                <p>该文件内容与已上传的 <strong>{{ duplicateFileInfo.existingFile }}</strong> 相同</p>
                <p class="warning-meta">上传时间：{{ duplicateFileInfo.uploadedAt }}</p>
                <div class="warning-actions">
                  <button class="use-existing-btn" @click="useExistingRag">
                    使用已有文件
                  </button>
                  <button class="dismiss-btn" @click="duplicateFileInfo.show = false">
                    取消
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 已上传文件列表 -->
          <div v-if="ragList.length > 0" class="uploaded-files-section">
            <h4>📚 已上传的文件 ({{ ragList.length }})</h4>
            <div class="uploaded-files-list">
              <div 
                v-for="rag in ragList" 
                :key="rag.rag_id"
                class="uploaded-file-item"
                :class="{ active: currentRagId === rag.rag_id, inactive: rag.active === false }"
                @click="selectRagAndClose(rag)"
              >
                <span class="file-icon">{{ rag.active === false ? '💤' : '📄' }}</span>
                <span class="file-name">{{ getFileName(rag.file_path) }}</span>
                <span class="file-status" v-if="rag.active === false">需激活</span>
                <span class="file-action">{{ currentRagId === rag.rag_id ? '✓ 当前' : '→ 选择' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat View (使用 v-show 保持状态) -->
      <div v-show="currentView === 'chat' && hasRags && !showUploadPanel" class="view-container chat-view">
        <div class="chat-with-tools-layout">
          <!-- Main Chat Area -->
              <div class="chat-container">
            <!-- Chat Messages -->
            <div class="chat-messages" ref="chatContainer">
              <div v-if="chatHistory.length === 0" class="chat-empty">
                <div class="empty-icon">💭</div>
                <h3>开始对话</h3>
                <p>向您的 AI 助手提问任何关于文档的问题</p>
                
                <!-- Suggestion Cards -->
                <div class="suggestion-grid">
                  <button 
                    v-for="suggestion in chatSuggestions" 
                    :key="suggestion"
                    class="suggestion-card"
                    @click="sendSuggestion(suggestion)"
                  >
                    {{ suggestion }}
                  </button>
                </div>
                  </div>
              
              <div 
                v-for="(msg, index) in chatHistory" 
                :key="index" 
                class="chat-message"
                :class="msg.role"
              >
                <div class="message-avatar">
                  {{ msg.role === 'user' ? '👤' : '🤖' }}
                </div>
                <div class="message-content">
                  <div class="message-header">
                    <span class="message-role">{{ msg.role === 'user' ? '您' : (msg.role === 'bot' || msg.role === 'assistant' ? 'AI 助手' : msg.role) }}</span>
                    <span v-if="msg.streaming" class="typing-indicator">
                      <span></span><span></span><span></span>
                    </span>
                  </div>
                  <div class="message-text" v-html="formatMessage(msg.content)"></div>
                  <!-- NFT 铸造按钮 -->
                  <div v-if="(msg.role === 'assistant' || msg.role === 'bot') && !msg.streaming && msg.content" class="message-actions">
                    <button 
                      class="mint-nft-btn"
                      @click="openMintModal(msg, index)"
                      title="将此答案铸造为 NFT"
                    >
                      🎨 铸造 NFT
                    </button>
                  </div>
                </div>
                </div>
              </div>

            <!-- Chat Input -->
            <div class="chat-input-container">
              <div class="input-wrapper">
                <textarea 
                  v-model="question"
                  class="chat-input"
                  placeholder="输入您的问题..."
                  @keydown.enter.exact.prevent="sendMessage"
                  :disabled="isAsking"
                  rows="1"
                  ref="chatInput"
                ></textarea>
                <button 
                  class="send-button"
                  @click="sendMessage"
                  :disabled="!question.trim() || isAsking"
                >
                  <span v-if="!isAsking">→</span>
                  <div v-else class="send-spinner"></div>
                </button>
              </div>
              <div class="input-actions">
                <div class="input-hint">
                  按 Enter 发送 • 当前知识库：{{ getFileName(currentRagFilePath) }}
                </div>
                <button 
                  v-if="chatHistory.length > 0"
                  class="join-discussion-chat-btn"
                  @click="joinDiscussionFromChat"
                >
                  💬 进入讨论
                </button>
              </div>
            </div>
              </div>

          <!-- Right Toolbar (仅在 chat 视图显示，但使用 v-show 保持状态) -->
          <aside v-show="currentView === 'chat'" class="right-toolbar" :class="{ 'collapsed': rightToolbarCollapsed }">
            <div class="toolbar-toggle" @click="rightToolbarCollapsed = !rightToolbarCollapsed">
              <span v-if="rightToolbarCollapsed">◀</span>
              <span v-else>▶</span>
            </div>
            
            <div v-if="!rightToolbarCollapsed" class="toolbar-content">
              <!-- Knowledge Graph Section -->
              <div class="toolbar-section kg-section">
                <div class="section-header">
                  <span class="section-icon">🕸️</span>
                  <span class="section-title">知识图谱</span>
                  <button class="expand-btn" @click="showKnowledgeGraphModal = true" title="放大查看">
                    ⤢
                  </button>
                </div>
                <div class="kg-thumbnail" @click="showKnowledgeGraphModal = true">
                  <svg v-if="knowledgeGraph.nodes.length > 0" class="kg-mini" viewBox="0 0 200 150">
                    <!-- Render mini graph nodes -->
                    <g v-for="(node, idx) in knowledgeGraph.nodes.slice(0, 20)" :key="'n-'+idx">
                      <circle 
                        :cx="30 + (idx % 5) * 35" 
                        :cy="25 + Math.floor(idx / 5) * 35"
                        :r="Math.min(node.size || 6, 12)"
                        :fill="getNodeColor(node.type)"
                        opacity="0.8"
                      />
                    </g>
                    <!-- Render mini graph links -->
                    <g v-for="(link, idx) in knowledgeGraph.links.slice(0, 15)" :key="'l-'+idx">
                      <line
                        :x1="getLinkCoord(link.source, 'x')"
                        :y1="getLinkCoord(link.source, 'y')"
                        :x2="getLinkCoord(link.target, 'x')"
                        :y2="getLinkCoord(link.target, 'y')"
                        stroke="#888"
                        stroke-width="1"
                        opacity="0.4"
                      />
                    </g>
                  </svg>
                  <div v-else class="kg-placeholder">
                    <span>📊</span>
                    <p>知识图谱生成中...</p>
                  </div>
                  <div class="kg-stats">
                    <span>{{ knowledgeGraph.nodes.length }} 实体</span>
                    <span>{{ knowledgeGraph.links.length }} 关系</span>
                  </div>
                </div>
              </div>
              
              <!-- Divider -->
              <div class="toolbar-divider"></div>
              
              <!-- Files Section -->
              <div class="toolbar-section files-section">
                <div class="section-header">
                  <span class="section-icon">📁</span>
                  <span class="section-title">已上传文件</span>
                  <span class="file-count">{{ ragFiles.length }}</span>
                </div>
                <div class="files-list">
                  <div 
                    v-for="file in ragFiles" 
                    :key="file.path"
                    class="file-item"
                    :title="file.name"
                  >
                    <span class="file-icon">{{ getFileIcon(file.name) }}</span>
                    <div class="file-info">
                      <span class="file-name">{{ truncateFileName(file.name, 18) }}</span>
                      <span class="file-meta">{{ file.size_human }} • {{ file.uploaded_at }}</span>
                    </div>
                  </div>
                  <div v-if="ragFiles.length === 0" class="no-files">
                    暂无文件
                  </div>
                </div>
                <button class="add-file-btn" @click="showUploadPanel = true">
                  ➕ 添加文件
                </button>
              </div>
            </div>
          </aside>
        </div>
        
        <!-- Knowledge Graph Modal (使用 @antv/g6 的新版可视化) -->
        <div v-if="showKnowledgeGraphModal" class="kg-modal-overlay" @click.self="showKnowledgeGraphModal = false">
          <div class="kg-modal">
            <div class="kg-modal-header">
              <h3>🕸️ 知识图谱</h3>
              <div class="kg-modal-actions">
                <button class="kg-action-btn" @click="refreshKnowledgeGraph">🔄 刷新</button>
                <button class="close-btn" @click="showKnowledgeGraphModal = false">✕</button>
              </div>
            </div>
            <div class="kg-modal-content">
              <GraphCanvas
                ref="graphCanvasRef"
                :graphData="g6GraphData"
                :graphInfo="kgStats"
                :showControls="true"
                @node-click="handleNodeClick"
                @edge-click="handleEdgeClick"
                @canvas-click="handleCanvasClick"
                @search="handleGraphSearch"
              />
              <GraphDetailPanel
                :visible="showGraphDetail"
                :item="selectedGraphItem"
                :type="selectedGraphItemType"
                :graphData="g6GraphData"
                @close="showGraphDetail = false"
                    />
                  </div>
                </div>
              </div>
      </div>

      <!-- Document Parallel View (仅用户自己的 RAG 可用) -->
      <div v-show="currentView === 'pdfChat' && hasRags && currentRagIsOwned" class="view-container pdf-chat-view">
        <PdfParallelView
          v-if="documentContent || pdfUrl"
          :pdf-url="pdfUrl"
          :document-content="documentContent"
          :document-type="documentType"
          :document-name="documentName"
          :rag-id="currentRagId"
          :auth-token="authToken"
          :is-owner="currentRagIsOwned"
          @citation-click="handlePdfCitationClick"
        />
        <div v-else class="pdf-loading">
          <div class="loading-spinner"></div>
          <p>正在加载 PDF 文件...</p>
        </div>
      </div>

      <!-- Research View - QNN Deep Research (使用 v-show 保持状态) -->
      <div v-show="currentView === 'research' && hasRags" class="view-container research-view">
        <div class="research-container">
          <div class="research-header">
            <div class="research-icon">🧠</div>
            <div class="research-info">
              <h2>QNN 深度研究</h2>
              <p>质化神经网络 · 多Agent协作 · 反思迭代</p>
            </div>
          </div>
          
          <!-- 研究问题输入 -->
          <div class="research-input-area">
            <textarea 
              v-model="researchQuery"
              class="research-input"
              placeholder="详细描述您要深入研究的问题... 例如：分析项目的核心架构设计理念和技术选型的优缺点"
              rows="4"
            ></textarea>
          </div>

          <!-- QNN 网络配置 -->
          <div class="qnn-config-section">
            <div class="config-header">
              <span class="config-icon">⚙️</span>
              <span class="config-title">QNN 网络配置</span>
              <span class="config-subtitle">更高参数 = 更深入分析（但更耗时）</span>
            </div>
            
            <div class="config-grid">
              <!-- 网络深度 -->
              <div class="config-item">
                <div class="config-label">
                  <span class="label-icon">📊</span>
                  <span>网络深度</span>
                </div>
                <div class="config-slider">
                  <input type="range" v-model.number="qnnConfig.depth" min="1" max="4" step="1">
                  <span class="slider-value">{{ qnnConfig.depth }} 层</span>
                </div>
                <div class="config-hint">层数越多，分析越层次化</div>
              </div>
              
              <!-- Agent 数量 -->
              <div class="config-item">
                <div class="config-label">
                  <span class="label-icon">🤖</span>
                  <span>每层 Agent</span>
                </div>
                <div class="config-slider">
                  <input type="range" v-model.number="qnnConfig.agentsPerLayer" min="2" max="6" step="1">
                  <span class="slider-value">{{ qnnConfig.agentsPerLayer }} 个</span>
                </div>
                <div class="config-hint">更多Agent = 更多视角</div>
              </div>
              
              <!-- 迭代次数 -->
              <div class="config-item">
                <div class="config-label">
                  <span class="label-icon">🔄</span>
                  <span>迭代轮次</span>
                </div>
                <div class="config-slider">
                  <input type="range" v-model.number="qnnConfig.maxEpochs" min="1" max="5" step="1">
                  <span class="slider-value">{{ qnnConfig.maxEpochs }} 轮</span>
                </div>
                <div class="config-hint">更多迭代 = 更深入反思</div>
              </div>
            </div>
            
            <!-- 时间估算 -->
            <div class="time-estimate">
              <span class="estimate-icon">⏱️</span>
              <span class="estimate-text">
                预计耗时: <strong>{{ estimatedTime }}</strong>
                （{{ totalAgents }} 个 Agent × {{ qnnConfig.maxEpochs }} 轮迭代）
              </span>
            </div>
          </div>

          <!-- MBTI 人格选择 -->
          <div class="mbti-section">
            <div class="mbti-header">
              <span class="mbti-icon">🎭</span>
              <span class="mbti-title">Agent 人格配置</span>
              <span class="mbti-subtitle">选择 {{ qnnConfig.agentsPerLayer }} 种人格类型</span>
            </div>
            <div class="mbti-grid">
              <label 
                v-for="(profile, mbti) in mbtiProfiles" 
                :key="mbti"
                class="mbti-option"
                :class="{ selected: qnnConfig.selectedMbtis.includes(mbti), disabled: !qnnConfig.selectedMbtis.includes(mbti) && qnnConfig.selectedMbtis.length >= qnnConfig.agentsPerLayer }"
              >
                <input 
                  type="checkbox" 
                  :value="mbti" 
                  v-model="qnnConfig.selectedMbtis"
                  :disabled="!qnnConfig.selectedMbtis.includes(mbti) && qnnConfig.selectedMbtis.length >= qnnConfig.agentsPerLayer"
                >
                <div class="mbti-content">
                  <span class="mbti-type">{{ mbti }}</span>
                  <span class="mbti-name">{{ profile.name }}</span>
                </div>
              </label>
            </div>
          </div>

          <!-- 开始研究按钮 -->
          <button 
            class="research-button"
            @click="startQNNResearch"
            :disabled="!researchQuery.trim() || isResearching || qnnConfig.selectedMbtis.length < 2"
          >
            <span v-if="!isResearching">🚀 启动 QNN 深度研究</span>
            <span v-else>🧠 研究进行中...</span>
          </button>

          <!-- 研究进度 -->
          <div v-if="researchProgress.length > 0" class="research-progress">
            <div class="progress-header">
              <span class="progress-icon">📡</span>
              <span>研究进度</span>
            </div>
            <div class="progress-log">
              <div 
                v-for="(msg, index) in researchProgress" 
                :key="index"
                class="progress-item"
                :class="msg.type"
              >
                {{ msg.message }}
              </div>
            </div>
          </div>

          <!-- Epoch 详情 -->
          <div v-if="researchEpochs.length > 0" class="epochs-section">
            <div class="epochs-header">
              <span>🔄 研究迭代过程</span>
            </div>
            <div 
              v-for="(epoch, index) in researchEpochs" 
              :key="index"
              class="epoch-card"
            >
              <div class="epoch-header">
                <span class="epoch-number">Epoch {{ epoch.epoch }}</span>
                <span class="epoch-duration">{{ (epoch.duration_ms / 1000).toFixed(1) }}s</span>
              </div>
              <div class="epoch-problem">
                <strong>研究问题：</strong>{{ epoch.problem }}
              </div>
              <div class="epoch-synthesis">
                <strong>综合结论：</strong>{{ epoch.synthesis_preview }}
              </div>
            </div>
          </div>

          <!-- 最终报告 -->
          <div v-if="researchResult" class="research-result">
            <div class="result-header">
              <span class="result-icon">📋</span>
              <span>研究报告</span>
              <span class="result-meta">
                {{ researchResult.epochs_completed }} 轮迭代 · {{ (researchResult.total_duration_ms / 1000).toFixed(1) }}s
              </span>
            </div>
            
            <!-- 关键洞察 -->
            <div v-if="researchResult.insights && researchResult.insights.length > 0" class="insights-section">
              <div class="insights-title">💡 关键洞察</div>
              <ul class="insights-list">
                <li v-for="(insight, i) in researchResult.insights" :key="i">{{ insight }}</li>
              </ul>
            </div>
            
            <!-- 完整报告 -->
            <div class="full-report">
              <div class="report-content" v-html="formatMarkdown(researchResult.final_answer)"></div>
            </div>
            
            <!-- 网络摘要 -->
            <div v-if="researchResult.network_summary" class="network-summary">
              <div class="summary-title">🧠 QNN 网络信息</div>
              <div class="summary-stats">
                <span>{{ researchResult.network_summary.depth }} 层深度</span>
                <span>{{ researchResult.network_summary.agents?.length || 0 }} 个 Agent</span>
                <span>{{ researchResult.network_summary.total_epochs }} 轮迭代</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Memory View -->
      <div v-if="currentView === 'memory'" class="view-container memory-view">
        <div class="memory-container">
          <div class="memory-header">
            <h2>记忆库</h2>
            <p>AI 会记住跨对话的重要上下文</p>
          </div>
          
          <div class="memory-list">
            <div 
              v-for="(memory, index) in memories" 
              :key="index"
              class="memory-card"
            >
              <div class="memory-icon">💾</div>
              <div class="memory-content">
                <div class="memory-text">{{ memory.text }}</div>
                <div class="memory-meta">
                  <span class="memory-date">{{ memory.date }}</span>
                  <span class="memory-source">{{ memory.source }}</span>
                </div>
              </div>
              <button class="memory-delete" @click="deleteMemory(index)">×</button>
            </div>
            
            <div v-if="memories.length === 0" class="memory-empty">
              <div class="empty-icon">🧠</div>
              <p>还没有保存的记忆。与 AI 对话来创建记忆。</p>
            </div>
          </div>
          
          <div class="memory-add">
            <input 
              v-model="newMemory"
              type="text" 
              placeholder="添加新记忆..."
              @keydown.enter="addMemory"
            >
            <button @click="addMemory">+ 添加</button>
          </div>
        </div>
      </div>

      <!-- RAG 大厅 View -->
      <div v-if="currentView === 'ragHall'" class="view-container hall-view">
        <div class="hall-container">
          <div class="hall-header">
            <div class="hall-title">
              <h2>🏛️ RAG 知识库大厅</h2>
              <p>探索公开的知识库，与其他用户一起讨论</p>
            </div>
            <button class="create-rag-btn" @click="showUploadPanel = true; currentView = 'chat'">
              ➕ 创建知识库
            </button>
          </div>

          <div class="hall-grid">
            <div 
              v-for="rag in ragHallList" 
              :key="rag.rag_id"
              class="rag-card"
              @click="enterRagFromHall(rag)"
            >
              <div class="rag-card-header">
                <div class="rag-card-icon">📚</div>
                <div class="rag-card-meta">
                  <span v-if="rag.has_active_discussion" class="active-discussion-badge">
                    🔴 讨论中
                  </span>
                  <span class="user-count-badge">
                    👥 {{ rag.recent_user_count }} 人在线
                  </span>
                </div>
              </div>
              <h3 class="rag-card-title">{{ rag.title }}</h3>
              <p class="rag-card-info">
                <span class="rag-arch">{{ rag.arch }}</span>
                <span class="rag-date">{{ rag.created_at }}</span>
              </p>
              <div class="rag-card-actions">
                <button class="action-btn primary" @click.stop="enterRagChat(rag)">
                  🤖 进入问答
                </button>
                <button class="action-btn secondary" @click.stop="joinRagDiscussion(rag.rag_id)">
                  💬 加入讨论
                </button>
              </div>
            </div>

            <div v-if="ragHallList.length === 0" class="hall-empty">
              <div class="empty-icon">🏛️</div>
              <h3>暂无公开的知识库</h3>
              <p>创建第一个知识库来开始吧！</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 讨论大厅 View -->
      <div v-if="currentView === 'discussionHall'" class="view-container hall-view">
        <div class="hall-container">
          <div class="hall-header">
            <div class="hall-title">
              <h2>💬 讨论大厅</h2>
              <p>查看正在进行的讨论，加入感兴趣的话题</p>
            </div>
          </div>

          <div class="hall-grid">
            <div 
              v-for="room in discussionRooms" 
              :key="room.room_id"
              class="discussion-card"
              @click="joinRoom(room.room_id, room.rag_id)"
            >
              <div class="discussion-card-header">
                <div class="discussion-card-icon">💬</div>
                <div class="discussion-status">
                  <span class="live-badge">🔴 LIVE</span>
                </div>
              </div>
              <h3 class="discussion-card-title">RAG: {{ room.rag_id.slice(0, 20) }}...</h3>
              <div class="discussion-stats">
                <span class="stat">👥 {{ room.user_count }} 人参与</span>
                <span class="stat">💬 {{ room.message_count }} 条消息</span>
              </div>
              <div class="discussion-users">
                <span 
                  v-for="user in room.users.slice(0, 5)" 
                  :key="user.user_id"
                  class="user-avatar-small"
                >
                  {{ user.username.charAt(0) }}
                </span>
                <span v-if="room.users.length > 5" class="more-users">
                  +{{ room.users.length - 5 }}
                </span>
              </div>
              <button class="join-discussion-btn" @click.stop="joinRoom(room.room_id, room.rag_id)">
                加入讨论
              </button>
            </div>

            <div v-if="discussionRooms.length === 0" class="hall-empty">
              <div class="empty-icon">💬</div>
              <h3>暂无活跃的讨论</h3>
              <p>前往 RAG 大厅，开启新的讨论！</p>
              <button class="goto-hall-btn" @click="currentView = 'ragHall'; loadRagHall()">
                前往 RAG 大厅
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 实时讨论 View -->
      <div v-if="currentView === 'discussion'" class="view-container discussion-view">
        <div class="discussion-container">
          <div class="discussion-header">
            <div class="discussion-info">
              <h2>💬 实时讨论</h2>
              <p>RAG: {{ currentDiscussionRoom?.rag_id }}</p>
            </div>
            <div class="discussion-members">
              <span class="member-count">
                👥 {{ currentDiscussionRoom?.users?.length || 0 }} 人在线
              </span>
              <button class="leave-btn" @click="leaveDiscussion">
                退出讨论
              </button>
            </div>
          </div>

          <div class="discussion-messages" ref="discussionMessagesRef">
            <div 
              v-for="msg in discussionMessages" 
              :key="msg.id"
              class="discussion-message"
              :class="{ 
                'own-message': msg.user_id === currentUserId,
                'system-message': msg.message_type === 'system'
              }"
            >
              <div v-if="msg.message_type !== 'system'" class="msg-avatar">
                {{ msg.username.charAt(0) }}
              </div>
              <div class="msg-body">
                <div v-if="msg.message_type !== 'system'" class="msg-header">
                  <span class="msg-username">{{ msg.username }}</span>
                  <span class="msg-time">{{ msg.formatted_time }}</span>
                </div>
                <div class="msg-content" :class="{ 'system-content': msg.message_type === 'system' }">
                  {{ msg.content }}
                </div>
              </div>
            </div>
          </div>

          <div class="discussion-input">
            <input 
              v-model="discussionInput"
              type="text"
              placeholder="输入消息..."
              @keydown.enter="sendDiscussionMessage"
              :disabled="!isDiscussionConnected"
            >
            <button 
              @click="sendDiscussionMessage"
              :disabled="!discussionInput.trim() || !isDiscussionConnected"
            >
              发送
            </button>
          </div>
        </div>
      </div>
      
      <!-- Dashboard View -->
      <div v-if="currentView === 'dashboard'" class="view-container dashboard-view">
        <div class="dashboard-container">
          <!-- Stats Overview -->
          <div class="stats-grid">
            <StatsCard 
              icon="💬" 
              label="总对话数" 
              :value="dashboardStats.total_conversations || 0"
              variant="primary"
            />
            <StatsCard 
              icon="📄" 
              label="已上传文档" 
              :value="dashboardStats.total_documents || 0"
              variant="info"
            />
            <StatsCard 
              icon="🧠" 
              label="记忆条目" 
              :value="dashboardStats.total_memories || 0"
              variant="success"
            />
            <StatsCard 
              icon="🔬" 
              label="深度研究" 
              :value="dashboardStats.research_count || 0"
              variant="warning"
            />
            <StatsCard 
              icon="🔗" 
              label="图谱节点" 
              :value="dashboardStats.graph_nodes || 0"
            />
            <StatsCard 
              icon="↔️" 
              label="图谱关系" 
              :value="dashboardStats.graph_edges || 0"
            />
          </div>
          
          <!-- User Persona Section -->
          <div class="dashboard-section persona-section">
            <h3 class="section-title">👤 用户画像</h3>
            <div class="persona-card">
              <div class="persona-avatar">
                <span class="avatar-icon">{{ userPersona.name?.charAt(0) || '?' }}</span>
              </div>
              <div class="persona-info">
                <h4 class="persona-name">{{ userPersona.name || currentUser }}</h4>
                <p class="persona-role">{{ userPersona.role || '知识探索者' }}</p>
                <div class="persona-tags">
                  <span 
                    v-for="tag in (userPersona.tags || []).slice(0, 5)" 
                    :key="tag" 
                    class="persona-tag"
                  >{{ tag }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Usage Section -->
          <div class="dashboard-section usage-section">
            <h3 class="section-title">📈 使用统计</h3>
            <div class="usage-grid">
              <div class="usage-item">
                <div class="usage-icon">🤖</div>
                <div class="usage-details">
                  <span class="usage-value">{{ usageStats.chat || 0 }}</span>
                  <span class="usage-label">问答对话</span>
                </div>
              </div>
              <div class="usage-item">
                <div class="usage-icon">🔬</div>
                <div class="usage-details">
                  <span class="usage-value">{{ usageStats.research || 0 }}</span>
                  <span class="usage-label">深度研究</span>
                </div>
              </div>
              <div class="usage-item">
                <div class="usage-icon">💬</div>
                <div class="usage-details">
                  <span class="usage-value">{{ usageStats.discussion || 0 }}</span>
                  <span class="usage-label">讨论参与</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Recent Conversations -->
          <div class="dashboard-section conversations-section">
            <h3 class="section-title">💭 最近对话</h3>
            <div class="conversations-list">
              <div 
                v-for="conv in recentConversations" 
                :key="conv.id" 
                class="conversation-item"
                @click="goToConversation(conv)"
              >
                <div class="conv-icon">💬</div>
                <div class="conv-content">
                  <h4 class="conv-title">{{ conv.title || '未命名对话' }}</h4>
                  <p class="conv-preview">{{ conv.preview || '...' }}</p>
                </div>
                <span class="conv-time">{{ conv.time || '-' }}</span>
              </div>
              <div v-if="recentConversations.length === 0" class="empty-conversations">
                <span class="empty-icon">📭</span>
                <p>暂无对话记录</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Spark Dashboard View -->
      <div v-if="currentView === 'spark'" class="view-container spark-view">
        <SparkDashboard />
      </div>
      
      <!-- Web3 Hub View -->
      <div v-if="currentView === 'web3'" class="view-container web3-view">
        <Web3Hub :is-logged-in="isLoggedIn" />
      </div>
      
      <!-- Loading Overlay -->
      <div v-if="isInitializing" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>正在加载...</p>
      </div>
    </main>
    
    <!-- Auth Modal -->
    <div v-if="showAuthModal" class="auth-modal-overlay" @click.self="showAuthModal = false">
      <div class="auth-modal">
        <button class="auth-close-btn" @click="showAuthModal = false">✕</button>
        
        <div class="auth-header">
          <h2>{{ authMode === 'login' ? '欢迎回来' : '创建账户' }}</h2>
          <p>{{ authMode === 'login' ? '登录您的 RAG Studio 账户' : '注册新账户开始使用' }}</p>
        </div>
        
        <div class="auth-tabs">
          <button 
            class="auth-tab" 
            :class="{ active: authMode === 'login' }"
            @click="authMode = 'login'"
          >登录</button>
          <button 
            class="auth-tab" 
            :class="{ active: authMode === 'register' }"
            @click="authMode = 'register'"
          >注册</button>
        </div>
        
        <form class="auth-form" @submit.prevent="handleAuth">
          <div class="form-group">
            <label>用户名</label>
            <input 
              v-model="authForm.username" 
              type="text" 
              placeholder="输入用户名"
              required
              minlength="3"
            >
          </div>
          
          <div v-if="authMode === 'register'" class="form-group">
            <label>邮箱</label>
            <input 
              v-model="authForm.email" 
              type="email" 
              placeholder="输入邮箱地址"
              required
            >
          </div>
          
          <div class="form-group">
            <label>密码</label>
            <input 
              v-model="authForm.password" 
              type="password" 
              placeholder="输入密码"
              required
              minlength="6"
            >
          </div>
          
          <div v-if="authError" class="auth-error">
            {{ authError }}
          </div>
          
          <button type="submit" class="auth-submit-btn" :disabled="isAuthLoading">
            <span v-if="!isAuthLoading">{{ authMode === 'login' ? '登录' : '注册' }}</span>
            <span v-else>处理中...</span>
          </button>
        </form>
        
        <div class="auth-footer">
          <p v-if="authMode === 'login'">
            还没有账户？ <a @click="authMode = 'register'">立即注册</a>
          </p>
          <p v-else>
            已有账户？ <a @click="authMode = 'login'">立即登录</a>
          </p>
        </div>
      </div>
    </div>
    
    <!-- NFT 铸造模态框 -->
    <div v-if="showMintModal" class="mint-modal-overlay" @click.self="showMintModal = false">
      <div class="mint-modal">
        <button class="mint-close-btn" @click="showMintModal = false">✕</button>
        
        <div class="mint-header">
          <h2>🎨 铸造知识 NFT</h2>
          <p>将 AI 答案永久保存到区块链</p>
        </div>
        
        <div class="mint-content">
          <div class="mint-preview">
            <div class="preview-label">问题</div>
            <div class="preview-question">{{ mintContent.question }}</div>
            <div class="preview-label">答案预览</div>
            <div class="preview-answer">{{ mintContent.answer?.substring(0, 300) }}{{ mintContent.answer?.length > 300 ? '...' : '' }}</div>
          </div>
          
          <div v-if="!walletConnected" class="mint-wallet-section">
            <button class="connect-wallet-btn" @click="connectWalletForMint">
              🔗 连接钱包
            </button>
            <p class="wallet-hint">需要连接 MetaMask 钱包来铸造 NFT</p>
          </div>
          
          <div v-else class="mint-wallet-info">
            <span class="wallet-address">{{ shortenAddress(walletAddress) }}</span>
            <span class="network-badge">{{ networkName }}</span>
          </div>
          
          <div class="mint-status" v-if="mintStatus">
            <div :class="['status-message', mintStatus.type]">
              {{ mintStatus.message }}
            </div>
          </div>
          
          <div class="mint-actions">
            <button 
              class="mint-btn-primary"
              @click="mintNFT"
              :disabled="!walletConnected || isMinting"
            >
              <span v-if="!isMinting">🚀 铸造 NFT (0.001 ETH)</span>
              <span v-else>⏳ 铸造中...</span>
            </button>
            <button class="mint-btn-secondary" @click="showMintModal = false">
              取消
            </button>
          </div>
          
          <div class="mint-notice">
            <p>⚠️ 铸造需要支付少量 Gas 费用和 0.001 ETH 铸造费</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import GraphCanvas from './components/GraphCanvas.vue'
import GraphDetailPanel from './components/GraphDetailPanel.vue'
import StatsCard from './components/StatsCard.vue'
import PdfParallelView from './components/PdfParallelView.vue'
import SparkDashboard from './components/SparkDashboard.vue'
import Web3Hub from './components/Web3Hub.vue'
import MintNFTModal from './components/MintNFTModal.vue'

// API
const API_BASE = 'http://localhost:8000'

// State
const isDarkMode = ref(false)
const sidebarCollapsed = ref(false)
const currentView = ref('ragHall')  // 默认进入 RAG 大厅
const isLoggedIn = ref(false)
const currentUser = ref('')
const authToken = ref('')
const isInitializing = ref(true)

// Auth Modal State
const showAuthModal = ref(false)
const authMode = ref('login')  // 'login' or 'register'
const authForm = ref({
  username: '',
  email: '',
  password: ''
})
const authError = ref('')
const isAuthLoading = ref(false)

// NFT Mint State
const showMintModal = ref(false)
const mintContent = ref({
  question: '',
  answer: '',
  citations: []
})
const walletConnected = ref(false)
const walletAddress = ref('')
const networkName = ref('Sepolia')
const isMinting = ref(false)
const mintStatus = ref(null)
const mintedNFTs = ref([])

// RAG State
const currentRagId = ref('')
const currentArch = ref('aipartner')
const ragList = ref([])
const showUploadPanel = ref(false)

// Right Toolbar State
const rightToolbarCollapsed = ref(false)
const knowledgeGraph = ref({ nodes: [], links: [] })
const ragFiles = ref([])
const showKnowledgeGraphModal = ref(false)
const selectedKgNode = ref(null)
const kgZoom = ref(1)
const kgPan = ref({ x: 0, y: 0 })
const kgViewBox = ref({ width: 800, height: 600 })
const isDraggingKg = ref(false)
const dragStart = ref({ x: 0, y: 0 })

// G6 Graph State (新的知识图谱状态)
const graphCanvasRef = ref(null)
const g6GraphData = ref({ nodes: [], edges: [] })
const kgStats = ref({ total_nodes: 0, total_edges: 0 })
const showGraphDetail = ref(false)
const selectedGraphItem = ref(null)
const selectedGraphItemType = ref('node')

// Document Parallel View State
const pdfUrl = ref('')
const documentContent = ref('')
const documentName = ref('')
const documentType = ref('') // 'pdf', 'text', 'markdown'
const currentRagIsOwned = ref(true) // 当前用户自己创建的 RAG

// Computed
const hasRags = computed(() => ragList.value.length > 0)
const currentRagFilePath = computed(() => {
  const rag = ragList.value.find(r => r.rag_id === currentRagId.value)
  return rag ? rag.file_path : ''
})

// Load document for parallel view (supports all file types)
const loadDocumentForParallelView = async () => {
  if (!currentRagId.value || !authToken.value) {
    documentContent.value = ''
    pdfUrl.value = ''
    return
  }
  
  try {
    // First, try to get document info
    const resp = await fetch(`${API_BASE}/v1/rag/${currentRagId.value}/document-info`, {
        headers: { 'Authorization': `Bearer ${authToken.value}` }
    })
      if (resp.ok) {
      const data = await resp.json()
      if (data.documents && data.documents.length > 0) {
        const doc = data.documents[0]
        documentName.value = doc.name
        
        // Check if it's a PDF
        if (doc.name.toLowerCase().endsWith('.pdf')) {
          documentType.value = 'pdf'
          pdfUrl.value = `${API_BASE}/v1/rag/${currentRagId.value}/file/${doc.name}`
          documentContent.value = ''
        } else {
          // For text files, load content
          documentType.value = doc.name.endsWith('.md') ? 'markdown' : 'text'
          pdfUrl.value = ''
          
          // Load text content
          const contentResp = await fetch(`${API_BASE}/v1/rag/${currentRagId.value}/document-content`, {
            headers: { 'Authorization': `Bearer ${authToken.value}` }
          })
          if (contentResp.ok) {
            const contentData = await contentResp.json()
            documentContent.value = contentData.content || ''
          }
        }
      }
      }
    } catch (e) {
    console.log('Document load failed:', e)
  }
}

// Upload State
const fileInput = ref(null)
const isDragging = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const duplicateFileInfo = ref({
  show: false,
  existingFile: '',
  existingRagId: '',
  uploadedAt: ''
})

// Chat State
const chatHistory = ref([])
const question = ref('')
const isAsking = ref(false)
const chatContainer = ref(null)
const chatInput = ref(null)
const useStream = ref(true)

// Research State
const researchQuery = ref('')
const isResearching = ref(false)
const researchSteps = ref([])
const researchProgress = ref([])
const researchEpochs = ref([])
const researchResult = ref(null)

// QNN Configuration
const qnnConfig = ref({
  depth: 2,
  agentsPerLayer: 3,
  maxEpochs: 2,
  selectedMbtis: ['INTJ', 'INTP', 'ENTJ']
})

// MBTI Profiles
const mbtiProfiles = ref({
  INTJ: { name: '策略家', traits: '理性、独立、追求效率' },
  INTP: { name: '逻辑学家', traits: '好奇、创新、追求真理' },
  ENTJ: { name: '指挥官', traits: '果断、领导力强、目标导向' },
  ENTP: { name: '辩论家', traits: '机智、挑战传统、善于辩论' },
  INFJ: { name: '提倡者', traits: '洞察力强、理想主义' },
  INFP: { name: '调解者', traits: '理想主义、创造力' },
  ENFJ: { name: '主角', traits: '魅力、影响力、善于激励' },
  ENFP: { name: '竞选者', traits: '热情、创造力、善于连接' },
  ISTJ: { name: '物流师', traits: '可靠、务实、注重细节' },
  ISFJ: { name: '守护者', traits: '细心、忠诚、注重和谐' },
  ESTJ: { name: '执行者', traits: '组织能力强、直接' },
  ESFJ: { name: '领事', traits: '合作、关怀、注重社交' }
})

// Computed: 总 Agent 数
const totalAgents = computed(() => qnnConfig.value.depth * qnnConfig.value.agentsPerLayer)

// Computed: 预估时间
const estimatedTime = computed(() => {
  const seconds = totalAgents.value * 15 * qnnConfig.value.maxEpochs + qnnConfig.value.maxEpochs * 10
  if (seconds < 60) return `${seconds} 秒`
  return `${Math.round(seconds / 60)} 分钟`
})

const researchOptions = ref({
  searchWeb: true,
  runCode: false,
  searchDocs: true
})

// Memory State
const memories = ref([])
const newMemory = ref('')

// RAG Hall State
const ragHallList = ref([])

// Discussion State
const discussionRooms = ref([])
const currentDiscussionRoom = ref(null)
const discussionMessages = ref([])
const discussionInput = ref('')
const isDiscussionConnected = ref(false)
const discussionWebSocket = ref(null)
const discussionMessagesRef = ref(null)
const currentUserId = ref('')

// Chat Suggestions
const chatSuggestions = ref([
  '📝 总结这篇文档',
  '🔍 有哪些关键要点？',
  '❓ 解释一下主要概念',
  '📊 分析数据模式'
])

// Dashboard State
const dashboardStats = ref({
  total_conversations: 0,
  total_documents: 0,
  total_memories: 0,
  research_count: 0,
  graph_nodes: 0,
  graph_edges: 0
})
const userPersona = ref({
  name: '',
  role: '',
  tags: []
})
const usageStats = ref({
  chat: 0,
  research: 0,
  discussion: 0
})
const recentConversations = ref([])

// Methods
const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light')
}

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const goHome = () => {
  if (hasRags.value) {
    currentView.value = 'chat'
  } else {
    showUploadPanel.value = true
  }
}

const getFileName = (filePath) => {
  if (!filePath) return '未知文件'
  return filePath.split('/').pop() || filePath
}

const selectRag = async (rag) => {
  // 如果 RAG 未激活，先激活它
  if (rag.active === false) {
    try {
      const response = await fetch(`${API_BASE}/v1/rag/activate`, {
      method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken.value}`
        },
        body: JSON.stringify({ rag_id: rag.rag_id })
      })
      
      if (!response.ok) {
        const error = await response.json()
        console.error('Failed to activate RAG:', error)
        alert(`激活失败: ${error.detail || '请重试'}`)
        return
      }
      
      // 更新列表中的状态
      const idx = ragList.value.findIndex(r => r.rag_id === rag.rag_id)
      if (idx >= 0) {
        ragList.value[idx].active = true
    }
  } catch (e) {
      console.error('Error activating RAG:', e)
      alert('激活 RAG 失败，请重试')
      return
    }
  }
  
  currentRagId.value = rag.rag_id
  currentView.value = 'chat'
  chatHistory.value = [] // 切换 RAG 时清空对话历史
  localStorage.setItem('last_rag_id', rag.rag_id)
  currentRagIsOwned.value = true // 用户自己选择的 RAG 默认是自己的
  
  // 加载右侧工具栏数据
  loadKnowledgeGraph()
  loadRagFiles()
}

const selectRagAndClose = async (rag) => {
  await selectRag(rag)
  showUploadPanel.value = false
}

// Dashboard Methods
const loadDashboard = async () => {
  try {
    // 并行加载所有仪表盘数据
    const [statsRes, personaRes, usageRes, convsRes] = await Promise.all([
      fetch(`${API_BASE}/v1/dashboard/stats`, {
        headers: { 'Authorization': `Bearer ${authToken.value}` }
      }),
      fetch(`${API_BASE}/v1/dashboard/persona`, {
        headers: { 'Authorization': `Bearer ${authToken.value}` }
      }),
      fetch(`${API_BASE}/v1/dashboard/usage`, {
        headers: { 'Authorization': `Bearer ${authToken.value}` }
      }),
      fetch(`${API_BASE}/v1/dashboard/conversations?limit=5`, {
        headers: { 'Authorization': `Bearer ${authToken.value}` }
      })
    ])
    
    if (statsRes.ok) {
      dashboardStats.value = await statsRes.json()
    }
    
    if (personaRes.ok) {
      userPersona.value = await personaRes.json()
    }
    
    if (usageRes.ok) {
      usageStats.value = await usageRes.json()
    }
    
    if (convsRes.ok) {
      const data = await convsRes.json()
      recentConversations.value = data.conversations || []
      }
    } catch (e) {
    console.error('Failed to load dashboard:', e)
  }
}

const goToConversation = (conv) => {
  if (conv.id) {
    currentRagId.value = conv.id
    currentView.value = 'chat'
  }
}

const onRagChange = async () => {
  chatHistory.value = []
  localStorage.setItem('last_rag_id', currentRagId.value)
  
  // 如果在 pdfChat 视图，重新加载文档
  if (currentView.value === 'pdfChat') {
    await loadDocumentForParallelView()
  }
  
  // 加载知识图谱
  loadKnowledgeGraph()
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleDrop = (e) => {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files?.length) {
    uploadFile(files[0])
  }
}

const handleFileSelect = (e) => {
  const files = e.target?.files
  if (files?.length) {
    uploadFile(files[0])
  }
}

const uploadFile = async (file) => {
  isUploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = '准备上传...'
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    // Simulate progress
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += Math.random() * 15
        if (uploadProgress.value > 30) uploadStatus.value = '解析文档...'
        if (uploadProgress.value > 50) uploadStatus.value = '构建语义索引...'
        if (uploadProgress.value > 70) uploadStatus.value = '生成嵌入向量...'
      }
    }, 500)
    
    const response = await fetch(`${API_BASE}/v1/rag/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      },
      body: formData
    })
    
    clearInterval(progressInterval)
    
    // 处理重复文件错误 (409 Conflict)
    if (response.status === 409) {
      const errorData = await response.json()
      const detail = errorData.detail || {}
      uploadProgress.value = 0
      uploadStatus.value = ''
      isUploading.value = false
      
      // 显示重复文件警告
      duplicateFileInfo.value = {
        show: true,
        existingFile: detail.existing_file || '未知文件',
        existingRagId: detail.existing_rag_id || '',
        uploadedAt: detail.uploaded_at || ''
      }
      return
    }
    
    if (!response.ok) throw new Error('Upload failed')
    
    const data = await response.json()
    uploadProgress.value = 100
    uploadStatus.value = '完成！'
    
    // 刷新 RAG 列表
    await loadRagList()
    
    // 选择新上传的 RAG
    currentRagId.value = data.rag_id
    currentArch.value = data.arch || 'aipartner'
    
    // 加载右侧工具栏数据
    loadKnowledgeGraph()
    loadRagFiles()
    
    setTimeout(() => {
      isUploading.value = false
      showUploadPanel.value = false
      currentView.value = 'chat'
    }, 1000)
    
  } catch (error) {
    console.error('Upload error:', error)
    uploadStatus.value = '上传失败，请重试。'
    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
    }, 2000)
  }
}

const loadRagList = async () => {
  try {
    const response = await fetch(`${API_BASE}/v1/rag/list`, {
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      ragList.value = data.rags || []
      
      // 如果有 RAG，选择上次使用的或第一个
      if (ragList.value.length > 0) {
        const lastRagId = localStorage.getItem('last_rag_id')
        let selectedRag = ragList.value.find(r => r.rag_id === lastRagId)
        
        if (!selectedRag) {
          selectedRag = ragList.value[0]
        }
        
        // 如果选中的 RAG 未激活，先激活它
        if (selectedRag.active === false) {
          try {
            const activateResp = await fetch(`${API_BASE}/v1/rag/activate`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken.value}`
              },
              body: JSON.stringify({ rag_id: selectedRag.rag_id })
            })
            
            if (activateResp.ok) {
              selectedRag.active = true
              // 更新列表中的状态
              const idx = ragList.value.findIndex(r => r.rag_id === selectedRag.rag_id)
              if (idx >= 0) {
                ragList.value[idx].active = true
              }
    }
  } catch (e) {
            console.error('Failed to auto-activate RAG:', e)
          }
        }
        
        currentRagId.value = selectedRag.rag_id
        currentRagIsOwned.value = true // 自己的 RAG
        
        // 加载知识图谱和文档信息
        loadKnowledgeGraph()
        loadDocumentForParallelView()
      }
    }
  } catch (e) {
    console.error('Failed to load RAG list:', e)
  }
}

// PDF Citation Click Handler
const handlePdfCitationClick = (citation) => {
  console.log('Citation clicked:', citation)
  // 可以在这里添加额外的逻辑，比如高亮显示或记录
}

// 加载知识图谱 (优先使用 Graphiti API，回退到旧 Graph API)
const loadKnowledgeGraph = async () => {
  if (!currentRagId.value) return
  
  try {
    // 首先尝试使用新的 Graphiti 知识图谱 API
    const graphitiResp = await fetch(`${API_BASE}/v1/knowledge-graph/${currentRagId.value}/graph`, {
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      }
    })
    
    if (graphitiResp.ok) {
      const graphitiResult = await graphitiResp.json()
      if (graphitiResult.success && graphitiResult.data) {
        const data = graphitiResult.data
        
        // 更新 G6 格式的数据
        g6GraphData.value = {
          nodes: (data.nodes || []).map(n => ({
            id: n.id,
            label: n.name,
            type: n.group,
            summary: n.summary
          })),
          edges: (data.links || []).map((e, idx) => ({
            id: `edge-${idx}`,
            source_id: e.source,
            target_id: e.target,
            type: e.type || 'RELATED_TO',
            fact: e.fact
          }))
        }
        
        // 兼容旧的 knowledgeGraph 格式 (用于缩略图)
        knowledgeGraph.value = {
          nodes: data.nodes || [],
          links: data.links || []
        }
        
        // 更新统计信息
        kgStats.value = data.stats || { total_nodes: 0, total_edges: 0 }
        
        // 计算节点位置 (用于缩略图)
        computeNodePositions()
        
        console.log('Loaded knowledge graph from Graphiti API:', data.stats)
        return
      }
    }
    
    // 回退到旧的图谱 API
    const response = await fetch(`${API_BASE}/v1/graph/subgraph?rag_id=${currentRagId.value}&keyword=*&max_nodes=100`, {
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      const data = result.data || { nodes: [], edges: [] }
      
      // 更新 G6 格式的数据
      g6GraphData.value = {
        nodes: data.nodes || [],
        edges: data.edges || []
      }
      
      // 兼容旧的 knowledgeGraph 格式 (用于缩略图)
      knowledgeGraph.value = {
        nodes: data.nodes || [],
        links: (data.edges || []).map(e => ({
          source: e.source_id,
          target: e.target_id,
          type: e.type
        }))
      }
      
      // 计算节点位置 (用于缩略图)
      computeNodePositions()
    }
    
    // 获取统计信息
    const statsResp = await fetch(`${API_BASE}/v1/graph/stats?rag_id=${currentRagId.value}`, {
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      }
    })
    
    if (statsResp.ok) {
      const statsResult = await statsResp.json()
      kgStats.value = statsResult.data || { total_nodes: 0, total_edges: 0 }
    }
    
  } catch (e) {
    console.error('Failed to load knowledge graph:', e)
    knowledgeGraph.value = { nodes: [], links: [] }
    g6GraphData.value = { nodes: [], edges: [] }
  }
}

// 计算节点位置（改进的螺旋布局，更加分散）
const nodePositions = ref({})
const computeNodePositions = () => {
  const nodes = knowledgeGraph.value.nodes
  const width = kgViewBox.value.width
  const height = kgViewBox.value.height
  const centerX = width / 2
  const centerY = height / 2
  
  // 按类型分组节点
  const nodesByType = {}
  nodes.forEach(node => {
    const type = node.type || node.group || 'default'
    if (!nodesByType[type]) nodesByType[type] = []
    nodesByType[type].push(node)
  })
  
  const types = Object.keys(nodesByType)
  const typeCount = types.length
  
  // 每种类型占据一个扇区
  types.forEach((type, typeIdx) => {
    const typeNodes = nodesByType[type]
    const sectorAngle = (2 * Math.PI) / Math.max(typeCount, 1)
    const sectorStart = typeIdx * sectorAngle
    
    // 在扇区内使用螺旋布局
    typeNodes.forEach((node, nodeIdx) => {
      // 螺旋参数
      const spiralFactor = 0.15
      const baseRadius = Math.min(width, height) * 0.15
      const maxRadius = Math.min(width, height) * 0.42
      const progress = nodeIdx / Math.max(typeNodes.length - 1, 1)
      const radius = baseRadius + (maxRadius - baseRadius) * progress
      
      // 在扇区内分布
      const angleOffset = (nodeIdx * spiralFactor) % (sectorAngle * 0.8)
      const angle = sectorStart + sectorAngle * 0.1 + angleOffset
      
      // 添加一些随机偏移避免完全重叠
      const jitterX = (Math.random() - 0.5) * 30
      const jitterY = (Math.random() - 0.5) * 30
      
      nodePositions.value[node.id] = {
        x: centerX + radius * Math.cos(angle) + jitterX,
        y: centerY + radius * Math.sin(angle) + jitterY
      }
    })
  })
}

// 加载 RAG 文件列表
const loadRagFiles = async () => {
  if (!currentRagId.value) return
  
  try {
    const response = await fetch(`${API_BASE}/v1/rag/${currentRagId.value}/files`, {
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      ragFiles.value = data.files || []
    }
  } catch (e) {
    console.error('Failed to load RAG files:', e)
    ragFiles.value = []
  }
}

// 知识图谱辅助函数
const getNodeColor = (type) => {
  const colors = {
    person: '#FF6B6B',
    organization: '#4ECDC4',
    technology: '#45B7D1',
    concept: '#96CEB4',
    location: '#DDA0DD'
  }
  return colors[type] || '#999'
}

const getLinkCoord = (nodeId, axis) => {
  // 简化版：为缩略图使用索引位置
  const nodes = knowledgeGraph.value.nodes
  const idx = nodes.findIndex(n => n.id === nodeId)
  if (idx < 0) return 50
  return axis === 'x' ? 30 + (idx % 5) * 35 : 25 + Math.floor(idx / 5) * 35
}

const getFullNodeCoord = (nodeId, axis) => {
  const pos = nodePositions.value[nodeId]
  if (!pos) return axis === 'x' ? 400 : 300
  return pos[axis]
}

const getFileIcon = (fileName) => {
  if (!fileName) return '📄'
  const ext = fileName.split('.').pop()?.toLowerCase()
  const icons = {
    pdf: '📕',
    txt: '📝',
    md: '📘',
    docx: '📗',
    doc: '📗',
    pptx: '📙',
    ppt: '📙'
  }
  return icons[ext] || '📄'
}

const truncateFileName = (name, maxLen = 20) => {
  if (!name) return ''
  if (name.length <= maxLen) return name
  return name.slice(0, maxLen - 3) + '...'
}

// 知识图谱交互
const selectKgNode = (node) => {
  selectedKgNode.value = node
}

const startDrag = (e) => {
  isDraggingKg.value = true
  dragStart.value = { x: e.clientX - kgPan.value.x, y: e.clientY - kgPan.value.y }
}

const onDrag = (e) => {
  if (!isDraggingKg.value) return
  kgPan.value = {
    x: e.clientX - dragStart.value.x,
    y: e.clientY - dragStart.value.y
  }
}

const endDrag = () => {
  isDraggingKg.value = false
}

const onZoom = (e) => {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  kgZoom.value = Math.max(0.3, Math.min(3, kgZoom.value + delta))
}

const resetKgView = () => {
  kgZoom.value = 1
  kgPan.value = { x: 0, y: 0 }
}

// G6 图谱交互处理
const handleNodeClick = (nodeData) => {
  selectedGraphItem.value = nodeData
  selectedGraphItemType.value = 'node'
  showGraphDetail.value = true
}

const handleEdgeClick = (edgeData) => {
  selectedGraphItem.value = edgeData
  selectedGraphItemType.value = 'edge'
  showGraphDetail.value = true
}

const handleCanvasClick = () => {
  showGraphDetail.value = false
  selectedGraphItem.value = null
}

const handleGraphSearch = async (keyword) => {
  if (!currentRagId.value) return
  
  try {
    const response = await fetch(
      `${API_BASE}/v1/graph/subgraph?rag_id=${currentRagId.value}&keyword=${encodeURIComponent(keyword)}&max_nodes=100`,
      {
        headers: {
          'Authorization': `Bearer ${authToken.value}`
        }
      }
    )
    
    if (response.ok) {
      const result = await response.json()
      const data = result.data || { nodes: [], edges: [] }
      
      g6GraphData.value = {
        nodes: data.nodes || [],
        edges: data.edges || []
      }
    }
  } catch (e) {
    console.error('Failed to search graph:', e)
  }
}

const refreshKnowledgeGraph = async () => {
  if (!currentRagId.value) return
  
  try {
    // 使用新的知识图谱构建 API
    const buildResp = await fetch(`${API_BASE}/v1/knowledge-graph/${currentRagId.value}/build`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken.value}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (buildResp.ok) {
      const result = await buildResp.json()
      console.log('Knowledge graph built:', result)
    }
    
    // 重新加载
    await loadKnowledgeGraph()
  } catch (e) {
    console.error('Failed to refresh graph:', e)
  }
}

// 使用已存在的 RAG（当检测到重复文件时）
const useExistingRag = async () => {
  const ragId = duplicateFileInfo.value.existingRagId
    if (!ragId) {
    duplicateFileInfo.value.show = false
    return
  }
  
  // 查找已存在的 RAG
  const existingRag = ragList.value.find(r => r.rag_id === ragId)
  if (existingRag) {
    await selectRag(existingRag)
  }
  
  duplicateFileInfo.value.show = false
  showUploadPanel.value = false
  currentView.value = 'chat'
}

const sendMessage = async () => {
  if (!question.value.trim() || isAsking.value) return
  
  const q = question.value
  chatHistory.value.push({ role: 'user', content: q })
  question.value = ''
  isAsking.value = true
  
  // Add empty bot message for streaming
  const botMsgIndex = chatHistory.value.length
  chatHistory.value.push({ role: 'bot', content: '', streaming: true })
  
  await nextTick()
  scrollToBottom()
  
  try {
    if (useStream.value) {
      // Stream mode
      const response = await fetch(`${API_BASE}/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken.value}`
        },
        body: JSON.stringify({ rag_id: currentRagId.value, question: q })
      })
      
      if (!response.ok) throw new Error('Chat failed')
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let content = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        content += chunk
        chatHistory.value[botMsgIndex].content = content
        
        await nextTick()
        scrollToBottom()
      }
      
      chatHistory.value[botMsgIndex].streaming = false
      
    } else {
      // Non-stream mode
      const response = await fetch(`${API_BASE}/v1/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken.value}`
        },
        body: JSON.stringify({ rag_id: currentRagId.value, question: q })
      })
      
      if (!response.ok) throw new Error('Chat failed')
      
      const data = await response.json()
      chatHistory.value[botMsgIndex].content = data.answer
      chatHistory.value[botMsgIndex].streaming = false
    }
    
  } catch (error) {
    console.error('Chat error:', error)
    chatHistory.value[botMsgIndex].content = '抱歉，出现了错误。请重试。'
    chatHistory.value[botMsgIndex].streaming = false
  } finally {
    isAsking.value = false
  }
}

const sendSuggestion = (suggestion) => {
  question.value = suggestion.replace(/^[^\s]+\s/, '') // Remove emoji prefix
  sendMessage()
}

const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// ==================== NFT 铸造功能 ====================
const openMintModal = (msg, index) => {
  // 找到该答案对应的问题
  let question = ''
  for (let i = index - 1; i >= 0; i--) {
    if (chatHistory.value[i]?.role === 'user') {
      question = chatHistory.value[i].content
      break
    }
  }
  
  mintContent.value = {
    question: question,
    answer: msg.content,
    citations: msg.citations || []
  }
  mintStatus.value = null
  showMintModal.value = true
}

const shortenAddress = (address) => {
  if (!address) return ''
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

const connectWalletForMint = async () => {
  if (typeof window.ethereum !== 'undefined') {
    try {
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' })
      if (accounts.length > 0) {
        walletAddress.value = accounts[0]
        walletConnected.value = true
        
        const chainId = await window.ethereum.request({ method: 'eth_chainId' })
        const chainIdNum = parseInt(chainId, 16)
        const networks = {
          1: 'Ethereum',
          11155111: 'Sepolia',
          80002: 'Polygon Amoy',
          84532: 'Base Sepolia'
        }
        networkName.value = networks[chainIdNum] || `Chain ${chainIdNum}`
        
        mintStatus.value = { type: 'success', message: '钱包已连接！' }
      }
  } catch (e) {
      console.error('Wallet connection failed:', e)
      mintStatus.value = { type: 'error', message: '钱包连接失败：' + e.message }
    }
  } else {
    mintStatus.value = { type: 'error', message: '请安装 MetaMask 钱包' }
  }
}

const mintNFT = async () => {
  if (!walletConnected.value) {
    mintStatus.value = { type: 'error', message: '请先连接钱包' }
    return
  }
  
  isMinting.value = true
  mintStatus.value = { type: 'info', message: '正在准备 NFT 数据...' }
  
  try {
    // 1. 调用后端准备铸造数据
    const prepareResp = await fetch(`${API_BASE}/v1/web3/nft/prepare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken.value}`
      },
      body: JSON.stringify({
        question: mintContent.value.question,
        answer: mintContent.value.answer,
        sources: mintContent.value.citations,
        user_address: walletAddress.value,
        metadata: {
          rag_id: currentRagId.value,
          timestamp: new Date().toISOString()
        }
      })
    })
    
    if (!prepareResp.ok) {
      const errData = await prepareResp.json()
      throw new Error(errData.detail || '准备数据失败')
    }
    
    const prepareData = await prepareResp.json()
    
    if (!prepareData.success) {
      throw new Error(prepareData.error || '准备数据失败')
    }
    
    mintStatus.value = { type: 'info', message: '已上传到 IPFS，正在调用合约...' }
    
    // 2. 如果有合约参数，调用合约铸造
    if (prepareData.transaction_params?.contract_address) {
      const txParams = prepareData.transaction_params
      
      // 使用 ethers.js 或直接调用 MetaMask
      const encodedData = await encodeContractCall(
        txParams.params.question,
        txParams.params.answerHash,
        txParams.params.ipfsCID
      )
      
      const txData = {
        to: txParams.contract_address,
        from: walletAddress.value,
        value: '0x' + Math.floor(0.001 * 1e18).toString(16), // 0.001 ETH
        gas: '0x' + (500000).toString(16), // 设置合理的 gas limit: 500000
        data: encodedData
      }
      
      try {
        const txHash = await window.ethereum.request({
          method: 'eth_sendTransaction',
          params: [txData]
        })
        
        mintStatus.value = { 
          type: 'success', 
          message: `🎉 NFT 铸造成功！交易哈希：${txHash.slice(0, 16)}...` 
        }
        
        // 保存到已铸造列表
        const newNFT = {
          txHash,
          tokenId: mintedNFTs.value.length + 1,
          question: mintContent.value.question,
          ipfsCID: prepareData.ipfs_cid,
          timestamp: new Date().toISOString()
        }
        mintedNFTs.value.push(newNFT)
        
        // 保存到 localStorage
        localStorage.setItem('mintedNFTs', JSON.stringify(mintedNFTs.value))
        
      } catch (txError) {
        throw new Error('交易被取消或失败：' + txError.message)
      }
      
    } else {
      // 没有合约地址，只保存 IPFS 数据
      mintStatus.value = { 
        type: 'success', 
        message: `✅ 内容已保存到 IPFS！CID: ${prepareData.ipfs_cid}` 
      }
      
      mintedNFTs.value.push({
        ipfsCID: prepareData.ipfs_cid,
        question: mintContent.value.question,
        timestamp: new Date().toISOString(),
        status: 'ipfs_only'
      })
    }
    
  } catch (e) {
    console.error('Mint error:', e)
    mintStatus.value = { type: 'error', message: '铸造失败：' + e.message }
  } finally {
    isMinting.value = false
  }
}

// 编码合约调用 - 使用 ethers.js ABI 编码
const encodeContractCall = async (question, answerHash, ipfsCID) => {
  // 动态导入 ethers
  const { ethers } = await import('ethers')
  
  // 使用 ethers.js 的 Interface 来正确编码
  const iface = new ethers.Interface([
    'function mintKnowledgeNFT(string question, bytes32 answerHash, string ipfsCID) payable returns (uint256)'
  ])
  
  // 确保 answerHash 是正确的 bytes32 格式
  let hashBytes32 = answerHash
  if (!answerHash.startsWith('0x')) {
    hashBytes32 = '0x' + answerHash
  }
  // 确保是 32 字节 (64 个十六进制字符 + 0x)
  if (hashBytes32.length < 66) {
    hashBytes32 = hashBytes32.padEnd(66, '0')
  }
  
  return iface.encodeFunctionData('mintKnowledgeNFT', [question, hashBytes32, ipfsCID])
}

const formatMessage = (content) => {
  if (!content) return ''
  
  let text = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // Paragraphs
  text = text.replace(/\n\n+/g, '</p><p class="msg-para">')
  text = text.replace(/\n/g, '<br>')
  
  // Icons
  text = text.replace(/(◆|▶|✓|→|✨|📊|🎯|⚠️|✅|❌|💡|🔍|📋|🧠|ℹ️)/g, '<span class="msg-icon">$1</span>')
  
  // Bold
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // Code
  text = text.replace(/`([^`]+)`/g, '<code class="msg-code">$1</code>')
  
  return `<p class="msg-para">${text}</p>`
}

// Research Methods
const startResearch = async () => {
  if (!researchQuery.value.trim() || isResearching.value) return
  
  isResearching.value = true
  researchSteps.value = [
    { title: '分析查询', description: '理解您的研究问题...', status: 'running' },
    { title: '搜索文档', description: '查找相关信息...', status: 'pending' },
    { title: '网络搜索', description: '搜索在线资源...', status: 'pending' },
    { title: '综合分析', description: '整合研究发现...', status: 'pending' }
  ]
  
  // Call actual research API
  try {
    const response = await fetch(`${API_BASE}/v1/research/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken.value}`
      },
      body: JSON.stringify({
        rag_id: currentRagId.value,
        query: researchQuery.value,
        options: researchOptions.value
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      // Update steps from response
      if (data.steps) {
        researchSteps.value = data.steps.map(s => ({
          title: s.title,
          description: s.description,
          status: s.status,
          result: s.result
        }))
      }
    }
  } catch (e) {
    console.error('Research failed:', e)
  }
  
  isResearching.value = false
}

// QNN Deep Research
const startQNNResearch = async () => {
  if (!researchQuery.value.trim() || isResearching.value) return
  if (qnnConfig.value.selectedMbtis.length < 2) {
    alert('请至少选择 2 种 MBTI 人格类型')
    return
  }
  
  isResearching.value = true
  researchProgress.value = []
  researchEpochs.value = []
  researchResult.value = null
  
  try {
    const response = await fetch(`${API_BASE}/v1/research/${currentRagId.value}/qnn-research`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken.value}`
      },
      body: JSON.stringify({
        query: researchQuery.value,
        qnn_depth: qnnConfig.value.depth,
        qnn_agents_per_layer: qnnConfig.value.agentsPerLayer,
        max_epochs: qnnConfig.value.maxEpochs,
        selected_mbtis: qnnConfig.value.selectedMbtis
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            
            if (data.type === 'status' || data.type === 'progress' || data.type === 'warning') {
              researchProgress.value.push({
                type: data.type,
                message: data.message
              })
            } else if (data.type === 'epoch') {
              researchProgress.value.push({
                type: 'epoch',
                message: `✅ Epoch ${data.epoch} 完成`
              })
            } else if (data.type === 'result') {
              researchResult.value = data
              if (data.epochs_detail) {
                researchEpochs.value = data.epochs_detail
              }
            } else if (data.type === 'error') {
              researchProgress.value.push({
                type: 'error',
                message: `❌ ${data.message}`
              })
            }
  } catch (e) {
            console.warn('Parse error:', e)
          }
        }
      }
    }
  } catch (e) {
    console.error('QNN Research failed:', e)
    researchProgress.value.push({
      type: 'error',
      message: `研究失败: ${e.message}`
    })
  }
  
  isResearching.value = false
}

// Format Markdown (simple version)
const formatMarkdown = (text) => {
  if (!text) return ''
  
  // 转义 HTML
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // 标题
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  
  // 粗体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  
  // 斜体
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  
  // 列表
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
  
  // 段落
  html = html.replace(/\n\n/g, '</p><p>')
  html = '<p>' + html + '</p>'
  
  // 换行
  html = html.replace(/\n/g, '<br>')
  
  return html
}

// Memory Methods
const loadMemories = async () => {
  if (!isLoggedIn.value) return
  
  try {
    const response = await fetch(`${API_BASE}/v1/memory/`, {
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      memories.value = result.memories.map(m => ({
        id: m.id,
        text: m.text,
        date: new Date(m.created_at).toLocaleDateString(),
        source: m.source === 'manual' ? '手动添加' : m.source === 'auto' ? '自动提取' : m.source,
        importance: m.importance
      }))
    }
  } catch (error) {
    console.error('加载记忆失败:', error)
  }
}

const addMemory = async () => {
  if (!newMemory.value.trim() || !isLoggedIn.value) return
  
  try {
    const response = await fetch(`${API_BASE}/v1/memory/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken.value}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: newMemory.value,
        source: 'manual',
        importance: 0.7
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      memories.value.unshift({
        id: result.memory.id,
        text: result.memory.text,
        date: new Date(result.memory.created_at).toLocaleDateString(),
        source: '手动添加',
        importance: result.memory.importance
      })
      newMemory.value = ''
    }
  } catch (error) {
    console.error('添加记忆失败:', error)
  }
}

const deleteMemory = async (index) => {
  if (!isLoggedIn.value) return
  
  const memory = memories.value[index]
  if (!memory?.id) {
    // 兼容旧的 localStorage 数据
    memories.value.splice(index, 1)
    return
  }
  
  try {
    const response = await fetch(`${API_BASE}/v1/memory/${memory.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      }
    })
    
    if (response.ok) {
      memories.value.splice(index, 1)
    }
  } catch (error) {
    console.error('删除记忆失败:', error)
  }
}

// RAG Hall Methods
const loadRagHall = async () => {
  try {
    const response = await fetch(`${API_BASE}/v1/rag/hall`, {
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      ragHallList.value = data.rags || []
    }
  } catch (e) {
    console.error('Failed to load RAG hall:', e)
  }
}

const enterRagFromHall = (rag) => {
  // 进入该 RAG 的问答界面
  currentRagId.value = rag.rag_id
  currentView.value = 'chat'
  chatHistory.value = []
}

const enterRagChat = async (rag) => {
  currentRagId.value = rag.rag_id
  currentView.value = 'chat'
  chatHistory.value = []
  
  // 记录访问
  try {
    await fetch(`${API_BASE}/v1/rag/access`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken.value}`
      },
      body: JSON.stringify({ rag_id: rag.rag_id })
    })
  } catch (e) {
    console.error('Failed to record RAG access:', e)
  }
}

// Discussion Methods
const loadDiscussionRooms = async () => {
  try {
    const response = await fetch(`${API_BASE}/v1/discussion/rooms`, {
      headers: {
        'Authorization': `Bearer ${authToken.value}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      discussionRooms.value = data.rooms || []
    }
  } catch (e) {
    console.error('Failed to load discussion rooms:', e)
  }
}

const joinRagDiscussion = async (ragId) => {
  try {
    const response = await fetch(`${API_BASE}/v1/discussion/join`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken.value}`
      },
      body: JSON.stringify({ rag_id: ragId })
    })
    
    if (response.ok) {
      const data = await response.json()
      await connectToDiscussion(data.room_id, ragId)
    }
  } catch (e) {
    console.error('Failed to join discussion:', e)
    alert('加入讨论失败，请重试')
  }
}

const joinRoom = async (roomId, ragId) => {
  await connectToDiscussion(roomId, ragId)
}

const connectToDiscussion = async (roomId, ragId) => {
  // 关闭现有连接
  if (discussionWebSocket.value) {
    discussionWebSocket.value.close()
  }
  
  // 获取用户ID
  const storedUser = localStorage.getItem('username') || currentUser.value
  
  // 建立 WebSocket 连接
  const wsUrl = `ws://localhost:8000/ws/discussion/${roomId}`
  const ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('WebSocket connected')
    // 发送认证消息
    ws.send(JSON.stringify({
      type: 'auth',
      user_id: storedUser,
      username: storedUser
    }))
    currentUserId.value = storedUser
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'history') {
      // 收到历史消息
      currentDiscussionRoom.value = data.data.room
      discussionMessages.value = data.data.messages || []
      isDiscussionConnected.value = true
      currentView.value = 'discussion'
      
      nextTick(() => scrollDiscussionToBottom())
    } else if (data.type === 'message') {
      // 收到新消息
      discussionMessages.value.push(data.data)
      nextTick(() => scrollDiscussionToBottom())
    } else if (data.type === 'pong') {
      // 心跳响应
    }
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    isDiscussionConnected.value = false
  }
  
  ws.onclose = () => {
    console.log('WebSocket closed')
    isDiscussionConnected.value = false
  }
  
  discussionWebSocket.value = ws
  
  // 启动心跳
  const heartbeat = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    } else {
      clearInterval(heartbeat)
    }
  }, 30000)
}

const sendDiscussionMessage = () => {
  if (!discussionInput.value.trim() || !isDiscussionConnected.value) return
  
  if (discussionWebSocket.value && discussionWebSocket.value.readyState === WebSocket.OPEN) {
    discussionWebSocket.value.send(JSON.stringify({
      type: 'message',
      content: discussionInput.value.trim()
    }))
    discussionInput.value = ''
  }
}

const leaveDiscussion = () => {
  if (discussionWebSocket.value) {
    discussionWebSocket.value.send(JSON.stringify({ type: 'leave' }))
    discussionWebSocket.value.close()
    discussionWebSocket.value = null
  }
  
  isDiscussionConnected.value = false
  discussionMessages.value = []
  currentDiscussionRoom.value = null
  currentView.value = 'discussionHall'
  loadDiscussionRooms()
}

const scrollDiscussionToBottom = () => {
  if (discussionMessagesRef.value) {
    discussionMessagesRef.value.scrollTop = discussionMessagesRef.value.scrollHeight
  }
}

// 从 Chat 进入讨论
const joinDiscussionFromChat = async () => {
  if (!currentRagId.value) return
  await joinRagDiscussion(currentRagId.value)
}

// Auth
const autoAuth = async () => {
  const storedToken = localStorage.getItem('auth_token')
  const storedUser = localStorage.getItem('username')
  
  if (storedToken) {
    try {
      const resp = await fetch(`${API_BASE}/v1/auth/me`, {
        headers: { 'Authorization': `Bearer ${storedToken}` }
      })
      if (resp.ok) {
        authToken.value = storedToken
        currentUser.value = storedUser || 'User'
        isLoggedIn.value = true
        return true
      }
    } catch (e) {
      console.log('Token validation failed')
    }
  }
  
  // 不再自动注册，默认未登录状态
  isLoggedIn.value = false
  currentView.value = 'ragHall'  // 未登录默认进入 RAG 大厅
  return false
}

// 登录/注册处理
const handleAuth = async () => {
  authError.value = ''
  isAuthLoading.value = true
  
  try {
    const endpoint = authMode.value === 'login' ? '/v1/auth/login' : '/v1/auth/register'
    const body = authMode.value === 'login' 
      ? { username: authForm.value.username, password: authForm.value.password }
      : { username: authForm.value.username, email: authForm.value.email, password: authForm.value.password }
    
    const resp = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    
    if (resp.ok) {
      const data = await resp.json()
      authToken.value = data.access_token
      currentUser.value = data.username || authForm.value.username
      isLoggedIn.value = true
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('username', currentUser.value)
      
      // 关闭模态框并清空表单
      showAuthModal.value = false
      authForm.value = { username: '', email: '', password: '' }
      
      // 加载用户数据
      await loadRagList()
      
      // 如果有 RAG，进入问答界面
      if (hasRags.value) {
        currentView.value = 'chat'
      }
    } else {
      const errorData = await resp.json()
      authError.value = errorData.detail || '认证失败，请重试'
    }
  } catch (e) {
    console.error('Auth failed:', e)
    authError.value = '网络错误，请检查连接'
  } finally {
    isAuthLoading.value = false
  }
}

// 退出登录
const logout = () => {
  authToken.value = ''
  currentUser.value = ''
  isLoggedIn.value = false
  ragList.value = []
  currentRagId.value = ''
  chatHistory.value = []
  localStorage.removeItem('auth_token')
  localStorage.removeItem('username')
  currentView.value = 'ragHall'
}

// Lifecycle
onMounted(async () => {
  // Load theme
  const savedTheme = localStorage.getItem('theme')
  isDarkMode.value = savedTheme === 'dark'
  
  // 尝试自动登录
  const authSuccess = await autoAuth()
  
  // 登录成功后加载记忆
  if (authSuccess) {
    loadMemories()
  }
  
  if (authSuccess) {
    // 已登录用户：加载 RAG 列表
    await loadRagList()
    
    // 根据是否有 RAG 决定显示什么
    if (hasRags.value) {
      currentView.value = 'chat'
      showUploadPanel.value = false
    } else {
      showUploadPanel.value = true
    }
  } else {
    // 未登录用户：默认进入 RAG 大厅
    currentView.value = 'ragHall'
    loadRagHall()
  }
  
  isInitializing.value = false
})

// Watch for chat changes to scroll
watch(chatHistory, () => {
  nextTick(() => scrollToBottom())
}, { deep: true })
</script>

<style>
/* CSS Variables */
:root {
  --bg-primary: #fafafa;
  --bg-secondary: #ffffff;
  --bg-tertiary: #f3f4f6;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;
  --border-color: #e5e7eb;
  --accent-color: #f97316;
  --accent-light: #fed7aa;
  --accent-dark: #c2410c;
  --success-color: #10b981;
  --error-color: #ef4444;
  --gradient-primary: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
  --gradient-hero: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f97316 100%);
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
}

.dark-mode {
  --bg-primary: #0f0f0f;
  --bg-secondary: #1a1a1a;
  --bg-tertiary: #262626;
  --text-primary: #f9fafb;
  --text-secondary: #d1d5db;
  --text-muted: #9ca3af;
  --border-color: #374151;
  --accent-light: #431407;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
}

/* Layout */
.app-container {
  display: flex;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* Sidebar */
.sidebar {
  width: 260px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: fixed;
  height: 100vh;
  z-index: 100;
}

.sidebar-collapsed {
  width: 72px;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-toggle {
  background: var(--bg-tertiary);
  border: none;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  width: 100%;
  text-align: left;
}

.nav-item:hover:not(:disabled) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent-light);
  color: var(--accent-color);
}

.nav-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.nav-icon {
  font-size: 18px;
}

/* RAG List in Sidebar */
.rag-list-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.rag-list-header {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
}

.rag-list-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.rag-list-item:hover {
  background: var(--bg-tertiary);
}

.rag-list-item.active {
  background: var(--accent-light);
  color: var(--accent-color);
}

.rag-list-item.inactive {
  opacity: 0.6;
}

.rag-list-item.inactive:hover {
  opacity: 1;
}

.rag-item-icon {
  font-size: 14px;
}

.rag-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

/* Main Content */
.main-content {
  flex: 1;
  margin-left: 260px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
  position: relative;
}

.sidebar-collapsed + .main-content {
  margin-left: 72px;
}

.main-header {
  padding: 16px 32px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 50;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rag-selector {
  display: flex;
  align-items: center;
}

.rag-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  min-width: 150px;
}

.upload-toggle-btn {
  padding: 8px 16px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-toggle-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

.rag-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--success-color);
  color: white;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: white;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Upload Panel */
.upload-panel {
  padding: 32px;
  background: var(--bg-primary);
}

.upload-panel.is-overlay {
  position: absolute;
  top: 60px;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 40;
  overflow-y: auto;
}

.upload-panel-content {
  max-width: 700px;
  margin: 0 auto;
}

.upload-panel-header {
  text-align: center;
  margin-bottom: 24px;
}

.upload-panel-header h3 {
  font-size: 20px;
  margin-bottom: 8px;
}

.upload-panel-header p {
  color: var(--text-secondary);
}

.welcome-header {
  text-align: center;
  margin-bottom: 32px;
}

.hero-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
}

.gradient-text {
  background: var(--gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
}

/* Upload Card */
.upload-card {
  background: var(--bg-secondary);
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-xl);
  padding: 48px;
  margin-bottom: 32px;
  transition: all 0.3s ease;
}

.upload-card.compact {
  padding: 32px;
}

.upload-card.is-dragging {
  border-color: var(--accent-color);
  background: var(--accent-light);
}

.upload-dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.hidden-input {
  display: none;
}

.upload-icon-circle {
  width: 80px;
  height: 80px;
  background: var(--gradient-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(249, 115, 22, 0.3);
}

.upload-icon-circle.small {
  width: 56px;
  height: 56px;
  font-size: 24px;
  margin-bottom: 16px;
}

.upload-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.upload-text {
  text-align: center;
}

.upload-primary {
  display: block;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.upload-primary.uploading {
  color: var(--accent-color);
}

.upload-link {
  color: var(--accent-color);
  text-decoration: underline;
}

.upload-secondary {
  font-size: 13px;
  color: var(--text-muted);
}

.upload-progress {
  margin-top: 24px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--gradient-primary);
  transition: width 0.3s ease;
}

.progress-text {
  display: block;
  text-align: center;
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

/* Uploaded Files Section */
.uploaded-files-section {
  margin-top: 24px;
}

.uploaded-files-section h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-secondary);
}

.uploaded-files-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.uploaded-file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.uploaded-file-item:hover {
  border-color: var(--accent-color);
}

.uploaded-file-item.active {
  border-color: var(--accent-color);
  background: var(--accent-light);
}

.file-icon {
  font-size: 20px;
}

.file-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.file-action {
  font-size: 12px;
  color: var(--accent-color);
}

.file-status {
  font-size: 11px;
  color: var(--text-muted);
  padding: 2px 6px;
  background: var(--bg-tertiary);
  border-radius: 4px;
}

.uploaded-file-item.inactive {
  opacity: 0.7;
}

.uploaded-file-item.inactive:hover {
  opacity: 1;
}

/* View Container */
.view-container {
  flex: 1;
  overflow-y: auto;
}

/* Chat View */
.chat-view {
  padding: 0;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
}

/* Chat with Tools Layout */
.chat-with-tools-layout {
  display: flex;
  flex: 1;
  height: 100%;
  overflow: hidden;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* Right Toolbar */
.right-toolbar {
  width: 280px;
  background: var(--color-bg-secondary, #f8f9fa);
  border-left: 1px solid var(--color-border, #e5e7eb);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: relative;
}

.right-toolbar.collapsed {
  width: 40px;
}

.toolbar-toggle {
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: var(--color-primary, #ff7e33);
  border-radius: 12px 0 0 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  font-size: 12px;
  z-index: 10;
  box-shadow: -2px 0 8px rgba(0,0,0,0.1);
}

.toolbar-toggle:hover {
  background: var(--color-primary-dark, #e66b25);
}

.toolbar-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.toolbar-section {
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--color-text, #333);
}

.section-icon {
  font-size: 16px;
}

.section-title {
  flex: 1;
  font-size: 14px;
}

.expand-btn {
  background: none;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
  padding: 2px 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.expand-btn:hover {
  background: var(--color-primary, #ff7e33);
  color: white;
  border-color: var(--color-primary, #ff7e33);
}

/* Knowledge Graph Thumbnail */
.kg-section {
  flex: 0 0 auto;
}

.kg-thumbnail {
  background: white;
  border-radius: 8px;
  border: 1px solid var(--color-border, #e5e7eb);
  padding: 8px;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 120px;
}

.kg-thumbnail:hover {
  border-color: var(--color-primary, #ff7e33);
  box-shadow: 0 2px 8px rgba(255, 126, 51, 0.2);
}

.kg-mini {
  width: 100%;
  height: 100px;
}

.kg-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #999;
  font-size: 12px;
}

.kg-placeholder span {
  font-size: 32px;
  margin-bottom: 8px;
  opacity: 0.5;
}

.kg-stats {
  display: flex;
  justify-content: space-around;
  font-size: 11px;
  color: #666;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #eee;
}

.toolbar-divider {
  height: 1px;
  background: var(--color-border, #e5e7eb);
  margin: 16px 0;
}

/* Files Section */
.files-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.file-count {
  background: var(--color-primary, #ff7e33);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.files-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: white;
  border-radius: 8px;
  border: 1px solid var(--color-border, #e5e7eb);
  transition: all 0.2s;
}

.file-item:hover {
  border-color: var(--color-primary, #ff7e33);
}

.file-icon {
  font-size: 20px;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text, #333);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 11px;
  color: #999;
}

.no-files {
  text-align: center;
  color: #999;
  padding: 20px;
  font-size: 13px;
}

.add-file-btn {
  margin-top: 12px;
  padding: 10px;
  background: var(--color-primary, #ff7e33);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.add-file-btn:hover {
  background: var(--color-primary-dark, #e66b25);
}

/* Knowledge Graph Modal */
.kg-modal-overlay {
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
}

.kg-modal {
  background: white;
  border-radius: 16px;
  width: 90vw;
  max-width: 1200px;
  height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.kg-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
}

.kg-modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.kg-modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kg-action-btn {
  padding: 6px 12px;
  background: var(--accent-light);
  border: 1px solid var(--accent-color);
  border-radius: 6px;
  color: var(--accent-color);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.kg-action-btn:hover {
  background: var(--accent-color);
  color: white;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
  padding: 4px 8px;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f0f0f0;
}

.kg-modal-content {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #fafafa;
}

.kg-full {
  width: 100%;
  height: 100%;
  cursor: grab;
}

.kg-full:active {
  cursor: grabbing;
}

.node-group {
  cursor: pointer;
}

.node-group:hover circle {
  stroke-width: 3px;
  filter: drop-shadow(0 0 6px rgba(0,0,0,0.3));
}

.kg-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  gap: 16px;
  font-size: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-item .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.kg-controls {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  gap: 8px;
}

.kg-controls button {
  background: white;
  border: 1px solid #ddd;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.kg-controls button:hover {
  background: var(--color-primary, #ff7e33);
  color: white;
  border-color: var(--color-primary, #ff7e33);
}

.kg-node-detail {
  padding: 16px 24px;
  border-top: 1px solid #eee;
  background: #f9f9f9;
}

.kg-node-detail h4 {
  margin: 0 0 8px 0;
  color: var(--color-primary, #ff7e33);
}

.kg-node-detail p {
  margin: 4px 0;
  font-size: 13px;
  color: #666;
}

/* Duplicate File Warning */
.duplicate-warning {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 12px;
  margin-top: 16px;
}

.warning-icon {
  font-size: 32px;
}

.warning-content {
  flex: 1;
}

.warning-content h4 {
  margin: 0 0 8px 0;
  color: #856404;
}

.warning-content p {
  margin: 4px 0;
  color: #664d03;
  font-size: 14px;
}

.warning-meta {
  font-size: 12px !important;
  color: #997404 !important;
}

.warning-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.use-existing-btn {
  padding: 8px 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}

.use-existing-btn:hover {
  background: #218838;
}

.dismiss-btn {
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.dismiss-btn:hover {
  background: #5a6268;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
}

.chat-empty {
  text-align: center;
  padding: 48px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.chat-empty h3 {
  font-size: 20px;
  margin-bottom: 8px;
}

.chat-empty p {
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.suggestion-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-width: 500px;
  margin: 0 auto;
}

.suggestion-card {
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  text-align: left;
  transition: all 0.2s ease;
}

.suggestion-card:hover {
  border-color: var(--accent-color);
  background: var(--accent-light);
}

/* Chat Message */
.chat-message {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.chat-message.user .message-avatar {
  background: var(--gradient-primary);
}

.message-content {
  flex: 1;
  max-width: 70%;
}

.chat-message.user .message-content {
  text-align: right;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.chat-message.user .message-header {
  justify-content: flex-end;
}

.message-role {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: var(--accent-color);
  border-radius: 50%;
  animation: bounce 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.message-text {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
}

.chat-message.user .message-text {
  background: var(--gradient-primary);
  color: white;
  border: none;
}

.message-text .msg-para {
  margin: 0 0 12px;
}

.message-text .msg-para:last-child {
  margin-bottom: 0;
}

.message-text .msg-icon {
  margin-right: 6px;
}

.message-text .msg-code {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  font-size: 13px;
}

.chat-message.user .message-text .msg-code {
  background: rgba(255,255,255,0.2);
}

/* Chat Input */
.chat-input-container {
  padding: 24px 32px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-xl);
  padding: 8px 8px 8px 20px;
  border: 1px solid var(--border-color);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  resize: none;
  outline: none;
  color: var(--text-primary);
  font-family: inherit;
}

.chat-input::placeholder {
  color: var(--text-muted);
}

.send-button {
  width: 44px;
  height: 44px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.send-button:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.input-hint {
  text-align: center;
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

/* PDF Chat View */
.pdf-chat-view {
  padding: 0;
  height: calc(100vh - 80px);
  overflow: hidden;
}

.pdf-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
}

.pdf-loading .loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border-color);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

/* Research View */
.research-view {
  padding: 32px;
  display: flex;
  justify-content: center;
}

.research-container {
  max-width: 700px;
  width: 100%;
}

.research-header {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 32px;
}

.research-icon {
  font-size: 48px;
}

.research-info h2 {
  font-size: 24px;
  margin-bottom: 4px;
}

.research-info p {
  color: var(--text-secondary);
}

.research-input-area {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 32px;
}

.research-input {
  width: 100%;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px;
  font-size: 15px;
  resize: none;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: inherit;
  margin-bottom: 16px;
}

.research-options {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
}

.research-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.research-option input {
  accent-color: var(--accent-color);
}

.research-button {
  width: 100%;
  padding: 16px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.research-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(249, 115, 22, 0.3);
}

.research-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Research Steps */
.research-steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.research-step {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.research-step.completed {
  border-color: var(--success-color);
}

.research-step.running {
  border-color: var(--accent-color);
}

.step-indicator {
  width: 32px;
  height: 32px;
  background: var(--bg-tertiary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.research-step.completed .step-indicator {
  background: var(--success-color);
  color: white;
}

.research-step.running .step-indicator {
  background: var(--accent-color);
  color: white;
}

.step-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.step-content {
  flex: 1;
}

.step-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.step-description {
  font-size: 13px;
  color: var(--text-secondary);
}

.step-result {
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--success-color);
}

/* QNN Configuration Section */
.qnn-config-section {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.05) 0%, rgba(34, 197, 94, 0.05) 100%);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-top: 20px;
}

.config-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.config-icon {
  font-size: 20px;
}

.config-title {
  font-weight: 600;
  font-size: 15px;
}

.config-subtitle {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-left: auto;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
}

.label-icon {
  font-size: 14px;
}

.config-slider {
  display: flex;
  align-items: center;
  gap: 10px;
}

.config-slider input[type="range"] {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: var(--bg-tertiary);
  accent-color: var(--accent-color);
  cursor: pointer;
}

.slider-value {
  min-width: 50px;
  text-align: right;
  font-weight: 600;
  color: var(--accent-color);
  font-size: 14px;
}

.config-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.time-estimate {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  font-size: 13px;
}

.estimate-icon {
  font-size: 16px;
}

.estimate-text strong {
  color: var(--accent-color);
}

/* MBTI Section */
.mbti-section {
  margin-top: 20px;
  padding: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.mbti-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.mbti-icon {
  font-size: 20px;
}

.mbti-title {
  font-weight: 600;
}

.mbti-subtitle {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-left: auto;
}

.mbti-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.mbti-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--bg-tertiary);
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.mbti-option:hover:not(.disabled) {
  background: var(--bg-primary);
  border-color: var(--border-color);
}

.mbti-option.selected {
  background: rgba(249, 115, 22, 0.1);
  border-color: var(--accent-color);
}

.mbti-option.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.mbti-option input[type="checkbox"] {
  display: none;
}

.mbti-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mbti-type {
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.5px;
}

.mbti-name {
  font-size: 11px;
  color: var(--text-secondary);
}

/* Research Progress */
.research-progress {
  margin-top: 24px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
}

.progress-icon {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.progress-log {
  max-height: 200px;
  overflow-y: auto;
  padding: 12px 16px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

.progress-item {
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
}

.progress-item.status {
  color: var(--text-secondary);
}

.progress-item.progress {
  color: var(--accent-color);
}

.progress-item.warning {
  color: #f59e0b;
}

.progress-item.epoch {
  color: var(--success-color);
  font-weight: 500;
}

.progress-item.error {
  color: var(--danger-color);
}

/* Epochs Section */
.epochs-section {
  margin-top: 24px;
}

.epochs-header {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.epoch-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 12px;
}

.epoch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.epoch-number {
  font-weight: 700;
  color: var(--accent-color);
}

.epoch-duration {
  font-size: 12px;
  color: var(--text-tertiary);
}

.epoch-problem, .epoch-synthesis {
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 8px;
}

.epoch-problem strong, .epoch-synthesis strong {
  color: var(--text-secondary);
}

/* Research Result */
.research-result {
  margin-top: 24px;
  background: var(--bg-secondary);
  border: 1px solid var(--success-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(34, 197, 94, 0.1);
  border-bottom: 1px solid var(--border-color);
}

.result-icon {
  font-size: 20px;
}

.result-meta {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-tertiary);
}

.insights-section {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  background: rgba(249, 115, 22, 0.05);
}

.insights-title {
  font-weight: 600;
  margin-bottom: 12px;
}

.insights-list {
  margin: 0;
  padding-left: 20px;
}

.insights-list li {
  margin-bottom: 8px;
  line-height: 1.5;
  color: var(--text-primary);
}

.full-report {
  padding: 20px;
}

.report-content {
  font-size: 14px;
  line-height: 1.7;
}

.report-content h1, .report-content h2, .report-content h3 {
  margin-top: 16px;
  margin-bottom: 8px;
}

.report-content h1 { font-size: 20px; }
.report-content h2 { font-size: 18px; }
.report-content h3 { font-size: 16px; }

.report-content p {
  margin-bottom: 12px;
}

.report-content li {
  margin-bottom: 4px;
}

.network-summary {
  padding: 16px;
  background: var(--bg-tertiary);
  border-top: 1px solid var(--border-color);
}

.summary-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.summary-stats {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

/* Responsive */
@media (max-width: 768px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
  
  .mbti-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Memory View */
.memory-view {
  padding: 32px;
}

.memory-container {
  max-width: 700px;
  margin: 0 auto;
}

.memory-header {
  text-align: center;
  margin-bottom: 32px;
}

.memory-header h2 {
  font-size: 24px;
  margin-bottom: 8px;
}

.memory-header p {
  color: var(--text-secondary);
}

.memory-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.memory-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  align-items: flex-start;
}

.memory-icon {
  font-size: 24px;
}

.memory-content {
  flex: 1;
}

.memory-text {
  font-size: 14px;
  margin-bottom: 8px;
}

.memory-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

.memory-delete {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 20px;
  cursor: pointer;
  border-radius: var(--radius-sm);
}

.memory-delete:hover {
  background: var(--error-color);
  color: white;
}

.memory-empty {
  text-align: center;
  padding: 48px;
  color: var(--text-secondary);
}

.memory-add {
  display: flex;
  gap: 12px;
}

.memory-add input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
}

.memory-add button {
  padding: 12px 24px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

/* Loading Overlay */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border-color);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-overlay p {
  color: var(--text-secondary);
}

/* Nav Divider */
.nav-divider {
  height: 1px;
  background: var(--border-color);
  margin: 12px 16px;
}

/* Input Actions */
.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.join-discussion-chat-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.join-discussion-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Hall View */
.hall-view {
  padding: 32px;
  overflow-y: auto;
}

.hall-container {
  max-width: 1200px;
  margin: 0 auto;
}

.hall-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.hall-title h2 {
  font-size: 28px;
  margin-bottom: 8px;
}

.hall-title p {
  color: var(--text-secondary);
}

.create-rag-btn {
  padding: 12px 24px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.create-rag-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(249, 115, 22, 0.3);
}

.hall-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.hall-empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 64px;
  background: var(--bg-secondary);
  border-radius: var(--radius-xl);
  border: 2px dashed var(--border-color);
}

.hall-empty .empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.hall-empty h3 {
  font-size: 20px;
  margin-bottom: 8px;
}

.hall-empty p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.goto-hall-btn {
  padding: 12px 24px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

/* RAG Card */
.rag-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.rag-card:hover {
  border-color: var(--accent-color);
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.rag-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.rag-card-icon {
  font-size: 32px;
}

.rag-card-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.active-discussion-badge {
  padding: 4px 8px;
  background: #ef4444;
  color: white;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  animation: pulse 2s infinite;
}

.user-count-badge {
  padding: 4px 8px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: 12px;
  font-size: 11px;
}

.rag-card-title {
  font-size: 18px;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rag-card-info {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.rag-card-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.primary {
  background: var(--gradient-primary);
  color: white;
}

.action-btn.secondary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-btn:hover {
  transform: translateY(-1px);
}

/* Discussion Card */
.discussion-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.discussion-card:hover {
  border-color: #667eea;
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.discussion-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.discussion-card-icon {
  font-size: 32px;
}

.live-badge {
  padding: 4px 12px;
  background: #ef4444;
  color: white;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  animation: pulse 2s infinite;
}

.discussion-card-title {
  font-size: 16px;
  margin-bottom: 12px;
}

.discussion-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.discussion-stats .stat {
  font-size: 13px;
  color: var(--text-secondary);
}

.discussion-users {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
}

.user-avatar-small {
  width: 28px;
  height: 28px;
  background: var(--gradient-primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.more-users {
  width: 28px;
  height: 28px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
}

.join-discussion-btn {
  width: 100%;
  padding: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.join-discussion-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Discussion View */
.discussion-view {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

.discussion-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  padding: 24px;
}

.discussion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
}

.discussion-info h2 {
  font-size: 18px;
  margin-bottom: 4px;
}

.discussion-info p {
  font-size: 13px;
  color: var(--text-secondary);
}

.discussion-members {
  display: flex;
  align-items: center;
  gap: 16px;
}

.member-count {
  font-size: 13px;
  color: var(--text-secondary);
}

.leave-btn {
  padding: 8px 16px;
  background: var(--error-color);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.discussion-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
}

.discussion-message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeInUp 0.2s ease;
}

.discussion-message.own-message {
  flex-direction: row-reverse;
}

.discussion-message.system-message {
  justify-content: center;
}

.msg-avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.own-message .msg-avatar {
  background: var(--gradient-primary);
}

.msg-body {
  max-width: 70%;
}

.own-message .msg-body {
  text-align: right;
}

.msg-header {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.own-message .msg-header {
  flex-direction: row-reverse;
}

.msg-username {
  font-weight: 600;
  color: var(--text-primary);
}

.msg-time {
  color: var(--text-muted);
}

.msg-content {
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  font-size: 14px;
  line-height: 1.5;
}

.own-message .msg-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.system-content {
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  text-align: center;
  padding: 8px;
}

.discussion-input {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.discussion-input input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 14px;
}

.discussion-input button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.discussion-input button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.discussion-input button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Dashboard View */
.dashboard-view {
  padding: 24px;
  overflow-y: auto;
  height: calc(100vh - 60px);
}

/* Spark Dashboard View */
.spark-view {
  padding: 24px;
  overflow-y: auto;
  height: calc(100vh - 60px);
  background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
}

.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.dashboard-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Persona Section */
.persona-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-primary) 100%);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
}

.persona-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-color) 0%, #fb923c 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-icon {
  font-size: 32px;
  font-weight: 700;
  color: white;
}

.persona-info {
  flex: 1;
}

.persona-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.persona-role {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.persona-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.persona-tag {
  padding: 6px 12px;
  background: var(--accent-light);
  color: var(--accent-color);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

/* Usage Section */
.usage-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.usage-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.usage-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.usage-icon {
  font-size: 32px;
}

.usage-details {
  display: flex;
  flex-direction: column;
}

.usage-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'JetBrains Mono', monospace;
}

.usage-label {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Conversations Section */
.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.conversation-item:hover {
  background: var(--bg-primary);
  transform: translateX(4px);
}

.conv-icon {
  font-size: 24px;
}

.conv-content {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-preview {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-time {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.empty-conversations {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.empty-conversations .empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}

.empty-conversations p {
  font-size: 14px;
}

/* NFT Mint Button */
.message-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.mint-nft-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.mint-nft-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

/* NFT Mint Modal */
.mint-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
  animation: fadeIn 0.2s ease;
}

.mint-modal {
  background: var(--bg-secondary);
  border-radius: 20px;
  padding: 32px;
  width: 100%;
  max-width: 520px;
  position: relative;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
  animation: slideUp 0.3s ease;
}

.mint-close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  background: var(--bg-tertiary);
  border-radius: 50%;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 16px;
  transition: all 0.2s;
}

.mint-close-btn:hover {
  background: var(--error-color);
  color: white;
}

.mint-header {
  text-align: center;
  margin-bottom: 24px;
}

.mint-header h2 {
  font-size: 24px;
  margin-bottom: 8px;
}

.mint-header p {
  color: var(--text-secondary);
}

.mint-preview {
  background: var(--bg-tertiary);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.preview-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.preview-question {
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--primary-color);
}

.preview-answer {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
  max-height: 120px;
  overflow-y: auto;
}

.mint-wallet-section {
  text-align: center;
  padding: 20px;
}

.connect-wallet-btn {
  padding: 14px 28px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.connect-wallet-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

.wallet-hint {
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.mint-wallet-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  margin-bottom: 16px;
}

.wallet-address {
  font-family: monospace;
  padding: 4px 8px;
  background: var(--bg-primary);
  border-radius: 4px;
}

.network-badge {
  padding: 4px 10px;
  background: #10b981;
  color: white;
  border-radius: 12px;
  font-size: 12px;
}

.mint-status {
  margin-bottom: 16px;
}

.status-message {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
}

.status-message.info {
  background: #e0f2fe;
  color: #0369a1;
}

.status-message.success {
  background: #d1fae5;
  color: #059669;
}

.status-message.error {
  background: #fee2e2;
  color: #dc2626;
}

.mint-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.mint-btn-primary {
  flex: 1;
  padding: 14px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.mint-btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.mint-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mint-btn-secondary {
  padding: 14px 24px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: none;
  border-radius: 12px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}

.mint-btn-secondary:hover {
  background: var(--border-color);
}

.mint-notice {
  text-align: center;
  padding: 12px;
  background: #fef3c7;
  border-radius: 8px;
}

.mint-notice p {
  margin: 0;
  font-size: 13px;
  color: #92400e;
}

/* Auth Modal */
.auth-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.auth-modal {
  background: var(--bg-secondary);
  border-radius: var(--radius-xl);
  padding: 40px;
  width: 100%;
  max-width: 420px;
  position: relative;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  background: var(--bg-tertiary);
  border-radius: 50%;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 16px;
  transition: all 0.2s;
}

.auth-close-btn:hover {
  background: var(--error-color);
  color: white;
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.auth-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.auth-header p {
  font-size: 14px;
  color: var(--text-secondary);
}

.auth-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  background: var(--bg-tertiary);
  padding: 4px;
  border-radius: var(--radius-md);
}

.auth-tab {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.auth-tab.active {
  background: var(--bg-secondary);
  color: var(--accent-color);
  box-shadow: var(--shadow-sm);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.form-group input {
  padding: 14px 16px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 15px;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px var(--accent-light);
}

.auth-error {
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  color: #dc2626;
  font-size: 13px;
}

.dark-mode .auth-error {
  background: #450a0a;
  border-color: #7f1d1d;
  color: #fca5a5;
}

.auth-submit-btn {
  padding: 16px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}

.auth-submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(249, 115, 22, 0.3);
}

.auth-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.auth-footer p {
  font-size: 14px;
  color: var(--text-secondary);
}

.auth-footer a {
  color: var(--accent-color);
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}

.auth-footer a:hover {
  text-decoration: underline;
}

/* Login Button Styles */
.login-btn {
  width: 100%;
  padding: 12px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

.header-login-btn {
  padding: 10px 20px;
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.header-login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

/* User Info in Sidebar */
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: 8px;
}

.logout-btn {
  padding: 6px 10px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: var(--error-color);
  border-color: var(--error-color);
}

/* Nav item lock icon */
.nav-lock {
  font-size: 12px;
  margin-left: auto;
}

.nav-item.requires-login {
  opacity: 0.6;
}

.nav-item.requires-login:hover {
  opacity: 1;
}

/* Responsive */
@media (max-width: 768px) {
  .sidebar {
    width: 72px;
  }
  
  .sidebar .logo-text,
  .sidebar .nav-label,
  .sidebar .user-badge,
  .sidebar .rag-list-section {
    display: none;
  }
  
  .main-content {
    margin-left: 72px;
  }
  
  .suggestion-grid {
    grid-template-columns: 1fr;
  }
  
  .header-right {
    flex-wrap: wrap;
  }
  
  .auth-modal {
    margin: 16px;
    padding: 24px;
  }
}
</style>
