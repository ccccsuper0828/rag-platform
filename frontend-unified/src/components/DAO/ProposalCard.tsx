import React from 'react';
import { Link } from 'react-router-dom';
import { Calendar, User, ArrowRight } from 'lucide-react';
import { Proposal } from '../../types/governance';
import ProposalStatusBadge from './ProposalStatusBadge';
import VoteResults from './VoteResults';

interface ProposalCardProps {
  proposal?: Proposal;
}

const ProposalCard: React.FC<ProposalCardProps> = ({
  proposal = {
    id: '1',
    title: 'Sample Proposal',
    description: 'This is a sample proposal description',
    proposer: '0x1234...5678',
    createdAt: new Date(),
    startTime: new Date(),
    endTime: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    status: 'active' as const,
    votesFor: 12540,
    votesAgainst: 3420,
    votesAbstain: 890,
    totalVotes: 16850,
    quorum: 10000,
    executed: false,
    category: { id: '1', name: 'Treasury', color: 'purple' },
    actions: []
  }
}) => {
  console.log('ProposalCard rendered:', proposal.id);
  
  const timeRemaining = proposal.endTime.getTime() - Date.now();
  const daysRemaining = Math.ceil(timeRemaining / (1000 * 60 * 60 * 24));
  
  return (
    <div data-cmp="ProposalCard" className="bg-card border border-border rounded-lg p-6 shadow-custom hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <ProposalStatusBadge status={proposal.status} />
            <span className="text-xs bg-accent text-accent-foreground px-2 py-1 rounded">
              {proposal.category.name}
            </span>
          </div>
          <Link to={`/proposal?id=${proposal.id}`}>
            <h3 className="text-xl font-bold text-foreground hover:text-primary transition-colors mb-2">
              {proposal.title}
            </h3>
          </Link>
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {proposal.description}
          </p>
        </div>
      </div>
      
      <div className="flex items-center space-x-4 mb-4 text-xs text-muted-foreground">
        <div className="flex items-center space-x-1">
          <User size={14} />
          <span className="font-mono">{proposal.proposer}</span>
        </div>
        <div className="flex items-center space-x-1">
          <Calendar size={14} />
          <span>
            {proposal.status === 'active' 
              ? `${daysRemaining} days remaining`
              : new Date(proposal.createdAt).toLocaleDateString()
            }
          </span>
        </div>
      </div>
      
      <div className="mb-4">
        <VoteResults
          votesFor={proposal.votesFor}
          votesAgainst={proposal.votesAgainst}
          votesAbstain={proposal.votesAbstain}
          quorum={proposal.quorum}
        />
      </div>
      
      <Link
        to={`/proposal?id=${proposal.id}`}
        className="flex items-center justify-center space-x-2 w-full bg-gradient-to-r from-primary to-chart-2 text-primary-foreground px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity"
      >
        <span>View Details</span>
        <ArrowRight size={16} />
      </Link>
    </div>
  );
};

export default ProposalCard;