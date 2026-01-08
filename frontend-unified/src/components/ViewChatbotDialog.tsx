import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Copy, Code, Settings, BarChart3, Bot } from 'lucide-react';
import { toast } from 'sonner';

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

interface ViewChatbotDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  chatbot: Chatbot;
}

export function ViewChatbotDialog({ open, onOpenChange, chatbot }: ViewChatbotDialogProps) {
  const [copied, setCopied] = useState(false);

  const embedCode = `<!-- Chatbot Widget -->
<div id="chatbot-${chatbot.id}"></div>
<script>
  (function() {
    var script = document.createElement('script');
    script.src = 'https://cdn.chatbot.com/widget.js';
    script.setAttribute('data-chatbot-id', '${chatbot.id}');
    script.setAttribute('data-theme-color', '${chatbot.color}');
    document.head.appendChild(script);
  })();
</script>`;

  const apiCode = `// JavaScript SDK Example
import ChatbotSDK from 'chatbot-sdk';

const chatbot = new ChatbotSDK({
  chatbotId: '${chatbot.id}',
  apiKey: 'your-api-key',
  themeColor: '${chatbot.color}'
});

// Initialize chatbot
chatbot.init();

// Send a message programmatically
chatbot.sendMessage('Hello, how can I help you?');`;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast('Code copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div 
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: chatbot.color + '20' }}
            >
              <Bot className="h-4 w-4" style={{ color: chatbot.color }} />
            </div>
            {chatbot.name}
            <Badge variant={chatbot.status === 'active' ? 'default' : 'secondary'}>
              {chatbot.status}
            </Badge>
          </DialogTitle>
          <DialogDescription>
            {chatbot.description} ?{chatbot.website}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="integration" className="mt-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="integration">Integration</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="integration" className="space-y-4">
            <div>
              <h4 className="flex items-center gap-2 mb-2">
                <Code className="h-4 w-4" />
                HTML Embed Code
              </h4>
              <p className="text-sm text-muted-foreground mb-3">
                Copy and paste this code into your website's HTML to add the chatbot widget.
              </p>
              <div className="relative">
                <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                  <code>{embedCode}</code>
                </pre>
                <Button
                  size="sm"
                  variant="outline"
                  className="absolute top-2 right-2"
                  onClick={() => copyToClipboard(embedCode)}
                >
                  <Copy className="h-4 w-4" />
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>
            </div>

            <div>
              <h4 className="flex items-center gap-2 mb-2">
                <Code className="h-4 w-4" />
                JavaScript SDK
              </h4>
              <p className="text-sm text-muted-foreground mb-3">
                For more advanced integration, use our JavaScript SDK.
              </p>
              <div className="relative">
                <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                  <code>{apiCode}</code>
                </pre>
                <Button
                  size="sm"
                  variant="outline"
                  className="absolute top-2 right-2"
                  onClick={() => copyToClipboard(apiCode)}
                >
                  <Copy className="h-4 w-4" />
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="p-4 border rounded-lg">
                <h5>Widget Preview</h5>
                <div className="mt-2 p-3 bg-muted rounded text-center text-sm text-muted-foreground">
                  <Bot className="h-8 w-8 mx-auto mb-2" style={{ color: chatbot.color }} />
                  Chatbot widget will appear here on your website
                </div>
              </div>
              
              <div className="p-4 border rounded-lg">
                <h5>Quick Stats</h5>
                <div className="mt-2 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Conversations:</span>
                    <span>{chatbot.conversations}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Active:</span>
                    <span>{chatbot.lastActive}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status:</span>
                    <Badge variant={chatbot.status === 'active' ? 'default' : 'secondary'} className="text-xs">
                      {chatbot.status}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h5 className="flex items-center gap-2 mb-3">
                    <Settings className="h-4 w-4" />
                    Configuration
                  </h5>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Chatbot ID:</span>
                      <code className="text-xs bg-muted px-1 rounded">{chatbot.id}</code>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Website:</span>
                      <span>{chatbot.website}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Theme Color:</span>
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: chatbot.color }}
                        />
                        <code className="text-xs">{chatbot.color}</code>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h5>Behavior Settings</h5>
                  <div className="mt-3 space-y-2 text-sm text-muted-foreground">
                    <p>?Auto-greet visitors after 5 seconds</p>
                    <p>?Show typing indicators</p>
                    <p>?Collect visitor email</p>
                    <p>?Enable file uploads</p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            <div className="text-center py-8 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-4" />
              <p>Detailed analytics available with Supabase integration</p>
              <p className="text-sm">Connect to a backend to track conversation metrics, user engagement, and more</p>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}