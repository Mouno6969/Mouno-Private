import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Button } from '../components/ui/button';
import { Banknote, Loader2, Inbox } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import { PageHeader, StatusBadge, RelativeTime, CopyButton, EmptyState, TexturePanel } from '../components/common';

interface PayoutEntry {
  id: string;
  amount: number;
  method: string;
  details?: string;
  status: string;
  created_at?: string;
}

const Payout: React.FC = () => {
  const { token } = useAuth();
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('bKash');
  const [details, setDetails] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<PayoutEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  const fetchHistory = () => {
    setHistoryLoading(true);
    apiClient
      .get<PayoutEntry[]>('/api/payout/history', { silent: true })
      .then(r => setHistory(Array.isArray(r.data) ? r.data : []))
      .catch(() => {})
      .finally(() => setHistoryLoading(false));
  };

  useEffect(() => { if (token) fetchHistory(); else setHistoryLoading(false); }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || parseFloat(amount) <= 0) { toast.error('Enter a valid amount'); return; }
    setLoading(true);
    try {
      const res = await apiClient.post<{ success?: boolean; request_id?: string; message?: string }>(
        '/api/payout',
        { amount: parseFloat(amount), method, details },
        { silent: true }
      );
      if (res.data.success) {
        toast.success(`Payout request submitted: ${res.data.request_id}`);
        setAmount(''); setDetails('');
        fetchHistory();
      } else {
        toast.error(res.data.message || 'Request failed');
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to connect to server'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader
        icon={<Banknote className="h-7 w-7" />}
        eyebrow="Withdraw"
        title="Payout / Withdraw"
        description="Withdraw your referral earnings or balance"
      />

      <TexturePanel variant="primary" glow accentTop>
        <div className="p-5 sm:p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold tracking-tight">New Payout Request</h2>
            <p className="text-sm text-muted-foreground">Submit a withdrawal request for admin review</p>
          </div>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-2">
              <Label>Amount (BDT)</Label>
              <Input type="number" inputMode="numeric" className="num" placeholder="5000" value={amount} onChange={(e) => setAmount(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label>Method</Label>
              <select value={method} onChange={(e) => setMethod(e.target.value)} className="w-full h-10 rounded-md border bg-background px-3 text-sm">
                <option value="bKash">bKash</option>
                <option value="Nagad">Nagad</option>
                <option value="Bank">Bank Transfer</option>
                <option value="Crypto">Crypto</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Details (phone number, wallet address, etc.)</Label>
              <Input placeholder="01XXXXXXXXX" value={details} onChange={(e) => setDetails(e.target.value)} />
            </div>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Submit Request
            </Button>
          </form>
        </div>
      </TexturePanel>

      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="text-lg">Payout History</CardTitle>
        </CardHeader>
        <CardContent>
          {historyLoading && <div className="flex justify-center py-6"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>}
          {!historyLoading && history.length === 0 && (
            <EmptyState icon={<Inbox className="h-6 w-6" aria-hidden="true" />} title="No payout requests yet" description="Your withdrawal requests will appear here." />
          )}
          <div className="space-y-2">
            {history.map((p) => {
              const edge = p.status === 'paid' ? 'border-l-success' : p.status === 'rejected' ? 'border-l-destructive' : 'border-l-warning';
              return (
              <div key={p.id} className={`flex items-center justify-between p-3 rounded-lg bg-muted/30 border-l-2 ${edge} transition-colors hover:bg-muted/50`}>
                <div className="min-w-0">
                  <div className="inline-flex items-center gap-1.5 font-mono text-sm font-bold">{p.id}<CopyButton value={p.id} label="Copy request ID" /></div>
                  <div className="text-xs text-muted-foreground truncate">{p.method} — {p.details || '—'}</div>
                  <RelativeTime value={p.created_at} className="text-xs text-muted-foreground" />
                </div>
                <div className="text-right shrink-0">
                  <div className="num font-bold">৳{p.amount}</div>
                  <StatusBadge status={p.status} className="text-[10px]" />
                </div>
              </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Payout;
