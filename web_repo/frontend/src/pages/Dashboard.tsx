import React, { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { TrendingUp, Zap, ArrowRight, ShieldCheck, Users, Gift, Store, Layers, User as UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { BkashLogo, LifiLogo } from '../components/ui/brand-logos';
import { Link } from 'react-router-dom';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';
import { useMarket, useStats, useRecentActivity, useBalance, useTxLog } from '../lib/hooks';
import { SkeletonTableRows, SkeletonText } from '../components/ui/skeleton';
import { FlashValue, Freshness } from '../components/common';

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
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Welcome Section */}
      <section className="rounded-xl border border-border/70 bg-card/70 p-5 sm:p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <p className="label-eyebrow">Dashboard</p>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              {t('welcome')}, <span className="text-primary">{user ? user.username : 'Guest'}</span>
            </h1>
            <p className="text-sm text-muted-foreground">Manage your crypto assets across all major networks.</p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="success" className="px-3 py-1 gap-2">
              <span className="live-dot" />
              Online
            </Badge>
            <Freshness updatedAt={lastUpdated} label="Updated" />
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-lg shrink-0">
              <TrendingUp className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground">Live Rate (USDC)</p>
              {marketLoading && !marketData ? (
                <SkeletonText className="mt-1 h-5 w-16" />
              ) : (
                <FlashValue value={marketData?.rates?.solana} as="div" className="inline-block">
                  <p className="num text-lg font-bold tracking-tight">
                    {marketData?.rates?.solana ? `৳${marketData.rates.solana}` : '—'}
                  </p>
                </FlashValue>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-lg shrink-0">
              <Layers className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground">Funded Assets</p>
              {isLoggedIn && balanceLoading && !balanceData ? (
                <SkeletonText className="mt-1 h-5 w-12" />
              ) : isLoggedIn ? (
                <p className="text-lg font-bold tracking-tight">
                  {fundedAssetCount}
                  <span className="text-xs font-normal text-muted-foreground"> / {totalAssetCount}</span>
                </p>
              ) : (
                <p className="text-lg font-bold tracking-tight">
                  {NETWORK_LIST.length} Chains
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-lg shrink-0">
              <Zap className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground">
                {isLoggedIn ? 'Your Transactions' : 'Platform Orders'}
              </p>
              <p className="text-lg font-bold tracking-tight">
                {isLoggedIn ? recentTxCount : (stats?.total_orders ?? '—')}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2.5 bg-primary/10 text-primary rounded-lg shrink-0">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground">
                {isLoggedIn ? 'Account' : 'Members'}
              </p>
              <p className="text-lg font-bold tracking-tight truncate">
                {isLoggedIn ? user!.username : (stats?.total_users ?? '—')}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="group transition-all hover:border-primary/30">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <CardTitle className="text-lg">{t('buy')} Crypto</CardTitle>
                <CardDescription>Purchase USDC or USDT using bKash instantly.</CardDescription>
              </div>
              <BkashLogo className="shrink-0" />
            </div>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full font-semibold h-11">
              <Link to="/buy" className="flex items-center gap-2">
                Start Order <ArrowRight size={16} />
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="group transition-all hover:border-primary/30">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <CardTitle className="text-lg">{t('swap')} & Bridge</CardTitle>
                <CardDescription>Bridge assets between 20+ chains with LI.FI.</CardDescription>
              </div>
              <LifiLogo className="shrink-0" />
            </div>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full font-semibold h-11">
              <Link to="/swap" className="flex items-center gap-2">
                Launch Bridge <ArrowRight size={16} />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Market Table */}
      <Card className="overflow-hidden">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" /> Live Rates
              </CardTitle>
              <CardDescription>Live BDT conversion rates for stablecoins</CardDescription>
            </div>
            <Badge variant="secondary" className="text-[10px] font-mono uppercase">Real-time</Badge>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table className="min-w-[560px]">
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[150px] pl-6 text-xs font-medium uppercase tracking-wider">Network</TableHead>
                  <TableHead className="text-xs font-medium uppercase tracking-wider">Asset</TableHead>
                  <TableHead className="text-right text-xs font-medium uppercase tracking-wider">Market Cap</TableHead>
                  <TableHead className="text-right pr-6 text-xs font-medium uppercase tracking-wider">Rate (1 USDT/USDC)</TableHead>
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
                    <TableRow key={net.id} className="group hover:bg-muted/40 transition-colors">
                      <TableCell className="py-3 pl-6">
                        <div className="flex items-center gap-2.5">
                          <NetworkLogo id={net.id} size={22} />
                          <span className="font-medium text-sm">{net.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-[10px] px-1.5">USDT/USDC</Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-muted-foreground">
                        ৳{marketCap ? Number(marketCap).toLocaleString() : '—'}
                      </TableCell>
                      <TableCell className="py-3 text-right pr-6">
                        <div className="flex items-center justify-end gap-2">
                          <FlashValue value={rate} className="inline-block">
                            <span className="num text-sm font-bold">৳{rate || '—'}</span>
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

      {/* Bottom row: Quick links + Activity */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Quick Links */}
        <div className="grid grid-cols-2 gap-3 md:col-span-1">
          <Card className="hover:border-primary/30 transition-all">
            <Link to="/referral" className="p-4 flex flex-col items-center text-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              <span className="text-xs font-medium">{t('referral')}</span>
            </Link>
          </Card>
          <Card className="hover:border-primary/30 transition-all">
            <Link to="/gift" className="p-4 flex flex-col items-center text-center gap-2">
              <Gift className="h-5 w-5 text-primary" />
              <span className="text-xs font-medium">{t('gift')}</span>
            </Link>
          </Card>
          <Card className="hover:border-primary/30 transition-all col-span-2">
            <Link to="/seller" className="p-4 flex flex-row items-center justify-center gap-3">
              <Store className="h-5 w-5 text-primary" />
              <span className="text-xs font-medium">{t('sellers')}</span>
            </Link>
          </Card>
        </div>

        {/* Live Activity Feed */}
        <Card className="md:col-span-2 overflow-hidden">
          <CardHeader className="py-3 border-b border-border/60">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <span className="live-dot" />
              Live Activity
              {isDemoMode && (
                <Badge variant="warning" className="text-[8px] h-4 px-1.5 uppercase tracking-wider ml-2">
                  Demo
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border/50">
              {Array.isArray(recentActivity) && recentActivity.length > 0 ? recentActivity.slice(0, 5).map((act, i) => (
                <div key={i} className="p-3 flex items-center justify-between hover:bg-muted/30 transition-colors">
                  <div className="flex items-center gap-2.5">
                    <NetworkLogo id={act.network} size={16} />
                    <div className="flex flex-col">
                      <span className="text-xs font-medium">{act.amount_crypto} {act.network?.toUpperCase()}</span>
                      <span className="text-[10px] text-muted-foreground font-mono">{act.wallet}</span>
                    </div>
                  </div>
                  <Badge variant={act.status === 'completed' ? 'default' : 'secondary'} className="text-[9px] h-5 px-2">
                    {formatActivityStatus(act.status)}
                  </Badge>
                </div>
              )) : (
                <div className="p-8 flex flex-col items-center gap-2 text-center">
                  <p className="text-sm font-medium text-muted-foreground">No activity yet</p>
                  <p className="text-xs text-muted-foreground">Live transactions will appear here.</p>
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
