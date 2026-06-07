import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { TrendingUp, Zap, ArrowRight, ShieldCheck, Users, Gift, Store, Layers, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import Marquee from '../components/ui/marquee';
import { Badge } from '../components/ui/badge';
import { BkashLogo, LifiLogo } from '../components/ui/brand-logos';
import { Link } from 'react-router-dom';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [marketData, setMarketData] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    const controller = new AbortController();

    const fetchData = async () => {
      // Fetch market data (critical)
      try {
        const res = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/market`, { signal: controller.signal });
        if (!controller.signal.aborted) {
          setMarketData(res.data);
          setLastUpdated(new Date());
        }
      } catch (err) {
        if (!axios.isCancel(err)) console.error("Market fetch failed", err);
      }

      // Fetch global stats (optional)
      try {
        const res = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/stats`, { signal: controller.signal });
        if (!controller.signal.aborted) setStats(res.data);
      } catch (err) {
        if (!axios.isCancel(err)) console.error("Stats fetch failed", err);
      }

      // Fetch recent activity (optional)
      try {
        const res = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/recent-activity`, { signal: controller.signal });
        if (!controller.signal.aborted) setRecentActivity(res.data);
      } catch (err) {
        if (!axios.isCancel(err)) console.error("Activity fetch failed", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000); // Update every 10 seconds
    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, []);

  const networks = NETWORK_LIST;

  const formatActivityStatus = (status?: string) => {
    const map: Record<string, string> = {
      completed: 'fulfilled',
      pending: 'pending',
      processing: 'processing',
      failed: 'failed',
      cancelled: 'cancelled',
    };
    if (!status) return 'pending';
    return map[status] || status.charAt(0).toUpperCase() + status.slice(1);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Top Marquee 1: Latest transactions / news ticker */}
      <Marquee
        speed={35}
        containerClassName="bg-muted/40 border-y border-white/10 py-1.5 -mx-3 sm:-mx-5 lg:-mx-8"
        className="text-xs"
      >
        <span className="flex items-center gap-1.5 px-2">
          <span className="font-bold text-primary">Latest:</span>
          {recentActivity.length > 0 ? (
            recentActivity.slice(0, 6).map((act, i) => (
              <span key={i} className="text-muted-foreground">
                {act.amount_crypto} {act.network?.toUpperCase()} {formatActivityStatus(act.status)}
                {i < 5 ? '  •  ' : ''}
              </span>
            ))
          ) : (
            <>
              <span className="text-muted-foreground">15 ETH swapped on Solana</span>
              <span className="text-muted-foreground">•  500 USDT bought via bKash</span>
              <span className="text-muted-foreground">•  Order #349 fulfilled</span>
            </>
          )}
        </span>
      </Marquee>

      {/* Top Marquee 2: Live status ticker */}
      <Marquee
        speed={30}
        containerClassName="bg-green-500/5 border-y border-green-500/15 py-1 -mx-3 sm:-mx-5 lg:-mx-8 !mt-0"
        className="font-mono text-[10px] uppercase tracking-[0.2em] text-green-500"
      >
        <span className="flex items-center gap-2">▸ LIVE</span>
        <span className="flex items-center gap-2">▸ CROSS-CHAIN SWAPS ACTIVE</span>
        <span className="flex items-center gap-2">▸ SECURE P2P SETTLEMENT</span>
        <span className="flex items-center gap-2">▸ {stats?.total_users || '42'} ONBOARDINGS ONLINE</span>
        <span className="flex items-center gap-2">▸ LIFI PROTOCOL INTEGRATED</span>
        <span className="flex items-center gap-2">▸ 24/7 AUTOMATED DELIVERY</span>
        <span className="flex items-center gap-2">▸ AI ONBOARDING ONLINE</span>
      </Marquee>

      <section className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold tracking-tight lg:text-4xl">
            {t('welcome')}, <span className="text-primary">{user ? user.username : 'Guest'}</span>!
          </h1>
          <p className="text-muted-foreground">Manage your crypto assets across all major networks.</p>
        </div>
        <div className="flex flex-col items-end gap-1">
           <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20 px-3 py-1">
             <div className="mr-2 h-2 w-2 rounded-full bg-green-500 animate-pulse" />
             System: Online
           </Badge>
           <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
             Refreshed: {lastUpdated.toLocaleTimeString()}
           </span>
        </div>
      </section>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-3 sm:p-4 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="p-2 bg-muted text-foreground rounded-lg shrink-0">
                <TrendingUp className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] font-medium text-muted-foreground truncate">Live Rates</p>
                <p className="text-base sm:text-lg font-bold tracking-tight truncate">৳{marketData?.rates?.solana || '...'}</p>
              </div>
            </div>
            <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center shrink-0">
              {user ? (
                <span className="font-mono text-xs font-bold">{user.username?.[0]?.toUpperCase() || 'U'}</span>
              ) : (
                <UserIcon className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-3 sm:p-4 flex items-center gap-2.5">
            <div className="p-2 bg-muted text-muted-foreground rounded-lg shrink-0">
              <Zap className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-medium text-muted-foreground truncate">Network</p>
              <p className="text-base sm:text-lg font-bold tracking-tight truncate">Healthy</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-3 sm:p-4 flex items-center gap-2.5">
            <div className="p-2 bg-muted text-muted-foreground rounded-lg shrink-0">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-medium text-muted-foreground truncate">Security</p>
              <p className="text-base sm:text-lg font-bold tracking-tight truncate">{user ? user.username : 'Guest'}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-3 sm:p-4 flex items-center gap-2.5">
            <div className="p-2 bg-muted text-muted-foreground rounded-lg shrink-0">
              <Layers className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-medium text-muted-foreground truncate">Assets</p>
              <p className="text-base sm:text-lg font-bold tracking-tight truncate">Multi-Chain</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Area */}
      <div className="space-y-6">
        {/* Market Table - full width */}
        <Card className="overflow-hidden shadow-xl border-primary/10">
          <CardHeader className="bg-muted/30 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" /> {t('rates')}
                </CardTitle>
                <CardDescription>Live BDT conversion rates for stablecoins</CardDescription>
              </div>
              <Badge variant="secondary" className="font-mono uppercase text-[10px]">Real-time</Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-muted/50">
                    <TableHead className="w-[160px] pl-4 sm:pl-6 font-semibold uppercase text-[10px] tracking-wider">Network</TableHead>
                    <TableHead className="font-semibold uppercase text-[10px] tracking-wider">Asset</TableHead>
                    <TableHead className="text-right font-semibold uppercase text-[10px] tracking-wider">Market Cap</TableHead>
                    <TableHead className="text-right font-semibold uppercase text-[10px] tracking-wider whitespace-nowrap">Rate (1 USDT/USDC)</TableHead>
                    <TableHead className="text-right pr-4 sm:pr-6 font-semibold uppercase text-[10px] tracking-wider whitespace-nowrap">Rate (1 USDT/USDC)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {networks.map((net, idx) => {
                    const rate = marketData?.rates?.[net.id];
                    const change = marketData?.changes?.[net.id];
                    const marketCap = marketData?.market_caps?.[net.id];
                    const hasNumericChange = typeof change === 'number' && Number.isFinite(change);
                    const isUp = hasNumericChange ? change >= 0 : idx % 3 !== 1;
                    return (
                      <TableRow key={net.id} className="group hover:bg-primary/5 transition-colors">
                        <TableCell className="py-3.5 pl-4 sm:pl-6">
                          <div className="flex items-center gap-2.5">
                            <NetworkLogo id={net.id} size={24} />
                            <span className="font-semibold text-sm">{net.name}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="font-mono text-[9px] px-1.5">USDT/USDC</Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs text-muted-foreground whitespace-nowrap">
                          ৳{marketCap ? Number(marketCap).toLocaleString() : '...'}
                        </TableCell>
                        <TableCell className="py-3.5 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-2">
                            <span className="font-mono text-sm font-bold text-foreground">৳{rate || '...'}</span>
                            {hasNumericChange && (
                              <Badge
                                className={`text-[9px] h-4 px-1 font-mono border-0 ${isUp ? 'bg-green-500/15 text-green-500' : 'bg-red-500/15 text-red-500'}`}
                              >
                                {isUp ? '▲' : '▼'} {Math.abs(change).toFixed(3)}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="py-3.5 text-right pr-4 sm:pr-6 whitespace-nowrap">
                          <span className="font-mono text-sm font-bold text-primary">৳{rate || '...'}</span>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Buy Crypto */}
        <Card className="bg-card/50 backdrop-blur border-primary/10 overflow-hidden shadow-lg group transition-all hover:border-primary/30">
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1.5">
                <CardTitle className="text-2xl">{t('buy')}</CardTitle>
                <CardDescription className="text-muted-foreground">
                  Purchase USDC or USDT using bKash instantly.
                </CardDescription>
              </div>
              <BkashLogo className="shrink-0 mt-1" />
            </div>
          </CardHeader>
          <CardContent>
            <Button asChild variant="secondary" className="w-full font-bold h-12 shadow-md">
              <Link to="/buy" className="flex items-center gap-2">
                Start Order <ArrowRight size={18} />
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Swap & Bridge */}
        <Card className="bg-card/50 backdrop-blur border-primary/10 overflow-hidden shadow-lg group transition-all hover:border-primary/30">
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1.5">
                <CardTitle className="text-2xl text-foreground">{t('swap')}</CardTitle>
                <CardDescription className="text-muted-foreground">
                  Bridge assets between 20+ chains with LI.FI.
                </CardDescription>
              </div>
              <LifiLogo className="shrink-0 mt-1" />
            </div>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full font-bold h-12 border-primary/30 hover:bg-primary/10">
              <Link to="/swap" className="flex items-center gap-2">
                Launch Bridge <ArrowRight size={18} />
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Quick Action Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="bg-card/50 backdrop-blur hover:border-primary/30 transition-all group">
            <Link to="/referral" className="p-4 flex flex-col items-center text-center gap-2">
              <Users className="text-primary group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium">{t('referral')}</span>
            </Link>
          </Card>
          <Card className="bg-card/50 backdrop-blur hover:border-primary/30 transition-all group">
            <Link to="/gift" className="p-4 flex flex-col items-center text-center gap-2">
              <Gift className="text-primary group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium">{t('gift')}</span>
            </Link>
          </Card>
          <Card className="bg-card/50 backdrop-blur hover:border-primary/30 transition-all group col-span-2">
            <Link to="/seller" className="p-4 flex flex-row items-center justify-center gap-3">
              <Store className="text-primary group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium">{t('sellers')}</span>
            </Link>
          </Card>
        </div>

        {/* Live Activity Feed */}
        <Card className="border-primary/10 bg-card/50 backdrop-blur overflow-hidden">
          <CardHeader className="py-3 bg-muted/20">
            <CardTitle className="text-xs uppercase tracking-[0.2em] flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
              Live Activity
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-white/5">
              {recentActivity.length > 0 ? recentActivity.slice(0, 5).map((act, i) => (
                <div key={i} className="p-3 flex items-center justify-between hover:bg-white/5 transition-colors">
                  <div className="flex items-center gap-2">
                    <NetworkLogo id={act.network} size={16} />
                    <div className="flex flex-col">
                      <span className="text-[10px] font-mono font-bold leading-none">{act.amount_crypto} {act.network?.toUpperCase()}</span>
                      <span className="text-[9px] text-muted-foreground font-mono leading-none mt-1">{act.wallet}</span>
                    </div>
                  </div>
                  <Badge variant={act.status === 'completed' ? 'default' : 'secondary'} className="text-[8px] h-4 px-1 uppercase">
                    {act.status}
                  </Badge>
                </div>
              )) : (
                <div className="p-6 text-center text-[10px] text-muted-foreground uppercase tracking-widest">
                  Awaiting transactions...
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
