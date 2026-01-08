import React from 'react';
import { Clock, Coins, User, CheckCircle, AlertCircle, FileText } from 'lucide-react';
import { Task, TaskStatus } from '../../types/task';

interface TaskCardProps {
  task?: Task;
  onClaim?: (taskId: string) => void;
  onSubmit?: (taskId: string) => void;
  onApprove?: (taskId: string) => void;
  onDispute?: (taskId: string) => void;
  currentUserAddress?: string;
}

const TaskCard: React.FC<TaskCardProps> = ({
  task = {
    id: '1',
    title: 'Sample Task',
    description: 'This is a sample task description',
    reward: 0.5,
    deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    status: TaskStatus.OPEN,
    poster: '0x1234...5678',
    category: 'Development',
    skills: ['React', 'TypeScript'],
    createdAt: new Date()
  },
  onClaim = () => console.log('Claim task'),
  onSubmit = () => console.log('Submit task'),
  onApprove = () => console.log('Approve task'),
  onDispute = () => console.log('Raise dispute'),
  currentUserAddress = '0x9876...5432'
}) => {
  console.log('TaskCard rendered:', task.title);

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.OPEN:
        return 'bg-primary/10 text-primary';
      case TaskStatus.CLAIMED:
        return 'bg-chart-4/10 text-chart-4';
      case TaskStatus.SUBMITTED:
        return 'bg-chart-2/10 text-chart-2';
      case TaskStatus.COMPLETED:
        return 'bg-chart-3/10 text-chart-3';
      case TaskStatus.DISPUTED:
        return 'bg-destructive/10 text-destructive';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.COMPLETED:
        return <CheckCircle size={16} />;
      case TaskStatus.DISPUTED:
        return <AlertCircle size={16} />;
      default:
        return <FileText size={16} />;
    }
  };

  const daysUntilDeadline = Math.ceil((task.deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  const isOwner = task.poster === currentUserAddress;
  const isClaimer = task.claimer === currentUserAddress;

  return (
    <div data-cmp="TaskCard" className="bg-card border border-border rounded-lg p-6 shadow-custom hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-card-foreground mb-2">{task.title}</h3>
          <p className="text-muted-foreground text-sm line-clamp-2 mb-3">{task.description}</p>
        </div>
        <div className={`ml-4 px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getStatusColor(task.status)}`}>
          {getStatusIcon(task.status)}
          {task.status}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {task.skills.map((skill, index) => (
          <span key={index} className="px-2 py-1 bg-accent text-accent-foreground text-xs rounded-md">
            {skill}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center gap-2 text-sm">
          <Coins className="text-primary" size={16} />
          <span className="font-semibold text-card-foreground">{task.reward} ETH</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Clock className="text-muted-foreground" size={16} />
          <span className="text-muted-foreground">
            {daysUntilDeadline > 0 ? `${daysUntilDeadline} days` : 'Expired'}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-4 text-sm text-muted-foreground">
        <User size={14} />
        <span>Posted by {task.poster.slice(0, 6)}...{task.poster.slice(-4)}</span>
      </div>

      <div className="flex gap-2">
        {task.status === TaskStatus.OPEN && !isOwner && (
          <button
            onClick={() => onClaim(task.id)}
            className="flex-1 bg-primary text-primary-foreground px-4 py-2 rounded-md font-medium hover:bg-primary/90 transition-colors"
          >
            Claim Task
          </button>
        )}
        
        {task.status === TaskStatus.CLAIMED && isClaimer && (
          <button
            onClick={() => onSubmit(task.id)}
            className="flex-1 bg-primary text-primary-foreground px-4 py-2 rounded-md font-medium hover:bg-primary/90 transition-colors"
          >
            Submit Work
          </button>
        )}
        
        {task.status === TaskStatus.SUBMITTED && isOwner && (
          <>
            <button
              onClick={() => onApprove(task.id)}
              className="flex-1 bg-chart-3 text-primary-foreground px-4 py-2 rounded-md font-medium hover:bg-chart-3/90 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => onDispute(task.id)}
              className="flex-1 bg-destructive text-destructive-foreground px-4 py-2 rounded-md font-medium hover:bg-destructive/90 transition-colors"
            >
              Dispute
            </button>
          </>
        )}
        
        {task.status === TaskStatus.SUBMITTED && isClaimer && (
          <div className="flex-1 bg-muted text-muted-foreground px-4 py-2 rounded-md font-medium text-center">
            Awaiting Review
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskCard;