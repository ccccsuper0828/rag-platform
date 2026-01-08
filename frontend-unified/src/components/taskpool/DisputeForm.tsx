import React, { useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { DisputeForm as DisputeFormData } from '../../types/task';

interface DisputeFormProps {
  taskId?: string;
  taskTitle?: string;
  onSubmit?: (dispute: DisputeFormData) => void;
  onCancel?: () => void;
  userAddress?: string;
}

const DisputeForm: React.FC<DisputeFormProps> = ({
  taskId = '1',
  taskTitle = 'Sample Task',
  onSubmit = () => console.log('Submit dispute'),
  onCancel = () => console.log('Cancel'),
  userAddress = '0x1234...5678'
}) => {
  console.log('DisputeForm rendered for task:', taskId);

  const [reason, setReason] = useState('');
  const [evidence, setEvidence] = useState<string[]>([]);
  const [evidenceInput, setEvidenceInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Submitting dispute for task:', taskId);
    onSubmit({
      taskId,
      raisedBy: userAddress,
      reason,
      evidence
    });
  };

  const addEvidence = () => {
    if (evidenceInput.trim()) {
      setEvidence([...evidence, evidenceInput.trim()]);
      setEvidenceInput('');
    }
  };

  const removeEvidence = (index: number) => {
    setEvidence(evidence.filter((_, i) => i !== index));
  };

  return (
    <div data-cmp="DisputeForm" className="bg-card border border-border rounded-lg p-6 shadow-custom">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-destructive/10 rounded-lg">
            <AlertTriangle className="text-destructive" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-card-foreground">Raise Dispute</h2>
            <p className="text-muted-foreground text-sm mt-1">{taskTitle}</p>
          </div>
        </div>
        <button
          onClick={onCancel}
          className="text-muted-foreground hover:text-card-foreground transition-colors"
        >
          <X size={24} />
        </button>
      </div>

      <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 mb-6">
        <p className="text-sm text-destructive">
          Please provide a clear reason for the dispute and supporting evidence. Disputes will be reviewed by arbitrators.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Reason for Dispute
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[150px]"
            placeholder="Explain why you are raising this dispute"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Supporting Evidence
          </label>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={evidenceInput}
              onChange={(e) => setEvidenceInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addEvidence())}
              className="flex-1 px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Add evidence link or description"
            />
            <button
              type="button"
              onClick={addEvidence}
              className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
            >
              Add
            </button>
          </div>
          {evidence.length > 0 && (
            <div className="space-y-2">
              {evidence.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <span className="text-sm text-muted-foreground">{item}</span>
                  <button
                    type="button"
                    onClick={() => removeEvidence(index)}
                    className="text-destructive hover:text-destructive/80 transition-colors"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            className="flex-1 bg-destructive text-destructive-foreground px-6 py-3 rounded-md font-medium hover:bg-destructive/90 transition-colors"
          >
            Submit Dispute
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

export default DisputeForm;