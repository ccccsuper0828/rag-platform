import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Minus, Check } from 'lucide-react';
import { VoteChoice } from '../../types/governance';

interface VotePanelProps {
  proposalId?: string;
  votingPower?: number;
  hasVoted?: boolean;
  userVote?: VoteChoice;
  onVote?: (choice: VoteChoice, reason: string) => void;
}

const VotePanel: React.FC<VotePanelProps> = ({
  proposalId = '1',
  votingPower = 15420,
  hasVoted = false,
  userVote,
  onVote = () => console.log('Vote cast')
}) => {
  const [selectedChoice, setSelectedChoice] = useState<VoteChoice | null>(userVote || null);
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  console.log('VotePanel rendered for proposal:', proposalId);
  
  const handleVote = async () => {
    if (!selectedChoice) return;
    
    setIsSubmitting(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    onVote(selectedChoice, reason);
    setIsSubmitting(false);
  };
  
  const voteOptions = [
    {
      choice: 'for' as VoteChoice,
      label: 'Vote For',
      icon: ThumbsUp,
      className: 'from-chart-3 to-chart-3 hover:opacity-90'
    },
    {
      choice: 'against' as VoteChoice,
      label: 'Vote Against',
      icon: ThumbsDown,
      className: 'from-destructive to-destructive hover:opacity-90'
    },
    {
      choice: 'abstain' as VoteChoice,
      label: 'Abstain',
      icon: Minus,
      className: 'from-muted-foreground to-muted-foreground hover:opacity-90'
    }
  ];
  
  if (hasVoted && userVote) {
    const votedOption = voteOptions.find(opt => opt.choice === userVote);
    const Icon = votedOption?.icon || Check;
    
    return (
      <div data-cmp="VotePanel" className="bg-card border border-border rounded-lg p-6 shadow-custom">
        <div className="flex items-center justify-center space-x-3 mb-4">
          <div className="p-3 bg-gradient-to-r from-chart-3 to-chart-3 rounded-full">
            <Check className="text-primary-foreground" size={24} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Vote Recorded</h3>
            <p className="text-sm text-muted-foreground">
              You voted <span className="font-semibold">{userVote}</span> with {votingPower.toLocaleString()} votes
            </p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div data-cmp="VotePanel" className="bg-card border border-border rounded-lg p-6 shadow-custom">
      <h3 className="text-lg font-semibold text-foreground mb-4">Cast Your Vote</h3>
      
      <div className="mb-4 p-4 bg-accent rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Your Voting Power</span>
          <span className="text-xl font-bold text-foreground">{votingPower.toLocaleString()}</span>
        </div>
      </div>
      
      <div className="space-y-3 mb-4">
        {voteOptions.map(({ choice, label, icon: Icon, className }) => (
          <button
            key={choice}
            onClick={() => setSelectedChoice(choice)}
            className={`w-full flex items-center justify-between p-4 rounded-lg border-2 transition-all ${
              selectedChoice === choice
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-muted-foreground'
            }`}
          >
            <div className="flex items-center space-x-3">
              <div className={`p-2 bg-gradient-to-r ${className} rounded-lg`}>
                <Icon className="text-primary-foreground" size={20} />
              </div>
              <span className="font-medium text-foreground">{label}</span>
            </div>
            {selectedChoice === choice && (
              <Check className="text-primary" size={20} />
            )}
          </button>
        ))}
      </div>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-foreground mb-2">
          Reason (Optional)
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Share why you're voting this way..."
          className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          rows={3}
        />
      </div>
      
      <button
        onClick={handleVote}
        disabled={!selectedChoice || isSubmitting}
        className="w-full bg-gradient-to-r from-primary to-chart-2 text-primary-foreground px-4 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSubmitting ? 'Submitting Vote...' : 'Submit Vote'}
      </button>
    </div>
  );
};

export default VotePanel;