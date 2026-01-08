import { Task, TaskStatus, Dispute, DisputeStatus, TaskSubmission } from '../types/task';

// Mock contract interaction - Replace with actual Web3 integration
export class TaskManagerContract {
  private tasks: Task[] = [];
  private disputes: Dispute[] = [];
  
  constructor() {
    console.log('TaskManagerContract initialized');
    this.initializeMockData();
  }

  private initializeMockData() {
    // Mock tasks for demonstration
    this.tasks = [
      {
        id: '1',
        title: 'Build React Dashboard',
        description: 'Create a responsive admin dashboard with charts and tables using React and TypeScript',
        reward: 0.5,
        deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        status: TaskStatus.OPEN,
        poster: '0x1234...5678',
        category: 'Development',
        skills: ['React', 'TypeScript', 'TailwindCSS'],
        createdAt: new Date()
      },
      {
        id: '2',
        title: 'Design Landing Page',
        description: 'Design a modern, conversion-optimized landing page for a SaaS product',
        reward: 0.3,
        deadline: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
        status: TaskStatus.CLAIMED,
        poster: '0xabcd...efgh',
        claimer: '0x9876...5432',
        category: 'Design',
        skills: ['Figma', 'UI/UX', 'Web Design'],
        createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
      },
      {
        id: '3',
        title: 'Smart Contract Audit',
        description: 'Audit an ERC-20 token smart contract for security vulnerabilities',
        reward: 1.2,
        deadline: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000),
        status: TaskStatus.SUBMITTED,
        poster: '0x5555...6666',
        claimer: '0x7777...8888',
        submittedWork: 'Audit report attached with findings and recommendations',
        submissionDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
        category: 'Security',
        skills: ['Solidity', 'Security', 'Smart Contracts'],
        createdAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000)
      },
      {
        id: '4',
        title: 'Write Technical Documentation',
        description: 'Create comprehensive API documentation for a blockchain platform',
        reward: 0.4,
        deadline: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000),
        status: TaskStatus.OPEN,
        poster: '0x2222...3333',
        category: 'Documentation',
        skills: ['Technical Writing', 'API Documentation', 'Blockchain'],
        createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000)
      }
    ];
  }

  async getTasks(): Promise<Task[]> {
    console.log('Fetching tasks from contract');
    return [...this.tasks];
  }

  async getTaskById(id: string): Promise<Task | undefined> {
    console.log('Fetching task by ID:', id);
    return this.tasks.find(task => task.id === id);
  }

  async createTask(taskData: Omit<Task, 'id' | 'status' | 'createdAt'>): Promise<Task> {
    console.log('Creating new task:', taskData);
    const newTask: Task = {
      ...taskData,
      id: Date.now().toString(),
      status: TaskStatus.OPEN,
      createdAt: new Date()
    };
    this.tasks.push(newTask);
    return newTask;
  }

  async claimTask(taskId: string, claimerAddress: string): Promise<Task> {
    console.log('Claiming task:', taskId, 'by:', claimerAddress);
    const task = this.tasks.find(t => t.id === taskId);
    if (!task) throw new Error('Task not found');
    if (task.status !== TaskStatus.OPEN) throw new Error('Task is not available');
    
    task.status = TaskStatus.CLAIMED;
    task.claimer = claimerAddress;
    return task;
  }

  async submitTask(submission: TaskSubmission, submitterAddress: string): Promise<Task> {
    console.log('Submitting task:', submission.taskId);
    const task = this.tasks.find(t => t.id === submission.taskId);
    if (!task) throw new Error('Task not found');
    if (task.claimer !== submitterAddress) throw new Error('Only claimer can submit');
    
    task.status = TaskStatus.SUBMITTED;
    task.submittedWork = submission.deliverables;
    task.submissionDate = new Date();
    return task;
  }

  async approveTask(taskId: string, approverAddress: string): Promise<Task> {
    console.log('Approving task:', taskId);
    const task = this.tasks.find(t => t.id === taskId);
    if (!task) throw new Error('Task not found');
    if (task.poster !== approverAddress) throw new Error('Only poster can approve');
    if (task.status !== TaskStatus.SUBMITTED) throw new Error('Task not submitted');
    
    task.status = TaskStatus.COMPLETED;
    task.completionDate = new Date();
    return task;
  }

  async raiseDispute(taskId: string, disputeData: Omit<Dispute, 'id' | 'createdAt' | 'status'>): Promise<Dispute> {
    console.log('Raising dispute for task:', taskId);
    const task = this.tasks.find(t => t.id === taskId);
    if (!task) throw new Error('Task not found');
    
    const dispute: Dispute = {
      ...disputeData,
      id: Date.now().toString(),
      taskId,
      status: DisputeStatus.PENDING,
      createdAt: new Date()
    };
    
    this.disputes.push(dispute);
    task.status = TaskStatus.DISPUTED;
    task.disputeId = dispute.id;
    return dispute;
  }

  async getDisputes(): Promise<Dispute[]> {
    console.log('Fetching disputes');
    return [...this.disputes];
  }

  async resolveDispute(disputeId: string, resolution: string, arbitratorAddress: string): Promise<Dispute> {
    console.log('Resolving dispute:', disputeId);
    const dispute = this.disputes.find(d => d.id === disputeId);
    if (!dispute) throw new Error('Dispute not found');
    
    dispute.status = DisputeStatus.RESOLVED;
    dispute.resolution = resolution;
    dispute.arbitrator = arbitratorAddress;
    dispute.resolvedAt = new Date();
    
    const task = this.tasks.find(t => t.id === dispute.taskId);
    if (task) {
      task.status = TaskStatus.COMPLETED;
    }
    
    return dispute;
  }
}

export const taskManager = new TaskManagerContract();