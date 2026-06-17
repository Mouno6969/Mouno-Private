import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Sparkles, Target, CalendarClock, ShieldCheck, Lock, Plus, Trash2, Pause, Play,
  RefreshCw, AlertCircle, CheckCircle2, Clock,
} from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { AsyncButton } from '../components/ui/async-button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { NetworkLogo } from '../constants/networks';
import { useAuth } from '../context/AuthContext';
import { apiClient, getErrorMessage } from '../lib/apiClient';

// Shared chain catalogue — same set the Swap page exposes.
const CHAINS = [
  { id: '1', name: 'Ethereum', symbol: 'ETH', networkId: 'ethereum', native: '0x0000000000000000000000000000000000000000', stable: '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48' },
  { id: '56', name: 'BSC', symbol: 'BNB', networkId: 'bsc', native: '0x0000000000000000000000000000000000000000', stable: '0x55d398326f99059ff775485246999027b3197955' },
  { id: '137', name: 'Polygon', symbol: 'POL', networkId: 'polygon', native: '0x0000000000000000000000000000000000000000', stable: '0x2791bca1f2de4661ed88a30c99a7a9449aa84174' },
  { id: '8453', name: 'Base', symbol: 'ETH', networkId: 'base', native: '0x0000000000000000000000000000000000000000', stable: '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913' },
  { id: '43114', name: 'Avalanche', symbol: 'AVAX', networkId: 'avalanche', native: '0x0000000000000000000000000000000000000000', stable: '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e' },
  { id: '1151111081099710', name: 'Solana', symbol: 'SOL', networkId: 'solana', native: '11111111111111111111111111111111', stable: 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' },
];

const chainById = (id: string) => CHAINS.find((c) => c.id === id) || CHAINS[0];

export interface SwapIntent {
  from_chain_id: string;
  from_chain_name: string;
  from_token: string;
  to_chain_id: string;
  to_chain_name: string;
  to_token: string;
  amount: string;
  preference: string;
}

// ───────────────────────────────────────────────────────────────────────────
// Shared intent form (chain / token / amount) reused by both tabs.
// ───────────────────────────────────────────────────────────────────────────
interface IntentFormProps {
  intent: SwapIntent;
  onChange: (next: SwapIntent) => void;
}

const IntentForm: React.FC<IntentFormProps> = ({ intent, onChange }) => {
  const setFromChain = (id: string) => {
    const c = chainById(id);
    onChange({ ...intent, from_chain_id: id, from_chain_name: c.name, from_token: c.native });
  };
  const setToChain = (id: string) => {
    const c = chainById(id);
    onChange({ ...intent, to_chain_id: id, to_chain_name: c.name, to_token: c.stable });
  };

  return (
    <div className="space-y-4">
      {/* You Pay */}
      <div className="rounded-2xl bg-muted/40 p-5 border border-muted transition-all focus-within:border-primary/30">
        <span className="text-xs font-bold uppercase text-muted-foreground tracking-tighter">You Pay</span>
        <div className="flex items-center gap-4 mt-2">
          <Input
            type="number"
            placeholder="0.0"
            className="border-none bg-transparent text-3xl font-black p-0 h-auto focus-visible:ring-0 placeholder:text-muted-foreground/30"
            value={intent.amount}
            onChange={(e) => onChange({ ...intent, amount: e.target.value })}
          />
          <Select value={intent.from_chain_id} onValueChange={setFromChain}>
            <SelectTrigger className="w-[150px] h-12 rounded-xl bg-card border-muted font-bold">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CHAINS.map((chain) => (
                <SelectItem key={chain.id} value={chain.id}>
                  <NetworkLogo id={chain.networkId} size={16} className="mr-2" /> {chain.symbol}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Input
          className="mt-3 h-9 text-xs font-mono bg-card/60 border-muted"
          placeholder="From token address (or 'native')"
          value={intent.from_token}
          onChange={(e) => onChange({ ...intent, from_token: e.target.value })}
        />
      </div>

      {/* You Receive */}
      <div className="rounded-2xl bg-muted/40 p-5 border border-muted">
        <span className="text-xs font-bold uppercase text-muted-foreground tracking-tighter">You Receive</span>
        <div className="flex items-center justify-end gap-4 mt-2">
          <Select value={intent.to_chain_id} onValueChange={setToChain}>
            <SelectTrigger className="w-[150px] h-12 rounded-xl bg-card border-muted font-bold">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CHAINS.map((chain) => (
                <SelectItem key={chain.id} value={chain.id}>
                  <NetworkLogo id={chain.networkId} size={16} className="mr-2" /> {chain.symbol}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Input
          className="mt-3 h-9 text-xs font-mono bg-card/60 border-muted"
          placeholder="To token address"
          value={intent.to_token}
          onChange={(e) => onChange({ ...intent, to_token: e.target.value })}
        />
      </div>

      {/* Routing preference */}
      <div className="flex items-center gap-2">
        <span className="text-[11px] font-bold uppercase text-muted-foreground tracking-widest">Route</span>
        <Select value={intent.preference} onValueChange={(v) => onChange({ ...intent, preference: v })}>
          <SelectTrigger className="h-9 w-32 rounded-xl bg-card border-muted text-xs font-bold">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="cheapest">Cheapest</SelectItem>
            <SelectItem value="fastest">Fastest</SelectItem>
          </SelectContent>
        </Select>
        <Badge variant="outline" className="ml-auto h-5 px-2 text-[9px] bg-primary/5 border-primary/20 text-primary">
          MULTI-HOP ROUTING
        </Badge>
      </div>
    </div>
  );
};

const defaultIntent = (): SwapIntent => {
  const from = chainById('1');
  const to = chainById('137');
  return {
    from_chain_id: from.id, from_chain_name: from.name, from_token: from.native,
    to_chain_id: to.id, to_chain_name: to.name, to_token: to.stable,
    amount: '', preference: 'cheapest',
  };
};

// ───────────────────────────────────────────────────────────────────────────
type Tab = 'limit' | 'scheduled' | 'setup';

interface LimitOrder {
  order_id: string;
  status: string;
  amount: string;
  to_chain_id: string;
  direction: string;
  target_price: string;
  last_price?: string;
}

interface Schedule {
  schedule_id: string;
  status: string;
  amount: string;
  to_chain_id: string;
  interval_key?: string;
  next_run?: string;
  runs_count?: number;
}

const Automation: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();

  const [tab, setTab] = useState<Tab>('limit');
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [limitOrders, setLimitOrders] = useState<LimitOrder[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  // tracks the id of a row whose action is currently in-flight, for per-row spinners
  const [pendingRow, setPendingRow] = useState<string | null>(null);

  // ── setup password ──
  const [pw, setPw] = useState('');
  const [savingPw, setSavingPw] = useState(false);

  // ── limit form ──
  const [limitIntent, setLimitIntent] = useState<SwapIntent>(defaultIntent());
  const [direction, setDirection] = useState('below');
  const [targetPrice, setTargetPrice] = useState('');
  const [creatingLimit, setCreatingLimit] = useState(false);

  // ── scheduled form ──
  const [schedIntent, setSchedIntent] = useState<SwapIntent>(defaultIntent());
  const [interval, setIntervalKey] = useState('weekly');
  const [creatingSched, setCreatingSched] = useState(false);

  const loadStatus = useCallback(async () => {
    try {
      const res = await apiClient.get<{ configured: boolean }>('/api/automation/setup-password', { silent: true });
      setConfigured(!!res.data.configured);
    } catch {
      setConfigured(false);
    }
  }, []);

  const loadLimitOrders = useCallback(async () => {
    try {
      const res = await apiClient.get<{ orders: LimitOrder[] }>('/api/automation/limit-orders', { silent: true });
      setLimitOrders(res.data.orders || []);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const loadSchedules = useCallback(async () => {
    try {
      const res = await apiClient.get<{ schedules: Schedule[] }>('/api/automation/scheduled-buys', { silent: true });
      setSchedules(res.data.schedules || []);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    if (!token) return;
    loadStatus();
    loadLimitOrders();
    loadSchedules();
  }, [token, loadStatus, loadLimitOrders, loadSchedules]);

  const savePassword = async () => {
    if (!pw) return;
    setSavingPw(true);
    try {
      await apiClient.post('/api/automation/setup-password', { password: pw }, { silent: true });
      toast.success('Auto-sign enabled');
      setPw('');
      setConfigured(true);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not enable auto-sign'));
    } finally {
      setSavingPw(false);
    }
  };

  const createLimit = async () => {
    setCreatingLimit(true);
    try {
      await apiClient.post('/api/automation/limit-orders', {
        ...limitIntent, direction, target_price: targetPrice,
      }, { silent: true });
      toast.success('Limit order created');
      setTargetPrice('');
      setLimitIntent(defaultIntent());
      loadLimitOrders();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not create limit order'));
    } finally {
      setCreatingLimit(false);
    }
  };

  const cancelLimit = async (orderId: string) => {
    setPendingRow(`${orderId}:cancel`);
    try {
      await apiClient.delete(`/api/automation/limit-orders/${orderId}`, { silent: true });
      toast.success('Limit order cancelled');
      loadLimitOrders();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not cancel'));
    } finally {
      setPendingRow(null);
    }
  };

  const updateLimitPrice = async (orderId: string) => {
    const next = window.prompt('New target price (USD):');
    if (!next) return;
    setPendingRow(`${orderId}:edit`);
    try {
      await apiClient.patch(`/api/automation/limit-orders/${orderId}`, { target_price: next }, { silent: true });
      toast.success('Target price updated');
      loadLimitOrders();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not update'));
    } finally {
      setPendingRow(null);
    }
  };

  const createSched = async () => {
    setCreatingSched(true);
    try {
      await apiClient.post('/api/automation/scheduled-buys', {
        ...schedIntent, interval_key: interval,
      }, { silent: true });
      toast.success('Auto-buy created');
      setSchedIntent(defaultIntent());
      loadSchedules();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not create auto-buy'));
    } finally {
      setCreatingSched(false);
    }
  };

  const toggleSched = async (schedule: Schedule) => {
    const next = schedule.status === 'paused' ? 'active' : 'paused';
    setPendingRow(`${schedule.schedule_id}:toggle`);
    try {
      await apiClient.patch(`/api/automation/scheduled-buys/${schedule.schedule_id}`, { status: next }, { silent: true });
      toast.success(next === 'active' ? 'Resumed' : 'Paused');
      loadSchedules();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not update'));
    } finally {
      setPendingRow(null);
    }
  };

  const cancelSched = async (scheduleId: string) => {
    setPendingRow(`${scheduleId}:cancel`);
    try {
      await apiClient.delete(`/api/automation/scheduled-buys/${scheduleId}`, { silent: true });
      toast.success('Auto-buy cancelled');
      loadSchedules();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not cancel'));
    } finally {
      setPendingRow(null);
    }
  };

  if (!token) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <Sparkles className="h-10 w-10 text-primary mx-auto mb-4" />
        <h1 className="text-2xl font-bold">{t('smart_trading')}</h1>
        <p className="text-muted-foreground mt-2">Please sign in to manage your automations.</p>
      </div>
    );
  }

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      active: 'bg-green-500/10 text-green-500 border-green-500/20',
      filled: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
      triggered: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
      paused: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
      failed: 'bg-destructive/10 text-destructive border-destructive/20',
      cancelled: 'bg-muted text-muted-foreground border-muted',
    };
    return (
      <Badge variant="outline" className={`text-[9px] uppercase font-bold ${map[status] || ''}`}>
        {status}
      </Badge>
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <section className="space-y-1 text-center md:text-left">
        <div className="flex items-center justify-center md:justify-start gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Sparkles className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">{t('smart_trading')}</h1>
        </div>
        <p className="text-muted-foreground">{t('smart_trading_desc')}</p>
      </section>

      {/* Auto-sign reminder */}
      {configured === false && (
        <Alert className="bg-amber-500/5 border-amber-500/20">
          <AlertCircle className="h-4 w-4 text-amber-500" />
          <AlertDescription className="text-xs text-muted-foreground">
            Auto-sign is not set up yet. Configure it in the <button className="font-bold text-primary underline" onClick={() => setTab('setup')}>Auto-Sign Setup</button> tab before creating automations.
          </AlertDescription>
        </Alert>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none">
        {([
          { key: 'limit', label: t('limit_orders'), icon: <Target className="h-4 w-4" /> },
          { key: 'scheduled', label: t('scheduled_buys'), icon: <CalendarClock className="h-4 w-4" /> },
          { key: 'setup', label: t('auto_sign_setup'), icon: <Lock className="h-4 w-4" /> },
        ] as { key: Tab; label: string; icon: React.ReactNode }[]).map((it) => (
          <Button
            key={it.key}
            variant={tab === it.key ? 'default' : 'outline'}
            size="sm"
            className="rounded-full gap-2 shrink-0"
            onClick={() => setTab(it.key)}
          >
            {it.icon}
            {it.label}
          </Button>
        ))}
      </div>

      {/* ── Limit Orders ── */}
      {tab === 'limit' && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
          <div className="lg:col-span-3">
            <Card className="shadow-2xl border-primary/10">
              <CardHeader>
                <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                  <Target className="h-4 w-4 text-primary" /> {t('create_limit_order')}
                </CardTitle>
                <CardDescription>Auto buy/sell when the target token hits your USD price.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <IntentForm intent={limitIntent} onChange={setLimitIntent} />
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-[11px] font-bold uppercase text-muted-foreground tracking-widest">Trigger</span>
                    <Select value={direction} onValueChange={setDirection}>
                      <SelectTrigger className="mt-1 h-11 rounded-xl bg-card border-muted font-bold">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="below">Price ≤ target</SelectItem>
                        <SelectItem value="above">Price ≥ target</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <span className="text-[11px] font-bold uppercase text-muted-foreground tracking-widest">Target ($)</span>
                    <Input
                      type="number"
                      placeholder="0.00"
                      className="mt-1 h-11 rounded-xl bg-card border-muted font-bold"
                      value={targetPrice}
                      onChange={(e) => setTargetPrice(e.target.value)}
                    />
                  </div>
                </div>
                <AsyncButton
                  className="w-full h-12 rounded-2xl font-black"
                  loading={creatingLimit}
                  loadingText={t('create_limit_order')}
                  disabled={!configured || !limitIntent.amount || !targetPrice}
                  onClick={createLimit}
                >
                  <Plus className="h-5 w-5 mr-2" /> {t('create_limit_order')}
                </AsyncButton>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-2">
            <Card className="border-primary/10">
              <CardHeader>
                <CardTitle className="text-sm font-bold flex items-center justify-between">
                  <span>{t('your_limit_orders')}</span>
                  <Button variant="ghost" size="icon" aria-label="Refresh limit orders" className="h-7 w-7" onClick={loadLimitOrders}>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {limitOrders.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-6">No limit orders yet.</p>
                )}
                {limitOrders.map((o) => (
                  <div key={o.order_id} className="rounded-xl border border-muted p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold">{o.order_id}</span>
                      {statusBadge(o.status)}
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                      {o.amount} → {chainById(o.to_chain_id).symbol} when price {o.direction === 'below' ? '≤' : '≥'} ${o.target_price}
                    </p>
                    {o.last_price && (
                      <p className="text-[10px] text-muted-foreground">Last seen: ${o.last_price}</p>
                    )}
                    {o.status === 'active' && (
                      <div className="flex gap-2">
                        <AsyncButton
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px] flex-1"
                          loading={pendingRow === `${o.order_id}:edit`}
                          onClick={() => updateLimitPrice(o.order_id)}
                        >
                          Edit Price
                        </AsyncButton>
                        <AsyncButton
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px] flex-1 text-destructive"
                          loading={pendingRow === `${o.order_id}:cancel`}
                          onClick={() => cancelLimit(o.order_id)}
                        >
                          <Trash2 className="h-3 w-3 mr-1" /> Cancel
                        </AsyncButton>
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* ── Scheduled Buys ── */}
      {tab === 'scheduled' && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
          <div className="lg:col-span-3">
            <Card className="shadow-2xl border-primary/10">
              <CardHeader>
                <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                  <CalendarClock className="h-4 w-4 text-primary" /> {t('create_scheduled_buy')}
                </CardTitle>
                <CardDescription>Recurring auto-buy on a fixed interval.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <IntentForm intent={schedIntent} onChange={setSchedIntent} />
                <div>
                  <span className="text-[11px] font-bold uppercase text-muted-foreground tracking-widest">Frequency</span>
                  <Select value={interval} onValueChange={setIntervalKey}>
                    <SelectTrigger className="mt-1 h-11 rounded-xl bg-card border-muted font-bold">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="weekly">Weekly</SelectItem>
                      <SelectItem value="monthly">Monthly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <AsyncButton
                  className="w-full h-12 rounded-2xl font-black"
                  loading={creatingSched}
                  loadingText={t('create_scheduled_buy')}
                  disabled={!configured || !schedIntent.amount}
                  onClick={createSched}
                >
                  <Plus className="h-5 w-5 mr-2" /> {t('create_scheduled_buy')}
                </AsyncButton>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-2">
            <Card className="border-primary/10">
              <CardHeader>
                <CardTitle className="text-sm font-bold flex items-center justify-between">
                  <span>{t('your_scheduled_buys')}</span>
                  <Button variant="ghost" size="icon" aria-label="Refresh scheduled buys" className="h-7 w-7" onClick={loadSchedules}>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {schedules.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-6">No scheduled buys yet.</p>
                )}
                {schedules.map((s) => (
                  <div key={s.schedule_id} className="rounded-xl border border-muted p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold">{s.schedule_id}</span>
                      {statusBadge(s.status)}
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                      {s.amount} → {chainById(s.to_chain_id).symbol} · {s.interval_key}
                    </p>
                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> Next: {s.next_run ? new Date(s.next_run).toLocaleString() : '—'}</span>
                      <span className="flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> Runs: {s.runs_count}</span>
                    </div>
                    {s.status !== 'cancelled' && (
                      <div className="flex gap-2">
                        <AsyncButton
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px] flex-1"
                          loading={pendingRow === `${s.schedule_id}:toggle`}
                          onClick={() => toggleSched(s)}
                        >
                          {s.status === 'paused' ? <><Play className="h-3 w-3 mr-1" /> Resume</> : <><Pause className="h-3 w-3 mr-1" /> Pause</>}
                        </AsyncButton>
                        <AsyncButton
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px] flex-1 text-destructive"
                          loading={pendingRow === `${s.schedule_id}:cancel`}
                          onClick={() => cancelSched(s.schedule_id)}
                        >
                          <Trash2 className="h-3 w-3 mr-1" /> Cancel
                        </AsyncButton>
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* ── Auto-Sign Setup ── */}
      {tab === 'setup' && (
        <div className="max-w-xl mx-auto">
          <Card className="shadow-2xl border-primary/10">
            <CardHeader>
              <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <Lock className="h-4 w-4 text-primary" /> {t('auto_sign_setup')}
              </CardTitle>
              <CardDescription>
                Enter your personal wallet password once. It is encrypted with the server master key and used only to auto-sign your triggered automations.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {configured && (
                <Alert className="bg-green-500/5 border-green-500/20">
                  <ShieldCheck className="h-4 w-4 text-green-500" />
                  <AlertDescription className="text-xs text-muted-foreground">
                    Auto-sign is currently <span className="font-bold text-green-500">enabled</span>. Re-enter your password below to update it.
                  </AlertDescription>
                </Alert>
              )}
              <div>
                <span className="text-[11px] font-bold uppercase text-muted-foreground tracking-widest">Wallet Password</span>
                <Input
                  type="password"
                  placeholder="••••••••"
                  className="mt-1 h-12 rounded-xl bg-card border-muted"
                  value={pw}
                  onChange={(e) => setPw(e.target.value)}
                />
              </div>
              <AsyncButton
                className="w-full h-12 rounded-2xl font-black"
                loading={savingPw}
                loadingText={configured ? 'Update Auto-Sign' : 'Enable Auto-Sign'}
                disabled={!pw}
                onClick={savePassword}
              >
                <ShieldCheck className="h-5 w-5 mr-2" /> {configured ? 'Update Auto-Sign' : 'Enable Auto-Sign'}
              </AsyncButton>
              <div className="p-4 rounded-xl bg-muted/30 border border-muted flex items-start gap-3">
                <ShieldCheck className="h-5 w-5 text-green-500 shrink-0" />
                <p className="text-[10px] text-muted-foreground leading-tight">
                  Your password is never stored in plaintext and never returned by the API. Cancel any automation any time to wipe its stored credentials.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Automation;
