import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import Marquee from '../components/ui/marquee';
import { useAuth } from '../context/AuthContext';
import { Send, Terminal, Cpu, ShieldCheck, Activity } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const Support: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sessionId = useMemo(
    () => Math.random().toString(36).slice(2, 8).toUpperCase(),
    []
  );
  const trafficBars = useMemo(
    () => Array.from({ length: 10 }, () => Math.random() * 100),
    []
  );

  useEffect(() => {
    setMessages(prev => {
      if (prev.length > 0) return prev; // don't wipe an active conversation
      const welcome = i18n.language === 'bn'
        ? 'সিস্টেম অনলাইন। আমি আপনার AI সাপোর্ট অ্যাসিস্ট্যান্ট। কিভাবে সাহায্য করতে পারি?'
        : 'System Online. I am your AI Support assistant. How can I help you today?';
      return [
        { role: 'system', content: '>>> INITIALIZING MOUNO_OS v0.1...' },
        { role: 'system', content: '>>> CONNECTION ESTABLISHED VIA ENCRYPTED CHANNEL' },
        { role: 'assistant', content: welcome },
      ];
    });
  }, [i18n.language]);

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
      const res = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ question: userMessage })
      });
      let data: any = null;
      try { data = await res.json(); } catch { /* non-JSON response */ }
      if (res.ok && data?.answer) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: data?.message || data?.answer || 'ERROR: UPLINK_FAILURE' }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'CRITICAL_ERROR: NETWORK_OFFLINE' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-4 font-mono relative md:h-[calc(100dvh-12rem)] md:min-h-0 md:overflow-hidden">
      <div className="scanline" />

      <Marquee speed={40} className="bg-primary text-black border-none py-0.5 font-bold">
        <span className="flex items-center gap-2 text-[9px] uppercase tracking-tighter">AI SUPPORT SYSTEM v0.1 • STATUS: NOMINAL • UPLINK: ENCRYPTED • MODEL: LLAMA-3 • SESSION: {sessionId}</span>
      </Marquee>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 md:flex-1 md:min-h-0 md:overflow-hidden">
        {/* Technical Sidebar */}
        <div className="hidden md:flex flex-col gap-4">
          <Card className="bg-black/50 border-white/10">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-tighter flex items-center gap-2">
                <Cpu className="h-3 w-3" /> System Status
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 space-y-2">
              <div className="flex justify-between text-[10px]">
                <span className="text-muted-foreground uppercase">Kernel</span>
                <span className="text-primary">v0.1-prod</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-muted-foreground uppercase">AI Node</span>
                <span className="text-green-500 animate-pulse">● ACTIVE</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-muted-foreground uppercase">Latency</span>
                <span className="text-primary">24ms</span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-black/50 border-white/10">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-tighter flex items-center gap-2">
                <ShieldCheck className="h-3 w-3" /> Security
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="text-[10px] text-muted-foreground">
                <p>E2E Encryption: ENABLED</p>
                <p className="mt-1">All queries are processed anonymously through Mouno Engine.</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-black/50 border-white/10 flex-1">
            <CardHeader className="p-4">
              <CardTitle className="text-xs uppercase tracking-tighter flex items-center gap-2">
                <Activity className="h-3 w-3" /> Traffic
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 overflow-hidden">
              <div className="space-y-1 opacity-50">
                 {trafficBars.map((width, i) => (
                   <div key={i} className="h-1 bg-white/10 w-full" style={{ width: `${width}%` }} />
                 ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Chat Area */}
        <Card className="md:col-span-3 h-[calc(100dvh-13rem)] md:h-full flex flex-col bg-black border-white/20 shadow-[0_0_20px_rgba(255,255,255,0.05)]">
          <CardHeader className="border-b border-white/10 py-3">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.2em]">
              <Terminal className="h-4 w-4" />
              {t('support')} OS
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 min-h-0 overflow-hidden p-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:20px_20px]">
            <div ref={scrollRef} className="h-full overflow-y-auto overscroll-contain p-4">
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
          <CardFooter className="p-4 border-t border-white/10 bg-black">
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
              <Button type="submit" size="icon" disabled={loading || !input.trim()} className="bg-white text-black hover:bg-white/90">
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default Support;
