import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, MessageSquare, Send, Loader2, BookOpen, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';

// API 基础 URL
const API_BASE = '/api';

// 获取 token
const getToken = () => localStorage.getItem('token') || '';

interface RAGDocument {
  rag_id: string;
  name?: string;
  file_path?: string;
  arch?: string;
  created_at?: string;
  active?: boolean;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{ text: string; page?: number }>;
}

const RAGKnowledge: React.FC = () => {
  // 状态
  const [documents, setDocuments] = useState<RAGDocument[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<RAGDocument | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // 聊天状态
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  
  // PDF 预览状态
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // 引用
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 加载文档列表
  useEffect(() => {
    loadDocuments();
  }, []);

  // 自动滚动到最新消息
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/v1/rag/list`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.rags || []);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  // 上传文件
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('arch', 'aipartner');

    try {
      const response = await fetch(`${API_BASE}/v1/rag/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setUploadProgress(100);
        await loadDocuments();
        
        // 自动选择新上传的文档
        if (data.rag_id) {
          const newDoc = { rag_id: data.rag_id, name: file.name, file_path: data.file_path };
          setSelectedDoc(newDoc);
          loadPdfPreview(data.rag_id);
        }
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('文件上传失败，请重试');
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  // 加载 PDF 预览
  const loadPdfPreview = async (ragId: string) => {
    try {
      const url = `${API_BASE}/v1/rag/pdf/${ragId}`;
      setPdfUrl(url);
    } catch (error) {
      console.error('Failed to load PDF:', error);
    }
  };

  // 选择文档
  const handleSelectDocument = (doc: RAGDocument) => {
    setSelectedDoc(doc);
    setMessages([]);
    loadPdfPreview(doc.rag_id);
  };

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedDoc || isSending) return;

    const userMessage: ChatMessage = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsSending(true);

    try {
      const response = await fetch(`${API_BASE}/v1/rag/${selectedDoc.rag_id}/chat-with-citations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({
          question: inputMessage,
          mode: 'detailed'
        })
      });

      if (response.ok) {
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let assistantContent = '';
        let citations: Array<{ text: string; page?: number }> = [];

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.content) {
                    assistantContent += data.content;
                  }
                  if (data.citations) {
                    citations = data.citations;
                  }
                } catch {
                  // 非 JSON 内容，直接追加
                  assistantContent += line.slice(6);
                }
              }
            }

            // 更新消息
            setMessages(prev => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage?.role === 'assistant') {
                lastMessage.content = assistantContent;
                lastMessage.citations = citations;
              } else {
                newMessages.push({
                  role: 'assistant',
                  content: assistantContent,
                  citations
                });
              }
              return newMessages;
            });
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '抱歉，处理您的问题时出现错误，请重试。'
      }]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full max-w-[1600px] mx-auto px-6 py-6">
        {/* 标题 */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            RAG Knowledge Base
          </h1>
          <p className="text-muted-foreground">
            Upload documents and chat with AI to extract knowledge insights
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* 左侧：文档列表 */}
          <div className="lg:col-span-3">
            <Card className="h-[calc(100vh-200px)]">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Documents
                </CardTitle>
                <CardDescription>Your uploaded knowledge bases</CardDescription>
              </CardHeader>
              <CardContent>
                {/* 上传按钮 */}
                <div className="mb-4">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".pdf,.txt,.md"
                    className="hidden"
                  />
                  <Button 
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full gap-2"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Upload className="h-4 w-4" />
                    )}
                    Upload Document
                  </Button>
                  {uploadProgress > 0 && uploadProgress < 100 && (
                    <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  )}
                </div>

                {/* 文档列表 */}
                <ScrollArea className="h-[calc(100vh-400px)]">
                  <div className="space-y-2">
                    {documents.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        No documents yet. Upload one to start!
                      </p>
                    ) : (
                      documents.map((doc) => (
                        <div
                          key={doc.rag_id}
                          onClick={() => handleSelectDocument(doc)}
                          className={`p-3 rounded-lg cursor-pointer transition-colors ${
                            selectedDoc?.rag_id === doc.rag_id
                              ? 'bg-primary/10 border border-primary'
                              : 'bg-card hover:bg-accent border border-transparent'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium truncate">
                              {doc.name || doc.file_path?.split('/').pop() || doc.rag_id}
                            </span>
                          </div>
                          {doc.active && (
                            <Badge variant="secondary" className="mt-1 text-xs">
                              Active
                            </Badge>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* 中间：PDF 预览 */}
          <div className="lg:col-span-4">
            <Card className="h-[calc(100vh-200px)]">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Document Preview
                  </span>
                  {pdfUrl && (
                    <div className="flex items-center gap-2 text-sm font-normal">
                      <Button 
                        variant="outline" 
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage <= 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span>{currentPage} / {totalPages}</span>
                      <Button 
                        variant="outline" 
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage >= totalPages}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="h-[calc(100%-80px)]">
                {pdfUrl ? (
                  <iframe
                    src={`${pdfUrl}#page=${currentPage}`}
                    className="w-full h-full rounded-lg border"
                    title="PDF Preview"
                  />
                ) : (
                  <div className="h-full flex items-center justify-center text-muted-foreground">
                    <div className="text-center">
                      <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>Select a document to preview</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 右侧：AI 聊天 */}
          <div className="lg:col-span-5">
            <Card className="h-[calc(100vh-200px)] flex flex-col">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-yellow-500" />
                  AI Research Assistant
                </CardTitle>
                <CardDescription>
                  {selectedDoc 
                    ? `Chatting with: ${selectedDoc.name || selectedDoc.rag_id}`
                    : 'Select a document to start chatting'
                  }
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col overflow-hidden">
                {/* 消息列表 */}
                <ScrollArea className="flex-1 pr-4">
                  <div className="space-y-4">
                    {messages.length === 0 ? (
                      <div className="text-center py-12 text-muted-foreground">
                        <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>Start a conversation about your document</p>
                        <p className="text-sm mt-2">Try asking:</p>
                        <div className="mt-3 space-y-2">
                          {[
                            "What is the main topic of this document?",
                            "Summarize the key points",
                            "What conclusions can be drawn?"
                          ].map((q, i) => (
                            <Button
                              key={i}
                              variant="outline"
                              size="sm"
                              className="text-xs"
                              onClick={() => {
                                setInputMessage(q);
                                if (selectedDoc) handleSendMessage();
                              }}
                              disabled={!selectedDoc}
                            >
                              {q}
                            </Button>
                          ))}
                        </div>
                      </div>
                    ) : (
                      messages.map((msg, index) => (
                        <div
                          key={index}
                          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                              msg.role === 'user'
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-muted'
                            }`}
                          >
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            {msg.citations && msg.citations.length > 0 && (
                              <div className="mt-2 pt-2 border-t border-white/20">
                                <p className="text-xs opacity-70 mb-1">Sources:</p>
                                {msg.citations.map((citation, i) => (
                                  <Badge key={i} variant="secondary" className="text-xs mr-1 mb-1">
                                    {citation.page ? `Page ${citation.page}` : `Source ${i + 1}`}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                    <div ref={chatEndRef} />
                  </div>
                </ScrollArea>

                {/* 输入框 */}
                <div className="mt-4 flex gap-2">
                  <Input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder={selectedDoc ? "Ask a question..." : "Select a document first"}
                    disabled={!selectedDoc || isSending}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!selectedDoc || !inputMessage.trim() || isSending}
                    size="icon"
                  >
                    {isSending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RAGKnowledge;

