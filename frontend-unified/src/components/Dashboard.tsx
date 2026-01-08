import logoUrl from '../assets/logo.svg';
import { useState } from 'react';
import { Bot,Eye,Plus,Trash2, Edit, Users, MessageSquare, Zap, Paperclip,ArrowUp } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { CreateChatbotDialog } from './CreateChatbotDialog';
import { ViewChatbotDialog } from './ViewChatbotDialog';
import { EditChatbotDialog } from './EditChatbotDialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import CitationsList from './CitationsList';
import AnswerDisplay from './AnswersDisplay';
import TrendingQuestions from './TrendingQuestions';
import LumosPanel from './LumosPanel';

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

const mockChatbots: Chatbot[] = [
  {
    id: '1',
    name: 'E-commerce Support',
    website: 'shop.example.com',
    status: 'active',
    conversations: 1247,
    lastActive: '2 minutes ago',
    color: '#3B82F6',
    description: 'Handles customer support for online store'
  },
  {
    id: '2',
    name: 'Lead Generator',
    website: 'landing.example.com',
    status: 'active',
    conversations: 856,
    lastActive: '1 hour ago',
    color: '#10B981',
    description: 'Qualifies leads and collects contact information'
  },
  {
    id: '3',
    name: 'FAQ Assistant',
    website: 'docs.example.com',
    status: 'inactive',
    conversations: 432,
    lastActive: '3 days ago',
    color: '#8B5CF6',
    description: 'Answers frequently asked questions'
  }
];

export function Dashboard() {
  const [chatbots, setChatbots] = useState<Chatbot[]>(mockChatbots);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showViewDialog, setShowViewDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedChatbot, setSelectedChatbot] = useState<Chatbot | null>(null);

  const handleCreateChatbot = (data: { name: string; website: string; description: string; color: string }) => {
    const newChatbot: Chatbot = {
      id: Date.now().toString(),
      name: data.name,
      website: data.website,
      status: 'active',
      conversations: 0,
      lastActive: 'Just created',
      color: data.color,
      description: data.description
    };
    setChatbots([...chatbots, newChatbot]);
  };

  const handleEditChatbot = (data: { name: string; website: string; description: string; color: string }) => {
    if (!selectedChatbot) return;
    
    setChatbots(chatbots.map(bot => 
      bot.id === selectedChatbot.id 
        ? { ...bot, ...data }
        : bot
    ));
  };

  const handleDeleteChatbot = (id: string) => {
    setChatbots(chatbots.filter(bot => bot.id !== id));
  };

  const totalConversations = chatbots.reduce((sum, bot) => sum + bot.conversations, 0);
  const activeChatbots = chatbots.filter(bot => bot.status === 'active').length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-bold text-foreground bg-gradient-to-r from-primary to-yellow-500 bg-clip-text text-transparent mb-2">
            Homepage
          </h1>
          <p className="text-muted-foreground">
            Ask your RAG and evaluate answers.
          </p>
        </div>
      
      </div>

      <Tabs defaultValue="Ask Agent" className="space-y-6">
        <TabsList>
          <TabsTrigger value="Ask Agent">Ask Agent</TabsTrigger>
          <TabsTrigger value="Citations">Citations</TabsTrigger>
          <TabsTrigger value="chatbots">Chatbots</TabsTrigger>
        </TabsList>
        <TabsContent value="Ask Agent" className="space-y-6">
           <Card>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <img src={logoUrl} alt="Logo" className="h-12 w-12 mx-auto mb-4" />
                <p className="text-sm">Connect to a backend to store and analyze conversation data</p>
              </div>
              <div className="w-full mb-8 relative z-10">
                <div className="relative group max-w-4xl mx-auto">
                  <div className="absolute inset-0 bg-gradient-to-r from-primary to-yellow-600 rounded-3xl opacity-20 blur-xl group-hover:opacity-30 transition-opacity"></div>
                  <div className="relative bg-card rounded-2xl border border-border shadow-lg p-2 flex flex-col">
                    <textarea 
                      className="w-full bg-transparent border-none focus:ring-0 text-lg p-4 min-h-[80px] text-foreground placeholder:text-muted-foreground/50 resize-none font-medium" 
                      placeholder="Message LUMOS." 
                    />
                   <div className="flex items-center justify-between px-2 pb-2">
                     <div className="flex items-center gap-2">
                       <button className="p-2 text-muted-foreground hover:text-primary hover:bg-secondary rounded-full transition-colors" title="Voice Input">
                         <Paperclip className="w-5 h-5" />
                       </button>
                     </div>
                     <button className="bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl px-6 py-2.5 font-medium transition-all flex items-center gap-2 shadow-md">
                       <span>Ask</span>
                       <ArrowUp className="w-4 h-4" />
                     </button>
                   </div>
                 </div>
               </div>
             </div>
            </CardContent>
          </Card>
          <AnswerDisplay/>
          <LumosPanel/>
        </TabsContent>

        <TabsContent value="Citations" className="space-y-6">
          {/* Ciations */}
          <CitationsList />
          <TrendingQuestions/>
        </TabsContent>

        <TabsContent value="chatbots" className="space-y-6">
             {/* Stats Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Total Chatbots</CardTitle>
                <Bot className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">{chatbots.length}</div>
                <p className="text-xs text-muted-foreground">
                  {activeChatbots} active
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Conversations</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">{totalConversations.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  +12% from last month
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Active Users</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">2,547</div>
                <p className="text-xs text-muted-foreground">
                  +8% from last month
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Response Time</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">1.2s</div>
                <p className="text-xs text-muted-foreground">
                  -0.3s from last month
                </p>
              </CardContent>
            </Card>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {chatbots.map((chatbot) => (
              <Card key={chatbot.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: chatbot.color + '20' }}
                      >
                        <Bot className="h-4 w-4" style={{ color: chatbot.color }} />
                      </div>
                      <CardTitle className="text-lg">{chatbot.name}</CardTitle>
                    </div>
                    <Badge variant={chatbot.status === 'active' ? 'default' : 'secondary'}>
                      {chatbot.status}
                    </Badge>
                  </div>
                  <CardDescription>{chatbot.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Website:</span>
                      <span>{chatbot.website}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Conversations:</span>
                      <span>{chatbot.conversations}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Last Active:</span>
                      <span>{chatbot.lastActive}</span>
                    </div>
                  </div>
      
                  
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => {
                        setSelectedChatbot(chatbot);
                        setShowViewDialog(true);
                      }}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        setSelectedChatbot(chatbot);
                        setShowEditDialog(true);
                      }}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleDeleteChatbot(chatbot.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
           <div className="absolute left-1/2 bottom-4 transform -translate-x-1/2">
             <Button aria-label="Create chatbot" onClick={() => setShowCreateDialog(true)} className="gap-2">
               <Plus className="h-4 w-4" />
               Create Chatbot
             </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <CreateChatbotDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSubmit={handleCreateChatbot}
      />

      {selectedChatbot && (
        <>
          <ViewChatbotDialog
            open={showViewDialog}
            onOpenChange={setShowViewDialog}
            chatbot={selectedChatbot}
          />
          
          <EditChatbotDialog
            open={showEditDialog}
            onOpenChange={setShowEditDialog}
            chatbot={selectedChatbot}
            onSubmit={handleEditChatbot}
          />
        </>
      )}
    </div>
  );
}