import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import Marquee from '../components/ui/marquee';
import { useAuth } from '../context/AuthContext';
import { Send, Terminal, Cpu, ShieldCheck, Plus, Trash2, MessageSquare, X, LifeBuoy } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface ChatSession {
  id: number;
  title: string;
  updated_at?: string;
}

const API = process.env.REACT_APP_API_URL || '';

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

  const authHeaders = useMemo(
    () => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }),
    [token]
  );

  // Load the list of chat sessions (logged-in users only).
  const loadSessions = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/api/ai/sessions`, { headers: authHeaders });
      if (!res.ok) return;
      const data = await res.json();
      setSessions(Array.isArray(data?.sessions) ? data.sessions : []);
    } catch {
      /* offline: keep current list */
    }
  }, [token, authHeaders]);

  // Load messages for a specific session.
  const openSession = useCallback(async (sessionId: number) => {
    setActiveSessionId(sessionId);
    setHistoryOpen(false);
    if (!token) return;
    try {
      const res = await fetch(`${API}/api/ai/sessions/${sessionId}/messages`, { headers: authHeaders });
      if (!res.ok) {
        setMessages(welcomeMessages);
        return;
      }
      const data = await res.json();
      const loaded: Message[] = Array.isArray(data?.messages)
        ? data.messages.map((m: any) => ({ role: m.role, content: m.content }))
        : [];
      setMessages(loaded.length ? [welcomeMessages[0], ...loaded] : welcomeMessages);
    } catch {
      setMessages(welcomeMessages);
    }
  }, [token, authHeaders, welcomeMessages]);

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
      await fetch(`${API}/api/ai/sessions/${sessionId}`, { method: 'DELETE', headers: authHeaders });
    } catch {
      /* ignore */
    }
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (activeSessionId === sessionId) startNewChat();
  }, [token, authHeaders, activeSessionId, startNewChat]);

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
      const res = await fetch(`${API}/api/ai/chat`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ question: userMessage, session_id: activeSessionId }),
      });
      let data: any = null;
      try { data = await res.json(); } catch { /* non-JSON response */ }
      if (res.ok && data?.answer) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
        if (data.session_id && data.session_id !== activeSessionId) {
          setActiveSessionId(data.session_id);
        }
        setCanEscalate(Boolean(data.suggest_escalation));
        // Refresh history so the new/updated session shows up.
        if (token) loadSessions();
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: data?.message || data?.answer || 'ERROR: UPLINK_FAILURE' }]);
        setCanEscalate(true);
      }
    } catch (err) {
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
      const res = await fetch(`${API}/api/support/tickets`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ session_id: activeSessionId, subject: firstUserMsg.slice(0, 120) }),
      });
      const data = await res.json();
      if (res.ok && data?.ticket?.id) {
        navigate(`/tickets?open=${data.ticket.id}`);
      } else {
        setMessages(prev => [...prev, { role: 'system', content: '>>> ESCALATION_FAILED' }]);
      }
    } catch {
      setMessages(prev => [...prev, { role: 'system', content: '>>> ESCALATION_FAILED: NETWORK_OFFLINE' }]);
    } finally {
      setEscalating(false);
    }
  }, [token, escalating, messages, authHeaders, activeSessionId, navigate]);

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
            className="w-full bg-white text-black hover:bg-white/90 uppercase text-xs tracking-widest gap-2 h-9"
          >
            <Plus className="h-4 w-4" /> {i18n.language === 'bn' ? 'নতুন চ্যাট' : 'New Chat'}
          </Button>

          <Card className="bg-black/50 border-white/10 flex-1 min-h-0 flex flex-col">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-tighter flex items-center gap-2">
                <MessageSquare className="h-3 w-3" /> {i18n.language === 'bn' ? 'চ্যাট হিস্টোরি' : 'Chat History'}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2 pt-0 flex-1 min-h-0 overflow-y-auto">
              {!token ? (
                <p className="text-[10px] text-muted-foreground px-2">
                  {i18n.language === 'bn' ? 'হিস্টোরি দেখতে লগইন করুন।' : 'Log in to keep chat history.'}
                </p>
              ) : sessions.length === 0 ? (
                <p className="text-[10px] text-muted-foreground px-2">
                  {i18n.language === 'bn' ? 'এখনো কোনো চ্যাট নেই।' : 'No conversations yet.'}
                </p>
              ) : (
                <div className="space-y-1">
                  {sessions.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => openSession(s.id)}
                      className={`group w-full flex items-center justify-between gap-2 px-2 py-1.5 text-left text-[11px] border transition-colors ${
                        activeSessionId === s.id
                          ? 'border-white/40 bg-white/10 text-white'
                          : 'border-transparent hover:border-white/20 hover:bg-white/5 text-muted-foreground'
                      }`}
                    >
                      <span className="truncate flex-1">{s.title || 'New chat'}</span>
                      <Trash2
                        className="h-3 w-3 shrink-0 opacity-0 group-hover:opacity-60 hover:!opacity-100 hover:text-red-400"
                        onClick={(e) => deleteSession(s.id, e)}
                      />
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-black/50 border-white/10">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-tighter flex items-center gap-2">
                <Cpu className="h-3 w-3" /> System Status
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 space-y-2">
              <div className="flex justify-between text-[10px]">
                <span className="text-muted-foreground uppercase">AI Node</span>
                <span className="text-green-500 animate-pulse">● ACTIVE</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-muted-foreground uppercase flex items-center gap-1"><ShieldCheck className="h-3 w-3" /> E2E</span>
                <span className="text-primary">ENABLED</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Chat Area */}
        <Card className="md:col-span-3 h-[calc(100dvh-13rem)] md:h-full flex flex-col bg-black border-white/20 shadow-[0_0_20px_rgba(255,255,255,0.05)]">
          <CardHeader className="border-b border-white/10 py-3 flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.2em]">
              <Terminal className="h-4 w-4" />
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
                className="h-7 px-2 text-[10px] uppercase tracking-widest gap-1 text-white"
              >
                <MessageSquare className="h-3 w-3" /> {i18n.language === 'bn' ? 'হিস্টোরি' : 'History'}
              </Button>
              <Button
                onClick={startNewChat}
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-[10px] uppercase tracking-widest gap-1 text-primary"
              >
                <Plus className="h-3 w-3" /> {i18n.language === 'bn' ? 'নতুন' : 'New'}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 min-h-0 overflow-hidden p-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:20px_20px]">
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
                        <div className={`inline-block px-3 py-2 text-sm border break-words whitespace-pre-wrap ${
                          m.role === 'user'
                          ? 'bg-white text-black border-white'
                          : 'bg-black text-white border-white/20'
                        }`}>
                          {m.role === 'assistant' && <span className="text-primary mr-2">◈</span>}
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
          <CardFooter className="p-4 border-t border-white/10 bg-black flex-col gap-2 items-stretch">
            {token && (
              <Button
                type="button"
                onClick={handleEscalate}
                disabled={escalating}
                variant={canEscalate ? 'default' : 'ghost'}
                className={`w-full gap-2 uppercase text-[10px] tracking-widest h-8 ${
                  canEscalate
                    ? 'bg-primary text-white hover:bg-primary/90 animate-pulse'
                    : 'text-muted-foreground border border-white/10 hover:text-white'
                }`}
              >
                <LifeBuoy className="h-3 w-3" />
                {escalating
                  ? (i18n.language === 'bn' ? 'টিকেট তৈরি হচ্ছে...' : 'Creating ticket...')
                  : t('escalate_to_human')}
              </Button>
            )}
            <form className="flex w-full gap-2" onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-primary font-bold">{'>'}</span>
                <Input
                  placeholder="COMMAND_INPUT..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                  className="pl-7 bg-transparent border-white/20 focus:border-white focus:ring-0 uppercase placeholder:opacity-30"
                />
              </div>
              <Button type="submit" size="icon" aria-label="send" disabled={loading || !input.trim()} className="bg-white text-black hover:bg-white/90">
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </CardFooter>
        </Card>
      </div>

      {/* Mobile chat history panel */}
      {historyOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/70"
            onClick={() => setHistoryOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute left-0 top-0 h-full w-[80%] max-w-xs bg-black border-r border-white/20 flex flex-col shadow-[0_0_30px_rgba(0,0,0,0.8)]">
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <span className="text-xs uppercase tracking-tighter flex items-center gap-2 text-white">
                <MessageSquare className="h-3 w-3" /> {i18n.language === 'bn' ? 'চ্যাট হিস্টোরি' : 'Chat History'}
              </span>
              <Button
                onClick={() => setHistoryOpen(false)}
                size="icon"
                variant="ghost"
                aria-label="close history"
                className="h-7 w-7 text-white"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="p-3 border-b border-white/10">
              <Button
                onClick={startNewChat}
                className="w-full bg-white text-black hover:bg-white/90 uppercase text-xs tracking-widest gap-2 h-9"
              >
                <Plus className="h-4 w-4" /> {i18n.language === 'bn' ? 'নতুন চ্যাট' : 'New Chat'}
              </Button>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto p-2">
              {!token ? (
                <p className="text-[10px] text-muted-foreground px-2">
                  {i18n.language === 'bn' ? 'হিস্টোরি দেখতে লগইন করুন।' : 'Log in to keep chat history.'}
                </p>
              ) : sessions.length === 0 ? (
                <p className="text-[10px] text-muted-foreground px-2">
                  {i18n.language === 'bn' ? 'এখনো কোনো চ্যাট নেই।' : 'No conversations yet.'}
                </p>
              ) : (
                <div className="space-y-1">
                  {sessions.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => openSession(s.id)}
                      className={`group w-full flex items-center justify-between gap-2 px-2 py-2 text-left text-[11px] border transition-colors ${
                        activeSessionId === s.id
                          ? 'border-white/40 bg-white/10 text-white'
                          : 'border-transparent hover:border-white/20 hover:bg-white/5 text-muted-foreground'
                      }`}
                    >
                      <span className="truncate flex-1">{s.title || 'New chat'}</span>
                      <Trash2
                        className="h-3 w-3 shrink-0 opacity-60 hover:!opacity-100 hover:text-red-400"
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
