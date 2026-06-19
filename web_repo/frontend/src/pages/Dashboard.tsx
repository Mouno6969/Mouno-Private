import React, { useEffect, useRef, useState } from 'react';
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
import { useMarket, useStats, useRecentActivity, useBalance, useTxLog } from '../lib/hooks';
import { SkeletonTableRows, SkeletonText } from '../components/ui/skeleton';
import { FlashValue } from '../components/common';

const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();

  const { data: marketData, isLoading: marketLoading } = useMarket();
  const { data: stats } = useStats();
  const { data: recentActivity } = useRecentActivity();

  // User-scoped data — only fetched when logged in.
  const isLoggedIn = !!user;
  const { data: balanceData, isLoading: balanceLoading } = useBalance(isLoggedIn);
  const { data: txData } = useTxLog(isLoggedIn);

  // Derive real, user-scoped stats from the live data above.
  const balances = balanceData?.balances ?? {};
  const fundedAssetCount = Object.values(balances).filter((v) => Number(v) > 0).length;
  const totalAssetCount = Object.keys(balances).length;
  const recentTxCount = txData.length;

  // Surface when the live market data was last refreshed.
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const lastMarketRef = useRef<unknown>(null);
  useEffect(() => {
    if (marketData && marketData !== lastMarketRef.current) {
      lastMarketRef.current = marketData;
      setLastUpdated(new Date());
    }
  }, [marketData]);

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
        containerClassName="bg-muted/40 border-y border-border/60 py-1.5 -mx-3 sm:-mx-5 lg:-mx-8"
        className="text-xs"
      >
        <span className="flex items-center gap-1.5 px-2">
          <span className="font-bold text-primary">Latest:</span>
          {Array.isArray(recentActivity) && recentActivity.length > 0 ? (
            recentActivity.slice(0, 6).map((act, i) => (
              <span key={i} className="text-muted-foreground">
                {act.amount_crypto} {act.network?.toUpperCase()} {formatActivityStatus(act.status)}
                {i < 5 ? '  •  ' : ''}
              </span>
            ))
          ) : (
            <span className="text-muted-foreground">Live activity will appear here.</span>
          )}
        </span>
      </Marquee>

      {/* Top Marquee 2: Live status ticker */}
      <Marquee
        speed={30}
        containerClassName="bg-success/5 border-y border-success/15 py-1 -mx-3 sm:-mx-5 lg:-mx-8 !mt-0"
        className="font-mono text-[10px] uppercase tracking-[0.2em] text-success"
      >
        <span className="flex items-center gap-2">▸ LIVE</span>
        <span className="flex items-center gap-2">▸ CROSS-CHAIN SWAPS ACTIVE</span>
        <span className="flex items-center gap-2">▸ SECURE P2P SETTLEMENT</span>
        {stats?.total_users ? (
          <span className="flex items-center gap-2">▸ {stats.total_users} ONBOARDINGS ONLINE</span>
        ) : null}
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
           <Badge variant="success" className="px-3 py-1">
             <div className="mr-2 h-2 w-2 rounded-full bg-success animate-pulse" />
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
                <p className="text-sm font-medium text-muted-foreground truncate">Live Rate (USDC)</p>
                {marketLoading && !marketData ? (
                  <SkeletonText className="mt-1 h-5 w-16" />
                ) : (
                  <FlashValue value={marketData?.rates?.solana} className="inline-block px-1 -mx-1">
                    <p className="num text-base sm:text-lg font-bold tracking-tight truncate">
                      {marketData?.rates?.solana ? `৳${marketData.rates.solana}` : 'N/A'}
                    </p>
                  </FlashValue>
                )}
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
              <Layers className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-muted-foreground truncate">Funded Assets</p>
              {isLoggedIn && balanceLoading && !balanceData ? (
                <SkeletonText className="mt-1 h-5 w-12" />
              ) : isLoggedIn ? (
                <p className="text-base sm:text-lg font-bold tracking-tight truncate">
                  {fundedAssetCount}
                  <span className="text-xs font-normal text-muted-foreground"> / {totalAssetCount}</span>
                </p>
              ) : (
                <p className="text-base sm:text-lg font-bold tracking-tight truncate">
                  {NETWORK_LIST.length} Chains
                </p>
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
              <p className="text-sm font-medium text-muted-foreground truncate">
                {isLoggedIn ? 'Your Transactions' : 'Platform Orders'}
              </p>
              <p className="text-base sm:text-lg font-bold tracking-tight truncate">
                {isLoggedIn ? recentTxCount : (stats?.total_orders ?? '—')}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-3 sm:p-4 flex items-center gap-2.5">
            <div className="p-2 bg-muted text-muted-foreground rounded-lg shrink-0">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-muted-foreground truncate">
                {isLoggedIn ? 'Account' : 'Members'}
              </p>
              <p className="text-base sm:text-lg font-bold tracking-tight truncate">
                {isLoggedIn ? user!.username : (stats?.total_users ?? '—')}
              </p>
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
              <Table className="min-w-[600px]">
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-muted/50">
                    <TableHead className="w-[150px] pl-4 sm:pl-6 font-semibold uppercase text-[10px] tracking-wider whitespace-nowrap">Network</TableHead>
                    <TableHead className="font-semibold uppercase text-[10px] tracking-wider">Asset</TableHead>
                    <TableHead className="text-right font-semibold uppercase text-[10px] tracking-wider">Market Cap</TableHead>
                    <TableHead className="text-right pr-4 sm:pr-6 font-semibold uppercase text-[10px] tracking-wider whitespace-nowrap">Rate (1 USDT/USDC)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {marketLoading && !marketData ? (
                    <SkeletonTableRows rows={NETWORK_LIST.length} cols={4} />
                  ) : (
                    networks.map((net, idx) => {
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
                            <span className="font-semibold text-sm whitespace-nowrap">{net.name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="whitespace-nowrap">
                          <Badge variant="outline" className="font-mono text-[9px] px-1.5">USDT/USDC</Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs text-muted-foreground whitespace-nowrap">
                          ৳{marketCap ? Number(marketCap).toLocaleString() : '...'}
                        </TableCell>
                        <TableCell className="py-3.5 text-right pr-4 sm:pr-6 whitespace-nowrap">
                          <div className="flex items-center justify-end gap-2">
                            <FlashValue value={rate} className="inline-block px-1 -mx-1">
                              <span className="num text-sm font-bold text-foreground">৳{rate || '...'}</span>
                            </FlashValue>
                            {hasNumericChange && (
                              <Badge
                                className={`text-[9px] h-4 px-1 font-mono border-0 ${isUp ? 'bg-success/15 text-success' : 'bg-destructive/15 text-destructive'}`}
                              >
                                {isUp ? '▲' : '▼'} {Math.abs(change).toFixed(3)}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })
                  )}
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
              <div className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
              Live Activity
              {isDemoMode && (
                <Badge variant="warning" className="text-[8px] h-4 px-1.5 uppercase tracking-wider">
                  Demo data
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border/50">
                {Array.isArray(recentActivity) && recentActivity.length > 0 ? recentActivity.slice(0, 5).map((act, i) => (
                <div key={i} className="p-3 flex items-center justify-between hover:bg-secondary/40 transition-colors">
                  <div className="flex items-center gap-2">
                    <NetworkLogo id={act.network} size={16} />
                    <div className="flex flex-col">
                      <span className="text-[10px] font-mono font-bold leading-none">{act.amount_crypto} {act.network?.toUpperCase()}</span>
                      <span className="text-[9px] text-muted-foreground font-mono leading-none mt-1">{act.wallet}</span>
                    </div>
                  </div>
                  <Badge variant={act.status === 'completed' ? 'default' : 'secondary'} className="text-[8px] h-4 px-1 uppercase">
                    {formatActivityStatus(act.status)}
                  </Badge>
                </div>
              )) : (
                <div className="p-6 flex flex-col items-center gap-1 text-center">
                  <p className="text-xs font-medium text-foreground">No public activity yet</p>
                  <p className="text-[10px] text-muted-foreground">Live activity will appear here.</p>
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
