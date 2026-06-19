import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { AsyncButton } from '../components/ui/async-button';
import { Input } from '../components/ui/input';
import Marquee from '../components/ui/marquee';
import { useAuth } from '../context/AuthContext';
import { Send, Terminal, Cpu, ShieldCheck, Plus, Trash2, MessageSquare, X, LifeBuoy } from 'lucide-react';
import { apiClient } from '../lib/apiClient';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface ChatSession {
  id: number;
  title: string;
  updated_at?: string;
}

const Support: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [canEscalate, setCanEscalate] = useState(false);
  const [escalating, setEscalating] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const welcomeMessages = useMemo<Message[]>(() => {
    const welcome = i18n.language === 'bn'
      ? 'সিস্টেম অনলাইন। আমি আপনার AI সাপোর্ট অ্যাসিস্ট্যান্ট। কিভাবে সাহায্য করতে পারি?'
      : 'System Online. I am your AI Support assistant. How can I help you today?';
    return [
      { role: 'system', content: '>>> INITIALIZING MOUNO_OS v0.1...' },
      { role: 'system', content: '>>> CONNECTION ESTABLISHED VIA ENCRYPTED CHANNEL' },
      { role: 'assistant', content: welcome },
    ];
  }, [i18n.language]);

  // Load the list of chat sessions (logged-in users only).
  const loadSessions = useCallback(async () => {
    if (!token) return;
    try {
      const res = await apiClient.get<{ sessions: ChatSession[] }>('/api/ai/sessions', { silent: true });
      setSessions(Array.isArray(res.data?.sessions) ? res.data.sessions : []);
    } catch {
      /* offline: keep current list */
    }
  }, [token]);

  // Load messages for a specific session.
  const openSession = useCallback(async (sessionId: number) => {
    setActiveSessionId(sessionId);
    setHistoryOpen(false);
    if (!token) return;
    try {
      const res = await apiClient.get<{ messages: { role: Message['role']; content: string }[] }>(
        `/api/ai/sessions/${sessionId}/messages`,
        { silent: true }
      );
      const loaded: Message[] = Array.isArray(res.data?.messages)
        ? res.data.messages.map((m) => ({ role: m.role, content: m.content }))
        : [];
      setMessages(loaded.length ? [welcomeMessages[0], ...loaded] : welcomeMessages);
    } catch {
      setMessages(welcomeMessages);
    }
  }, [token, welcomeMessages]);

  const startNewChat = useCallback(() => {
    setActiveSessionId(null);
    setMessages(welcomeMessages);
    setInput('');
    setHistoryOpen(false);
    setCanEscalate(false);
  }, [welcomeMessages]);

  const deleteSession = useCallback(async (sessionId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!token) return;
    try {
      await apiClient.delete(`/api/ai/sessions/${sessionId}`, { silent: true });
    } catch {
      /* ignore */
    }
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (activeSessionId === sessionId) startNewChat();
  }, [token, activeSessionId, startNewChat]);

  // Initial load.
  useEffect(() => {
    setMessages(welcomeMessages);
    if (token) loadSessions();
  }, [token, welcomeMessages, loadSessions]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const res = await apiClient.post<{ answer?: string; session_id?: number; suggest_escalation?: boolean; message?: string }>(
        '/api/ai/chat',
        { question: userMessage, session_id: activeSessionId },
        { silent: true }
      );
      const data = res.data;
      if (data?.answer) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.answer as string }]);
        if (data.session_id && data.session_id !== activeSessionId) {
          setActiveSessionId(data.session_id);
        }
        setCanEscalate(Boolean(data.suggest_escalation));
        // Refresh history so the new/updated session shows up.
        if (token) loadSessions();
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: data?.message || 'ERROR: UPLINK_FAILURE' }]);
        setCanEscalate(true);
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'CRITICAL_ERROR: NETWORK_OFFLINE' }]);
      setCanEscalate(true);
    } finally {
      setLoading(false);
    }
  };

  // Escalate the current conversation to a human support agent by creating a
  // ticket (carrying the AI chat session_id + transcript), then navigate to it.
  const handleEscalate = useCallback(async () => {
    if (!token || escalating) return;
    setEscalating(true);
    const firstUserMsg = messages.find(m => m.role === 'user')?.content || 'Support request';
    try {
      const res = await apiClient.post<{ ticket?: { id: number } }>(
        '/api/support/tickets',
        { session_id: activeSessionId, subject: firstUserMsg.slice(0, 120) },
        { silent: true }
      );
      if (res.data?.ticket?.id) {
        navigate(`/tickets?open=${res.data.ticket.id}`);
      } else {
        setMessages(prev => [...prev, { role: 'system', content: '>>> ESCALATION_FAILED' }]);
      }
    } catch {
      setMessages(prev => [...prev, { role: 'system', content: '>>> ESCALATION_FAILED: NETWORK_OFFLINE' }]);
    } finally {
      setEscalating(false);
    }
  }, [token, escalating, messages, activeSessionId, navigate]);

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-4 font-mono relative md:h-[calc(100dvh-12rem)] md:min-h-0 md:overflow-hidden">
      <div className="scanline" />

      <Marquee speed={40} className="bg-primary text-white border-none py-0.5 font-bold">
        <span className="flex items-center gap-2 text-[9px] uppercase tracking-tighter">AI SUPPORT SYSTEM v0.1 • STATUS: NOMINAL • UPLINK: ENCRYPTED • MODEL: LLAMA-3 • MEMORY: HONCHO</span>
      </Marquee>

      <div className="grid grid-cols-1 md:grid-cols-4 md:grid-rows-1 gap-4 md:flex-1 md:min-h-0 md:overflow-hidden">
        {/* Sidebar: Chat history + System status */}
        <div className="hidden md:flex flex-col gap-4 md:min-h-0">
          <Button
            onClick={startNewChat}
            className="w-full gap-2 text-xs h-9"
          >
            <Plus className="h-4 w-4" /> {i18n.language === 'bn' ? 'নতুন চ্যাট' : 'New Chat'}
          </Button>

          <Card className="glass-panel flex-1 min-h-0 flex flex-col">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground flex items-center gap-2">
                <MessageSquare className="h-3.5 w-3.5" /> {i18n.language === 'bn' ? 'চ্যাট হিস্টোরি' : 'Chat History'}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2 pt-0 flex-1 min-h-0 overflow-y-auto">
              {!token ? (
                <p className="text-xs text-muted-foreground px-2">
                  {i18n.language === 'bn' ? 'হিস্টোরি দেখতে লগইন করুন।' : 'Log in to keep chat history.'}
                </p>
              ) : sessions.length === 0 ? (
                <p className="text-xs text-muted-foreground px-2">
                  {i18n.language === 'bn' ? 'এখনো কোনো চ্যাট নেই।' : 'No conversations yet.'}
                </p>
              ) : (
                <div className="space-y-1">
                  {sessions.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => openSession(s.id)}
                      className={`group w-full flex items-center justify-between gap-2 px-2 py-1.5 text-left text-xs rounded-lg border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                        activeSessionId === s.id
                          ? 'border-primary/40 bg-primary/10 text-foreground'
                          : 'border-transparent hover:border-border hover:bg-secondary/60 text-muted-foreground'
                      }`}
                    >
                      <span className="truncate flex-1">{s.title || 'New chat'}</span>
                      <Trash2
                        className="h-3.5 w-3.5 shrink-0 opacity-0 group-hover:opacity-60 hover:!opacity-100 hover:text-destructive"
                        onClick={(e) => deleteSession(s.id, e)}
                      />
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="glass-panel">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground flex items-center gap-2">
                <Cpu className="h-3.5 w-3.5" /> System Status
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground uppercase tracking-wide">AI Node</span>
                <span className="text-success flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" /> Active</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground uppercase tracking-wide flex items-center gap-1"><ShieldCheck className="h-3.5 w-3.5" /> E2E</span>
                <span className="text-info">Enabled</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Chat Area */}
        <Card className="glass-strong md:col-span-3 h-[calc(100dvh-13rem)] md:h-full flex flex-col">
          <CardHeader className="border-b border-border py-3 flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-sm font-semibold tracking-tight text-foreground">
              <Terminal className="h-4 w-4 text-primary" />
              {t('support')} OS
            </CardTitle>
            <Button
              onClick={startNewChat}
              size="sm"
              variant="ghost"
              className="md:hidden h-7 px-2 text-[10px] uppercase tracking-widest gap-1 text-primary"
            >
              <Plus className="h-3 w-3" /> {i18n.language === 'bn' ? 'নতুন' : 'New'}
            </Button>
            <div className="md:hidden flex items-center gap-1">
              <Button
                onClick={() => setHistoryOpen(true)}
                size="sm"
                variant="ghost"
                className="h-8 px-2 text-xs gap-1.5 text-foreground"
              >
                <MessageSquare className="h-3.5 w-3.5" /> {i18n.language === 'bn' ? 'হিস্টোরি' : 'History'}
              </Button>
              <Button
                onClick={startNewChat}
                size="sm"
                variant="ghost"
                className="h-8 px-2 text-xs gap-1.5 text-primary"
              >
                <Plus className="h-3.5 w-3.5" /> {i18n.language === 'bn' ? 'নতুন' : 'New'}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 min-h-0 overflow-hidden p-0 bg-[linear-gradient(hsl(var(--foreground)/0.02)_1px,transparent_1px),linear-gradient(90deg,hsl(var(--foreground)/0.02)_1px,transparent_1px)] bg-[size:20px_20px]">
            <div ref={scrollRef} className="h-full overflow-y-auto p-4">
              <div className="space-y-4">
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[90%] ${m.role === 'user' ? 'text-right' : ''}`}>
                      {m.role === 'system' ? (
                        <div className="text-[10px] text-muted-foreground mb-1 opacity-50 break-words">
                          {m.content}
                        </div>
                      ) : (
                        <div className={`inline-block px-3.5 py-2 text-sm rounded-2xl border break-words whitespace-pre-wrap ${
                          m.role === 'user'
                          ? 'bg-primary text-primary-foreground border-primary rounded-br-md'
                          : 'bg-muted text-foreground border-border rounded-bl-md'
                        }`}>
                          {m.role === 'assistant' && <span className="text-primary mr-1.5">◈</span>}
                          {m.content}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="text-primary text-xs animate-pulse tracking-widest uppercase">
                      ◈ Computing response...
                    </div>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
          <CardFooter className="p-4 border-t border-border flex-col gap-2 items-stretch">
            {token && (
              <Button
                type="button"
                onClick={handleEscalate}
                disabled={escalating}
                variant={canEscalate ? 'default' : 'outline'}
                className={`w-full gap-2 text-xs h-9 ${canEscalate ? 'animate-pulse' : 'text-muted-foreground'}`}
              >
                <LifeBuoy className="h-3.5 w-3.5" />
                {escalating
                  ? (i18n.language === 'bn' ? 'টিকেট তৈরি হচ্ছে...' : 'Creating ticket...')
                  : t('escalate_to_human')}
              </Button>
            )}
            <form className="flex w-full gap-2" onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-primary font-bold">{'>'}</span>
                <Input
                  placeholder="Type a command…"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                  className="pl-7"
                />
              </div>
              <AsyncButton type="submit" size="icon" aria-label="send" loading={loading} disabled={!input.trim()}>
                <Send className="h-4 w-4" />
              </AsyncButton>
            </form>
          </CardFooter>
        </Card>
      </div>

      {/* Mobile chat history panel */}
      {historyOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-background/70 backdrop-blur-sm"
            onClick={() => setHistoryOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute left-0 top-0 h-full w-[80%] max-w-xs glass-strong border-r border-border flex flex-col shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <span className="text-xs uppercase tracking-wide flex items-center gap-2 text-foreground">
                <MessageSquare className="h-3.5 w-3.5" /> {i18n.language === 'bn' ? 'চ্যাট হিস্টোরি' : 'Chat History'}
              </span>
              <Button
                onClick={() => setHistoryOpen(false)}
                size="icon"
                variant="ghost"
                aria-label="close history"
                className="h-8 w-8 text-foreground"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="p-3 border-b border-border">
              <Button
                onClick={startNewChat}
                className="w-full gap-2 text-xs h-9"
              >
                <Plus className="h-4 w-4" /> {i18n.language === 'bn' ? 'নতুন চ্যাট' : 'New Chat'}
              </Button>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto p-2">
              {!token ? (
                <p className="text-xs text-muted-foreground px-2">
                  {i18n.language === 'bn' ? 'হিস্টোরি দেখতে লগইন করুন।' : 'Log in to keep chat history.'}
                </p>
              ) : sessions.length === 0 ? (
                <p className="text-xs text-muted-foreground px-2">
                  {i18n.language === 'bn' ? 'এখনো কোনো চ্যাট নেই।' : 'No conversations yet.'}
                </p>
              ) : (
                <div className="space-y-1">
                  {sessions.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => openSession(s.id)}
                      className={`group w-full flex items-center justify-between gap-2 px-2 py-2 text-left text-xs rounded-lg border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                        activeSessionId === s.id
                          ? 'border-primary/40 bg-primary/10 text-foreground'
                          : 'border-transparent hover:border-border hover:bg-secondary/60 text-muted-foreground'
                      }`}
                    >
                      <span className="truncate flex-1">{s.title || 'New chat'}</span>
                      <Trash2
                        className="h-3.5 w-3.5 shrink-0 opacity-60 hover:!opacity-100 hover:text-destructive"
                        onClick={(e) => deleteSession(s.id, e)}
                      />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Support;
