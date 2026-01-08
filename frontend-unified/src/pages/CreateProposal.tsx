import React, { useState } from 'react';
import { ArrowLeft, Plus} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const CreateProposal: React.FC = () => {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('treasury');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  console.log('CreateProposal page rendered');
  
  const categories = [
    { id: 'treasury', name: 'Treasury' },
    { id: 'governance', name: 'Governance' },
    { id: 'protocol', name: 'Protocol' },
    { id: 'other', name: 'Other' }
  ];
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    console.log('Proposal created:', { title, description, category });
    navigate('/proposals');
  };
  
  return (
    <div className="py-8 px-8">
      <Link
        to="/proposals"
        className="inline-flex items-center space-x-2 text-muted-foreground hover:text-foreground mb-6 transition-colors"
      >
        <ArrowLeft size={20} />
        <span>Back to Proposals</span>
      </Link>
      
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Create New Proposal
          </h1>
          <p className="text-muted-foreground">
            Submit a proposal for the DAO to vote on
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Proposal Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter a clear, concise title"
                  required
                  className="w-full px-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Category *
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Description *
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Provide a detailed description of your proposal, including rationale, implementation details, and expected outcomes"
                  required
                  rows={10}
                  className="w-full px-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                />
                <p className="text-xs text-muted-foreground mt-2">
                  Supports Markdown formatting
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Voting Parameters
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Voting Delay (days)
                </label>
                <input
                  type="number"
                  defaultValue={1}
                  min={0}
                  max={7}
                  className="w-full px-4 py-3 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Time before voting starts
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Voting Period (days)
                </label>
                <input
                  type="number"
                  defaultValue={7}
                  min={1}
                  max={14}
                  className="w-full px-4 py-3 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  How long voting will be open
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-card border border-border rounded-lg p-6 shadow-custom">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">
                Proposed Actions
              </h3>
              <button
                type="button"
                className="flex items-center space-x-2 text-sm text-primary hover:text-primary/80 font-medium"
              >
                <Plus size={16} />
                <span>Add Action</span>
              </button>
            </div>
            <p className="text-sm text-muted-foreground">
              No actions added yet. Actions will be executed if the proposal passes.
            </p>
          </div>
          
          <div className="flex items-center justify-between pt-6 border-t border-border">
            <Link
              to="/proposals"
              className="px-6 py-3 text-foreground hover:text-muted-foreground transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={isSubmitting || !title || !description}
              className="bg-gradient-to-r from-primary to-chart-2 text-primary-foreground px-8 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Creating Proposal...' : 'Create Proposal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateProposal;