import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { TrendingUp, Battery, Wallet, Zap, ArrowRight, ShieldCheck, Globe, ShoppingCart, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Link } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [marketData, setMarketData] = useState<any>(null);

  useEffect(() => {
    const fetchMarket = async () => {
      try {
        const res = await axios.get('/api/market');
        setMarketData(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchMarket();
  }, []);

  const networks = [
    { id: 'solana', name: 'Solana (SOL)', icon: '🪐', color: 'text-purple-400' },
    { id: 'trc20', name: 'Tron (TRC20)', icon: '🔋', color: 'text-red-400' },
    { id: 'polygon', name: 'Polygon (MATIC)', icon: '🟣', color: 'text-indigo-400' },
    { id: 'bsc', name: 'BSC (BNB)', icon: '🟡', color: 'text-yellow-400' },
    { id: 'ton', name: 'TON', icon: '💎', color: 'text-blue-400' },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <section className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold tracking-tight lg:text-4xl">
            {t('welcome')}, <span className="text-primary">{user ? user.username : 'Guest'}</span>!
          </h1>
          <p className="text-muted-foreground">Manage your crypto assets across all major networks.</p>
        </div>
        <div className="flex gap-2">
           <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 px-3 py-1">
             <Globe className="mr-1 h-3 w-3" /> System: Online
           </Badge>
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
              <p className="text-sm font-medium text-muted-foreground">{t('rates')}</p>
              <p className="text-2xl font-bold tracking-tight">৳{marketData?.rates?.solana || '...'}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-green-500/10 text-green-500 rounded-xl">
              <Zap className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Network</p>
              <p className="text-2xl font-bold tracking-tight">Healthy</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 text-purple-500 rounded-xl">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Security</p>
              <p className="text-2xl font-bold tracking-tight">{user ? 'Verified' : 'Guest'}</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-primary/10 transition-all hover:border-primary/30">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-yellow-500/10 text-yellow-500 rounded-xl">
              <Wallet className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Assets</p>
              <p className="text-2xl font-bold tracking-tight">Multi-Chain</p>
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
                      <span className="text-2xl">{net.icon}</span>
                      <span className="font-semibold">{net.name}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-[10px]">USDT/USDC</Badge>
                    </TableCell>
                    <TableCell className="py-4 text-right pr-6">
                       <span className="font-mono text-lg font-bold text-primary group-hover:scale-105 transition-transform inline-block">
                         ৳{marketData?.rates?.[net.id] || marketData?.rates?.solana || '...'}
                       </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="flex flex-col gap-6">
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
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
