import React, { useState, useEffect, useCallback } from 'react';
import {
  Wallet, Key, Shield, Eye, EyeOff, AlertTriangle, Send, RefreshCw, Loader2,
  Plus, Copy, Trash2, X, Check,
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { NETWORK_LIST, NETWORK_MAP, NetworkLogo } from '../constants/networks';
import { apiClient, ApiUnavailableError, getErrorMessage } from '../lib/apiClient';
import type { ApiEnvelope } from '../types';

interface WalletBalancesData {
  wallets: WalletItem[];
}
interface MasterStatusData {
  has_master: boolean;
}
interface SendResultData {
  tx_hash?: string;
}

interface WalletItem {
  id: number;
  network: string;
  label: string | null;
  wallet_address: string | null;
  balance?: number | null;
  native_balance?: number | null;
  asset?: string | null;
}

const truncate = (addr?: string | null) =>
  addr ? `${addr.slice(0, 6)}…${addr.slice(-4)}` : '—';

// ─── Lightweight modal ───
const Modal: React.FC<{ open: boolean; onClose: () => void; title: string; children: React.ReactNode }> = ({
  open, onClose, title, children,
}) => {
  if (!open) return null;
  const titleId = `modal-title-${title.replace(/\s+/g, '-').toLowerCase()}`;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="w-full max-w-md rounded-lg border border-primary/10 bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 id={titleId} className="text-base font-bold">{title}</h2>
          <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={onClose} aria-label="Close dialog">
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
};

const MyWallet: React.FC = () => {
  const { token } = useAuth();
  const [wallets, setWallets] = useState<WalletItem[]>([]);
  const [hasMaster, setHasMaster] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [backendStale, setBackendStale] = useState(false);

  // Add wallet form
  const [addOpen, setAddOpen] = useState(false);
  const [aNetwork, setANetwork] = useState('solana');
  const [aMode, setAMode] = useState<'create' | 'import'>('create');
  const [aPrivateKey, setAPrivateKey] = useState('');
  const [aLabel, setALabel] = useState('');
  const [aMasterPwd, setAMasterPwd] = useState('');
  const [aShowKey, setAShowKey] = useState(false);
  const [aBusy, setABusy] = useState(false);

  // Send form
  const [sendWallet, setSendWallet] = useState<WalletItem | null>(null);
  const [sDest, setSDest] = useState('');
  const [sAmount, setSAmount] = useState('');
  const [sMasterPwd, setSMasterPwd] = useState('');
  const [sBusy, setSBusy] = useState(false);

  // Delete form
  const [delWallet, setDelWallet] = useState<WalletItem | null>(null);
  const [delPwd, setDelPwd] = useState('');
  const [delBusy, setDelBusy] = useState(false);

  const loadMasterStatus = useCallback(async () => {
    try {
      const res = await apiClient.get<ApiEnvelope<MasterStatusData>>(
        '/api/wallets/master/status',
        { silent: true }
      );
      const data = res.data;
      if (data.ok) setHasMaster(!!data.data?.has_master);
    } catch (err) {
      if (err instanceof ApiUnavailableError) setBackendStale(true);
      /* otherwise ignore - balances loader surfaces connection errors */
    }
  }, []);

  const loadBalances = useCallback(async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true);
    try {
      const res = await apiClient.get<ApiEnvelope<WalletBalancesData>>(
        '/api/wallets/balances',
        { silent: true }
      );
      const data = res.data;
      if (data.ok) {
        setWallets(data.data?.wallets || []);
        setBackendStale(false);
      } else {
        toast.error(data.message || 'Failed to load balances');
      }
    } catch (err) {
      if (err instanceof ApiUnavailableError) {
        setBackendStale(true);
      } else {
        toast.error(getErrorMessage(err, 'Connection error'));
      }
    } finally {
      if (showSpinner) setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    if (!token) return;
    (async () => {
      setLoading(true);
      await Promise.all([loadMasterStatus(), loadBalances()]);
      setLoading(false);
    })();
  }, [token, loadMasterStatus, loadBalances]);

  const copy = (text?: string | null) => {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => toast.success('Address copied'));
  };

  // ─── Add wallet ───
  const submitAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aMasterPwd) { toast.error('Master password is required'); return; }
    if (aMode === 'import' && !aPrivateKey) { toast.error('Private key is required to import'); return; }
    setABusy(true);
    try {
      const res = await apiClient.post<ApiEnvelope<unknown>>(
        '/api/wallets',
        {
          network: aNetwork,
          mode: aMode,
          private_key: aMode === 'import' ? aPrivateKey.trim() : undefined,
          label: aLabel.trim() || undefined,
          master_password: aMasterPwd,
        },
        { silent: true }
      );
      const data = res.data;
      if (data.ok) {
        toast.success(hasMaster ? 'Wallet added' : 'Master password set and wallet added');
        setHasMaster(true);
        setAddOpen(false);
        setAPrivateKey(''); setALabel(''); setAMasterPwd('');
        await loadBalances(true);
      } else {
        toast.error(data.message || 'Failed to add wallet');
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Connection error'));
    } finally {
      setABusy(false);
    }
  };

  // ─── Send ───
  const submitSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sendWallet) return;
    if (!sDest.trim() || !sAmount || !sMasterPwd) { toast.error('All fields are required'); return; }
    const amount = parseFloat(sAmount);
    if (!Number.isFinite(amount) || amount <= 0) { toast.error('Enter a valid amount greater than 0'); return; }
    setSBusy(true);
    try {
      const res = await apiClient.post<ApiEnvelope<SendResultData>>(
        `/api/wallets/${sendWallet.id}/send`,
        {
          to_address: sDest.trim(),
          amount,
          asset: sendWallet.asset || undefined,
          master_password: sMasterPwd,
        },
        { silent: true }
      );
      const data = res.data;
      if (data.ok) {
        toast.success(`Sent! Tx: ${truncate(data.data?.tx_hash)}`);
        setSendWallet(null);
        setSDest(''); setSAmount(''); setSMasterPwd('');
        await loadBalances(true);
      } else {
        toast.error(data.message || 'Send failed');
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Connection error'));
    } finally {
      setSBusy(false);
    }
  };

  // ─── Delete ───
  const submitDelete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!delWallet) return;
    if (!delPwd) { toast.error('Master password is required'); return; }
    setDelBusy(true);
    try {
      const res = await apiClient.delete<ApiEnvelope<unknown>>(
        `/api/wallets/${delWallet.id}`,
        { data: { master_password: delPwd }, silent: true }
      );
      const data = res.data;
      if (data.ok) {
        toast.success('Wallet removed');
        setDelWallet(null);
        setDelPwd('');
        await Promise.all([loadMasterStatus(), loadBalances(true)]);
      } else {
        toast.error(data.message || 'Failed to remove wallet');
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Connection error'));
    } finally {
      setDelBusy(false);
    }
  };

  // Group wallets by network
  const grouped = wallets.reduce<Record<string, WalletItem[]>>((acc, w) => {
    (acc[w.network] = acc[w.network] || []).push(w);
    return acc;
  }, {});

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Wallet className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">My Wallets</h1>
            <p className="text-muted-foreground text-sm">
              {wallets.length > 0
                ? `${wallets.length} wallet${wallets.length > 1 ? 's' : ''} across ${Object.keys(grouped).length} network${Object.keys(grouped).length > 1 ? 's' : ''}`
                : 'Connect multiple wallets across any network'}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => loadBalances(true)} disabled={refreshing || loading}>
            {refreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            <span className="ml-1">Refresh</span>
          </Button>
          <Button size="sm" onClick={() => setAddOpen(true)}>
            <Plus className="h-4 w-4 mr-1" /> Add Wallet
          </Button>
        </div>
      </div>

      <Alert className="bg-warning/5 border-warning/20">
        <Shield className="h-4 w-4" />
        <AlertTitle className="text-xs font-bold">One master password</AlertTitle>
        <AlertDescription className="text-xs">
          {hasMaster
            ? 'Balances load automatically. Your master password is only required to send or delete a wallet.'
            : 'The first wallet you add sets your master password. Every wallet key is encrypted with it. We never store it in plaintext.'}
        </AlertDescription>
      </Alert>

      {backendStale && (
        <Alert className="bg-destructive/5 border-destructive/20">
          <AlertTriangle className="h-4 w-4 text-destructive" />
          <AlertTitle className="text-xs font-bold text-destructive">Wallet service unavailable</AlertTitle>
          <AlertDescription className="text-xs">
            The server is running an older version that does not include the wallet endpoints yet.
            Restart or redeploy the backend, then press Refresh.
            <Button variant="outline" size="sm" className="mt-2 h-7" onClick={() => loadBalances(true)} disabled={refreshing}>
              {refreshing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
              <span className="ml-1">Retry</span>
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading wallets…
        </div>
      ) : backendStale ? null : wallets.length === 0 ? (
        <Card className="border-primary/10">
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <div className="p-3 bg-primary/10 rounded-full">
              <Wallet className="h-7 w-7 text-primary" />
            </div>
            <p className="text-sm text-muted-foreground max-w-sm">
              No wallets yet. Add your first wallet to set a master password and start tracking balances.
            </p>
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="h-4 w-4 mr-1" /> Add your first wallet
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([network, items]) => {
            const meta = NETWORK_MAP[network];
            return (
              <div key={network} className="space-y-2">
                <div className="flex items-center gap-2">
                  <NetworkLogo id={network} size={20} />
                  <h2 className="text-sm font-bold tracking-tight">{meta?.name || network}</h2>
                  <span className="text-xs text-muted-foreground">({items.length})</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {items.map((w) => (
                    <Card key={w.id} className="border-primary/10">
                      <CardContent className="p-4 space-y-3">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="font-semibold text-sm truncate">
                              {w.label || meta?.name || network}
                            </p>
                            <button
                              type="button"
                              onClick={() => copy(w.wallet_address)}
                              aria-label={`Copy wallet address ${w.wallet_address || ''}`}
                              className="flex items-center gap-1 text-xs text-muted-foreground font-mono hover:text-foreground"
                            >
                              {truncate(w.wallet_address)}
                              <Copy className="h-3 w-3" />
                            </button>
                          </div>
                          <NetworkLogo id={network} size={28} />
                        </div>
                        <div className="rounded-md bg-muted/30 px-3 py-2">
                          <p className="text-lg font-bold">
                            {w.balance != null ? w.balance : '—'}{' '}
                            <span className="text-xs font-medium text-muted-foreground">{w.asset || meta?.asset}</span>
                          </p>
                          {w.native_balance != null && (
                            <p className="text-xs text-muted-foreground">Gas: {w.native_balance}</p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1"
                            onClick={() => { setSendWallet(w); setSDest(''); setSAmount(''); setSMasterPwd(''); }}
                          >
                            <Send className="h-3.5 w-3.5 mr-1" /> Send
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive hover:text-destructive"
                            aria-label={`Remove wallet ${w.label || meta?.name || network}`}
                            onClick={() => { setDelWallet(w); setDelPwd(''); }}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add wallet modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title={hasMaster ? 'Add Wallet' : 'Add Wallet & Set Master Password'}>
        <form onSubmit={submitAdd} className="space-y-4">
          <div className="space-y-2">
            <Label>Network</Label>
            <select value={aNetwork} onChange={(e) => setANetwork(e.target.value)} className="w-full h-10 rounded-md border bg-background px-3 text-sm">
              {NETWORK_LIST.map((n) => <option key={n.id} value={n.id}>{n.name} ({n.asset})</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <Label>Source</Label>
            <div className="flex gap-2">
              <Button type="button" size="sm" variant={aMode === 'create' ? 'default' : 'outline'} className="flex-1" onClick={() => setAMode('create')}>
                {aMode === 'create' && <Check className="h-3.5 w-3.5 mr-1" />} Create new
              </Button>
              <Button type="button" size="sm" variant={aMode === 'import' ? 'default' : 'outline'} className="flex-1" onClick={() => setAMode('import')}>
                {aMode === 'import' && <Check className="h-3.5 w-3.5 mr-1" />} Import key
              </Button>
            </div>
          </div>
          {aMode === 'import' && (
            <div className="space-y-2">
              <Label>Private Key</Label>
              <div className="relative">
                <Input
                  type={aShowKey ? 'text' : 'password'}
                  placeholder="Paste your private key"
                  value={aPrivateKey}
                  onChange={(e) => setAPrivateKey(e.target.value)}
                  className="font-mono pr-10"
                />
                <Button type="button" variant="ghost" size="icon" aria-label={aShowKey ? 'Hide private key' : 'Show private key'} className="absolute right-1 top-0.5 h-9 w-9" onClick={() => setAShowKey(!aShowKey)}>
                  {aShowKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          )}
          <div className="space-y-2">
            <Label>Label <span className="text-muted-foreground">(optional)</span></Label>
            <Input placeholder="e.g. Main, Savings" value={aLabel} onChange={(e) => setALabel(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>{hasMaster ? 'Master Password' : 'Create Master Password'}</Label>
            <Input type="password" placeholder={hasMaster ? 'Enter your master password' : 'Set one master password for all wallets'} value={aMasterPwd} onChange={(e) => setAMasterPwd(e.target.value)} />
            {!hasMaster && (
              <p className="text-xs text-muted-foreground">This will be your single password for every wallet. Keep it safe — it cannot be recovered.</p>
            )}
          </div>
          <Button type="submit" disabled={aBusy} className="w-full">
            {aBusy ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Key className="h-4 w-4 mr-2" />}
            {hasMaster ? 'Add Wallet' : 'Set Password & Add Wallet'}
          </Button>
        </form>
      </Modal>

      {/* Send modal */}
      <Modal open={!!sendWallet} onClose={() => setSendWallet(null)} title="Send Crypto">
        {sendWallet && (
          <form onSubmit={submitSend} className="space-y-4">
            <div className="flex items-center gap-2 rounded-md bg-muted/30 px-3 py-2">
              <NetworkLogo id={sendWallet.network} size={22} />
              <div className="min-w-0">
                <p className="text-sm font-semibold truncate">{sendWallet.label || NETWORK_MAP[sendWallet.network]?.name || sendWallet.network}</p>
                <p className="text-xs text-muted-foreground font-mono">{truncate(sendWallet.wallet_address)}</p>
              </div>
              <span className="ml-auto text-xs text-muted-foreground">
                {sendWallet.balance != null ? `${sendWallet.balance} ${sendWallet.asset || ''}` : ''}
              </span>
            </div>
            <div className="space-y-2">
              <Label>Recipient Address</Label>
              <Input placeholder="Destination wallet address" value={sDest} onChange={(e) => setSDest(e.target.value)} className="font-mono" />
            </div>
            <div className="space-y-2">
              <Label>Amount ({sendWallet.asset || NETWORK_MAP[sendWallet.network]?.asset})</Label>
              <Input type="number" step="any" placeholder="0.00" value={sAmount} onChange={(e) => setSAmount(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Master Password</Label>
              <Input type="password" placeholder="Required to sign this transaction" value={sMasterPwd} onChange={(e) => setSMasterPwd(e.target.value)} />
            </div>
            <Alert className="bg-destructive/5 border-destructive/20">
              <AlertTriangle className="h-4 w-4 text-destructive" />
              <AlertDescription className="text-xs">Blockchain transactions are irreversible. Double-check the address and amount.</AlertDescription>
            </Alert>
            <Button type="submit" disabled={sBusy} className="w-full" variant="destructive">
              {sBusy ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
              Send
            </Button>
          </form>
        )}
      </Modal>

      {/* Delete modal */}
      <Modal open={!!delWallet} onClose={() => setDelWallet(null)} title="Remove Wallet">
        {delWallet && (
          <form onSubmit={submitDelete} className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Remove <span className="font-semibold text-foreground">{delWallet.label || NETWORK_MAP[delWallet.network]?.name || delWallet.network}</span>{' '}
              (<span className="font-mono">{truncate(delWallet.wallet_address)}</span>)? This deletes the encrypted key from the server.
            </p>
            <div className="space-y-2">
              <Label>Master Password</Label>
              <Input type="password" placeholder="Required to remove this wallet" value={delPwd} onChange={(e) => setDelPwd(e.target.value)} />
            </div>
            <Button type="submit" disabled={delBusy} className="w-full" variant="destructive">
              {delBusy ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
              Remove Wallet
            </Button>
          </form>
        )}
      </Modal>
    </div>
  );
};

export default MyWallet;
