export enum TaskStatus {
  OPEN = 'OPEN',
  CLAIMED = 'CLAIMED',
  SUBMITTED = 'SUBMITTED',
  COMPLETED = 'COMPLETED',
  DISPUTED = 'DISPUTED',
  CANCELLED = 'CANCELLED'
}

export enum DisputeStatus {
  PENDING = 'PENDING',
  REVIEWING = 'REVIEWING',
  RESOLVED = 'RESOLVED',
  REJECTED = 'REJECTED'
}

export interface Task {
  id: string;
  title: string;
  description: string;
  reward: number; // in ETH or token
  deadline: Date;
  status: TaskStatus;
  poster: string; // wallet address
  claimer?: string; // wallet address
  submittedWork?: string;
  submissionDate?: Date;
  completionDate?: Date;
  category: string;
  skills: string[];
  createdAt: Date;
  disputeId?: string;
}

export interface Dispute {
  id: string;
  taskId: string;
  raisedBy: string; // wallet address
  reason: string;
  evidence: string[];
  status: DisputeStatus;
  createdAt: Date;
  resolvedAt?: Date;
  resolution?: string;
  arbitrator?: string;
}

export interface TaskSubmission {
  taskId: string;
  deliverables: string;
  notes: string;
  attachments?: string[];
  submittedAt: Date;
}

export interface TaskCreationForm {
  title: string;
  description: string;
  reward: number;
  deadline: Date;
  category: string;
  skills: string[];
}

export interface DisputeForm {
  taskId: string;
  reason: string;
  evidence: string[];
}

export interface User {
  address: string;
  balance: number;
  tasksPosted: number;
  tasksClaimed: number;
  tasksCompleted: number;
  reputation: number;
}