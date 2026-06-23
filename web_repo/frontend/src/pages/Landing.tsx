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
  Menu,
  X,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import Marquee from '../components/ui/marquee';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';

const FEATURES = [
  {
    icon: <ShoppingCart className="h-5 w-5" />,
    title: 'Buy with bKash',
    desc: 'Purchase USDT or USDC instantly using bKash. No bank needed, no friction — pure settlement.',
  },
  {
    icon: <RefreshCw className="h-5 w-5" />,
    title: 'Cross-Chain Bridge',
    desc: 'Bridge assets across 20+ chains powered by LI.FI. One interface, zero guesswork.',
  },
  {
    icon: <ShieldCheck className="h-5 w-5" />,
    title: 'Secure P2P Settlement',
    desc: 'Every order verified. Every transaction tracked. Security calibrated for real money.',
  },
  {
    icon: <MessageSquare className="h-5 w-5" />,
    title: '24/7 AI Support',
    desc: 'Automated onboarding and instant answers. Help that never sleeps, in Bangla or English.',
  },
  {
    icon: <Users className="h-5 w-5" />,
    title: 'Referrals That Pay',
    desc: 'Invite, share, and earn. Track every referral and payout from a single dashboard.',
  },
  {
    icon: <Gift className="h-5 w-5" />,
    title: 'Gift Codes & Giveaways',
    desc: 'Redeem gift codes and join giveaways. Extra value for every active member.',
  },
];

const STEPS = [
  { num: '1', title: 'Create Account', desc: 'Register in seconds with a username and password. No KYC headache.' },
  { num: '2', title: 'Fund with bKash', desc: 'Send BDT via bKash and submit your transaction ID. Rates are live.' },
  { num: '3', title: 'Receive Crypto', desc: 'Get USDT/USDC delivered to your wallet. Automated, fast, done.' },
];

const STATS = [
  { value: '20+', label: 'Supported Networks' },
  { value: '24/7', label: 'Automated Delivery' },
  { value: 'LI.FI', label: 'Protocol Integrated' },
  { value: '৳ BDT', label: 'bKash Native' },
];

const Landing: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <div className="min-h-screen">
      {/* ── Sticky Header ── */}
      <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-lg">
        <div className="mx-auto max-w-6xl flex items-center justify-between h-16 px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5">
            <img src="/logo.jpg" alt="Mouno" className="h-8 w-8 rounded-lg object-cover" />
            <span className="text-lg font-bold tracking-tight">Mouno</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">How It Works</a>
            <a href="#why" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Why Us</a>
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <Button asChild variant="ghost" size="sm">
              <Link to="/login">Log In</Link>
            </Button>
            <Button asChild size="sm">
              <Link to="/register">Get Started</Link>
            </Button>
          </div>

          {/* Mobile menu toggle */}
          <button
            type="button"
            className="md:hidden p-2 text-muted-foreground hover:text-foreground"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile nav dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border/60 bg-background/95 backdrop-blur-lg px-4 py-4 space-y-3">
            <a href="#features" onClick={() => setMobileMenuOpen(false)} className="block text-sm text-muted-foreground hover:text-foreground py-1">Features</a>
            <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)} className="block text-sm text-muted-foreground hover:text-foreground py-1">How It Works</a>
            <a href="#why" onClick={() => setMobileMenuOpen(false)} className="block text-sm text-muted-foreground hover:text-foreground py-1">Why Us</a>
            <div className="flex gap-2 pt-2 border-t border-border/60">
              <Button asChild variant="outline" size="sm" className="flex-1">
                <Link to="/login">Log In</Link>
              </Button>
              <Button asChild size="sm" className="flex-1">
                <Link to="/register">Get Started</Link>
              </Button>
            </div>
          </div>
        )}
      </header>

      <div className="mx-auto max-w-6xl px-4 sm:px-6 space-y-20 md:space-y-28 pb-20">
        {/* ── Hero ── */}
        <section className="pt-16 md:pt-24 flex flex-col items-center text-center gap-6">
          <span className="inline-flex items-center gap-2 rounded-full border border-success/30 bg-success/10 px-4 py-1.5 text-xs font-medium text-success">
            <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
            BGC Crypto v2.0 is live
          </span>

          <h1 className="max-w-3xl text-4xl font-extrabold leading-[1.1] tracking-tight sm:text-5xl lg:text-6xl text-balance">
            Bangladesh&apos;s Crypto Gateway.{' '}
            <span className="text-primary">Buy. Swap. Settle.</span>
          </h1>

          <p className="max-w-2xl text-base sm:text-lg leading-relaxed text-muted-foreground">
            The fastest way to buy USDT and USDC with bKash, bridge across 20+ chains, and manage
            every transaction in one powerful dashboard.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto pt-2">
            <Button asChild size="lg" className="h-12 font-semibold w-full sm:w-auto px-8">
              <Link to="/register" className="flex items-center justify-center gap-2">
                Create Free Account <ArrowRight size={18} />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="h-12 font-semibold w-full sm:w-auto px-8">
              <Link to="/login" className="flex items-center justify-center gap-2">
                Log In
              </Link>
            </Button>
          </div>

          <p className="text-xs text-muted-foreground pt-2">
            No hidden fees &middot; bKash native &middot; Live BDT rates
          </p>
        </section>

        {/* ── Trust marquee ── */}
        <section className="space-y-4">
          <p className="text-center text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Powering transactions across leading networks
          </p>
          <Marquee
            speed={30}
            containerClassName="border-y border-border/60 py-4"
            className=""
          >
            <span className="flex items-center gap-10 px-4">
              {NETWORK_LIST.map((net) => (
                <span key={net.id} className="flex items-center gap-2 text-muted-foreground">
                  <NetworkLogo id={net.id} size={22} />
                  <span className="text-sm font-medium">{net.name}</span>
                </span>
              ))}
            </span>
          </Marquee>
        </section>

        {/* ── Features ── */}
        <section id="features" className="space-y-10">
          <div className="text-center space-y-3">
            <p className="text-xs font-medium uppercase tracking-wider text-primary">Features</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              One Platform. Every Tool.
            </h2>
            <p className="max-w-xl mx-auto text-muted-foreground">
              Everything you need to buy, swap, and manage crypto — built for Bangladesh.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f, idx) => (
              <div
                key={idx}
                className="group rounded-xl border border-border/70 bg-card/60 p-6 flex flex-col gap-4 transition-all hover:border-primary/40 hover:bg-card/80 hover:shadow-lg hover:shadow-primary/5"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  {f.icon}
                </div>
                <h3 className="text-base font-semibold">{f.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── How it works ── */}
        <section id="how-it-works" className="space-y-10">
          <div className="text-center space-y-3">
            <p className="text-xs font-medium uppercase tracking-wider text-primary">How It Works</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Three Steps to Settlement
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {STEPS.map((s) => (
              <div key={s.num} className="relative rounded-xl border border-border/70 bg-card/60 p-6 flex flex-col gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-lg">
                  {s.num}
                </span>
                <h3 className="text-lg font-semibold">{s.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Stats ── */}
        <section className="rounded-xl border border-border/70 bg-card/60 overflow-hidden">
          <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-border/60">
            {STATS.map((stat) => (
              <div key={stat.label} className="p-6 sm:p-8 flex flex-col gap-1.5 items-center text-center">
                <span className="text-2xl sm:text-3xl font-extrabold tracking-tight">{stat.value}</span>
                <span className="text-xs text-muted-foreground font-medium">
                  {stat.label}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* ── Why choose us ── */}
        <section id="why" className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div className="space-y-6">
            <div className="space-y-3">
              <p className="text-xs font-medium uppercase tracking-wider text-primary">Why BGC Crypto</p>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
                No Compromise. No Lock-In.
              </h2>
            </div>
            <ul className="space-y-3">
              {[
                'Instant bKash-to-crypto orders',
                'Live BDT conversion rates',
                'Cross-chain swaps via LI.FI',
                'Transparent order & TX history',
                'Bangla + English interface',
              ].map((item) => (
                <li key={item} className="flex items-center gap-3">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-primary shrink-0">
                    <Check className="h-3 w-3" />
                  </span>
                  <span className="text-sm text-muted-foreground">{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-border/70 bg-card/60 p-5 flex flex-col gap-2">
              <Zap className="h-5 w-5 text-primary" />
              <p className="text-sm font-semibold">Fast Delivery</p>
              <p className="text-xs text-muted-foreground leading-relaxed">Automated crypto delivery around the clock.</p>
            </div>
            <div className="rounded-xl border border-border/70 bg-card/60 p-5 flex flex-col gap-2">
              <ShieldCheck className="h-5 w-5 text-primary" />
              <p className="text-sm font-semibold">Verified Orders</p>
              <p className="text-xs text-muted-foreground leading-relaxed">Every payment checked before release.</p>
            </div>
            <div className="rounded-xl border border-border/70 bg-card/60 p-5 flex flex-col gap-2">
              <Layers className="h-5 w-5 text-primary" />
              <p className="text-sm font-semibold">Multi-Chain</p>
              <p className="text-xs text-muted-foreground leading-relaxed">Support for all major stablecoin networks.</p>
            </div>
            <div className="rounded-xl border border-border/70 bg-card/60 p-5 flex flex-col gap-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              <p className="text-sm font-semibold">Real Support</p>
              <p className="text-xs text-muted-foreground leading-relaxed">AI + human help whenever you need it.</p>
            </div>
          </div>
        </section>

        {/* ── Final CTA ── */}
        <section className="rounded-xl border border-border/70 bg-card/60 px-6 py-14 sm:px-10 sm:py-20 text-center flex flex-col items-center gap-6">
          <h2 className="max-w-2xl text-3xl sm:text-4xl font-extrabold tracking-tight">
            Ready to Move Your Money?
          </h2>
          <p className="max-w-xl text-sm sm:text-base leading-relaxed text-muted-foreground">
            Join BGC Crypto today and experience bKash-native crypto trading built for Bangladesh.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
            <Button asChild size="lg" className="h-12 font-semibold w-full sm:w-auto px-8">
              <Link to="/register" className="flex items-center justify-center gap-2">
                Get Started — Free <ArrowRight size={18} />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="h-12 font-semibold w-full sm:w-auto px-8">
              <Link to="/login">I Already Have an Account</Link>
            </Button>
          </div>
        </section>

        {/* ── Footer ── */}
        <footer className="border-t border-border/60 pt-10 pb-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <img src="/logo.jpg" alt="Mouno" className="h-7 w-7 rounded-lg object-cover" />
              <span className="text-sm font-semibold">Mouno — BGC Crypto</span>
            </div>
            <nav className="flex items-center gap-6 text-sm text-muted-foreground">
              <Link to="/faq" className="hover:text-foreground transition-colors">FAQ</Link>
              <Link to="/guide" className="hover:text-foreground transition-colors">Guide</Link>
              <Link to="/terms" className="hover:text-foreground transition-colors">Terms</Link>
              <Link to="/support" className="hover:text-foreground transition-colors">Support</Link>
            </nav>
            <p className="text-xs text-muted-foreground">
              &copy; {new Date().getFullYear()} BGC Crypto. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Landing;
