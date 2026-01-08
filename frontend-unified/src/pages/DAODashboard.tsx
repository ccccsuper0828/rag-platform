import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import React from 'react';
import GovernanceStats from '../components/DAO/GovernanceStats';
import VotingPowerCard from '../components/DAO/VotingPowerCard';
import ProposalCard from '../components/DAO/ProposalCard';
import ActivityFeed from '../components/DAO/ActivityFeed';
import { Proposal } from '../types/governance';
import Proposals from "./Proposals";
import CreateProposal from "./CreateProposal";
import ProposalDetail from "./ProposalDetail";
import Analytics from "./Analytics";
const now = Date.now()
const Dashboard: React.FC = () => {
  console.log('Dashboard page rendered');
  
  const activeProposals: Proposal[] = [
    {
      id: 'prop-1',
      title: 'Treasury Allocation for Q1 2024',
      description: 'Proposal to allocate 500K USDC from treasury for development initiatives including smart contract audits, bug bounties, and developer grants.',
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
      description: 'Extend the standard voting period from 5 days to 7 days to allow more community participation and discussion.',
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
    }
  ];
  
  return (
    <div className="py-8 px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Governance Dashboard
        </h1>
        <p className="text-muted-foreground">
          Participate in DAO decision-making and shape the future of our protocol
        </p>
      </div>
      <Tabs defaultValue="DAODashboard" className="space-y-6">
        <TabsList>
           <TabsTrigger value="DAODashboard">Overveiw</TabsTrigger>
           <TabsTrigger value="Proposals">Proposals</TabsTrigger>
           <TabsTrigger value="CreateProposal">CreateProposal</TabsTrigger>
           <TabsTrigger value="ProposalDetail">ProposalDetail</TabsTrigger>
           <TabsTrigger value="Analytics">Analytics</TabsTrigger>
        </TabsList>
        <TabsContent value="DAODashboard" className="space-y-6">
        
      
      <div className="mb-8">
        <GovernanceStats />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-foreground mb-4">Active Proposals</h2>
            <div className="space-y-4">
              {activeProposals.map((proposal) => (
                <ProposalCard key={proposal.id} proposal={proposal} />
              ))}
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          <VotingPowerCard />
          <ActivityFeed />
        </div>
      </div>
        </TabsContent>
        <TabsContent value="Proposals" className="space-y-6">
          <Proposals/>
        </TabsContent>
        <TabsContent value="CreateProposal" className="space-y-6">
          <CreateProposal/>
        </TabsContent>
        <TabsContent value="ProposalDetail" className="space-y-6">
          <ProposalDetail/>
        </TabsContent>
        <TabsContent value="Analytics" className="space-y-6">
          <Analytics/>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;