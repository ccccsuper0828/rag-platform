import React, { useState } from 'react';
import { X, Upload } from 'lucide-react';
import { TaskSubmission } from '../../types/task';

interface TaskSubmissionFormProps {
  taskId?: string;
  taskTitle?: string;
  onSubmit?: (submission: TaskSubmission) => void;
  onCancel?: () => void;
}

const TaskSubmissionForm: React.FC<TaskSubmissionFormProps> = ({
  taskId = '1',
  taskTitle = 'Sample Task',
  onSubmit = () => console.log('Submit work'),
  onCancel = () => console.log('Cancel')
}) => {
  console.log('TaskSubmissionForm rendered for task:', taskId);

  const [deliverables, setDeliverables] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Submitting work for task:', taskId);
    onSubmit({
      taskId,
      deliverables,
      notes,
      submittedAt: new Date()
    });
  };

  return (
    <div data-cmp="TaskSubmissionForm" className="bg-card border border-border rounded-lg p-6 shadow-custom">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-card-foreground">Submit Work</h2>
          <p className="text-muted-foreground text-sm mt-1">{taskTitle}</p>
        </div>
        <button
          onClick={onCancel}
          className="text-muted-foreground hover:text-card-foreground transition-colors"
        >
          <X size={24} />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Deliverables
          </label>
          <textarea
            value={deliverables}
            onChange={(e) => setDeliverables(e.target.value)}
            className="w-full px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[150px]"
            placeholder="Describe what you've completed and provide links to your work"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Additional Notes
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[100px]"
            placeholder="Any additional information or context"
          />
        </div>

        <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
          <Upload className="mx-auto text-muted-foreground mb-2" size={32} />
          <p className="text-muted-foreground text-sm mb-2">Upload supporting files</p>
          <button
            type="button"
            className="text-primary hover:text-primary/80 text-sm font-medium"
          >
            Browse Files
          </button>
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            className="flex-1 bg-primary text-primary-foreground px-6 py-3 rounded-md font-medium hover:bg-primary/90 transition-colors"
          >
            Submit Work
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-3 bg-secondary text-secondary-foreground rounded-md font-medium hover:bg-secondary/80 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default TaskSubmissionForm;