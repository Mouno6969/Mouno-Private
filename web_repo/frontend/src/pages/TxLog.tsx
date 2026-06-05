import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ScrollText, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { NetworkLogo, NETWORK_MAP } from '../constants/networks';

interface TxEntry {
  trx_id: string;
  amount_bdt: number;
  amount_crypto: number;
  network: string;
  wallet: string;
  status: string;
  created_at: string;
  order_id: string | null;
  source: string;
}

const TxLog: React.FC = () => {
  const { token } = useAuth();
  const [txs, setTxs] = useState<TxEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTxLog = () => {
    setLoading(true);
    fetch('/api/txlog', { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(r => r.json())
      .then(d => setTxs(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { if (token) fetchTxLog(); else setLoading(false); }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const shortWallet = (w: string) => w ? `${w.slice(0, 6)}...${w.slice(-4)}` : 'N/A';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <ScrollText className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">TX Log</h1>
            <p className="text-muted-foreground text-sm">Complete transaction history</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={fetchTxLog} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {loading && (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
      )}

      {!loading && txs.length === 0 && (
        <Card><CardContent className="py-12 text-center text-muted-foreground">No transactions yet.</CardContent></Card>
      )}

      <div className="space-y-3">
        {txs.map((tx) => (
          <Card key={tx.trx_id} className="border-primary/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-3">
                  <NetworkLogo id={tx.network} size={28} />
                  <div>
                    <div className="font-semibold text-sm">{NETWORK_MAP[tx.network]?.name || tx.network}</div>
                    <div className="text-xs text-muted-foreground">{tx.created_at?.slice(0, 16)}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold">{tx.amount_crypto} {NETWORK_MAP[tx.network]?.asset || ''}</div>
                  <div className="text-xs text-muted-foreground">{tx.source}</div>
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between flex-wrap gap-2 text-xs">
                <span className="font-mono text-muted-foreground">Wallet: {shortWallet(tx.wallet)}</span>
                {tx.order_id && <span className="font-mono text-muted-foreground">{tx.order_id}</span>}
                <Badge variant={tx.status === 'completed' ? 'default' : 'destructive'} className="text-[10px]">
                  {tx.status}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default TxLog;
