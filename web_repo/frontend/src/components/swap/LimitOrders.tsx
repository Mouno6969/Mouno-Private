import React, { useState, useMemo } from 'react';
import axios from 'axios';
import { Target, TrendingUp, TrendingDown, Info, Trash2, Clock, ShieldCheck } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import TokenSelect, { TokenLogo } from './TokenSelect';
import { TOKEN_PRICE_USD } from '../../constants/tokens';

const Loader2 = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
);

interface LimitOrder {
  id: string;
  side: 'buy' | 'sell';
  asset: string;
  targetPrice: string;
  amountBdt: string;
  createdAt: number;
}

const LimitOrders: React.FC = () => {
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [asset, setAsset] = useState('BTC');
  const [targetPrice, setTargetPrice] = useState('');
  const [amountBdt, setAmountBdt] = useState('');
  const [loading, setLoading] = useState(false);
  const [orders, setOrders] = useState<LimitOrder[]>([]);

  const marketPrice = TOKEN_PRICE_USD[asset] || 0;
  const target = parseFloat(targetPrice) || 0;
  const diffPct = useMemo(() => {
    if (!target || !marketPrice) return 0;
    return ((target - marketPrice) / marketPrice) * 100;
  }, [target, marketPrice]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetPrice || !amountBdt) return;
    setLoading(true);
    const order: LimitOrder = {
      id: Math.random().toString(36).slice(2, 8).toUpperCase(),
      side,
      asset,
      targetPrice,
      amountBdt,
      createdAt: Date.now(),
    };
    try {
      await axios.post(`${process.env.REACT_APP_API_URL || ''}/api/orders/limit`, order);
    } catch (err) {
      console.error(err);
    } finally {
      setOrders((prev) => [order, ...prev]);
      setTargetPrice('');
      setAmountBdt('');
      setLoading(false);
    }
  };

  const cancelOrder = (id: string) => {
    setOrders((prev) => prev.filter((o) => o.id !== id));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
      <div className="lg:col-span-3 space-y-6">
        <form onSubmit={handleSubmit}>
          <Card className="shadow-2xl border-primary/10 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/50 via-primary to-primary/50"></div>
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Create Limit Order</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Buy / Sell toggle */}
              <div className="grid grid-cols-2 gap-2 p-1 rounded-xl bg-muted/40 border border-muted">
                <button
                  type="button"
                  onClick={() => setSide('buy')}
                  className={`flex items-center justify-center gap-2 h-11 rounded-lg font-bold text-sm transition-all ${side === 'buy' ? 'bg-green-500/15 text-green-500 ring-1 ring-green-500/40' : 'text-muted-foreground'}`}
                >
                  <TrendingUp className="h-4 w-4" /> Buy When
                </button>
                <button
                  type="button"
                  onClick={() => setSide('sell')}
                  className={`flex items-center justify-center gap-2 h-11 rounded-lg font-bold text-sm transition-all ${side === 'sell' ? 'bg-red-500/15 text-red-500 ring-1 ring-red-500/40' : 'text-muted-foreground'}`}
                >
                  <TrendingDown className="h-4 w-4" /> Sell When
                </button>
              </div>

              {/* Asset */}
              <div className="space-y-3">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Asset</Label>
                <TokenSelect value={asset} onChange={setAsset} className="w-full" />
                <p className="text-[11px] text-muted-foreground">
                  Current market price: <span className="font-mono font-bold text-foreground">${marketPrice.toLocaleString()}</span>
                </p>
              </div>

              {/* Target price */}
              <div className="space-y-3">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Trigger Price (USD)</Label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground font-bold font-mono">$</span>
                  <Input
                    type="number"
                    className="pl-9 h-14 text-xl font-bold font-mono bg-muted/20"
                    placeholder={side === 'buy' ? 'e.g. 50000' : 'e.g. 75000'}
                    value={targetPrice}
                    onChange={(e) => setTargetPrice(e.target.value)}
                    required
                  />
                </div>
                {target > 0 && (
                  <p className={`text-[11px] font-bold ${diffPct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {diffPct >= 0 ? '▲' : '▼'} {Math.abs(diffPct).toFixed(2)}% {diffPct >= 0 ? 'above' : 'below'} current price
                  </p>
                )}
              </div>

              {/* Amount */}
              <div className="space-y-3">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Amount to {side === 'buy' ? 'Spend' : 'Sell'} (BDT)</Label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground font-bold font-mono">৳</span>
                  <Input
                    type="number"
                    className="pl-9 h-14 text-xl font-bold font-mono bg-muted/20"
                    placeholder="Min 500"
                    value={amountBdt}
                    onChange={(e) => setAmountBdt(e.target.value)}
                    required
                  />
                </div>
              </div>

              <Alert className="bg-amber-500/5 border-amber-500/20">
                <Info className="h-4 w-4 text-amber-400" />
                <AlertDescription className="text-xs text-muted-foreground">
                  Your order executes automatically the moment {asset} {side === 'buy' ? 'drops to' : 'rises to'} your trigger price. No need to watch the charts.
                </AlertDescription>
              </Alert>
            </CardContent>
            <CardFooter>
              <Button
                type="submit"
                disabled={loading || !targetPrice || !amountBdt}
                className="w-full h-14 text-lg font-black rounded-2xl shadow-xl shadow-primary/20"
              >
                {loading ? (
                  <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Placing Order...</>
                ) : (
                  <>Set {side === 'buy' ? 'Buy' : 'Sell'} Limit Order</>
                )}
              </Button>
            </CardFooter>
          </Card>
        </form>
      </div>

      {/* Active orders */}
      <div className="lg:col-span-2 space-y-6">
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" /> Active Limit Orders
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {orders.length === 0 ? (
              <div className="text-center py-8">
                <Target className="h-8 w-8 text-muted-foreground/30 mx-auto mb-3" />
                <p className="text-xs text-muted-foreground">No active limit orders yet. Create one to automate your entries.</p>
              </div>
            ) : (
              orders.map((o) => (
                <div key={o.id} className="p-4 rounded-xl border border-muted bg-muted/20 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 font-bold text-sm">
                      <TokenLogo symbol={o.asset} size={18} /> {o.asset}
                      <Badge variant="outline" className={`text-[9px] ${o.side === 'buy' ? 'text-green-500 border-green-500/30' : 'text-red-500 border-red-500/30'}`}>
                        {o.side.toUpperCase()}
                      </Badge>
                    </span>
                    <button onClick={() => cancelOrder(o.id)} className="text-muted-foreground hover:text-destructive transition-colors" aria-label="Cancel order">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Trigger</span>
                    <span className="font-mono font-bold">${parseFloat(o.targetPrice).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Amount</span>
                    <span className="font-mono font-bold">৳{parseFloat(o.amountBdt).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-1 text-[10px] text-amber-500 font-bold uppercase pt-1">
                    <Clock className="h-3 w-3" /> Waiting for trigger
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
        <Alert className="bg-blue-500/5 border-blue-500/10">
          <ShieldCheck className="h-4 w-4 text-blue-400" />
          <AlertDescription className="text-xs text-muted-foreground">
            Limit orders are monitored 24/7. We notify you on Telegram the instant your order fills.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
};

export default LimitOrders;
