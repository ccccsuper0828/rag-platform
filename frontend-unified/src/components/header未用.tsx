import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Vote, FileText, PlusCircle, BarChart3, Wallet } from 'lucide-react';

const Header: React.FC = () => {
  const location = useLocation();
  
  console.log('Header rendered, current path:', location.pathname);
  
  const isActive = (path: string) => location.pathname === path;
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: Vote },
    { path: '/proposals', label: 'Proposals', icon: FileText },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  ];
  
  return (
    <header data-cmp="Header" className="bg-card border-b border-border sticky top-0 z-50 shadow-custom">
      <div className="w-full max-w-[1440px] mx-auto px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-primary to-chart-2 rounded-lg flex items-center justify-center">
              <Vote className="text-primary-foreground" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">DAO Governance</h1>
              <p className="text-xs text-muted-foreground">Decentralized Decision Making</p>
            </div>
          </Link>
          
          <nav className="flex items-center space-x-1">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive(path)
                    ? 'bg-primary text-primary-foreground shadow-custom'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                }`}
              >
                <Icon size={18} />
                <span>{label}</span>
              </Link>
            ))}
          </nav>
          
          <div className="flex items-center space-x-3">
            <Link
              to="/create-proposal"
              className="flex items-center space-x-2 bg-gradient-to-r from-primary to-chart-2 text-primary-foreground px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity"
            >
              <PlusCircle size={18} />
              <span>New Proposal</span>
            </Link>
            <button className="flex items-center space-x-2 bg-card border border-border px-4 py-2 rounded-lg font-medium text-foreground hover:bg-accent transition-colors">
              <Wallet size={18} />
              <span className="font-mono">0x742d...4a8f</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;