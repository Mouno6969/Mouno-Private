import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { TrendingUp, Wallet, Zap, ArrowRight, ShieldCheck, ShoppingCart, RefreshCw, Users, Gift, Store } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import Marquee from '../components/ui/marquee';
import { Badge } from '../components/ui/badge';
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
      try {
        const [marketRes, statsRes, activityRes] = await Promise.all([
          axios.get(`${process.env.REACT_APP_API_URL || ''}/api/market`, { signal: controller.signal }),
          axios.get(`${process.env.REACT_APP_API_URL || ''}/api/stats`, { signal: controller.signal }),
          axios.get(`${process.env.REACT_APP_API_URL || ''}/api/recent-activity`, { signal: controller.signal })
        ]);

        if (!controller.signal.aborted) {
          setMarketData(marketRes.data);
          setStats(statsRes.data);
          setRecentActivity(activityRes.data);
          setLastUpdated(new Date());
        }
      } catch (err) {
        if (!axios.isCancel(err)) {
          console.error(err);
        }
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

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <Marquee speed={30} className="font-mono text-[10px] uppercase tracking-[0.2em] mb-4">
        <span className="flex items-center gap-2">◈ {stats?.total_users || '...'} USERS REGISTERED</span>
        <span className="flex items-center gap-2">◈ {stats?.completed_orders || '...'} ORDERS COMPLETED</span>
        <span className="flex items-center gap-2">◈ LIFI PROTOCOL INTEGRATED</span>
        <span className="flex items-center gap-2">◈ 24/7 AUTOMATED DELIVERY</span>
        <span className="flex items-center gap-2">◈ CROSS-CHAIN SWAPS ACTIVE</span>
        <span className="flex items-center gap-2">◈ SECURE P2P SETTLEMENT</span>
        <span className="flex items-center gap-2">◈ AI ONBOARDING ONLINE</span>
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 text-blue-500 rounded-xl">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">{user ? t('orders') : 'Total Orders'}</p>
              <p className="text-2xl font-bold tracking-tight">
                {user ? user.telegram_stats?.total_orders || 0 : stats?.completed_orders || '...'}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-green-500/10 text-green-500 rounded-xl">
              <Zap className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Volume (BDT)</p>
              <p className="text-2xl font-bold tracking-tight">
                ৳{user ? user.telegram_stats?.total_bdt || 0 : stats?.total_volume_bdt?.toLocaleString() || '...'}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 text-purple-500 rounded-xl">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Users</p>
              <p className="text-2xl font-bold tracking-tight">{stats?.total_users || '...'}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-yellow-500/10 text-yellow-500 rounded-xl">
              <Wallet className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Best Rate</p>
              <p className="text-2xl font-bold tracking-tight">৳{marketData?.rates?.solana || '...'}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Market Table */}
        <Card className="lg:col-span-2 overflow-hidden shadow-xl border-primary/10">
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
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-muted/50">
                  <TableHead className="w-[200px] pl-6 font-semibold uppercase text-[10px] tracking-wider">Network</TableHead>
                  <TableHead className="font-semibold uppercase text-[10px] tracking-wider">Asset</TableHead>
                  <TableHead className="text-right pr-6 font-semibold uppercase text-[10px] tracking-wider">Rate (1 USDT/USDC)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {networks.map((net) => (
                  <TableRow key={net.id} className="group hover:bg-primary/5 transition-colors">
                    <TableCell className="py-4 pl-6 flex items-center gap-3">
                      <NetworkLogo id={net.id} size={28} />
                      <span className="font-semibold">{net.name}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-[10px]">USDT/USDC</Badge>
                    </TableCell>
                    <TableCell className="py-4 text-right pr-6">
                       <span className="font-mono text-lg font-bold text-primary group-hover:scale-105 transition-transform inline-block">
                         ৳{marketData?.rates?.[net.id] || '...'}
                       </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Quick Actions & Live Feed */}
        <div className="flex flex-col gap-6">
          {/* Live Activity Feed */}
          <Card className="border-primary/10 bg-black/40 overflow-hidden">
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

          <Card className="bg-primary text-primary-foreground overflow-hidden border-none shadow-lg relative group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-125 transition-transform duration-500">
              <ShoppingCart size={120} />
            </div>
            <CardHeader>
              <CardTitle className="text-2xl">{t('buy')}</CardTitle>
              <CardDescription className="text-primary-foreground/70">
                Purchase USDC or USDT using bKash instantly.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="secondary" className="w-full font-bold h-12 shadow-md">
                <Link to="/buy" className="flex items-center gap-2">
                  Start Order <ArrowRight size={18} />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-primary/20 overflow-hidden shadow-lg relative group">
             <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-125 transition-transform duration-500">
              <RefreshCw size={120} />
            </div>
            <CardHeader>
              <CardTitle className="text-2xl text-white">{t('swap')}</CardTitle>
              <CardDescription className="text-gray-400">
                Bridge assets between 20+ chains with LI.FI.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" className="w-full font-bold h-12 border-primary/30 hover:bg-primary/10 text-primary">
                <Link to="/swap" className="flex items-center gap-2">
                  Launch Bridge <ArrowRight size={18} />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <div className="grid grid-cols-2 gap-4">
            <Card className="hover:border-primary/30 transition-all group">
              <Link to="/referral" className="p-4 flex flex-col items-center text-center gap-2">
                <Users className="text-primary group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium">{t('referral')}</span>
              </Link>
            </Card>
            <Card className="hover:border-primary/30 transition-all group">
              <Link to="/gift" className="p-4 flex flex-col items-center text-center gap-2">
                <Gift className="text-primary group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium">{t('gift')}</span>
              </Link>
            </Card>
            <Card className="hover:border-primary/30 transition-all group col-span-2">
              <Link to="/seller" className="p-4 flex flex-row items-center justify-center gap-3">
                <Store className="text-primary group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium">{t('sellers')}</span>
              </Link>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
