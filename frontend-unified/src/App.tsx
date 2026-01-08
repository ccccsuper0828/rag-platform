import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Header from './components/Header';
import { SidebarProvider, Sidebar, SidebarContent } from './components/ui/sidebar';
import { Dashboard } from './components/Dashboard';
import { DashboardSidebar } from './components/DashboardSidebar';
import LuminaAsset from './pages/Dashboard';
import DAODashboard from './pages/DAODashboard';
import TaskPool from './pages/taskpool';
import RAGKnowledge from './pages/RAGKnowledge';
import Login from './pages/Login';

const queryClient = new QueryClient();

// 认证检查
const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

// 受保护的路由组件
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

// 主应用布局
function AppLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const sidebarWidth = isSidebarOpen ? 256 : 0;
  const location = useLocation();

  // 登录页面不显示侧边栏
  if (location.pathname === '/login') {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
      </Routes>
    );
  }

  return (
    <ProtectedRoute>
     <SidebarProvider>
       {/* 根容器：相对定位，占满屏幕 */}
       <div style={{ 
         position: 'relative', 
         width: '100%', 
         height: '100vh', 
         overflow: 'hidden' 
       }}>
         {/* 侧边栏：绝对定位，避免影响主内容区流布局 */}
         <Header/>
         <Sidebar 
           style={{
             position: 'absolute',
             top: 50,
             left: 0,
             width: sidebarWidth,
             height: 'calc(100vh - 64px)',
             transition: 'width 0.3s ease'
           }}
           className="transition-all duration-300"
          >
           <SidebarContent>
             <DashboardSidebar />
             <button 
               onClick={() => setIsSidebarOpen(!isSidebarOpen)}
               className="mt-4 px-3 py-2 bg-gray-100 rounded hover:bg-gray-200"
             >
              
             </button>
           </SidebarContent>
         </Sidebar>
        
         {/* 主内容区：绝对定位，左边距等于侧边栏宽度，强制居中 */}
         <main 
           style={{
             position: 'absolute',
             top: 50,
             left: sidebarWidth,
             right: 0,
             height: 'calc(100vh - 64px)',
             overflow: 'auto',
             transition: 'left 0.3s ease',
            // 核心居中样式（不受flex影响）
             display: 'flex',
             justifyContent: 'center', // 水平居中
             padding: '2rem'
           }}
         >
           {/* 内容容器：限制最大宽度，和Mac一致 */}
           <div style={{ 
             maxWidth: '1200px', 
             width: '100%' 
           }}>
             <button 
               onClick={() => setIsSidebarOpen(!isSidebarOpen)}
               className="m-4 px-3 py-2 bg-black text-white rounded"
             >
               ☰
             </button>
             <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/rag-knowledge" element={<RAGKnowledge />} />
              <Route path="/lumina-assets" element={<LuminaAsset />} />
              <Route path="/dao-governance" element={<DAODashboard />} />
              <Route path="/taskpool" element={<TaskPool />} />
            </Routes>
           </div>
         </main>
       </div>
     </SidebarProvider>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </QueryClientProvider>
  );
}