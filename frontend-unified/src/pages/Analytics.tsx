import React from 'react';
import { TrendingUp, Users, FileText, Vote } from 'lucide-react';
import GovernanceStats from '../components/DAO/GovernanceStats';

const Analytics: React.FC = () => {
  console.log('Analytics page rendered');
  
  const topVoters = [
    { address: '0x742d...4a8f', votes: 45, power: 125000 },
    { address: '0x1a2b...3c4d', votes: 38, power: 98000 },
    { address: '0x5e6f...7g8h', votes: 32, power: 87000 },
    { address: '0x9i0j...1k2l', votes: 28, power: 75000 },
    { address: '0x3m4n...5o6p', votes: 25, power: 68000 }
  ];
  
  return (
    <div className="py-8 px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Governance Analytics
        </h1>
        <p className="text-muted-foreground">
          Insights into DAO participation and voting trends
        </p>
      </div>
      
      <div className="mb-8">
        <GovernanceStats />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
          <h3 className="text-lg font-semibold text-foreground mb-4">
            Top Voters
          </h3>
          <div className="space-y-3">
            {topVoters.map((voter, index) => (
              <div key={voter.address} className="flex items-center justify-between p-3 bg-accent rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-primary to-chart-2 rounded-full flex items-center justify-center text-sm font-bold text-primary-foreground">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-mono text-sm text-foreground">{voter.address}</p>
                    <p className="text-xs text-muted-foreground">
                      {voter.votes} votes cast
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-foreground">
                    {voter.power.toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground">voting power</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
          <h3 className="text-lg font-semibold text-foreground mb-4">
            Participation Trends
          </h3>
          <div className="h-64 bg-accent rounded-lg flex items-center justify-center">
            <p className="text-muted-foreground">Chart visualization coming soon</p>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
          <div className="flex items-center space-x-3 mb-3">
            <div className="p-3 bg-gradient-to-r from-primary to-chart-2 rounded-lg">
              <Vote className="text-primary-foreground" size={20} />
            </div>
            <h4 className="font-semibold text-foreground">Avg Turnout</h4>
          </div>
          <p className="text-3xl font-bold text-foreground">68.5%</p>
          <p className="text-sm text-muted-foreground mt-1">Last 30 days</p>
        </div>
        
        <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
          <div className="flex items-center space-x-3 mb-3">
            <div className="p-3 bg-gradient-to-r from-chart-3 to-chart-3 rounded-lg">
              <FileText className="text-primary-foreground" size={20} />
            </div>
            <h4 className="font-semibold text-foreground">Pass Rate</h4>
          </div>
          <p className="text-3xl font-bold text-foreground">72%</p>
          <p className="text-sm text-muted-foreground mt-1">All time</p>
        </div>
        
        <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
          <div className="flex items-center space-x-3 mb-3">
            <div className="p-3 bg-gradient-to-r from-chart-4 to-chart-4 rounded-lg">
              <Users className="text-primary-foreground" size={20} />
            </div>
            <h4 className="font-semibold text-foreground">New Voters</h4>
          </div>
          <p className="text-3xl font-bold text-foreground">+124</p>
          <p className="text-sm text-muted-foreground mt-1">This month</p>
        </div>
        
        <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
          <div className="flex items-center space-x-3 mb-3">
            <div className="p-3 bg-gradient-to-r from-chart-2 to-chart-2 rounded-lg">
              <TrendingUp className="text-primary-foreground" size={20} />
            </div>
            <h4 className="font-semibold text-foreground">Growth</h4>
          </div>
          <p className="text-3xl font-bold text-foreground">+15%</p>
          <p className="text-sm text-muted-foreground mt-1">MoM</p>
        </div>
      </div>
    </div>
  );
};

export default Analytics;