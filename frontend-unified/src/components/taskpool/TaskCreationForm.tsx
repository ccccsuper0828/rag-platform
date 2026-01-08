import React, { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { TaskCreationForm as TaskFormData } from '../../types/task';
const now = Date.now()
interface TaskCreationFormProps {
  onSubmit?: (formData: TaskFormData) => void;
  onCancel?: () => void;
}

const TaskCreationForm: React.FC<TaskCreationFormProps> = ({
  onSubmit = () => console.log('Submit task'),
  onCancel = () => console.log('Cancel')
}) => {
  console.log('TaskCreationForm rendered');

  const [formData, setFormData] = useState<TaskFormData>({
    title: '',
    description: '',
    reward: 0,
    deadline: new Date(now + 7 * 24 * 60 * 60 * 1000),
    category: 'Development',
    skills: []
  });

  const [skillInput, setSkillInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Submitting task:', formData);
    onSubmit(formData);
  };

  const addSkill = () => {
    if (skillInput.trim() && !formData.skills.includes(skillInput.trim())) {
      setFormData({
        ...formData,
        skills: [...formData.skills, skillInput.trim()]
      });
      setSkillInput('');
    }
  };

  const removeSkill = (skill: string) => {
    setFormData({
      ...formData,
      skills: formData.skills.filter(s => s !== skill)
    });
  };

  return (
    <div data-cmp="TaskCreationForm" className="bg-card border border-border rounded-lg p-6 shadow-custom">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-card-foreground">Create New Task</h2>
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
            Task Title
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="w-full px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Enter task title"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[120px]"
            placeholder="Describe the task requirements"
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-2">
              Reward (ETH)
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.reward}
              onChange={(e) => setFormData({ ...formData, reward: parseFloat(e.target.value) })}
              className="w-full px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="0.5"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-card-foreground mb-2">
              Deadline
            </label>
            <input
              type="date"
              value={formData.deadline.toISOString().split('T')[0]}
              onChange={(e) => setFormData({ ...formData, deadline: new Date(e.target.value) })}
              className="w-full px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Category
          </label>
          <select
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            className="w-full px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option>Development</option>
            <option>Design</option>
            <option>Marketing</option>
            <option>Writing</option>
            <option>Security</option>
            <option>Documentation</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Required Skills
          </label>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
              className="flex-1 px-4 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Add a skill"
            />
            <button
              type="button"
              onClick={addSkill}
              className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
            >
              <Plus size={20} />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.skills.map((skill, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-accent text-accent-foreground rounded-full text-sm flex items-center gap-2"
              >
                {skill}
                <button
                  type="button"
                  onClick={() => removeSkill(skill)}
                  className="hover:text-destructive transition-colors"
                >
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            className="flex-1 bg-primary text-primary-foreground px-6 py-3 rounded-md font-medium hover:bg-primary/90 transition-colors"
          >
            Create Task
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

export default TaskCreationForm;