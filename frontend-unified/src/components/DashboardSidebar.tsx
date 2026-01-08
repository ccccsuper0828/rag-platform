import { useNavigate, useLocation } from 'react-router-dom';
import { Bot, Database, Vote, ClipboardList, Settings, HelpCircle, ChevronRight, BookOpen, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { Separator } from './ui/separator';

export function DashboardSidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  // 菜单项 - 添加 RAG Knowledge 作为核心功能
  const menuItems = [
    { label: 'AI Agents', icon: Bot, path: '/' },
    { label: 'RAG Knowledge', icon: BookOpen, path: '/rag-knowledge', highlight: true },
    { label: 'Lumina NFT Assets', icon: Database, path: '/lumina-assets' },
    { label: 'DAO Governance', icon: Vote, path: '/dao-governance' },
    { label: 'Task Pool', icon: ClipboardList, path: '/taskpool' }
  ];

  const bottomItems = [
    { label: 'Settings', icon: Settings, path: '/settings' },
    { label: 'Support', icon: HelpCircle, path: '/support' }
  ];

  return (
    <div className="flex flex-col h-full p-4">
      {/* 主导航 */}
      <nav className="flex-1 space-y-2">
        {menuItems.map(({ label, icon: Icon, path, highlight }) => {
          const isActive = location.pathname === path;
          return (
            <Button
              key={path}
              variant="ghost"
              onClick={() => navigate(path)}
              className={`w-full justify-start gap-2 relative ${
                isActive ? 'bg-gray-100 shadow-lg font-bold' : ''
              } ${highlight && !isActive ? 'bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200' : ''}`}
            >
              <Icon className={`h-4 w-4 ${highlight ? 'text-blue-600' : ''}`} />
              <span className={highlight ? 'text-blue-700' : ''}>{label}</span>
              {highlight && !isActive && (
                <Sparkles className="h-3 w-3 text-yellow-500 absolute right-8" />
              )}
              {isActive && (
                <ChevronRight
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600"
                  size={16}
                />
              )}
            </Button>
          );
        })}
      </nav>

      <Separator className="my-4" />

      {/* 底部 Settings + Support */}
      <div className="space-y-2">
        {bottomItems.map(({ label, icon: Icon, path }) => {
          const isActive = location.pathname === path;
          return (
            <Button
              key={path}
              variant="ghost"
              onClick={() => navigate(path)}
              className={`w-full justify-start gap-2 relative ${
                isActive ? 'bg-gray-100 shadow-lg font-bold' : ''
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
              {isActive && (
                <ChevronRight
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600"
                  size={16}
                />
              )}
            </Button>
          );
        })}
      </div>
    </div>
  );
}
