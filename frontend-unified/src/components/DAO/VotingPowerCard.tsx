import React from 'react';
import { Coins, Award, ArrowRight } from 'lucide-react';
import { VotingPower } from '../../types/governance';

interface VotingPowerCardProps {
  votingPower?: VotingPower;
}

const VotingPowerCard: React.FC<VotingPowerCardProps> = ({
  votingPower = {
    total: 15420,
    fromTokens: 12000,
    fromReputation: 3420,
    delegated: 0
  }
}) => {
  console.log('VotingPowerCard rendered');
  
  const tokenPercentage = (votingPower.fromTokens / votingPower.total) * 100;
  const reputationPercentage = (votingPower.fromReputation / votingPower.total) * 100;
  
  return (
    <div data-cmp="VotingPowerCard" className="bg-card border border-border rounded-lg p-6 shadow-custom">
      <h3 className="text-lg font-semibold text-foreground mb-4">Your Voting Power</h3>
      
      <div className="mb-6">
        <div className="flex items-baseline justify-between mb-2">
          <span className="text-3xl font-bold text-foreground">
            {votingPower.total.toLocaleString()}
          </span>
          <span className="text-sm text-muted-foreground">votes</span>
        </div>
        
        <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
          <div className="flex h-full">
            <div 
              className="bg-gradient-to-r from-primary to-chart-2 h-full"
              style={{ width: `${tokenPercentage}%` }}
            />
            <div 
              className="bg-gradient-to-r from-chart-3 to-chart-4 h-full"
              style={{ width: `${reputationPercentage}%` }}
            />
          </div>
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-accent rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-primary to-chart-2 rounded">
              <Coins className="text-primary-foreground" size={16} />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Token Holdings</p>
              <p className="text-xs text-muted-foreground">
                {((votingPower.fromTokens / votingPower.total) * 100).toFixed(1)}% of power
              </p>
            </div>
          </div>
          <span className="font-semibold text-foreground">
            {votingPower.fromTokens.toLocaleString()}
          </span>
        </div>
        
        <div className="flex items-center justify-between p-3 bg-accent rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-chart-3 to-chart-4 rounded">
              <Award className="text-primary-foreground" size={16} />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Reputation Score</p>
              <p className="text-xs text-muted-foreground">
                {((votingPower.fromReputation / votingPower.total) * 100).toFixed(1)}% of power
              </p>
            </div>
          </div>
          <span className="font-semibold text-foreground">
            {votingPower.fromReputation.toLocaleString()}
          </span>
        </div>
      </div>
      
      {votingPower.delegated > 0 && (
        <div className="mt-4 p-3 bg-muted rounded-lg border border-border">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Delegated Votes</span>
            <span className="font-semibold text-foreground">
              +{votingPower.delegated.toLocaleString()}
            </span>
          </div>
        </div>
      )}
      
      <button className="w-full mt-4 flex items-center justify-center space-x-2 bg-gradient-to-r from-primary to-chart-2 text-primary-foreground px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity">
        <span>Manage Delegation</span>
        <ArrowRight size={16} />
      </button>
    </div>
  );
};

export default VotingPowerCard;