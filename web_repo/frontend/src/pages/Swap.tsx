import React, { useState } from 'react';
import { RefreshCw, Shuffle, Target, CalendarClock, Layers } from 'lucide-react';
import CrossChainBridge from '../components/swap/CrossChainBridge';
import MultiLegSwap from '../components/swap/MultiLegSwap';
import LimitOrders from '../components/swap/LimitOrders';
import ScheduledBuy from '../components/swap/ScheduledBuy';

type TabId = 'bridge' | 'multi-leg' | 'limit' | 'schedule';

const TABS: { id: TabId; label: string; icon: React.ReactNode; desc: string }[] = [
  { id: 'multi-leg', label: 'Multi-Leg Swap', icon: <Shuffle className="h-4 w-4" />, desc: 'Convert one asset directly into another (e.g. BTC → ETH).' },
  { id: 'limit', label: 'Limit Orders', icon: <Target className="h-4 w-4" />, desc: 'Auto-buy or sell when the price hits your target.' },
  { id: 'schedule', label: 'Buy on Schedule', icon: <CalendarClock className="h-4 w-4" />, desc: 'Recurring auto-buys — invest a fixed amount on a schedule.' },
  { id: 'bridge', label: 'Cross-Chain Bridge', icon: <RefreshCw className="h-4 w-4" />, desc: 'Move assets across 20+ networks with deep liquidity.' },
];

const Swap: React.FC = () => {
  const [tab, setTab] = useState<TabId>('multi-leg');
  const active = TABS.find((t) => t.id === tab)!;

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      <section className="space-y-1 text-center md:text-left">
        <div className="flex items-center justify-center md:justify-start gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Layers className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Trade & Automate</h1>
        </div>
        <p className="text-muted-foreground">{active.desc}</p>
      </section>

      {/* Tab navigation */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 p-1.5 rounded-2xl bg-muted/40 border border-muted">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`flex items-center justify-center gap-2 h-12 rounded-xl text-xs md:text-sm font-bold transition-all ${
              tab === t.id
                ? 'bg-primary/15 text-primary ring-1 ring-primary/40 shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {t.icon}
            <span className="truncate">{t.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {tab === 'bridge' && <CrossChainBridge />}
        {tab === 'multi-leg' && <MultiLegSwap />}
        {tab === 'limit' && <LimitOrders />}
        {tab === 'schedule' && <ScheduledBuy />}
      </div>
    </div>
  );
};

export default Swap;
