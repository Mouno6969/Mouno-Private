import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Send,
  ShieldCheck,
  Loader2,
  RefreshCw,
  Trash2,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Search,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { PageHeader, StatusBadge, EmptyState } from '../components/common';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import { toast } from 'sonner';

interface ForwardStatus {
  available: boolean;
  connected: boolean;
  display_name: string | null;
  limits: { max_targets: number; min_interval_minutes: number };
}

interface Dialog {
  id: string;
  title: string;
  username: string | null;
  type: 'group' | 'channel';
}

interface Schedule {
  schedule_id: string;
  targets: string[];
  message: string;
  interval_minutes: number;
  status: string;
  last_run: string | null;
  last_result: string | null;
  created_at: string;
}

type Step = 'phone' | 'code' | 'password';

const ForwardTelegram: React.FC = () => {
  const { t } = useTranslation();

  const [status, setStatus] = useState<ForwardStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);

  // Connect flow
  const [step, setStep] = useState<Step>('phone');
  const [apiId, setApiId] = useState('');
  const [apiHash, setApiHash] = useState('');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [connecting, setConnecting] = useState(false);

  // Composer
  const [dialogs, setDialogs] = useState<Dialog[]>([]);
  const [loadingDialogs, setLoadingDialogs] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [manualTargets, setManualTargets] = useState('');
  const [dialogQuery, setDialogQuery] = useState('');
  const [message, setMessage] = useState('');
  const [intervalMin, setIntervalMin] = useState('');
  const [sending, setSending] = useState(false);

  const [schedules, setSchedules] = useState<Schedule[]>([]);

  const loadStatus = async () => {
    try {
      const res = await apiClient.get<ForwardStatus>('/api/forward/status', { silent: true });
      setStatus(res.data);
      return res.data;
    } catch (err) {
      toast.error(getErrorMessage(err));
      return null;
    } finally {
      setLoadingStatus(false);
    }
  };

  const loadSchedules = async () => {
    try {
      const res = await apiClient.get<{ schedules: Schedule[] }>('/api/forward/schedules', { silent: true });
      setSchedules(res.data.schedules || []);
    } catch {
      /* non-fatal */
    }
  };

  const loadDialogs = async () => {
    setLoadingDialogs(true);
    try {
      const res = await apiClient.get<{ dialogs: Dialog[] }>('/api/forward/dialogs');
      setDialogs(res.data.dialogs || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not load your groups/channels'));
    } finally {
      setLoadingDialogs(false);
    }
  };

  useEffect(() => {
    loadStatus().then((s) => {
      if (s?.connected) {
        loadDialogs();
        loadSchedules();
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Connect flow ───────────────────────────────────────────────────────────
  const sendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnecting(true);
    try {
      await apiClient.post('/api/forward/send-code', { api_id: apiId, api_hash: apiHash, phone }, { silent: true });
      setStep('code');
      toast.success('Login code sent to your Telegram app.');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setConnecting(false);
    }
  };

  const verifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnecting(true);
    try {
      const res = await apiClient.post<{ status: string }>('/api/forward/verify-code', { code }, { silent: true });
      if (res.data.status === 'password_needed') {
        setStep('password');
        toast.message('Two-step verification is on — enter your Telegram password.');
      } else {
        await onConnected();
      }
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setConnecting(false);
    }
  };

  const verifyPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnecting(true);
    try {
      await apiClient.post('/api/forward/verify-password', { password }, { silent: true });
      await onConnected();
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setConnecting(false);
    }
  };

  const onConnected = async () => {
    toast.success('Personal Telegram account connected.');
    setCode('');
    setPassword('');
    setStep('phone');
    const s = await loadStatus();
    if (s?.connected) {
      loadDialogs();
      loadSchedules();
    }
  };

  const disconnect = async () => {
    if (!confirm('Disconnect your Telegram account and stop all scheduled forwards?')) return;
    try {
      await apiClient.post('/api/forward/disconnect', {});
      toast.success('Disconnected.');
      setDialogs([]);
      setSelected(new Set());
      setSchedules([]);
      await loadStatus();
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  // ── Composer ─────────────────────────────────────────────────────────────
  const maxTargets = status?.limits.max_targets ?? 45;
  const minInterval = status?.limits.min_interval_minutes ?? 15;

  const toggleTarget = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else if (next.size < maxTargets) next.add(id);
      else toast.warning(`You can select up to ${maxTargets} targets.`);
      return next;
    });
  };

  const filteredDialogs = useMemo(() => {
    const q = dialogQuery.trim().toLowerCase();
    if (!q) return dialogs;
    return dialogs.filter(
      (d) => d.title.toLowerCase().includes(q) || (d.username || '').toLowerCase().includes(q),
    );
  }, [dialogs, dialogQuery]);

  const allTargets = useMemo(() => {
    const manual = manualTargets
      .split(/[\s,]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    return [...Array.from(selected), ...manual];
  }, [selected, manualTargets]);

  const send = async (scheduled: boolean) => {
    if (!message.trim()) {
      toast.error('Enter a message to forward.');
      return;
    }
    if (allTargets.length === 0) {
      toast.error('Select or enter at least one target.');
      return;
    }
    if (scheduled) {
      const iv = parseInt(intervalMin, 10);
      if (!iv || iv < minInterval) {
        toast.error(`Minimum interval is ${minInterval} minutes.`);
        return;
      }
    }
    setSending(true);
    try {
      const body: Record<string, unknown> = { targets: allTargets, message };
      if (scheduled) body.interval_minutes = parseInt(intervalMin, 10);
      const res = await apiClient.post<{ status: string; sent?: number; summary?: string }>(
        '/api/forward/send',
        body,
        { silent: true },
      );
      if (res.data.status === 'scheduled') {
        toast.success('Scheduled forward started.');
        setInterval('');
        loadSchedules();
      } else {
        toast.success(res.data.summary || `Sent to ${res.data.sent} target(s).`);
      }
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSending(false);
    }
  };

  const stopSchedule = async (id: string) => {
    try {
      await apiClient.post(`/api/forward/schedules/${id}/stop`, {});
      toast.success('Scheduled forward stopped.');
      loadSchedules();
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────
  if (loadingStatus) {
    return (
      <div className="max-w-3xl mx-auto py-20 text-center text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin mx-auto" />
      </div>
    );
  }

  if (status && !status.available) {
    return (
      <div className="max-w-3xl mx-auto">
        <PageHeader icon={<Send className="h-6 w-6" />} eyebrow="Telegram" title={t('forward_telegram')} />
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>Telegram forwarding is not available on this server right now.</AlertDescription>
        </Alert>
      </div>
    );
  }

  const securityNote = (
    <Alert>
      <ShieldCheck className="h-4 w-4" />
      <AlertDescription className="text-xs">
        Only connect your <strong>own</strong> Telegram account. Connecting lets this site send messages as you. Never
        share Telegram login codes with anyone in chats, groups, or bot DMs.
      </AlertDescription>
    </Alert>
  );

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader
        icon={<Send className="h-6 w-6" />}
        eyebrow="Telegram"
        title={t('forward_telegram')}
        description="Connect your personal Telegram account and forward a message to many of your groups and channels — once or on a repeating schedule."
        actions={
          status?.connected ? (
            <div className="flex items-center gap-2">
              <StatusBadge status="active" label={status.display_name || 'Connected'} />
              <Button variant="outline" size="sm" onClick={disconnect}>
                <Trash2 className="h-4 w-4 mr-2" /> Disconnect
              </Button>
            </div>
          ) : undefined
        }
      />

      {!status?.connected ? (
        <Card>
          <CardHeader>
            <CardTitle>Connect your Telegram account</CardTitle>
            <CardDescription>
              Get your <strong>API ID</strong> and <strong>API hash</strong> from{' '}
              <a href="https://my.telegram.org" target="_blank" rel="noreferrer" className="text-primary underline">
                my.telegram.org
              </a>{' '}
              → API development tools.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {securityNote}

            {step === 'phone' && (
              <form onSubmit={sendCode} className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>API ID</Label>
                    <Input value={apiId} onChange={(e) => setApiId(e.target.value)} placeholder="12345678" inputMode="numeric" />
                  </div>
                  <div className="space-y-2">
                    <Label>API hash</Label>
                    <Input value={apiHash} onChange={(e) => setApiHash(e.target.value)} placeholder="32-character hash" className="font-mono" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Phone number (with country code)</Label>
                  <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+8801XXXXXXXXX" />
                </div>
                <Button type="submit" className="w-full" disabled={connecting || !apiId || !apiHash || !phone}>
                  {connecting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
                  Send login code
                </Button>
              </form>
            )}

            {step === 'code' && (
              <form onSubmit={verifyCode} className="space-y-4">
                <div className="space-y-2">
                  <Label>Login code (from your Telegram app)</Label>
                  <Input
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="12345"
                    className="font-mono text-center text-lg tracking-widest"
                    inputMode="numeric"
                  />
                </div>
                <div className="flex gap-3">
                  <Button type="button" variant="outline" onClick={() => setStep('phone')} disabled={connecting}>
                    Back
                  </Button>
                  <Button type="submit" className="flex-1" disabled={connecting || !code}>
                    {connecting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
                    Verify code
                  </Button>
                </div>
              </form>
            )}

            {step === 'password' && (
              <form onSubmit={verifyPassword} className="space-y-4">
                <div className="space-y-2">
                  <Label>Two-step verification password</Label>
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Your Telegram 2FA password"
                  />
                </div>
                <Button type="submit" className="w-full" disabled={connecting || !password}>
                  {connecting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
                  Connect
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Composer */}
          <Card>
            <CardHeader>
              <CardTitle>Compose &amp; forward</CardTitle>
              <CardDescription>Text messages only. Selected: {allTargets.length}/{maxTargets} targets.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label>Message</Label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={4}
                  placeholder="Write the message to forward…"
                  className="w-full rounded-md border border-input bg-background p-3 text-sm"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Your groups &amp; channels</Label>
                  <Button variant="ghost" size="sm" onClick={loadDialogs} disabled={loadingDialogs}>
                    <RefreshCw className={`h-4 w-4 mr-1 ${loadingDialogs ? 'animate-spin' : ''}`} /> Reload
                  </Button>
                </div>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    value={dialogQuery}
                    onChange={(e) => setDialogQuery(e.target.value)}
                    placeholder="Search…"
                    className="pl-9"
                  />
                </div>
                <div className="max-h-64 overflow-y-auto rounded-md border border-border divide-y divide-border">
                  {loadingDialogs ? (
                    <div className="py-10 text-center text-muted-foreground">
                      <Loader2 className="h-5 w-5 animate-spin mx-auto" />
                    </div>
                  ) : filteredDialogs.length === 0 ? (
                    <div className="py-8 text-center text-sm text-muted-foreground">
                      No groups/channels found. Make sure your account is a member, then Reload.
                    </div>
                  ) : (
                    filteredDialogs.map((d) => (
                      <label key={d.id} className="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-muted/50">
                        <input
                          type="checkbox"
                          checked={selected.has(d.id)}
                          onChange={() => toggleTarget(d.id)}
                          className="h-4 w-4"
                        />
                        <span className="flex-1 min-w-0 truncate text-sm">{d.title}</span>
                        <Badge variant="outline" className="text-[10px] capitalize">{d.type}</Badge>
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Add targets manually (optional)</Label>
                <Input
                  value={manualTargets}
                  onChange={(e) => setManualTargets(e.target.value)}
                  placeholder="@channel, t.me/group, -1001234567890"
                />
                <p className="text-xs text-muted-foreground">@usernames, public t.me links, or numeric chat IDs, separated by spaces/commas.</p>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <Button className="flex-1" onClick={() => send(false)} disabled={sending}>
                  {sending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
                  Send once
                </Button>
                <div className="flex gap-2 flex-1">
                  <Input
                    value={intervalMin}
                    onChange={(e) => setIntervalMin(e.target.value.replace(/\D/g, ''))}
                    placeholder={`every N min (≥${minInterval})`}
                    inputMode="numeric"
                    className="w-40"
                  />
                  <Button variant="secondary" className="flex-1" onClick={() => send(true)} disabled={sending}>
                    <Clock className="h-4 w-4 mr-2" /> Schedule
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Active schedules */}
          <Card>
            <CardHeader>
              <CardTitle>Scheduled forwards</CardTitle>
              <CardDescription>Repeating forwards run on the server, even while you're offline.</CardDescription>
            </CardHeader>
            <CardContent>
              {schedules.length === 0 ? (
                <EmptyState
                  icon={<Clock className="h-6 w-6" />}
                  title="No scheduled forwards"
                  description="Set an interval above to start one."
                />
              ) : (
                <div className="space-y-3">
                  {schedules.map((s) => (
                    <div key={s.schedule_id} className="flex items-start justify-between gap-3 rounded-md border border-border p-3">
                      <div className="min-w-0 space-y-1">
                        <p className="text-sm font-medium truncate">{s.message}</p>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                          <span className="inline-flex items-center gap-1">
                            <Clock className="h-3 w-3" /> every {s.interval_minutes} min
                          </span>
                          <span>· {s.targets.length} targets</span>
                          {s.last_result && (
                            <span className="inline-flex items-center gap-1">
                              <CheckCircle2 className="h-3 w-3 text-success" /> {s.last_result}
                            </span>
                          )}
                        </div>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => stopSchedule(s.schedule_id)}>
                        Stop
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {securityNote}
        </>
      )}
    </div>
  );
};

export default ForwardTelegram;
