import React from 'react';
import { AlertTriangle, Clock, CheckCircle, XCircle, Scale } from 'lucide-react';
import { Dispute, DisputeStatus } from '../../types/task';

interface DisputeCardProps {
  dispute?: Dispute;
  onResolve?: (disputeId: string) => void;
  canResolve?: boolean;
}

const DisputeCard: React.FC<DisputeCardProps> = ({
  dispute = {
    id: '1',
    taskId: '1',
    raisedBy: '0x1234...5678',
    reason: 'Sample dispute reason',
    evidence: ['Evidence 1', 'Evidence 2'],
    status: DisputeStatus.PENDING,
    createdAt: new Date()
  },
  onResolve = () => console.log('Resolve dispute'),
  canResolve = false
}) => {
  console.log('DisputeCard rendered:', dispute.id);

  const getStatusColor = (status: DisputeStatus) => {
    switch (status) {
      case DisputeStatus.PENDING:
        return 'bg-chart-4/10 text-chart-4';
      case DisputeStatus.REVIEWING:
        return 'bg-chart-2/10 text-chart-2';
      case DisputeStatus.RESOLVED:
        return 'bg-chart-3/10 text-chart-3';
      case DisputeStatus.REJECTED:
        return 'bg-destructive/10 text-destructive';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getStatusIcon = (status: DisputeStatus) => {
    switch (status) {
      case DisputeStatus.PENDING:
        return <Clock size={16} />;
      case DisputeStatus.REVIEWING:
        return <Scale size={16} />;
      case DisputeStatus.RESOLVED:
        return <CheckCircle size={16} />;
      case DisputeStatus.REJECTED:
        return <XCircle size={16} />;
      default:
        return <AlertTriangle size={16} />;
    }
  };

  return (
    <div data-cmp="DisputeCard" className="bg-card border border-border rounded-lg p-6 shadow-custom">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-destructive/10 rounded-lg">
            <AlertTriangle className="text-destructive" size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-card-foreground">Dispute #{dispute.id}</h3>
            <p className="text-muted-foreground text-xs">Task ID: {dispute.taskId}</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getStatusColor(dispute.status)}`}>
          {getStatusIcon(dispute.status)}
          {dispute.status}
        </div>
      </div>

      <div className="mb-4">
        <h4 className="text-sm font-medium text-card-foreground mb-2">Reason</h4>
        <p className="text-muted-foreground text-sm">{dispute.reason}</p>
      </div>

      {dispute.evidence.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-card-foreground mb-2">Evidence</h4>
          <div className="space-y-1">
            {dispute.evidence.map((item, index) => (
              <div key={index} className="text-sm text-muted-foreground bg-muted p-2 rounded">
                {item}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-muted-foreground mb-4">
        <span>Raised by {dispute.raisedBy.slice(0, 6)}...{dispute.raisedBy.slice(-4)}</span>
        <span>{dispute.createdAt.toLocaleDateString()}</span>
      </div>

      {dispute.resolution && (
        <div className="bg-chart-3/10 border border-chart-3/20 rounded-lg p-3 mb-4">
          <h4 className="text-sm font-medium text-chart-3 mb-1">Resolution</h4>
          <p className="text-sm text-card-foreground">{dispute.resolution}</p>
          {dispute.arbitrator && (
            <p className="text-xs text-muted-foreground mt-1">
              By {dispute.arbitrator.slice(0, 6)}...{dispute.arbitrator.slice(-4)}
            </p>
          )}
        </div>
      )}

      {canResolve && dispute.status === DisputeStatus.PENDING && (
        <button
          onClick={() => onResolve(dispute.id)}
          className="w-full bg-primary text-primary-foreground px-4 py-2 rounded-md font-medium hover:bg-primary/90 transition-colors"
        >
          Review & Resolve
        </button>
      )}
    </div>
  );
};

export default DisputeCard;