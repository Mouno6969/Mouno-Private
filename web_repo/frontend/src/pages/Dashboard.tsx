import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import {
  ArrowUpRight,
  Terminal,
  Activity,
  Shield,
  Cpu,
  Zap,
  RefreshCw,
  Users,
  Gift,
  Store
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Link } from 'react-router-dom';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';

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

  const networks = NETWORK_LIST;

  return (
    <div className="space-y-16 animate-in fade-in slide-in-from-bottom-4 duration-700 font-sans">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-10">
        <div className="space-y-4 max-w-3xl">
          <div className="flex items-center gap-2 text-white/40 mb-6">
            <Terminal size={14} />
            <span className="text-[10px] uppercase tracking-[0.3em] font-mono">Terminal Initialized</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-heading font-bold tracking-tighter uppercase leading-[0.9]">
            {t('welcome')}, <br />
            <span className="text-white/40">{user ? user.username : 'Guest'}</span>
          </h1>
          <p className="text-white/40 text-lg max-w-xl font-medium tracking-tight">
            Mouno Web onboards you into the internet economy — discovery, automation, and infrastructure, unified into one permissionless platform.
          </p>
          <div className="pt-6 flex flex-wrap gap-4">
             <Button asChild size="lg" className="bg-white text-black rounded-none hover:bg-white/90 px-8 font-bold uppercase tracking-widest text-xs h-14">
                <Link to="/buy">Open Platform</Link>
             </Button>
             <Button asChild variant="outline" size="lg" className="border-white/10 rounded-none hover:bg-white/5 px-8 uppercase tracking-widest text-xs h-14">
                <Link to="/guide">Read System Brief</Link>
             </Button>
          </div>
        </div>
      </section>

      {/* Stats Board */}
      <div className="grid grid-cols-2 md:grid-cols-4 border border-white/10">
         {[
           { label: 'System Status', value: 'Nominal', icon: <Activity size={14} /> },
           { label: 'Security', value: 'Encrypted', icon: <Shield size={14} /> },
           { label: 'Network', value: 'Live', icon: <Zap size={14} /> },
           { label: 'Infrastructure', value: 'V1.0', icon: <Cpu size={14} /> },
         ].map((stat, i) => (
           <div key={i} className="p-6 border-r last:border-r-0 border-white/10 space-y-2">
              <div className="flex items-center gap-2 text-white/30">
                 {stat.icon}
                 <span className="text-[10px] uppercase tracking-widest font-mono">{stat.label}</span>
              </div>
              <p className="text-xl font-heading font-bold uppercase">{stat.value}</p>
           </div>
         ))}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Market Rates - Left Side */}
        <div className="lg:col-span-7 space-y-8">
           <div className="space-y-1">
              <h2 className="text-xs uppercase tracking-[0.3em] text-white/40 font-heading font-bold">01 ◈ Live Surface</h2>
              <h3 className="text-3xl font-heading font-bold uppercase tracking-tight">Digital Markets</h3>
           </div>

           <div className="border border-white/10 overflow-hidden">
            <Table>
              <TableHeader className="bg-white/5">
                <TableRow className="hover:bg-transparent border-white/10">
                  <TableHead className="pl-6 font-heading font-bold uppercase text-[10px] tracking-widest text-white/40 py-4">Network</TableHead>
                  <TableHead className="font-heading font-bold uppercase text-[10px] tracking-widest text-white/40">Asset</TableHead>
                  <TableHead className="text-right pr-6 font-heading font-bold uppercase text-[10px] tracking-widest text-white/40">Rate (BDT)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {networks.map((net) => (
                  <TableRow key={net.id} className="group hover:bg-white/5 transition-colors border-white/10">
                    <TableCell className="py-6 pl-6">
                      <div className="flex items-center gap-3">
                        <div className="grayscale group-hover:grayscale-0 transition-all duration-500">
                          <NetworkLogo id={net.id} size={24} />
                        </div>
                        <span className="font-heading font-bold uppercase tracking-wider text-sm">{net.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-[10px] font-mono text-white/40 uppercase tracking-widest">USDT/USDC</span>
                    </TableCell>
                    <TableCell className="py-6 text-right pr-6">
                       <span className="font-mono text-lg font-bold">
                         ৳{marketData?.rates?.[net.id] || '0.00'}
                       </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
           </div>
        </div>

        {/* Action Blocks - Right Side */}
        <div className="lg:col-span-5 flex flex-col gap-8">
           <div className="space-y-1">
              <h2 className="text-xs uppercase tracking-[0.3em] text-white/40 font-heading font-bold">02 ◈ Modules</h2>
              <h3 className="text-3xl font-heading font-bold uppercase tracking-tight">System Core</h3>
           </div>

           <div className="grid grid-cols-1 gap-4">
              <Link to="/buy" className="group border border-white/10 p-8 flex justify-between items-end hover:bg-white transition-all duration-300">
                 <div className="space-y-2">
                    <h4 className="text-sm font-heading font-bold uppercase tracking-widest text-white group-hover:text-black">Buy Crypto</h4>
                    <p className="text-xs text-white/40 group-hover:text-black/60 max-w-[200px]">Purchase USDC or USDT using local payment methods.</p>
                 </div>
                 <ArrowUpRight size={24} className="text-white/20 group-hover:text-black transition-colors" />
              </Link>

              <Link to="/swap" className="group border border-white/10 p-8 flex justify-between items-end hover:bg-white transition-all duration-300">
                 <div className="space-y-2">
                    <h4 className="text-sm font-heading font-bold uppercase tracking-widest text-white group-hover:text-black">Bridge & Swap</h4>
                    <p className="text-xs text-white/40 group-hover:text-black/60 max-w-[200px]">Cross-chain liquidity aggregator via LI.FI protocols.</p>
                 </div>
                 <ArrowUpRight size={24} className="text-white/20 group-hover:text-black transition-colors" />
              </Link>

              <div className="grid grid-cols-2 gap-4">
                 <Link to="/referral" className="group border border-white/10 p-6 flex flex-col gap-4 hover:bg-white transition-all duration-300">
                    <Users size={20} className="text-white/40 group-hover:text-black" />
                    <span className="text-[10px] font-heading font-bold uppercase tracking-widest group-hover:text-black">Referrals</span>
                 </Link>
                 <Link to="/gift" className="group border border-white/10 p-6 flex flex-col gap-4 hover:bg-white transition-all duration-300">
                    <Gift size={20} className="text-white/40 group-hover:text-black" />
                    <span className="text-[10px] font-heading font-bold uppercase tracking-widest group-hover:text-black">Rewards</span>
                 </Link>
              </div>

              <Link to="/seller" className="group border border-white/10 p-6 flex items-center gap-4 hover:bg-white transition-all duration-300">
                 <Store size={18} className="text-white/40 group-hover:text-black" />
                 <span className="text-[10px] font-heading font-bold uppercase tracking-widest group-hover:text-black">Reseller Infrastructure</span>
                 <ArrowUpRight size={14} className="ml-auto text-white/20 group-hover:text-black" />
              </Link>
           </div>
        </div>
      </div>

      {/* Technical Footer Section */}
      <section className="pt-16 border-t border-white/10 pb-8">
         <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="space-y-4">
               <h4 className="text-[11px] font-heading font-bold uppercase tracking-[0.2em]">03 ◈ Vision</h4>
               <p className="text-xs text-white/40 leading-relaxed font-medium">
                  We believe in a world where the internet is the primary economy. No gatekeepers, no borders, just code. Mouno Web is your portal to this permissionless future.
               </p>
            </div>
            <div className="space-y-4">
               <h4 className="text-[11px] font-heading font-bold uppercase tracking-[0.2em]">04 ◈ Protocol</h4>
               <p className="text-xs text-white/40 leading-relaxed font-medium">
                  Built on top of leading DeFi protocols and settlement layers. Every transaction is transparent, secure, and verifiable on-chain.
               </p>
            </div>
            <div className="space-y-4">
               <h4 className="text-[11px] font-heading font-bold uppercase tracking-[0.2em]">05 ◈ Community</h4>
               <p className="text-xs text-white/40 leading-relaxed font-medium">
                  Join a network of thousands of users who are already earning and transacting in the digital economy.
               </p>
            </div>
         </div>
      </section>
    </div>
  );
};

export default Dashboard;
