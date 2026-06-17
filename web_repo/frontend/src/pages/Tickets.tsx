import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { LifeBuoy, Send, ArrowLeft, CheckCircle2, RefreshCw } from 'lucide-react';
import { apiClient } from '../lib/apiClient';

type TicketStatus = 'open' | 'pending' | 'resolved' | 'closed';

interface Ticket {
  id: number;
  subject: string;
  status: TicketStatus;
  priority: string;
  created_at?: string;
  updated_at?: string;
}

interface TicketMessage {
  sender_role: 'user' | 'agent' | 'system';
  body: string;
  created_at?: string;
}

interface TicketDetail extends Ticket {
  messages: TicketMessage[];
}

const statusVariant: Record<TicketStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  open: 'default',
  pending: 'secondary',
  resolved: 'outline',
  closed: 'destructive',
};

const Tickets: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [active, setActive] = useState<TicketDetail | null>(null);
  const [reply, setReply] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const bn = i18n.language === 'bn';

  const statusLabel = useCallback((status: TicketStatus) => {
    const map: Record<TicketStatus, [string, string]> = {
      open: ['Open', 'খোলা'],
      pending: ['Pending', 'অপেক্ষমাণ'],
      resolved: ['Resolved', 'সমাধান হয়েছে'],
      closed: ['Closed', 'বন্ধ'],
    };
    return bn ? map[status][1] : map[status][0];
  }, [bn]);

  const loadTickets = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await apiClient.get<{ tickets: Ticket[] }>('/api/support/tickets', { silent: true });
      setTickets(Array.isArray(res.data?.tickets) ? res.data.tickets : []);
    } catch {
      /* offline */
    } finally {
      setLoading(false);
    }
  }, [token]);

  const openTicket = useCallback(async (id: number) => {
    if (!token) return;
    try {
      const res = await apiClient.get<{ ticket: TicketDetail }>(`/api/support/tickets/${id}`, { silent: true });
      if (res.data?.ticket) setActive(res.data.ticket);
    } catch {
      /* offline */
    }
  }, [token]);

  // Initial list load.
  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  // Deep-link: ?open=<id> opens that ticket (e.g. right after escalation).
  useEffect(() => {
    const openId = searchParams.get('open');
    if (openId) {
      openTicket(Number(openId));
    }
  }, [searchParams, openTicket]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [active]);

  const backToList = useCallback(() => {
    setActive(null);
    searchParams.delete('open');
    setSearchParams(searchParams, { replace: true });
    loadTickets();
  }, [searchParams, setSearchParams, loadTickets]);

  const sendReply = useCallback(async () => {
    if (!active || !reply.trim() || sending) return;
    setSending(true);
    try {
      const res = await apiClient.post<{ ticket: TicketDetail }>(
        `/api/support/tickets/${active.id}/messages`,
        { body: reply.trim() },
        { silent: true }
      );
      if (res.data?.ticket) setActive(res.data.ticket);
      setReply('');
    } catch {
      /* offline */
    } finally {
      setSending(false);
    }
  }, [active, reply, sending]);

  const markStatus = useCallback(async (status: TicketStatus) => {
    if (!active) return;
    try {
      const res = await apiClient.patch<{ ticket: TicketDetail }>(
        `/api/support/tickets/${active.id}`,
        { status },
        { silent: true }
      );
      if (res.data?.ticket) setActive(prev => (prev ? { ...prev, status: res.data.ticket.status } : prev));
    } catch {
      /* offline */
    }
  }, [active]);

  if (!token) {
    return (
      <div className="max-w-2xl mx-auto font-mono">
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground text-sm">
            {bn ? 'টিকেট দেখতে লগইন করুন।' : 'Log in to view your support tickets.'}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto font-mono">
      <div className="flex items-center justify-between mb-4">
        <h1 className="flex items-center gap-2 text-sm uppercase tracking-[0.2em]">
          <LifeBuoy className="h-4 w-4" /> {t('my_tickets')}
        </h1>
        {!active && (
          <Button onClick={loadTickets} size="sm" variant="ghost" className="h-8 gap-1 text-[10px] uppercase tracking-widest text-muted-foreground hover:text-white">
            <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} /> {bn ? 'রিফ্রেশ' : 'Refresh'}
          </Button>
        )}
      </div>

      {!active ? (
        <Card>
          <CardHeader className="border-b border-border py-3">
            <CardTitle className="text-xs uppercase tracking-tighter">{t('ticket_list')}</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {tickets.length === 0 ? (
              <p className="text-[11px] text-muted-foreground p-6 text-center">
                {bn ? 'এখনো কোনো টিকেট নেই। সাপোর্ট চ্যাট থেকে এজেন্টের কাছে এসকেলেট করুন।' : 'No tickets yet. Escalate from the support chat to reach a human agent.'}
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {tickets.map((ticket) => (
                  <li key={ticket.id}>
                    <button
                      onClick={() => openTicket(ticket.id)}
                      className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left hover:bg-muted/50 transition-colors"
                    >
                      <div className="min-w-0">
                        <p className="text-sm text-foreground truncate">#{ticket.id} · {ticket.subject}</p>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-widest mt-0.5">
                          {ticket.updated_at || ticket.created_at}
                        </p>
                      </div>
                      <Badge variant={statusVariant[ticket.status]} className="shrink-0 uppercase text-[9px] tracking-widest">
                        {statusLabel(ticket.status)}
                      </Badge>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card className="flex flex-col h-[calc(100dvh-14rem)]">
          <CardHeader className="border-b border-border py-3 flex-row items-center justify-between gap-2">
            <Button onClick={backToList} size="sm" variant="ghost" className="h-7 px-2 text-[10px] uppercase tracking-widest gap-1">
              <ArrowLeft className="h-3 w-3" /> {bn ? 'ফিরে যান' : 'Back'}
            </Button>
            <CardTitle className="text-xs uppercase tracking-tighter truncate flex-1 text-center">
              #{active.id} · {active.subject}
            </CardTitle>
            <Badge variant={statusVariant[active.status]} className="shrink-0 uppercase text-[9px] tracking-widest">
              {statusLabel(active.status)}
            </Badge>
          </CardHeader>

          <CardContent className="flex-1 min-h-0 overflow-hidden p-0">
            <div ref={scrollRef} className="h-full overflow-y-auto p-4 space-y-3">
              {active.messages?.map((m, i) => (
                <div key={i} className={`flex ${m.sender_role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[90%] inline-block px-3 py-2 text-sm border break-words whitespace-pre-wrap ${
                    m.sender_role === 'user'
                      ? 'bg-primary text-primary-foreground border-primary'
                      : m.sender_role === 'agent'
                        ? 'bg-primary/10 text-foreground border-primary/40'
                        : 'bg-muted text-muted-foreground border-border text-[11px]'
                  }`}>
                    {m.sender_role === 'agent' && <span className="text-primary mr-2">◈</span>}
                    {m.body}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>

          <CardFooter className="p-4 border-t border-border flex-col gap-2 items-stretch">
            {(active.status === 'open' || active.status === 'pending') && (
              <Button
                onClick={() => markStatus('resolved')}
                variant="ghost"
                className="w-full gap-2 uppercase text-[10px] tracking-widest h-8"
              >
                <CheckCircle2 className="h-3 w-3" /> {t('mark_resolved')}
              </Button>
            )}
            <form className="flex w-full gap-2" onSubmit={(e) => { e.preventDefault(); sendReply(); }}>
              <Input
                placeholder={bn ? 'আপনার উত্তর লিখুন...' : 'Type your reply...'}
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                disabled={sending}
              />
              <Button type="submit" size="icon" aria-label="send reply" disabled={sending || !reply.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </CardFooter>
        </Card>
      )}
    </div>
  );
};

export default Tickets;
