export type ProposalStatus = 'active' | 'passed' | 'rejected' | 'executed' | 'pending';
export type VoteChoice = 'for' | 'against' | 'abstain';

export interface Proposal {
  id: string;
  title: string;
  description: string;
  proposer: string;
  createdAt: Date;
  startTime: Date;
  endTime: Date;
  status: ProposalStatus;
  votesFor: number;
  votesAgainst: number;
  votesAbstain: number;
  totalVotes: number;
  quorum: number;
  executed: boolean;
  executedAt?: Date;
  category: ProposalCategory;
  actions: ProposalAction[];
}

export interface ProposalAction {
  target: string;
  value: string;
  signature: string;
  calldata: string;
  description: string;
}

export interface ProposalCategory {
  id: string;
  name: string;
  color: string;
}

export interface Vote {
  id: string;
  proposalId: string;
  voter: string;
  choice: VoteChoice;
  votingPower: number;
  tokenVotingPower: number;
  reputationVotingPower: number;
  timestamp: Date;
  reason?: string;
}

export interface VotingPower {
  total: number;
  fromTokens: number;
  fromReputation: number;
  delegated: number;
}

export interface GovernanceStats {
  totalProposals: number;
  activeProposals: number;
  passedProposals: number;
  rejectedProposals: number;
  executedProposals: number;
  totalVotes: number;
  uniqueVoters: number;
  participationRate: number;
  treasuryBalance: string;
  totalTokenSupply: string;
}

export interface Voter {
  address: string;
  votingPower: VotingPower;
  proposalsVoted: number;
  proposalsCreated: number;
  delegatedTo?: string;
  delegates: string[];
  reputation: number;
}

export interface CreateProposalForm {
  title: string;
  description: string;
  category: string;
  actions: ProposalAction[];
  startDelay: number;
  votingPeriod: number;
}