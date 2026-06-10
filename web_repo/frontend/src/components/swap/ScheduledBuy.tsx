import React, { useState, useMemo } from 'react';
import axios from 'axios';
import { CalendarClock, Repeat, Info, Trash2, Pause, Play, TrendingUp, ShieldCheck } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import TokenSelect, { TokenLogo } from './TokenSelect';

const Loader2 = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
);

type Frequency = 'daily' | 'weekly' | 'monthly';

const FREQUENCIES: { id: Frequency; label: string; perYear: number }[] = [
  { id: 'daily', label: 'Daily', perYear: 365 },
  { id: 'weekly', label: 'Weekly', perYear: 52 },
  { id: 'monthly', label: 'Monthly', perYear: 12 },
];

interface SchedulePlan {
  id: string;
  asset: string;
  amountBdt: string;
  frequency: Frequency;
  active: boolean;
  createdAt: number;
}

const ScheduledBuy: React.FC = () => {
  const [asset, setAsset] = useState('BTC');
  const [amountBdt, setAmountBdt] = useState('');
  const [frequency, setFrequency] = useState<Frequency>('weekly');
  const [loading, setLoading] = useState(false);
  const [plans, setPlans] = useState<SchedulePlan[]>([]);

  const yearlyProjection = useMemo(() => {
    const amt = parseFloat(amountBdt) || 0;
    const freq = FREQUENCIES.find((f) => f.id === frequency);
    return amt * (freq?.perYear || 0);
  }, [amountBdt, frequency]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amountBdt) return;
    setLoading(true);
    const plan: SchedulePlan = {
      id: Math.random().toString(36).slice(2, 8).toUpperCase(),
      asset,
      amountBdt,
      frequency,
      active: true,
      createdAt: Date.now(),
    };
    try {
      await axios.post(`${process.env.REACT_APP_API_URL || ''}/api/buy/schedule`, plan);
    } catch (err) {
      console.error(err);
    } finally {
      setPlans((prev) => [plan, ...prev]);
      setAmountBdt('');
      setLoading(false);
    }
  };

  const togglePlan = (id: string) => {
    setPlans((prev) => prev.map((p) => (p.id === id ? { ...p, active: !p.active } : p)));
  };

  const removePlan = (id: string) => {
    setPlans((prev) => prev.filter((p) => p.id !== id));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
      <div className="lg:col-span-3 space-y-6">
        <form onSubmit={handleSubmit}>
          <Card className="shadow-2xl border-primary/10 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/50 via-primary to-primary/50"></div>
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Set Up Recurring Buy</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Asset */}
              <div className="space-y-3">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Asset to Buy</Label>
                <TokenSelect value={asset} onChange={setAsset} className="w-full" />
              </div>

              {/* Amount */}
              <div className="space-y-3">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Amount per Buy (BDT)</Label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground font-bold font-mono">৳</span>
                  <Input
                    type="number"
                    className="pl-9 h-14 text-xl font-bold font-mono bg-muted/20"
                    placeholder="e.g. 1000"
                    value={amountBdt}
                    onChange={(e) => setAmountBdt(e.target.value)}
                    required
                  />
                </div>
              </div>

              {/* Frequency */}
              <div className="space-y-3">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Frequency</Label>
                <div className="grid grid-cols-3 gap-2 p-1 rounded-xl bg-muted/40 border border-muted">
                  {FREQUENCIES.map((f) => (
                    <button
                      key={f.id}
                      type="button"
                      onClick={() => setFrequency(f.id)}
                      className={`h-11 rounded-lg font-bold text-sm transition-all ${frequency === f.id ? 'bg-primary/15 text-primary ring-1 ring-primary/40' : 'text-muted-foreground'}`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {yearlyProjection > 0 && (
                <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 flex items-center justify-between animate-in slide-in-from-top-2 duration-300">
                  <span className="flex items-center gap-2 text-xs font-bold uppercase text-muted-foreground tracking-tighter">
                    <TrendingUp className="h-4 w-4 text-primary" /> Yearly Investment
                  </span>
                  <span className="font-mono font-black text-primary text-lg">৳{yearlyProjection.toLocaleString()}</span>
                </div>
              )}

              <Alert className="bg-amber-500/5 border-amber-500/20">
                <Info className="h-4 w-4 text-amber-400" />
                <AlertDescription className="text-xs text-muted-foreground">
                  We automatically buy {asset} {frequency} using your wallet balance. This is dollar-cost averaging — invest steadily without timing the market.
                </AlertDescription>
              </Alert>
            </CardContent>
            <CardFooter>
              <Button
                type="submit"
                disabled={loading || !amountBdt}
                className="w-full h-14 text-lg font-black rounded-2xl shadow-xl shadow-primary/20"
              >
                {loading ? (
                  <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Activating Plan...</>
                ) : (
                  <><Repeat className="mr-2 h-5 w-5" /> Start Auto-Buy Plan</>
                )}
              </Button>
            </CardFooter>
          </Card>
        </form>
      </div>

      {/* Active plans */}
      <div className="lg:col-span-2 space-y-6">
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <CalendarClock className="h-4 w-4 text-primary" /> Your Auto-Buy Plans
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {plans.length === 0 ? (
              <div className="text-center py-8">
                <Repeat className="h-8 w-8 text-muted-foreground/30 mx-auto mb-3" />
                <p className="text-xs text-muted-foreground">No recurring plans yet. Automate your investing to build wealth over time.</p>
              </div>
            ) : (
              plans.map((p) => (
                <div key={p.id} className={`p-4 rounded-xl border space-y-2 ${p.active ? 'border-primary/20 bg-muted/20' : 'border-muted bg-muted/10 opacity-60'}`}>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 font-bold text-sm">
                      <TokenLogo symbol={p.asset} size={18} /> {p.asset}
                      <Badge variant="outline" className="text-[9px] capitalize text-primary border-primary/30">{p.frequency}</Badge>
                    </span>
                    <div className="flex items-center gap-1">
                      <button onClick={() => togglePlan(p.id)} className="text-muted-foreground hover:text-primary transition-colors p-1" aria-label={p.active ? 'Pause plan' : 'Resume plan'}>
                        {p.active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                      </button>
                      <button onClick={() => removePlan(p.id)} className="text-muted-foreground hover:text-destructive transition-colors p-1" aria-label="Delete plan">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Amount</span>
                    <span className="font-mono font-bold">৳{parseFloat(p.amountBdt).toLocaleString()} / {p.frequency.replace('ly', '')}</span>
                  </div>
                  <div className={`flex items-center gap-1 text-[10px] font-bold uppercase pt-1 ${p.active ? 'text-green-500' : 'text-muted-foreground'}`}>
                    {p.active ? <><Play className="h-3 w-3" /> Active</> : <><Pause className="h-3 w-3" /> Paused</>}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
        <Alert className="bg-blue-500/5 border-blue-500/10">
          <ShieldCheck className="h-4 w-4 text-blue-400" />
          <AlertDescription className="text-xs text-muted-foreground">
            Pause or cancel anytime. Each automated buy uses the best live rate at execution.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
};

export default ScheduledBuy;
