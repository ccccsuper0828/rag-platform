import React from 'react';
import { ArrowLeft, ExternalLink, Calendar, User, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import ProposalStatusBadge from '../components/DAO/ProposalStatusBadge';
import VoteResults from '../components/DAO/VoteResults';
import VotePanel from '../components/DAO/VotePanel';
const now = Date.now();
const ProposalDetail: React.FC = () => {
  console.log('ProposalDetail page rendered');
  
  const proposal = {
    id: 'prop-1',
    title: 'Treasury Allocation for Q1 2024',
    description: 'This proposal seeks to allocate 500,000 USDC from the DAO treasury for critical development initiatives in Q1 2024.',
    fullDescription: `
## Overview
This proposal requests an allocation of 500,000 USDC from the DAO treasury to fund essential development activities during the first quarter of 2024.

## Budget Breakdown
- Smart Contract Audits: 200,000 USDC
- Bug Bounty Program: 150,000 USDC
- Developer Grants: 100,000 USDC
- Infrastructure Costs: 50,000 USDC

## Rationale
Investing in security audits and developer support will strengthen our protocol's foundation and foster ecosystem growth. The bug bounty program will incentivize security researchers to identify vulnerabilities before they can be exploited.

## Expected Outcomes
1. Two comprehensive security audits completed
2. Active bug bounty program attracting top researchers
3. At least 5 developer grants awarded
4. Improved infrastructure reliability

## Timeline
- Month 1: Contract audit firms selected and engaged
- Month 2: Bug bounty program launch
- Month 3: Developer grant applications reviewed and awarded
    `,
    proposer: '0x742d35a037451c8936085Af37aA7AD38B8a4a8f',
    createdAt: new Date(now - 2 * 24 * 60 * 60 * 1000),
    startTime: new Date(now - 1 * 24 * 60 * 60 * 1000),
    endTime: new Date(now + 5 * 24 * 60 * 60 * 1000),
    status: 'active' as const,
    votesFor: 12540,
    votesAgainst: 3420,
    votesAbstain: 890,
    quorum: 10000,
    category: 'Treasury',
    actions: [
      {
        target: '0x1234567890123456789012345678901234567890',
        value: '500000000000',
        signature: 'transfer(address,uint256)',
        calldata: '0x...',
        description: 'Transfer 500K USDC to development multisig'
      }
    ]
  };
  
  const timeRemaining = proposal.endTime.getTime() - now;
  const daysRemaining = Math.ceil(timeRemaining / (1000 * 60 * 60 * 24));
  
  return (
    <div className="py-8 px-8">
      <Link
        to="/proposals"
        className="inline-flex items-center space-x-2 text-muted-foreground hover:text-foreground mb-6 transition-colors"
      >
        <ArrowLeft size={20} />
        <span>Back to Proposals</span>
      </Link>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card border border-border rounded-lg p-8 shadow-custom">
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-3">
                  <ProposalStatusBadge status={proposal.status} />
                  <span className="text-xs bg-accent text-accent-foreground px-2 py-1 rounded">
                    {proposal.category}
                  </span>
                </div>
                <h1 className="text-3xl font-bold text-foreground mb-4">
                  {proposal.title}
                </h1>
                <p className="text-lg text-muted-foreground mb-6">
                  {proposal.description}
                </p>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-4 mb-6 pb-6 border-b border-border">
              <div className="flex items-center space-x-2 text-sm">
                <User className="text-muted-foreground" size={16} />
                <span className="text-muted-foreground">Proposed by</span>
                <a
                  href={`https://etherscan.io/address/${proposal.proposer}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-primary hover:text-primary/80 flex items-center space-x-1"
                >
                  <span>{proposal.proposer.slice(0, 6)}...{proposal.proposer.slice(-4)}</span>
                  <ExternalLink size={12} />
                </a>
              </div>
              
              <div className="flex items-center space-x-2 text-sm">
                <Calendar className="text-muted-foreground" size={16} />
                <span className="text-muted-foreground">Created</span>
                <span className="text-foreground">
                  {proposal.createdAt.toLocaleDateString()}
                </span>
              </div>
              
              <div className="flex items-center space-x-2 text-sm">
                <Clock className="text-muted-foreground" size={16} />
                <span className="text-muted-foreground">Time Remaining</span>
                <span className="text-foreground font-medium">
                  {daysRemaining} days
                </span>
              </div>
            </div>
            
            <div className="prose prose-slate max-w-none">
              <div className="whitespace-pre-wrap text-foreground">
                {proposal.fullDescription}
              </div>
            </div>
            
            {proposal.actions.length > 0 && (
              <div className="mt-8 pt-8 border-t border-border">
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  Proposed Actions
                </h3>
                <div className="space-y-3">
                  {proposal.actions.map((action, index) => (
                    <div key={index} className="bg-accent rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-sm font-medium text-foreground">
                          Action {index + 1}
                        </span>
                        <span className="text-xs bg-card px-2 py-1 rounded border border-border">
                          {action.signature}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        {action.description}
                      </p>
                      <div className="text-xs font-mono text-muted-foreground">
                        Target: {action.target}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="space-y-6">
          <VotePanel proposalId={proposal.id} />
          
          <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
            <VoteResults
              votesFor={proposal.votesFor}
              votesAgainst={proposal.votesAgainst}
              votesAbstain={proposal.votesAbstain}
              quorum={proposal.quorum}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProposalDetail;