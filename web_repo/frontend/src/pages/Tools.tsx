import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Wrench,
  Search,
  RotateCcw,
  Send,
  Loader2,
  Info,
  ShieldAlert,
  CheckCircle,
  XCircle,
  Copy,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

type ToolId = 'id-finder' | 'ata-refund' | 'forwarder';

const API = process.env.REACT_APP_API_URL || '';

const Tools: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const [activeTool, setActiveTool] = useState<ToolId>('id-finder');

  const tools: { id: ToolId; name: string; icon: React.ReactNode; description: string }[] = [
    {
      id: 'id-finder',
      name: 'Telegram ID Finder',
      icon: <Search className="h-5 w-5" />,
      description: 'Find user, group or channel IDs from public usernames and t.me links.',
    },
    {
      id: 'ata-refund',
      name: 'Solana ATA Refund',
      icon: <RotateCcw className="h-5 w-5" />,
      description: 'Close empty token accounts and reclaim refundable rent SOL.',
    },
    {
      id: 'forwarder',
      name: 'Message Forwarder',
      icon: <Send className="h-5 w-5" />,
      description: 'Send one message to multiple Telegram chats with your own bot token.',
    },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
      <section className="space-y-1">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Wrench className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">{t('free_tools')}</h1>
        </div>
        <p className="text-muted-foreground text-pretty">
          The same free services available in our Telegram bot, now on the web. No charge, ever.
        </p>
      </section>

      {/* Tool selector */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {tools.map((tool) => (
          <button
            key={tool.id}
            type="button"
            onClick={() => setActiveTool(tool.id)}
            className={`p-4 rounded-xl border text-left flex flex-col gap-2 transition-all ${
              activeTool === tool.id
                ? 'border-primary bg-primary/10 ring-1 ring-primary'
                : 'border-muted bg-card hover:border-primary/50'
            }`}
          >
            <div className={`flex items-center gap-2 font-bold ${activeTool === tool.id ? 'text-primary' : ''}`}>
              {tool.icon}
              <span className="text-sm">{tool.name}</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">{tool.description}</p>
          </button>
        ))}
      </div>

      {activeTool === 'id-finder' && <IdFinderTool token={token} />}
      {activeTool === 'ata-refund' && <AtaRefundTool token={token} />}
      {activeTool === 'forwarder' && <ForwarderTool token={token} />}
    </div>
  );
};

// ─── Telegram ID Finder ───
const IdFinderTool: React.FC<{ token: string | null }> = ({ token }) => {
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API}/api/tools/telegram-id?target=${encodeURIComponent(target.trim())}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) {
        setResult(data);
      } else {
        toast.error(data.message || 'Lookup failed');
      }
    } catch {
      toast.error('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
      <Card className="lg:col-span-2 shadow-xl border-primary/10">
        <CardHeader className="bg-muted/30">
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="h-4 w-4 text-primary" /> Telegram ID Finder
          </CardTitle>
          <CardDescription>Resolve a public username or link to its numeric Telegram ID</CardDescription>
        </CardHeader>
        <CardContent className="pt-6 space-y-6">
          <form onSubmit={handleLookup} className="space-y-4">
            <div className="space-y-3">
              <Label htmlFor="target" className="text-xs uppercase tracking-wider text-muted-foreground">
                Username / Link / ID
              </Label>
              <Input
                id="target"
                className="h-12 font-mono"
                placeholder="@username or t.me/username"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                required
              />
            </div>
            <Button type="submit" disabled={loading || !target.trim()} className="w-full h-12 font-bold">
              {loading ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Looking up...</>
              ) : (
                <><Search className="mr-2 h-4 w-4" /> Find ID</>
              )}
            </Button>
          </form>

          {result && (
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3 animate-in fade-in">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-bold tracking-widest text-muted-foreground">ID</span>
                <span className="font-mono font-black text-xl text-primary flex items-center gap-2">
                  {result.id}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground"
                    onClick={() => { navigator.clipboard.writeText(String(result.id)); toast.success('Copied!'); }}
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </Button>
                </span>
              </div>
              {result.type && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Type</span>
                  <Badge variant="outline" className="font-mono capitalize">{result.type}</Badge>
                </div>
              )}
              {result.title && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Name/Title</span>
                  <span className="font-medium">{result.title}</span>
                </div>
              )}
              {result.username && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Username</span>
                  <span className="font-mono">@{result.username}</span>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="text-sm font-bold flex items-center gap-2">
            <Info className="h-4 w-4 text-primary" /> Notes
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            'Public usernames and t.me links resolve directly.',
            'Private groups/channels usually require bot access — use the Telegram bot and forward a message instead.',
            'Numeric IDs are validated and echoed back with chat info when accessible.',
          ].map((text, i) => (
            <div key={i} className="flex gap-3 items-start">
              <div className="h-5 w-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">{i + 1}</div>
              <p className="text-xs text-muted-foreground leading-relaxed">{text}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

// ─── Solana ATA Refund ───
const AtaRefundTool: React.FC<{ token: string | null }> = ({ token }) => {
  const [privateKey, setPrivateKey] = useState('');
  const [checking, setChecking] = useState(false);
  const [refunding, setRefunding] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [refundResult, setRefundResult] = useState<any>(null);

  const handleCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    setChecking(true);
    setSummary(null);
    setRefundResult(null);
    try {
      const res = await fetch(`${API}/api/tools/ata/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ private_key: privateKey.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        setSummary(data);
      } else {
        toast.error(data.message || 'Check failed');
      }
    } catch {
      toast.error('Failed to connect to server');
    } finally {
      setChecking(false);
    }
  };

  const handleRefund = async () => {
    setRefunding(true);
    try {
      const res = await fetch(`${API}/api/tools/ata/refund`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ private_key: privateKey.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        setRefundResult(data);
        setPrivateKey('');
        const refundedSol = Number(data.total_sol ?? 0).toFixed(6);
        toast.success(`Refunded ~${refundedSol} SOL`);
      } else {
        toast.error(data.message || 'Refund failed');
      }
    } catch {
      toast.error('Failed to connect to server');
    } finally {
      setRefunding(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
      <Card className="lg:col-span-2 shadow-xl border-primary/10">
        <CardHeader className="bg-muted/30">
          <CardTitle className="text-lg flex items-center gap-2">
            <RotateCcw className="h-4 w-4 text-primary" /> Solana ATA Refund
          </CardTitle>
          <CardDescription>Check empty Associated Token Accounts and reclaim rent SOL</CardDescription>
        </CardHeader>
        <CardContent className="pt-6 space-y-6">
          <Alert className="bg-amber-500/5 border-amber-500/20 text-amber-200">
            <ShieldAlert className="h-4 w-4" />
            <AlertTitle className="text-sm">Security</AlertTitle>
            <AlertDescription className="text-xs">
              Only connect your own wallet. Your private key is used once for this operation and is never stored.
              ATAs that still hold tokens are never touched.
            </AlertDescription>
          </Alert>

          <form onSubmit={handleCheck} className="space-y-4">
            <div className="space-y-3">
              <Label htmlFor="pk" className="text-xs uppercase tracking-wider text-muted-foreground">
                Solana Private Key (base58)
              </Label>
              <Input
                id="pk"
                type="password"
                className="h-12 font-mono"
                placeholder="Your wallet private key"
                value={privateKey}
                onChange={(e) => setPrivateKey(e.target.value)}
                required
              />
            </div>
            <Button type="submit" disabled={checking || !privateKey.trim()} className="w-full h-12 font-bold" variant="outline">
              {checking ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Checking ATAs...</>
              ) : (
                <><Search className="mr-2 h-4 w-4" /> Check ATA Accounts</>
              )}
            </Button>
          </form>

          {summary && (
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3 animate-in fade-in">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Wallet</span>
                <span className="font-mono text-xs">{summary.wallet?.slice(0, 6)}...{summary.wallet?.slice(-4)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Refundable empty ATAs</span>
                <Badge variant="outline" className="font-mono">{summary.refundable_count}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Estimated refundable SOL</span>
                <span className="font-mono font-black text-xl text-primary">{Number(summary.total_sol ?? 0).toFixed(6)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Skipped (has balance)</span>
                <Badge variant="secondary" className="font-mono">{summary.non_empty_count}</Badge>
              </div>
              {summary.refundable_count > 0 && (
                <Button onClick={handleRefund} disabled={refunding} className="w-full h-12 font-bold mt-2">
                  {refunding ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Refunding SOL...</>
                  ) : (
                    <><RotateCcw className="mr-2 h-4 w-4" /> Refund {Number(summary.total_sol ?? 0).toFixed(6)} SOL</>
                  )}
                </Button>
              )}
            </div>
          )}

          {refundResult && (
            <div className="rounded-xl border border-green-500/30 bg-green-500/5 p-5 space-y-3 animate-in fade-in">
              <div className="flex items-center gap-2 text-green-500 font-bold">
                <CheckCircle className="h-5 w-5" /> Refund complete
              </div>
              <p className="text-sm text-muted-foreground">
                Closed {refundResult.refunded_count ?? 0} accounts, returned ~{Number(refundResult.total_sol ?? 0).toFixed(6)} SOL.
              </p>
              {refundResult.failed_batches && refundResult.failed_batches.length > 0 && (
                <div className="text-amber-600 text-sm border-t border-green-500/20 pt-2 mt-2">
                  <p className="font-semibold">{refundResult.failed_batches.length} batch(es) encountered issues:</p>
                  {refundResult.failed_batches.slice(0, 3).map((batch: any, i: number) => (
                    <p key={i} className="text-xs text-amber-600/70">{batch.error}</p>
                  ))}
                </div>
              )}
              {refundResult.signatures?.map((sig: string, i: number) => (
                <p key={i} className="font-mono text-[10px] text-muted-foreground break-all">{sig}</p>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="text-sm font-bold flex items-center gap-2">
            <Info className="h-4 w-4 text-primary" /> What is this?
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            'Every SPL token you ever held created an Associated Token Account (ATA) with a small rent deposit (~0.002 SOL each).',
            'Empty ATAs can be safely closed — the rent SOL goes back to your own wallet.',
            'A small Solana network fee applies per refund transaction.',
          ].map((text, i) => (
            <div key={i} className="flex gap-3 items-start">
              <div className="h-5 w-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">{i + 1}</div>
              <p className="text-xs text-muted-foreground leading-relaxed">{text}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

// ─── Telegram Message Forwarder ───
const ForwarderTool: React.FC<{ token: string | null }> = ({ token }) => {
  const [botToken, setBotToken] = useState('');
  const [chatIds, setChatIds] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setResults(null);
    try {
      const res = await fetch(`${API}/api/tools/forward`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ bot_token: botToken.trim(), chat_ids: chatIds, message }),
      });
      const data = await res.json();
      if (res.ok) {
        setResults(data);
        toast.success(`Sent to ${data.sent} chat${data.sent === 1 ? '' : 's'}`);
      } else {
        toast.error(data.message || 'Send failed');
      }
    } catch {
      toast.error('Failed to connect to server');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
      <Card className="lg:col-span-2 shadow-xl border-primary/10">
        <CardHeader className="bg-muted/30">
          <CardTitle className="text-lg flex items-center gap-2">
            <Send className="h-4 w-4 text-primary" /> Telegram Message Forwarder
          </CardTitle>
          <CardDescription>One-time broadcast to your groups/channels using your own bot token</CardDescription>
        </CardHeader>
        <CardContent className="pt-6 space-y-6">
          <Alert className="bg-amber-500/5 border-amber-500/20 text-amber-200">
            <ShieldAlert className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Your bot token is used only for this request and never stored. Your bot must be a member
              (with send permission) of every target chat. Max 20 chats per send. For scheduled/repeating
              forwards and personal-account forwarding, use the Telegram bot.
            </AlertDescription>
          </Alert>

          <form onSubmit={handleSend} className="space-y-4">
            <div className="space-y-3">
              <Label htmlFor="bot-token" className="text-xs uppercase tracking-wider text-muted-foreground">
                Your Bot Token (from @BotFather)
              </Label>
              <Input
                id="bot-token"
                type="password"
                className="h-12 font-mono"
                placeholder="123456789:AAExample..."
                value={botToken}
                onChange={(e) => setBotToken(e.target.value)}
                required
              />
            </div>
            <div className="space-y-3">
              <Label htmlFor="chats" className="text-xs uppercase tracking-wider text-muted-foreground">
                Target Chats (comma or newline separated)
              </Label>
              <textarea
                id="chats"
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm font-mono shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring min-h-20"
                placeholder={'@mychannel\n-1001234567890'}
                value={chatIds}
                onChange={(e) => setChatIds(e.target.value)}
                required
              />
            </div>
            <div className="space-y-3">
              <Label htmlFor="message" className="text-xs uppercase tracking-wider text-muted-foreground">
                Message
              </Label>
              <textarea
                id="message"
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring min-h-28"
                placeholder="Write the message to forward..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
              />
            </div>
            <Button
              type="submit"
              disabled={sending || !botToken.trim() || !chatIds.trim() || !message.trim()}
              className="w-full h-12 font-bold"
            >
              {sending ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Sending...</>
              ) : (
                <><Send className="mr-2 h-4 w-4" /> Send Message</>
              )}
            </Button>
          </form>

          {results && (
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-2 animate-in fade-in">
              <div className="flex items-center gap-3 mb-2">
                <Badge variant="outline" className="font-mono text-green-500 border-green-500/30">{results.sent} sent</Badge>
                {results.failed > 0 && (
                  <Badge variant="outline" className="font-mono text-red-500 border-red-500/30">{results.failed} failed</Badge>
                )}
              </div>
              {results.results?.map((r: any, i: number) => (
                <div key={i} className="flex items-center justify-between gap-2 text-xs py-1 border-b border-white/5 last:border-0">
                  <span className="font-mono truncate">{r.chat}</span>
                  {r.ok ? (
                    <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />
                  ) : (
                    <span className="flex items-center gap-1 text-red-400 shrink-0">
                      <XCircle className="h-4 w-4" />
                      <span className="max-w-40 truncate">{r.error}</span>
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="text-sm font-bold flex items-center gap-2">
            <Info className="h-4 w-4 text-primary" /> How to use
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            'Create a bot with @BotFather and copy its token.',
            'Add your bot to the target groups/channels with permission to send messages.',
            'Paste chat @usernames or numeric IDs (use the ID Finder tool if needed).',
            'Write your message and hit send — delivery results show per chat.',
          ].map((text, i) => (
            <div key={i} className="flex gap-3 items-start">
              <div className="h-5 w-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">{i + 1}</div>
              <p className="text-xs text-muted-foreground leading-relaxed">{text}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

export default Tools;
