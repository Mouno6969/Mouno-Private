import React, { useState, useEffect } from 'react';
import { Wallet, Key, Shield, Eye, EyeOff, AlertTriangle, CheckCircle2, Send, RefreshCw, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { NETWORK_LIST } from '../constants/networks';

const MyWallet: React.FC = () => {
  const { token } = useAuth();
  const [tab, setTab] = useState<'setup' | 'balance' | 'send'>('setup');
  const [hasWallet, setHasWallet] = useState(false);
  const [walletNetwork, setWalletNetwork] = useState('');
  const [loading, setLoading] = useState(false);

  // Setup
  const [network, setNetwork] = useState('solana');
  const [privateKey, setPrivateKey] = useState('');
  const [password, setPassword] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [setupResult, setSetupResult] = useState<{address: string; network: string} | null>(null);

  // Balance
  const [balPassword, setBalPassword] = useState('');
  const [balanceInfo, setBalanceInfo] = useState<any>(null);

  // Send
  const [sendDest, setSendDest] = useState('');
  const [sendAmount, setSendAmount] = useState('');
  const [sendPassword, setSendPassword] = useState('');
  const [sendResult, setSendResult] = useState<any>(null);

  const headers = (): Record<string, string> => {
    const h: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
  };

  useEffect(() => {
    if (token) {
      fetch('/api/wallet/status', { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.json())
        .then(d => { setHasWallet(d.has_wallet); setWalletNetwork(d.network || ''); })
        .catch(() => {});
    }
  }, [token]);

  const setupWallet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!privateKey || !password || !network) { toast.error('All fields are required'); return; }
    setLoading(true);
    try {
      const res = await fetch('/api/wallet/setup', {
        method: 'POST', headers: headers(),
        body: JSON.stringify({ network, private_key: privateKey, password })
      });
      const data = await res.json();
      if (data.success) {
        toast.success('Wallet setup successful!');
        setSetupResult(data);
        setHasWallet(true);
        setWalletNetwork(data.network);
        setPrivateKey('');
        setPassword('');
      } else {
        toast.error(data.message || 'Setup failed');
      }
    } catch { toast.error('Connection error'); }
    finally { setLoading(false); }
  };

  const checkBalance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!balPassword) { toast.error('Password required'); return; }
    setLoading(true); setBalanceInfo(null);
    try {
      const res = await fetch('/api/wallet/balance', {
        method: 'POST', headers: headers(),
        body: JSON.stringify({ password: balPassword })
      });
      const data = await res.json();
      if (data.success) {
        setBalanceInfo(data.balance);
      } else {
        toast.error(data.message || 'Balance check failed');
      }
    } catch { toast.error('Connection error'); }
    finally { setLoading(false); }
  };

  const sendCrypto = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sendDest || !sendAmount || !sendPassword) { toast.error('All fields required'); return; }
    if (!window.confirm(`Send ${sendAmount} to ${sendDest}? This is irreversible!`)) return;
    setLoading(true); setSendResult(null);
    try {
      const res = await fetch('/api/wallet/send', {
        method: 'POST', headers: headers(),
        body: JSON.stringify({ destination: sendDest, amount: parseFloat(sendAmount), password: sendPassword })
      });
      const data = await res.json();
      if (data.success) {
        toast.success('Transaction sent!');
        setSendResult(data);
        setSendAmount('');
        setSendPassword('');
      } else {
        toast.error(data.message || 'Send failed');
      }
    } catch { toast.error('Connection error'); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Wallet className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Personal Wallet</h1>
          <p className="text-muted-foreground text-sm">
            {hasWallet
              ? <span className="text-green-500">Wallet connected ({walletNetwork})</span>
              : 'Setup your encrypted wallet'}
          </p>
        </div>
      </div>

      <Alert className="bg-amber-500/5 border-amber-500/20 text-amber-200">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle className="text-xs font-bold">Security</AlertTitle>
        <AlertDescription className="text-xs">
          Private key encrypted with your password on server. Never share your password. Admin/support will never ask for it.
        </AlertDescription>
      </Alert>

      <div className="flex gap-2">
        <Button variant={tab === 'setup' ? 'default' : 'outline'} size="sm" onClick={() => setTab('setup')}>
          <Key className="h-4 w-4 mr-1" /> Setup
        </Button>
        <Button variant={tab === 'balance' ? 'default' : 'outline'} size="sm" onClick={() => setTab('balance')} disabled={!hasWallet}>
          <RefreshCw className="h-4 w-4 mr-1" /> Balance
        </Button>
        <Button variant={tab === 'send' ? 'default' : 'outline'} size="sm" onClick={() => setTab('send')} disabled={!hasWallet}>
          <Send className="h-4 w-4 mr-1" /> Send
        </Button>
      </div>

      {tab === 'setup' && (
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle className="text-lg">{hasWallet ? 'Change Wallet' : 'Setup Wallet'}</CardTitle>
            <CardDescription>Select network, provide private key, set a password</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={setupWallet} className="space-y-4">
              <div className="space-y-2">
                <Label>Network</Label>
                <select value={network} onChange={(e) => setNetwork(e.target.value)} className="w-full h-10 rounded-md border bg-background px-3 text-sm">
                  {NETWORK_LIST.map(n => <option key={n.id} value={n.id}>{n.name} ({n.asset})</option>)}
                </select>
              </div>
              <div className="space-y-2">
                <Label>Private Key</Label>
                <div className="relative">
                  <Input
                    type={showKey ? 'text' : 'password'}
                    placeholder="Paste your private key"
                    value={privateKey}
                    onChange={(e) => setPrivateKey(e.target.value)}
                    className="font-mono pr-10"
                    required
                  />
                  <Button type="button" variant="ghost" size="icon" className="absolute right-1 top-0.5 h-9 w-9" onClick={() => setShowKey(!showKey)}>
                    {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Password (to encrypt your key)</Label>
                <Input type="password" placeholder="Strong password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </div>
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Shield className="h-4 w-4 mr-2" />}
                {hasWallet ? 'Replace Wallet' : 'Setup Wallet'}
              </Button>
            </form>
            {setupResult && (
              <Alert className="mt-4 bg-green-500/5 border-green-500/20">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <AlertTitle className="text-sm text-green-500">Wallet Connected!</AlertTitle>
                <AlertDescription className="text-xs font-mono">{setupResult.address}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'balance' && (
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle className="text-lg">Check Balance</CardTitle>
            <CardDescription>Enter your password to view wallet balance</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={checkBalance} className="space-y-4">
              <Input type="password" placeholder="Your wallet password" value={balPassword} onChange={(e) => setBalPassword(e.target.value)} required />
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Check Balance
              </Button>
            </form>
            {balanceInfo && (
              <div className="mt-4 p-4 rounded-lg bg-muted/30">
                <pre className="text-sm font-mono whitespace-pre-wrap">{typeof balanceInfo === 'object' ? JSON.stringify(balanceInfo, null, 2) : String(balanceInfo)}</pre>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'send' && (
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle className="text-lg">Send Crypto</CardTitle>
            <CardDescription>Send from your personal wallet</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={sendCrypto} className="space-y-4">
              <div className="space-y-2">
                <Label>Destination Wallet</Label>
                <Input placeholder="Recipient wallet address" value={sendDest} onChange={(e) => setSendDest(e.target.value)} className="font-mono" required />
              </div>
              <div className="space-y-2">
                <Label>Amount</Label>
                <Input type="number" step="any" placeholder="0.00" value={sendAmount} onChange={(e) => setSendAmount(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label>Password</Label>
                <Input type="password" placeholder="Your wallet password" value={sendPassword} onChange={(e) => setSendPassword(e.target.value)} required />
              </div>
              <Alert className="bg-destructive/5 border-destructive/20">
                <AlertTriangle className="h-4 w-4 text-destructive" />
                <AlertDescription className="text-xs">Blockchain transactions are irreversible. Double-check address and amount.</AlertDescription>
              </Alert>
              <Button type="submit" disabled={loading} className="w-full" variant="destructive">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
                Send
              </Button>
            </form>
            {sendResult && (
              <Alert className="mt-4 bg-green-500/5 border-green-500/20">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <AlertTitle className="text-sm text-green-500">Sent!</AlertTitle>
                <AlertDescription className="text-xs font-mono break-all">
                  {sendResult.tx_hash || sendResult.sig || JSON.stringify(sendResult)}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MyWallet;
