import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Button } from '../components/ui/button';
import { Banknote, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const Payout: React.FC = () => {
  const { token } = useAuth();
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('bKash');
  const [details, setDetails] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  const fetchHistory = () => {
    setHistoryLoading(true);
    fetch('/api/payout/history', { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(r => r.json())
      .then(d => setHistory(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setHistoryLoading(false));
  };

  useEffect(() => { if (token) fetchHistory(); else setHistoryLoading(false); }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || parseFloat(amount) <= 0) { toast.error('Enter a valid amount'); return; }
    setLoading(true);
    try {
      const res = await fetch('/api/payout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ amount: parseFloat(amount), method, details })
      });
      const data = await res.json();
      if (data.success) {
        toast.success(`Payout request submitted: ${data.request_id}`);
        setAmount(''); setDetails('');
        fetchHistory();
      } else {
        toast.error(data.message || 'Request failed');
      }
    } catch {
      toast.error('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Banknote className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Payout / Withdraw</h1>
          <p className="text-muted-foreground text-sm">Withdraw your referral earnings or balance</p>
        </div>
      </div>

      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="text-lg">New Payout Request</CardTitle>
          <CardDescription>Submit a withdrawal request for admin review</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-2">
              <Label>Amount (BDT)</Label>
              <Input type="number" placeholder="5000" value={amount} onChange={(e) => setAmount(e.target.value)} required />
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
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="text-lg">Payout History</CardTitle>
        </CardHeader>
        <CardContent>
          {historyLoading && <div className="flex justify-center py-6"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>}
          {!historyLoading && history.length === 0 && (
            <p className="text-center text-muted-foreground py-6">No payout requests yet.</p>
          )}
          <div className="space-y-3">
            {history.map((p) => (
              <div key={p.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <div>
                  <div className="font-mono text-sm font-bold">{p.id}</div>
                  <div className="text-xs text-muted-foreground">{p.method} — {p.details || 'N/A'}</div>
                  <div className="text-xs text-muted-foreground">{p.created_at?.slice(0, 16)}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold">৳{p.amount}</div>
                  <Badge variant={p.status === 'paid' ? 'default' : p.status === 'rejected' ? 'destructive' : 'secondary'} className="text-[10px]">
                    {p.status === 'paid' ? 'Paid' : p.status === 'rejected' ? 'Rejected' : 'Pending'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Payout;
