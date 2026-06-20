import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Search, Loader2, FileText } from 'lucide-react';
import { NetworkLogo, NETWORK_MAP } from '../constants/networks';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import { PageHeader, StatusBadge, CopyButton, RelativeTime, TexturePanel } from '../components/common';

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
      <PageHeader
        icon={<Search className="h-7 w-7" />}
        title="Order Status"
        description="Search by Order ID or TrxID"
        breadcrumbs={[
          { label: 'Orders', to: '/orders' },
          { label: 'Status' },
        ]}
      />

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
              <StatusBadge status={result.status ?? ''} />
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {result.order_id && <div className="flex items-center justify-between gap-2"><span className="text-muted-foreground">Order ID</span><span className="inline-flex items-center gap-1.5 font-mono">{result.order_id}<CopyButton value={result.order_id} label="Copy order ID" /></span></div>}
            {result.trx_id && <div className="flex justify-between gap-2"><span className="text-muted-foreground">TrxID</span><span className="font-mono text-xs">{result.trx_id}</span></div>}
            {result.amount_bdt && <div className="flex justify-between gap-2"><span className="text-muted-foreground">Amount (BDT)</span><span className="num font-bold">৳{result.amount_bdt}</span></div>}
            {result.amount_crypto && <div className="flex justify-between gap-2"><span className="text-muted-foreground">Crypto</span><span className="num">{result.amount_crypto} {NETWORK_MAP[result.network]?.asset || ''}</span></div>}
            {result.wallet && <div className="flex justify-between gap-2"><span className="text-muted-foreground">Wallet</span><span className="font-mono text-xs">{shortWallet(result.wallet)}</span></div>}
            {result.sig && <div className="flex justify-between gap-2"><span className="text-muted-foreground">TX Hash</span><span className="font-mono text-xs">{result.sig.slice(0, 16)}...</span></div>}
            {result.created_at && <div className="flex justify-between gap-2"><span className="text-muted-foreground">Date</span><RelativeTime value={result.created_at} /></div>}
          </CardContent>
        </Card>
      )}

      {receipt && (
        <TexturePanel variant="success" texture="dots-fine" glow scanline accentTop className="border-success/30">
          <div className="p-5 sm:p-6">
            <div className="flex items-center gap-2 pb-3 mb-1">
              <FileText className="h-4 w-4 text-success drop-shadow-[0_0_8px_hsl(var(--success)/0.6)]" />
              <span className="text-base font-semibold tracking-tight">Receipt</span>
              <span className="live-dot ml-1" />
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between gap-2"><span className="text-muted-foreground">Order</span><span className="inline-flex items-center gap-1.5 font-mono">{receipt.order_id}<CopyButton value={receipt.order_id} label="Copy order ID" /></span></div>
              <div className="flex justify-between gap-2"><span className="text-muted-foreground">Amount</span><span className="num">{receipt.amount_crypto} {NETWORK_MAP[receipt.network]?.asset || ''}</span></div>
              <div className="flex justify-between gap-2"><span className="text-muted-foreground">Network</span><span>{NETWORK_MAP[receipt.network]?.name || receipt.network}</span></div>
              <div className="flex justify-between gap-2"><span className="text-muted-foreground">Wallet</span><span className="font-mono text-xs">{shortWallet(receipt.wallet)}</span></div>
              {receipt.sig && <div className="flex items-start justify-between gap-2"><span className="text-muted-foreground shrink-0">TX Hash</span><span className="inline-flex items-center gap-1.5 font-mono text-xs break-all text-right">{receipt.sig.slice(0, 18)}…<CopyButton value={receipt.sig} label="Copy tx hash" /></span></div>}
              <div className="flex justify-between gap-2"><span className="text-muted-foreground">Date</span><RelativeTime value={receipt.created_at} /></div>
            </div>
          </div>
        </TexturePanel>
      )}
    </div>
  );
};

export default OrderStatus;
