import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Edit } from 'lucide-react';

interface Chatbot {
  id: string;
  name: string;
  website: string;
  status: 'active' | 'inactive';
  conversations: number;
  lastActive: string;
  color: string;
  description: string;
}

interface EditChatbotDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  chatbot: Chatbot;
  onSubmit: (data: { name: string; website: string; description: string; color: string }) => void;
}

const colors = [
  '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444', '#6B7280'
];

export function EditChatbotDialog({ open, onOpenChange, chatbot, onSubmit }: EditChatbotDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    website: '',
    description: '',
    color: colors[0]
  });

  useEffect(() => {
    if (chatbot) {
      setFormData({
        name: chatbot.name,
        website: chatbot.website,
        description: chatbot.description,
        color: chatbot.color
      });
    }
  }, [chatbot]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.name && formData.website) {
      onSubmit(formData);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit className="h-5 w-5" />
            Edit Chatbot
          </DialogTitle>
          <DialogDescription>
            Update your chatbot configuration
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-name">Chatbot Name</Label>
            <Input
              id="edit-name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Customer Support Bot"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-website">Website URL</Label>
            <Input
              id="edit-website"
              value={formData.website}
              onChange={(e) => setFormData({ ...formData, website: e.target.value })}
              placeholder="e.g., example.com"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-description">Description</Label>
            <Textarea
              id="edit-description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe what this chatbot does..."
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label>Theme Color</Label>
            <div className="flex gap-2">
              {colors.map((color) => (
                <button
                  key={color}
                  type="button"
                  className={`w-8 h-8 rounded-full border-2 ${
                    formData.color === color ? 'border-foreground' : 'border-border'
                  }`}
                  style={{ backgroundColor: color }}
                  onClick={() => setFormData({ ...formData, color })}
                />
              ))}
            </div>
          </div>

          <div className="flex gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} className="flex-1">
              Cancel
            </Button>
            <Button type="submit" className="flex-1">
              Save Changes
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}