import React, { useState } from 'react';
import { Search } from 'lucide-react';
import ProposalCard from '../components/DAO/ProposalCard';
import CategoryFilter from '../components/DAO/CategoryFilter';
import { Proposal, ProposalStatus } from '../types/governance';

const now = Date.now();
const Proposals: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  console.log('Proposals page rendered');
  


  const proposals: Proposal[] = [
    {
      id: 'prop-1',
      title: 'Treasury Allocation for Q1 2024',
      description: 'Proposal to allocate 500K USDC from treasury for development initiatives.',
      proposer: '0x742d...4a8f',
      createdAt: new Date(now - 2 * 24 * 60 * 60 * 1000),
      startTime: new Date(now - 1 * 24 * 60 * 60 * 1000),
      endTime: new Date(now + 5 * 24 * 60 * 60 * 1000),
      status: 'active',
      votesFor: 12540,
      votesAgainst: 3420,
      votesAbstain: 890,
      totalVotes: 16850,
      quorum: 10000,
      executed: false,
      category: { id: 'treasury', name: 'Treasury', color: 'purple' },
      actions: []
    },
    {
      id: 'prop-2',
      title: 'Update Governance Voting Period',
      description: 'Extend the standard voting period from 5 days to 7 days.',
      proposer: '0x1a2b...3c4d',
      createdAt: new Date(now - 3 * 24 * 60 * 60 * 1000),
      startTime: new Date(now - 2 * 24 * 60 * 60 * 1000),
      endTime: new Date(now + 4 * 24 * 60 * 60 * 1000),
      status: 'active',
      votesFor: 8920,
      votesAgainst: 5210,
      votesAbstain: 1240,
      totalVotes: 15370,
      quorum: 10000,
      executed: false,
      category: { id: 'governance', name: 'Governance', color: 'blue' },
      actions: []
    },
    {
      id: 'prop-3',
      title: 'Protocol Fee Structure Update',
      description: 'Reduce protocol fees from 0.3% to 0.25% to increase competitiveness.',
      proposer: '0x5e6f...7g8h',
      createdAt: new Date(now - 10 * 24 * 60 * 60 * 1000),
      startTime: new Date(now - 9 * 24 * 60 * 60 * 1000),
      endTime: new Date(now - 2 * 24 * 60 * 60 * 1000),
      status: 'passed',
      votesFor: 18920,
      votesAgainst: 2140,
      votesAbstain: 890,
      totalVotes: 21950,
      quorum: 10000,
      executed: true,
      executedAt: new Date(now- 1 * 24 * 60 * 60 * 1000),
      category: { id: 'protocol', name: 'Protocol', color: 'green' },
      actions: []
    }
  ];
  
  const statusFilters: { id: string; label: string; status?: ProposalStatus }[] = [
    { id: 'all', label: 'All Status' },
    { id: 'active', label: 'Active', status: 'active' },
    { id: 'passed', label: 'Passed', status: 'passed' },
    { id: 'rejected', label: 'Rejected', status: 'rejected' },
    { id: 'executed', label: 'Executed', status: 'executed' }
  ];
  
  const filteredProposals = proposals.filter(proposal => {
    const matchesCategory = selectedCategory === 'all' || proposal.category.id === selectedCategory;
    const matchesStatus = selectedStatus === 'all' || proposal.status === selectedStatus;
    const matchesSearch = proposal.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         proposal.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesStatus && matchesSearch;
  });
  
  return (
    <div className="py-8 px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">All Proposals</h1>
        <p className="text-muted-foreground">Browse and vote on governance proposals</p>
      </div>
      
      <div className="mb-6">
        <div className="relative max-w-xl">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
          <input
            type="text"
            placeholder="Search proposals..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>
      
      <div className="mb-6">
        <h3 className="text-sm font-medium text-foreground mb-3">Filter by Category</h3>
        <CategoryFilter
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
        />
      </div>
      
      <div className="mb-6">
        <h3 className="text-sm font-medium text-foreground mb-3">Filter by Status</h3>
        <div className="flex flex-wrap gap-2">
          {statusFilters.map((filter) => (
            <button
              key={filter.id}
              onClick={() => setSelectedStatus(filter.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                selectedStatus === filter.id
                  ? 'bg-gradient-to-r from-primary to-chart-2 text-primary-foreground shadow-custom'
                  : 'bg-accent text-accent-foreground hover:bg-accent/80'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>
      
      <div className="mb-4">
        <p className="text-muted-foreground">
          {filteredProposals.length} proposal{filteredProposals.length !== 1 ? 's' : ''} found
        </p>
      </div>
      
      <div className="space-y-4">
        {filteredProposals.map((proposal) => (
          <ProposalCard key={proposal.id} proposal={proposal} />
        ))}
      </div>
      
      {filteredProposals.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground text-lg mb-4">No proposals found</p>
          <button
            onClick={() => {
              setSelectedCategory('all');
              setSelectedStatus('all');
              setSearchQuery('');
            }}
            className="text-primary hover:text-primary/80 font-medium"
          >
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
};

export default Proposals;