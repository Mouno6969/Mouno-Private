import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Search, Loader2, FileText, CheckCircle, Clock, ArrowRight, ExternalLink, HelpCircle, AlertCircle, Shield } from 'lucide-react';
import { NetworkLogo, NETWORK_MAP } from '../constants/networks';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import { PageHeader, TexturePanel, CopyButton } from '../components/common';
import { Link } from 'react-router-dom';

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

const TIMELINE_STEPS = ['Order Placed', 'Payment Verified', 'Crypto Sent', 'Completed'];

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

  const getTimelineStep = (status?: string) => {
    switch (status) {
      case 'completed': return 4;
      case 'sent': return 3;
      case 'verified': return 2;
      case 'pending': return 1;
      default: return 0;
    }
  };

  const currentStep = getTimelineStep(result?.status);

  return (
    <div className="max-w-5xl mx-auto space-y-4 sm:space-y-6 px-1 sm:px-0 animate-in fade-in duration-300">
      <PageHeader
        icon={<Search className="h-7 w-7" />}
        eyebrow="Track"
        title="Order Status"
        description="Search by Order ID or bKash TrxID to track your order."
        breadcrumbs={[
          { label: 'Orders', to: '/orders' },
          { label: 'Status' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 items-start">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-5">
          {/* Search Card */}
          <TexturePanel variant="primary" accentTop>
            <div className="p-5 sm:p-6 space-y-4">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                  <Input
                    placeholder="ORD-XXXXXX or TrxID..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && lookup()}
                    className="pl-10 h-12 font-mono text-sm"
                  />
                </div>
                <Button onClick={lookup} disabled={loading} className="h-12 px-6 font-bold rounded-xl">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Search</>}
                </Button>
              </div>
            </div>
          </TexturePanel>

          {/* Error State */}
          {error && (
            <Card className="border-destructive/30 bg-destructive/5">
              <CardContent className="py-6 flex items-center justify-center gap-3">
                <AlertCircle className="h-5 w-5 text-destructive" />
                <span className="text-destructive font-medium">{error}</span>
              </CardContent>
            </Card>
          )}

          {/* Order Result */}
          {result && (
            <Card className="border-primary/15 shadow-lg overflow-hidden animate-in slide-in-from-top-2 duration-200">
              <CardContent className="p-5 sm:p-6 space-y-5">
                {/* Header Row */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <NetworkLogo id={result.network} size={28} />
                    <span className="font-bold">{NETWORK_MAP[result.network]?.name || result.network} Network</span>
                  </div>
                  <Badge
                    variant={result.status === 'completed' ? 'success' : result.status === 'pending' ? 'warning' : 'secondary'}
                    className="gap-1"
                  >
                    {result.status === 'completed' && <CheckCircle className="h-3 w-3" />}
                    {result.status === 'pending' && <Clock className="h-3 w-3" />}
                    {result.status}
                  </Badge>
                </div>

                {/* Details Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {result.order_id && (
                    <div className="p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40">
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Order ID</p>
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-sm">{result.order_id}</span>
                        <CopyButton value={result.order_id} label="Copy Order ID" />
                      </div>
                    </div>
                  )}
                  {result.trx_id && (
                    <div className="p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40">
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">TrxID</p>
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-sm">{result.trx_id}</span>
                        <CopyButton value={result.trx_id} label="Copy TrxID" />
                      </div>
                    </div>
                  )}
                  {result.amount_bdt && (
                    <div className="p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40">
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Amount (BDT)</p>
                      <span className="text-lg font-extrabold">৳{result.amount_bdt.toLocaleString()}</span>
                    </div>
                  )}
                  {result.amount_crypto && (
                    <div className="p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40">
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Crypto Received</p>
                      <span className="text-lg font-extrabold text-primary">{result.amount_crypto} {NETWORK_MAP[result.network]?.asset || ''}</span>
                    </div>
                  )}
                  {result.wallet && (
                    <div className="p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40">
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Wallet</p>
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs">{shortWallet(result.wallet)}</span>
                        <CopyButton value={result.wallet} label="Copy wallet" />
                      </div>
                    </div>
                  )}
                  {result.created_at && (
                    <div className="p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40">
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Date</p>
                      <span className="text-sm font-medium">{result.created_at?.slice(0, 16)}</span>
                    </div>
                  )}
                </div>

                {/* Timeline */}
                <div className="pt-4 border-t border-border/50 overflow-x-auto">
                  <div className="flex items-center justify-between min-w-[280px]">
                    {TIMELINE_STEPS.map((step, i) => {
                      const isCompleted = i < currentStep;
                      const isCurrent = i === currentStep - 1;
                      return (
                        <React.Fragment key={step}>
                          <div className="flex flex-col items-center gap-1">
                            <div className={`w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-[10px] sm:text-xs font-bold transition-all ${
                              isCompleted ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                            } ${isCurrent ? 'ring-2 ring-primary ring-offset-2 ring-offset-background' : ''}`}>
                              {isCompleted ? <CheckCircle className="h-3 w-3 sm:h-3.5 sm:w-3.5" /> : i + 1}
                            </div>
                            <span className={`text-[8px] sm:text-[9px] text-center max-w-[50px] sm:max-w-[60px] leading-tight ${isCompleted ? 'text-primary font-medium' : 'text-muted-foreground'}`}>
                              {step}
                            </span>
                          </div>
                          {i < TIMELINE_STEPS.length - 1 && (
                            <div className={`flex-1 h-0.5 mx-0.5 sm:mx-1 rounded-full ${i < currentStep - 1 ? 'bg-primary' : 'bg-muted'}`} />
                          )}
                        </React.Fragment>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Receipt */}
          {receipt && (
            <Card className="border-success/20 bg-success/5 animate-in slide-in-from-top-2 duration-200">
              <CardContent className="p-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-success/10 rounded-lg">
                      <CheckCircle className="h-5 w-5 text-success" />
                    </div>
                    <div>
                      <h3 className="font-bold">Transaction Receipt</h3>
                      <p className="text-xs text-muted-foreground">Your transaction was completed successfully.</p>
                    </div>
                  </div>
                </div>
                {receipt.sig && (
                  <div className="p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">TX Hash</p>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs break-all flex-1">{receipt.sig}</span>
                      <CopyButton value={receipt.sig} label="Copy TX Hash" />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Empty state when nothing searched yet */}
          {!result && !error && !loading && (
            <Card className="border-border/50">
              <CardContent className="py-12 text-center">
                <Search className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground font-medium">Enter an Order ID or TrxID to track your order</p>
                <p className="text-xs text-muted-foreground mt-1">You can find your Order ID in the confirmation message or your order history.</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Need Help */}
          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <HelpCircle className="h-4 w-4 text-primary" /> Need Help?
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
                  <Clock className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="text-xs font-medium">Order taking too long?</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">Some transactions may take longer due to network congestion.</p>
                    <Link to="/support" className="text-[10px] text-primary hover:underline mt-1 inline-flex items-center gap-1">
                      Contact Support <ArrowRight className="h-2.5 w-2.5" />
                    </Link>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
                  <AlertCircle className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="text-xs font-medium">Wrong status?</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">Check our troubleshooting guide for common issues.</p>
                    <Link to="/guide" className="text-[10px] text-primary hover:underline mt-1 inline-flex items-center gap-1">
                      View Guide <ArrowRight className="h-2.5 w-2.5" />
                    </Link>
                  </div>
                </div>
              </div>
              <Link to="/support" className="block">
                <Button variant="outline" className="w-full font-semibold text-sm">
                  <HelpCircle className="mr-2 h-4 w-4" /> Contact Support
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Safety Reminder */}
          <Card className="border-primary/10">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-primary/10 rounded-lg shrink-0">
                  <Shield className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-xs font-bold">Safety Reminder</p>
                  <p className="text-[10px] text-muted-foreground mt-1 leading-relaxed">
                    BGC Crypto will never ask for your password or 2FA code. Stay safe and trade securely.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default OrderStatus;
