import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title?: string;
  value?: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  gradient?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title = 'Statistic',
  value = '0',
  subtitle = '',
  icon: Icon,
  gradient = 'from-primary to-blue-500'
}) => {
  console.log('StatCard rendered:', title, value);
  
  return (
    <div 
      data-cmp="StatCard" 
      className="bg-card rounded-lg p-6 shadow-custom border border-border hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <p className="text-sm font-medium text-muted-foreground mb-1">{title}</p>
          <h3 className="text-lg font-semibold text-foreground">{value}</h3>
          {subtitle && (
            <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
          )}
        </div>
        {Icon && (
          <div className={`p-2 ml-2 rounded-lg bg-gradient-to-br ${gradient}`}>
            <Icon className="text-white" size={18} />
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;