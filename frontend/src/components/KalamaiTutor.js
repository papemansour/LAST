import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Send, Bot, User, Sparkles, Trash2, Plus, Clock, Loader2, MessageCircle, Brain } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import KalamaiQuiz from './KalamaiQuiz';

const KalamaiTutor = ({ userLevel = 'intermediate' }) => {
  const [activeTab, setActiveTab] = useState('chat');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I'm Kalamai, your personal English tutor at MyKalama! 🎓\n\nI'm here to help you improve your English 24/7. We can:\n- Have conversations in English\n- Practice grammar and vocabulary\n- Play word games\n- Take adaptive quizzes\n\nHow can I help you today?`
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [showSessions, setShowSessions] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Generate initial session ID
    const newSessionId = `kalamai_${Date.now()}`;
    setSessionId(newSessionId);
    fetchSessions();
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const response = await apiClient.get('/kalamai/sessions');
      setSessions(response.data || []);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const loadSession = async (sid) => {
    try {
      const response = await apiClient.get(`/kalamai/history?session_id=${sid}`);
      if (response.data && response.data.length > 0) {
        const conversation = response.data[0];
        setMessages(conversation.messages || []);
        setSessionId(sid);
        setShowSessions(false);
      }
    } catch (error) {
      console.error('Error loading session:', error);
      toast.error('Erreur lors du chargement de la conversation');
    }
  };

  const startNewSession = async () => {
    try {
      const response = await apiClient.post('/kalamai/new-session');
      setSessionId(response.data.session_id);
      setMessages([{
        role: 'assistant',
        content: `Hello! I'm Kalamai, your personal English tutor at MyKalama! 🎓\n\nI'm here to help you improve your English 24/7. We can:\n- Have conversations in English\n- Practice grammar and vocabulary\n- Play word games\n- Answer your questions\n\nHow can I help you today?`
      }]);
      toast.success('Nouvelle conversation démarrée!');
      fetchSessions();
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const deleteSession = async (sid, e) => {
    e.stopPropagation();
    try {
      await apiClient.delete(`/kalamai/session/${sid}`);
      toast.success('Conversation supprimée');
      fetchSessions();
      if (sid === sessionId) {
        startNewSession();
      }
    } catch (error) {
      console.error('Error deleting session:', error);
      toast.error('Erreur lors de la suppression');
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/kalamai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      // Add placeholder for assistant message
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                assistantMessage += data.content;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { role: 'assistant', content: assistantMessage };
                  return updated;
                });
              }
              if (data.error) {
                toast.error('Erreur: ' + data.error);
              }
            } catch (e) {
              // Ignore parsing errors
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Erreur lors de l\'envoi du message');
      setMessages(prev => prev.slice(0, -1)); // Remove loading placeholder
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-4" data-testid="kalamai-tutor">
      {/* Tabs for Chat and Quiz */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 bg-teal-100">
          <TabsTrigger 
            value="chat" 
            className="data-[state=active]:bg-teal-600 data-[state=active]:text-white"
            data-testid="kalamai-tab-chat"
          >
            <MessageCircle className="h-4 w-4 mr-2" />
            Conversation
          </TabsTrigger>
          <TabsTrigger 
            value="quiz" 
            className="data-[state=active]:bg-teal-600 data-[state=active]:text-white"
            data-testid="kalamai-tab-quiz"
          >
            <Brain className="h-4 w-4 mr-2" />
            Quiz Adaptatif
          </TabsTrigger>
        </TabsList>

        {/* Chat Tab */}
        <TabsContent value="chat" className="mt-4">
          <Card className="h-[550px] flex flex-col bg-gradient-to-br from-teal-50 to-emerald-50 border-teal-200">
            <CardHeader className="pb-3 border-b bg-white/80 backdrop-blur-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-emerald-500 rounded-full flex items-center justify-center shadow-lg">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-teal-700 text-base flex items-center gap-2">
                      Kalamai Chat
                      <Sparkles className="h-4 w-4 text-yellow-500" />
                    </CardTitle>
                    <p className="text-xs text-gray-500">Disponible 24h/24</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => setShowSessions(!showSessions)}
                    className="border-teal-300 text-teal-600 hover:bg-teal-50"
                  >
                    <Clock className="h-4 w-4 mr-1" />
                    Historique
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={startNewSession}
                    className="border-teal-300 text-teal-600 hover:bg-teal-50"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Nouveau
                  </Button>
                </div>
              </div>

              {/* Sessions Panel */}
              {showSessions && sessions.length > 0 && (
                <div className="mt-3 p-2 bg-white rounded-lg border border-teal-100 max-h-32 overflow-y-auto">
                  <p className="text-xs text-gray-500 mb-2">Conversations récentes:</p>
                  {sessions.map((session, idx) => (
                    <div 
                      key={session.session_id || idx}
                      onClick={() => loadSession(session.session_id)}
                      className="flex items-center justify-between p-2 hover:bg-teal-50 rounded cursor-pointer group"
                    >
                      <span className="text-sm truncate">
                        {formatTime(session.updated_at || session.created_at)}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => deleteSession(session.session_id, e)}
                        className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-600 hover:bg-red-50"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardHeader>

            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
              {/* Messages Area */}
              <ScrollArea ref={scrollRef} className="flex-1 p-4">
                <div className="space-y-4">
                  {messages.map((msg, idx) => (
                    <div 
                      key={idx}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`flex items-start gap-2 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                          msg.role === 'user' 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-gradient-to-br from-teal-500 to-emerald-500 text-white'
                        }`}>
                          {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                        </div>
                        <div className={`rounded-2xl px-4 py-2 ${
                          msg.role === 'user'
                            ? 'bg-blue-500 text-white rounded-br-none'
                            : 'bg-white shadow-sm border border-teal-100 rounded-bl-none'
                        }`}>
                          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                  {isLoading && messages[messages.length - 1]?.role === 'user' && (
                    <div className="flex justify-start">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-emerald-500 flex items-center justify-center">
                          <Loader2 className="h-4 w-4 text-white animate-spin" />
                        </div>
                        <div className="bg-white shadow-sm border border-teal-100 rounded-2xl rounded-bl-none px-4 py-2">
                          <div className="flex gap-1">
                            <span className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                            <span className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                            <span className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>

              {/* Input Area */}
              <div className="p-4 bg-white border-t border-teal-100">
                <div className="flex gap-2">
                  <Input
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything in English..."
                    className="flex-1 border-teal-200 focus:border-teal-400 focus:ring-teal-400"
                    disabled={isLoading}
                    data-testid="kalamai-input"
                  />
                  <Button 
                    onClick={sendMessage}
                    disabled={!input.trim() || isLoading}
                    className="bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-white px-4"
                    data-testid="kalamai-send"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quiz Tab */}
        <TabsContent value="quiz" className="mt-4">
          <KalamaiQuiz userLevel={userLevel} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default KalamaiTutor;
