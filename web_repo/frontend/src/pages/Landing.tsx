import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  ShoppingCart,
  RefreshCw,
  ShieldCheck,
  MessageSquare,
  Users,
  Gift,
  Check,
  Zap,
  Layers,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import Marquee from '../components/ui/marquee';
import { ASCIIText } from '../components/ui/ascii-text';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';

const FEATURES = [
  {
    id: '01',
    tag: 'BUY',
    icon: <ShoppingCart className="h-5 w-5" />,
    title: 'BUY WITH BKASH',
    desc: 'PURCHASE USDT OR USDC INSTANTLY USING BKASH. NO BANK. NO FRICTION. PURE SETTLEMENT.',
  },
  {
    id: '02',
    tag: 'SWAP',
    icon: <RefreshCw className="h-5 w-5" />,
    title: 'CROSS-CHAIN BRIDGE',
    desc: 'BRIDGE ASSETS ACROSS 20+ CHAINS POWERED BY LI.FI. ONE INTERFACE. ZERO GUESSWORK.',
  },
  {
    id: '03',
    tag: 'SECURE',
    icon: <ShieldCheck className="h-5 w-5" />,
    title: 'SECURE P2P SETTLEMENT',
    desc: 'EVERY ORDER VERIFIED. EVERY TRANSACTION TRACKED. SECURITY CALIBRATED FOR REAL MONEY.',
  },
  {
    id: '04',
    tag: 'AI',
    icon: <MessageSquare className="h-5 w-5" />,
    title: '24/7 AI SUPPORT',
    desc: 'AUTOMATED ONBOARDING AND INSTANT ANSWERS. HELP THAT NEVER SLEEPS, IN BANGLA OR ENGLISH.',
  },
  {
    id: '05',
    tag: 'EARN',
    icon: <Users className="h-5 w-5" />,
    title: 'REFERRALS THAT PAY',
    desc: 'INVITE. SHARE. EARN. TRACK EVERY REFERRAL AND PAYOUT FROM A SINGLE DASHBOARD.',
  },
  {
    id: '06',
    tag: 'BONUS',
    icon: <Gift className="h-5 w-5" />,
    title: 'GIFT CODES & GIVEAWAYS',
    desc: 'REDEEM GIFT CODES AND JOIN GIVEAWAYS. EXTRA VALUE FOR EVERY ACTIVE MEMBER.',
  },
];

const STEPS = [
  { id: '01', title: 'CREATE ACCOUNT', desc: 'REGISTER IN SECONDS WITH A USERNAME AND PASSWORD. NO KYC HEADACHE.' },
  { id: '02', title: 'FUND WITH BKASH', desc: 'SEND BDT VIA BKASH AND SUBMIT YOUR TRANSACTION ID. RATES ARE LIVE.' },
  { id: '03', title: 'RECEIVE CRYPTO', desc: 'GET USDT/USDC DELIVERED TO YOUR WALLET. AUTOMATED. FAST. DONE.' },
];

const STATS = [
  { value: '20+', label: 'SUPPORTED NETWORKS' },
  { value: '24/7', label: 'AUTOMATED DELIVERY' },
  { value: 'LI.FI', label: 'PROTOCOL INTEGRATED' },
  { value: '৳ BDT', label: 'BKASH NATIVE' },
];

const Landing: React.FC = () => {
  return (
    <div className="space-y-16 md:space-y-24 animate-in fade-in duration-500 -mt-2">
      {/* Hero */}
      <section className="relative border border-white/15 bg-card/40 backdrop-blur overflow-hidden">
        <div className="absolute inset-0 dot-matrix dot-matrix-fade pointer-events-none" aria-hidden="true" />
        <div className="scanline" />
        <div className="relative z-10 px-5 py-12 sm:px-10 sm:py-16 lg:py-24 flex flex-col items-start gap-6">
          <span className="inline-flex items-center gap-2 border border-green-500/30 bg-green-500/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.25em] text-green-500">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
            NEW // BGC CRYPTO V2.0 IS LIVE
          </span>

          <h1 className="max-w-4xl text-4xl font-extrabold uppercase leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl text-balance">
            BANGLADESH&apos;S CRYPTO GATEWAY.{' '}
            <span className="text-muted-foreground">BUY. SWAP. SETTLE.</span>
          </h1>

          <p className="max-w-2xl text-sm sm:text-base leading-relaxed text-muted-foreground">
            The fastest way to buy USDT and USDC with bKash, bridge across 20+ chains, and manage
            every transaction in one industrial-grade dashboard. From first taka to final settlement.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
            <Button asChild size="lg" className="h-12 font-bold w-full sm:w-auto">
              <Link to="/register" className="flex items-center justify-center gap-2">
                CREATE ACCOUNT <ArrowRight size={18} />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="h-12 font-bold w-full sm:w-auto border-white/30 hover:bg-white/10">
              <Link to="/login" className="flex items-center justify-center gap-2">
                LOGIN
              </Link>
            </Button>
          </div>

          <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
            NO HIDDEN FEES // BKASH NATIVE // LIVE BDT RATES
          </p>
        </div>
      </section>

      {/* Trust marquee */}
      <section className="space-y-4">
        <p className="text-center font-mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
          POWERING TRANSACTIONS ACROSS LEADING NETWORKS
        </p>
        <Marquee
          speed={30}
          containerClassName="border-y border-white/10 py-3 -mx-3 sm:-mx-5 lg:-mx-8"
          className=""
        >
          <span className="flex items-center gap-8 px-4">
            {NETWORK_LIST.map((net) => (
              <span key={net.id} className="flex items-center gap-2 text-muted-foreground">
                <NetworkLogo id={net.id} size={20} />
                <span className="font-mono text-xs uppercase tracking-widest">{net.name}</span>
              </span>
            ))}
          </span>
        </Marquee>
      </section>

      {/* Features */}
      <section className="space-y-8">
        <div className="space-y-2">
          <ASCIIText 
            text="FEATURES" 
            className="text-primary"
            animationDelay={60}
            size={0.9}
          />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-white/10 border border-white/10">
          {FEATURES.map((f) => (
            <div
              key={f.id}
              className="group bg-background p-6 flex flex-col gap-4 transition-colors hover:bg-card/60"
            >
              <div className="flex items-center justify-between">
                <div className="p-2 bg-muted text-foreground">{f.icon}</div>
                <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
                  [{f.tag}]
                </span>
              </div>
              <h3 className="text-lg font-bold uppercase tracking-tight">{f.title}</h3>
              <p className="text-xs leading-relaxed text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="space-y-8">
        <div className="space-y-2">
          <span className="font-mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
            [02] // HOW IT WORKS
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold uppercase tracking-tight text-balance">
            THREE STEPS TO SETTLEMENT
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {STEPS.map((s) => (
            <div key={s.id} className="border border-white/10 bg-card/40 p-6 flex flex-col gap-3">
              <span className="font-mono text-3xl font-bold text-muted-foreground/40">{s.id}</span>
              <h3 className="text-lg font-bold uppercase tracking-tight">{s.title}</h3>
              <p className="text-xs leading-relaxed text-muted-foreground">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats */}
      <section className="relative border border-white/10 bg-card/40 overflow-hidden">
        <div className="absolute inset-0 dot-matrix-fine pointer-events-none" aria-hidden="true" />
        <div className="relative grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-white/10">
          {STATS.map((stat) => (
            <div key={stat.label} className="p-6 sm:p-8 flex flex-col gap-1.5 items-center text-center">
              <span className="text-2xl sm:text-3xl font-extrabold tracking-tight">{stat.value}</span>
              <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
                {stat.label}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Why choose us */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        <div className="space-y-5">
          <span className="font-mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
            [03] // WHY BGC CRYPTO
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold uppercase tracking-tight text-balance">
            NO COMPROMISE. NO LOCK-IN.
          </h2>
          <ul className="space-y-3">
            {[
              'INSTANT BKASH-TO-CRYPTO ORDERS',
              'LIVE BDT CONVERSION RATES',
              'CROSS-CHAIN SWAPS VIA LI.FI',
              'TRANSPARENT ORDER & TX HISTORY',
              'BANGLA + ENGLISH INTERFACE',
            ].map((item) => (
              <li key={item} className="flex items-center gap-3">
                <span className="flex h-5 w-5 items-center justify-center border border-white/20 text-foreground shrink-0">
                  <Check className="h-3 w-3" />
                </span>
                <span className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
                  {item}
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div className="grid grid-cols-2 gap-px bg-white/10 border border-white/10">
          <div className="bg-background p-6 flex flex-col gap-2">
            <Zap className="h-5 w-5 text-foreground" />
            <p className="text-sm font-bold uppercase tracking-tight">FAST DELIVERY</p>
            <p className="text-[11px] text-muted-foreground leading-relaxed">AUTOMATED CRYPTO DELIVERY AROUND THE CLOCK.</p>
          </div>
          <div className="bg-background p-6 flex flex-col gap-2">
            <ShieldCheck className="h-5 w-5 text-foreground" />
            <p className="text-sm font-bold uppercase tracking-tight">VERIFIED ORDERS</p>
            <p className="text-[11px] text-muted-foreground leading-relaxed">EVERY PAYMENT CHECKED BEFORE RELEASE.</p>
          </div>
          <div className="bg-background p-6 flex flex-col gap-2">
            <Layers className="h-5 w-5 text-foreground" />
            <p className="text-sm font-bold uppercase tracking-tight">MULTI-CHAIN</p>
            <p className="text-[11px] text-muted-foreground leading-relaxed">SUPPORT FOR ALL MAJOR STABLECOIN NETWORKS.</p>
          </div>
          <div className="bg-background p-6 flex flex-col gap-2">
            <MessageSquare className="h-5 w-5 text-foreground" />
            <p className="text-sm font-bold uppercase tracking-tight">REAL SUPPORT</p>
            <p className="text-[11px] text-muted-foreground leading-relaxed">AI + HUMAN HELP WHENEVER YOU NEED IT.</p>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative border border-white/15 bg-card/40 overflow-hidden px-5 py-12 sm:px-10 sm:py-16 text-center flex flex-col items-center gap-6">
        <div className="absolute inset-0 dot-matrix dot-matrix-fade pointer-events-none" aria-hidden="true" />
        <h2 className="relative max-w-2xl text-3xl sm:text-4xl font-extrabold uppercase tracking-tight text-balance">
          READY TO MOVE YOUR MONEY?
        </h2>
        <p className="relative max-w-xl text-sm leading-relaxed text-muted-foreground">
          Join BGC Crypto today and experience bKash-native crypto trading built for Bangladesh.
        </p>
        <div className="relative flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <Button asChild size="lg" className="h-12 font-bold w-full sm:w-auto">
            <Link to="/register" className="flex items-center justify-center gap-2">
              GET STARTED — FREE <ArrowRight size={18} />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="h-12 font-bold w-full sm:w-auto border-white/30 hover:bg-white/10">
            <Link to="/login">I ALREADY HAVE AN ACCOUNT</Link>
          </Button>
        </div>
      </section>
    </div>
  );
};

export default Landing;
