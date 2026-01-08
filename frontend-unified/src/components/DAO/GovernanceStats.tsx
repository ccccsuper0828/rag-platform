import React from 'react';
import { FileText, Users, TrendingUp, DollarSign } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  trend?: number;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, subtitle, icon: Icon, trend }) => {
  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
      <div className="flex items-start justify-between mb-4">
        <div className="p-3 bg-gradient-to-r from-primary to-chart-2 rounded-lg">
          <Icon className="text-primary-foreground" size={24} />
        </div>
        {trend !== undefined && (
          <div className={`text-sm font-medium ${trend >= 0 ? 'text-chart-3' : 'text-destructive'}`}>
            {trend >= 0 ? '+' : ''}{trend}%
          </div>
        )}
      </div>
      <div>
        <p className="text-sm text-muted-foreground mb-1">{title}</p>
        <p className="text-3xl font-bold text-foreground">{value}</p>
        {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
      </div>
    </div>
  );
};

interface GovernanceStatsProps {
  totalProposals?: number;
  activeProposals?: number;
  uniqueVoters?: number;
  participationRate?: number;
  treasuryBalance?: string;
}

const GovernanceStats: React.FC<GovernanceStatsProps> = ({
  totalProposals = 156,
  activeProposals = 8,
  uniqueVoters = 1247,
  participationRate = 68.5,
  treasuryBalance = '2.4M'
}) => {
  console.log('GovernanceStats rendered');
  
  return (
    <div data-cmp="GovernanceStats" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatsCard
        title="Total Proposals"
        value={totalProposals}
        subtitle={`${activeProposals} active`}
        icon={FileText}
        trend={12}
      />
      <StatsCard
        title="Unique Voters"
        value={uniqueVoters.toLocaleString()}
        icon={Users}
        trend={8}
      />
      <StatsCard
        title="Participation Rate"
        value={`${participationRate}%`}
        icon={TrendingUp}
        trend={5}
      />
      <StatsCard
        title="Treasury Balance"
        value={`$${treasuryBalance}`}
        subtitle="USDC"
        icon={DollarSign}
        trend={-2}
      />
    </div>
  );
};

export default GovernanceStats;