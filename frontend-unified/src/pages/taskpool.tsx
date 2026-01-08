import React, { useState, useEffect } from 'react';
import { PlusCircle, Filter, Search, AlertCircle } from 'lucide-react';
import TaskCard from '../components/taskpool/TaskCard';
import TaskCreationForm from '../components/taskpool/TaskCreationForm';
import TaskSubmissionForm from '../components/taskpool/TaskSubmissionForm';
import DisputeForm from '../components/taskpool/DisputeForm';
import DisputeCard from '../components/taskpool/DisputeCard';
import { Task, TaskStatus, Dispute, TaskCreationForm as TaskFormData, TaskSubmission } from '../types/task';
import { taskManager } from '../utils/contract';

const Index: React.FC = () => {
  console.log('TaskPool page rendered');

  const [tasks, setTasks] = useState<Task[]>([]);
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [activeTab, setActiveTab] = useState<'all' | 'open' | 'claimed' | 'submitted' | 'completed' | 'disputed'>('all');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showSubmitForm, setShowSubmitForm] = useState(false);
  const [showDisputeForm, setShowDisputeForm] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentUserAddress] = useState('0x9876...5432'); // Mock user address

  useEffect(() => {
    loadTasks();
    loadDisputes();
  }, []);

  const loadTasks = async () => {
    try {
      const fetchedTasks = await taskManager.getTasks();
      console.log('Tasks loaded:', fetchedTasks.length);
      setTasks(fetchedTasks);
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  };

  const loadDisputes = async () => {
    try {
      const fetchedDisputes = await taskManager.getDisputes();
      console.log('Disputes loaded:', fetchedDisputes.length);
      setDisputes(fetchedDisputes);
    } catch (error) {
      console.error('Error loading disputes:', error);
    }
  };

  const handleCreateTask = async (formData: TaskFormData) => {
    try {
      console.log('Creating task:', formData);
      await taskManager.createTask({
        ...formData,
        poster: currentUserAddress
      });
      await loadTasks();
      setShowCreateForm(false);
    } catch (error) {
      console.error('Error creating task:', error);
    }
  };

  const handleClaimTask = async (taskId: string) => {
    try {
      console.log('Claiming task:', taskId);
      await taskManager.claimTask(taskId, currentUserAddress);
      await loadTasks();
    } catch (error) {
      console.error('Error claiming task:', error);
    }
  };

  const handleSubmitTask = async (submission: TaskSubmission) => {
    try {
      console.log('Submitting task:', submission.taskId);
      await taskManager.submitTask(submission, currentUserAddress);
      await loadTasks();
      setShowSubmitForm(false);
      setSelectedTask(null);
    } catch (error) {
      console.error('Error submitting task:', error);
    }
  };

  const handleApproveTask = async (taskId: string) => {
    try {
      console.log('Approving task:', taskId);
      await taskManager.approveTask(taskId, currentUserAddress);
      await loadTasks();
    } catch (error) {
      console.error('Error approving task:', error);
    }
  };

  const handleRaiseDispute = async (disputeData: any)
   => {
    try {
      console.log('Raising dispute:', disputeData);
      await taskManager.raiseDispute(disputeData.taskId, {
        ...disputeData,
        taskId: disputeData.taskId
      });
      await loadTasks();
      await loadDisputes();
      setShowDisputeForm(false);
      setSelectedTask(null);
    } catch (error) {
      console.error('Error raising dispute:', error);
    }
  };

  const handleResolveDispute = async (disputeId: string) => {
    try {
      console.log('Resolving dispute:', disputeId);
      await taskManager.resolveDispute(disputeId, 'Dispute resolved in favor of claimer', currentUserAddress);
      await loadDisputes();
      await loadTasks();
    } catch (error) {
      console.error('Error resolving dispute:', error);
    }
  };

  const filteredTasks = tasks.filter(task => {
    const matchesTab = activeTab === 'all' || task.status.toLowerCase() === activeTab;
    const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         task.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTab && matchesSearch;
  });

  const stats = {
    total: tasks.length,
    open: tasks.filter(t => t.status === TaskStatus.OPEN).length,
    claimed: tasks.filter(t => t.status === TaskStatus.CLAIMED).length,
    submitted: tasks.filter(t => t.status === TaskStatus.SUBMITTED).length,
    completed: tasks.filter(t => t.status === TaskStatus.COMPLETED).length,
    disputed: tasks.filter(t => t.status === TaskStatus.DISPUTED).length
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-[1440px] mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold text-foreground mb-2">Task Pool</h1>
              <p className="text-muted-foreground">Decentralized task management with smart contract integration</p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors flex items-center gap-2 shadow-custom"
            >
              <PlusCircle size={20} />
              Post Task
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="bg-card border border-border rounded-lg p-4 shadow-custom">
              <div className="text-2xl font-bold text-card-foreground">{stats.total}</div>
              <div className="text-muted-foreground text-sm">Total Tasks</div>
            </div>
            <div className="bg-card border border-border rounded-lg p-4 shadow-custom">
              <div className="text-2xl font-bold text-primary">{stats.open}</div>
              <div className="text-muted-foreground text-sm">Open</div>
            </div>
            <div className="bg-card border border-border rounded-lg p-4 shadow-custom">
              <div className="text-2xl font-bold text-chart-4">{stats.claimed}</div>
              <div className="text-muted-foreground text-sm">Claimed</div>
            </div>
            <div className="bg-card border border-border rounded-lg p-4 shadow-custom">
              <div className="text-2xl font-bold text-chart-2">{stats.submitted}</div>
              <div className="text-muted-foreground text-sm">Submitted</div>
            </div>
            <div className="bg-card border border-border rounded-lg p-4 shadow-custom">
              <div className="text-2xl font-bold text-chart-3">{stats.completed}</div>
              <div className="text-muted-foreground text-sm">Completed</div>
            </div>
            <div className="bg-card border border-border rounded-lg p-4 shadow-custom">
              <div className="text-2xl font-bold text-destructive">{stats.disputed}</div>
              <div className="text-muted-foreground text-sm">Disputed</div>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
            <input
              type="text"
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-ring shadow-custom"
            />
          </div>
          <button className="bg-card border border-border text-foreground px-6 py-3 rounded-lg font-medium hover:bg-accent transition-colors flex items-center gap-2 shadow-custom">
            <Filter size={20} />
            Filters
          </button>
        </div>

        {/* Tabs */}
        <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
          {(['all', 'open', 'claimed', 'submitted', 'completed', 'disputed'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                activeTab === tab
                  ? 'bg-primary text-primary-foreground shadow-custom'
                  : 'bg-card text-muted-foreground hover:bg-accent hover:text-accent-foreground border border-border'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tasks List */}
          <div className="lg:col-span-2">
            <h2 className="text-2xl font-bold text-foreground mb-4">Tasks</h2>
            <div className="space-y-4">
              {filteredTasks.length > 0 ? (
                filteredTasks.map(task => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    currentUserAddress={currentUserAddress}
                    onClaim={handleClaimTask}
                    onSubmit={(taskId) => {
                      setSelectedTask(task);
                      setShowSubmitForm(true);
                    }}
                    onApprove={handleApproveTask}
                    onDispute={(taskId) => {
                      setSelectedTask(task);
                      setShowDisputeForm(true);
                    }}
                  />
                ))
              ) : (
                <div className="bg-card border border-border rounded-lg p-12 text-center shadow-custom">
                  <p className="text-muted-foreground">No tasks found</p>
                </div>
              )}
            </div>
          </div>

          {/* Disputes Sidebar */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="text-destructive" size={24} />
              <h2 className="text-2xl font-bold text-foreground">Active Disputes</h2>
            </div>
            <div className="space-y-4">
              {disputes.length > 0 ? (
                disputes.map(dispute => (
                  <DisputeCard
                    key={dispute.id}
                    dispute={dispute}
                    canResolve={true}
                    onResolve={handleResolveDispute}
                  />
                ))
              ) : (
                <div className="bg-card border border-border rounded-lg p-6 text-center shadow-custom">
                  <p className="text-muted-foreground text-sm">No active disputes</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Modals */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <TaskCreationForm
                onSubmit={handleCreateTask}
                onCancel={() => setShowCreateForm(false)}
              />
            </div>
          </div>
        )}

        {showSubmitForm && selectedTask && (
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <TaskSubmissionForm
                taskId={selectedTask.id}
                taskTitle={selectedTask.title}
                onSubmit={handleSubmitTask}
                onCancel={() => {
                  setShowSubmitForm(false);
                  setSelectedTask(null);
                }}
              />
            </div>
          </div>
        )}

        {showDisputeForm && selectedTask && (
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <DisputeForm
                taskId={selectedTask.id}
                taskTitle={selectedTask.title}
                userAddress={currentUserAddress}
                onSubmit={handleRaiseDispute}
                onCancel={() => {
                  setShowDisputeForm(false);
                  setSelectedTask(null);
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;