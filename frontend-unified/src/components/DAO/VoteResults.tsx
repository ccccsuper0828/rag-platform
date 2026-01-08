import React from 'react';
import { ThumbsUp, ThumbsDown, Minus } from 'lucide-react';

interface VoteResultsProps {
  votesFor?: number;
  votesAgainst?: number;
  votesAbstain?: number;
  quorum?: number;
}

const VoteResults: React.FC<VoteResultsProps> = ({
  votesFor = 12540,
  votesAgainst = 3420,
  votesAbstain = 890,
  quorum = 10000
}) => {
  console.log('VoteResults rendered');
  
  const totalVotes = votesFor + votesAgainst + votesAbstain;
  const forPercentage = totalVotes > 0 ? (votesFor / totalVotes) * 100 : 0;
  const againstPercentage = totalVotes > 0 ? (votesAgainst / totalVotes) * 100 : 0;
  const abstainPercentage = totalVotes > 0 ? (votesAbstain / totalVotes) * 100 : 0;
  const quorumReached = totalVotes >= quorum;
  
  return (
    <div data-cmp="VoteResults" className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-foreground">Current Results</h4>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-muted-foreground">
            {totalVotes.toLocaleString()} votes
          </span>
          {quorumReached && (
            <span className="text-xs bg-chart-3/10 text-chart-3 px-2 py-1 rounded">
              Quorum Reached
            </span>
          )}
        </div>
      </div>
      
      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <ThumbsUp className="text-chart-3" size={16} />
              <span className="text-sm font-medium text-foreground">For</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold text-foreground">
                {votesFor.toLocaleString()}
              </span>
              <span className="text-xs text-muted-foreground">
                ({forPercentage.toFixed(1)}%)
              </span>
            </div>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-gradient-to-r from-chart-3 to-chart-3 h-2 rounded-full transition-all"
              style={{ width: `${forPercentage}%` }}
            />
          </div>
        </div>
        
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <ThumbsDown className="text-destructive" size={16} />
              <span className="text-sm font-medium text-foreground">Against</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold text-foreground">
                {votesAgainst.toLocaleString()}
              </span>
              <span className="text-xs text-muted-foreground">
                ({againstPercentage.toFixed(1)}%)
              </span>
            </div>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-gradient-to-r from-destructive to-destructive h-2 rounded-full transition-all"
              style={{ width: `${againstPercentage}%` }}
            />
          </div>
        </div>
        
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Minus className="text-muted-foreground" size={16} />
              <span className="text-sm font-medium text-foreground">Abstain</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold text-foreground">
                {votesAbstain.toLocaleString()}
              </span>
              <span className="text-xs text-muted-foreground">
                ({abstainPercentage.toFixed(1)}%)
              </span>
            </div>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-muted-foreground h-2 rounded-full transition-all"
              style={{ width: `${abstainPercentage}%` }}
            />
          </div>
        </div>
      </div>
      
      <div className="pt-3 border-t border-border">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Quorum Required</span>
          <span className="font-medium text-foreground">
            {quorum.toLocaleString()} votes
          </span>
        </div>
        <div className="w-full bg-muted rounded-full h-1.5 mt-2">
          <div
            className={`h-1.5 rounded-full transition-all ${
              quorumReached ? 'bg-chart-3' : 'bg-chart-4'
            }`}
            style={{ width: `${Math.min((totalVotes / quorum) * 100, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default VoteResults;