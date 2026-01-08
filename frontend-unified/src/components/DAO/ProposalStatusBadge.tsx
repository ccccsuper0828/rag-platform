import React from 'react';
import { ProposalStatus } from '../../types/governance';
import { CheckCircle, XCircle, Clock, Play, Check } from 'lucide-react';

interface ProposalStatusBadgeProps {
  status?: ProposalStatus;
}

const ProposalStatusBadge: React.FC<ProposalStatusBadgeProps> = ({
  status = 'active'
}) => {
  console.log('ProposalStatusBadge rendered:', status);
  
  const statusConfig = {
    active: {
      label: 'Active',
      icon: Play,
      className: 'bg-chart-2/10 text-chart-2 border-chart-2/20'
    },
    passed: {
      label: 'Passed',
      icon: CheckCircle,
      className: 'bg-chart-3/10 text-chart-3 border-chart-3/20'
    },
    rejected: {
      label: 'Rejected',
      icon: XCircle,
      className: 'bg-destructive/10 text-destructive border-destructive/20'
    },
    executed: {
      label: 'Executed',
      icon: Check,
      className: 'bg-chart-3/10 text-chart-3 border-chart-3/20'
    },
    pending: {
      label: 'Pending',
      icon: Clock,
      className: 'bg-chart-4/10 text-chart-4 border-chart-4/20'
    }
  };
  
  const config = statusConfig[status];
  const Icon = config.icon;
  
  return (
    <span
      data-cmp="ProposalStatusBadge"
      className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium border ${config.className}`}
    >
      <Icon size={14} />
      <span>{config.label}</span>
    </span>
  );
};

export default ProposalStatusBadge;