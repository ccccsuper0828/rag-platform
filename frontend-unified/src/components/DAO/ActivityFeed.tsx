import React from 'react';
import { Vote, FileText, CheckCircle} from 'lucide-react';

interface Activity {
  id: string;
  type: 'vote' | 'proposal' | 'execution';
  title: string;
  description: string;
  timestamp: Date;
  user: string;
}

interface ActivityFeedProps {
  activities?: Activity[];
}

const ActivityFeed: React.FC<ActivityFeedProps> = ({
  activities = [
    {
      id: '1',
      type: 'vote',
      title: 'Voted For',
      description: 'Treasury Allocation Proposal',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      user: '0x1234...5678'
    },
    {
      id: '2',
      type: 'proposal',
      title: 'New Proposal',
      description: 'Update Governance Parameters',
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
      user: '0xabcd...ef01'
    },
    {
      id: '3',
      type: 'execution',
      title: 'Proposal Executed',
      description: 'Token Buyback Program',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
      user: '0x9876...5432'
    }
  ]
}) => {
  console.log('ActivityFeed rendered with', activities.length, 'activities');
  
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'vote':
        return Vote;
      case 'proposal':
        return FileText;
      case 'execution':
        return CheckCircle;
      default:
        return FileText;
    }
  };
  
  const getTimeAgo = (timestamp: Date) => {
    const seconds = Math.floor((Date.now() - timestamp.getTime()) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };
  
  return (
    <div data-cmp="ActivityFeed" className="bg-card border border-border rounded-lg p-6 shadow-custom">
      <h3 className="text-lg font-semibold text-foreground mb-4">Recent Activity</h3>
      
      <div className="space-y-4">
        {activities.map((activity) => {
          const Icon = getActivityIcon(activity.type);
          
          return (
            <div key={activity.id} className="flex items-start space-x-3 p-3 bg-accent rounded-lg">
              <div className="p-2 bg-gradient-to-r from-primary to-chart-2 rounded-lg flex-shrink-0">
                <Icon className="text-primary-foreground" size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between mb-1">
                  <p className="text-sm font-medium text-foreground">{activity.title}</p>
                  <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                    {getTimeAgo(activity.timestamp)}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mb-1">{activity.description}</p>
                <p className="text-xs font-mono text-muted-foreground">{activity.user}</p>
              </div>
            </div>
          );
        })}
      </div>
      
      <button className="w-full mt-4 text-sm text-primary hover:text-primary/80 font-medium">
        View All Activity
      </button>
    </div>
  );
};

export default ActivityFeed;