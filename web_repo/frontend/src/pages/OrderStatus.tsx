import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Search, Loader2, FileText } from 'lucide-react';
import { NetworkLogo, NETWORK_MAP } from '../constants/networks';
import { apiClient, getErrorMessage } from '../lib/apiClient';

interface OrderLookup {
  found?: boolean;
  message?: string;
  status?: string;
  network: string;
  order_id?: string;
  trx_id?: string;
  amount_bdt?: number;
  amount_crypto?: number;
  wallet?: string;
  sig?: string;
  created_at?: string;
}

const OrderStatus: React.FC = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<OrderLookup | null>(null);
  const [receipt, setReceipt] = useState<OrderLookup | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const lookup = async () => {
    if (!query.trim()) return;
    setLoading(true); setError(''); setResult(null); setReceipt(null);
    try {
      const res = await apiClient.get<OrderLookup>(
        `/api/order/lookup?id=${encodeURIComponent(query.trim())}`,
        { silent: true }
      );
      if (res.data.found) {
        setResult(res.data);
        // Also try to fetch receipt
        try {
          const rRes = await apiClient.get<OrderLookup>(
            `/api/order/receipt?id=${encodeURIComponent(query.trim())}`,
            { silent: true }
          );
          if (rRes.data.found && rRes.data.status === 'completed') setReceipt(rRes.data);
        } catch {
          /* receipt is optional */
        }
      } else {
        setError(res.data.message || 'Order not found');
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to connect to server'));
    } finally {
      setLoading(false);
    }
  };

  const shortWallet = (w?: string) => w ? `${w.slice(0, 8)}...${w.slice(-6)}` : 'N/A';

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Search className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Order Status</h1>
          <p className="text-muted-foreground text-sm">Search by Order ID or TrxID</p>
        </div>
      </div>

      <Card className="border-primary/10">
        <CardContent className="p-4">
          <div className="flex gap-2">
            <Input
              placeholder="ORD-XXXXXX or TrxID..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && lookup()}
              className="font-mono"
            />
            <Button onClick={lookup} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-destructive/30">
          <CardContent className="py-6 text-center text-destructive">{error}</CardContent>
        </Card>
      )}

      {result && (
        <Card className="border-primary/10">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <NetworkLogo id={result.network} size={20} />
                {NETWORK_MAP[result.network]?.name || result.network}
              </CardTitle>
              <Badge variant={result.status === 'completed' ? 'default' : result.status === 'pending' ? 'secondary' : 'destructive'}>
                {result.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {result.order_id && <div className="flex justify-between"><span className="text-muted-foreground">Order ID</span><span className="font-mono">{result.order_id}</span></div>}
            {result.trx_id && <div className="flex justify-between"><span className="text-muted-foreground">TrxID</span><span className="font-mono text-xs">{result.trx_id}</span></div>}
            {result.amount_bdt && <div className="flex justify-between"><span className="text-muted-foreground">Amount (BDT)</span><span className="font-bold">৳{result.amount_bdt}</span></div>}
            {result.amount_crypto && <div className="flex justify-between"><span className="text-muted-foreground">Crypto</span><span className="font-mono">{result.amount_crypto} {NETWORK_MAP[result.network]?.asset || ''}</span></div>}
            {result.wallet && <div className="flex justify-between"><span className="text-muted-foreground">Wallet</span><span className="font-mono text-xs">{shortWallet(result.wallet)}</span></div>}
            {result.sig && <div className="flex justify-between"><span className="text-muted-foreground">TX Hash</span><span className="font-mono text-xs">{result.sig.slice(0, 16)}...</span></div>}
            {result.created_at && <div className="flex justify-between"><span className="text-muted-foreground">Date</span><span>{result.created_at?.slice(0, 16)}</span></div>}
          </CardContent>
        </Card>
      )}

      {receipt && (
        <Card className="border-success/20 bg-success/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-4 w-4 text-success" /> Receipt
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Order</span><span className="font-mono">{receipt.order_id}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Amount</span><span className="font-mono">{receipt.amount_crypto} {NETWORK_MAP[receipt.network]?.asset || ''}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Network</span><span>{NETWORK_MAP[receipt.network]?.name || receipt.network}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Wallet</span><span className="font-mono text-xs">{shortWallet(receipt.wallet)}</span></div>
            {receipt.sig && <div className="flex justify-between"><span className="text-muted-foreground">TX Hash</span><span className="font-mono text-xs break-all">{receipt.sig}</span></div>}
            <div className="flex justify-between"><span className="text-muted-foreground">Date</span><span>{receipt.created_at?.slice(0, 16)}</span></div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default OrderStatus;
