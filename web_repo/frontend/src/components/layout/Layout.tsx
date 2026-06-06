import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import {
  LogOut,
  Menu,
  X,
  ChevronRight,
  Monitor
} from 'lucide-react';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu"
import { Avatar, AvatarFallback } from "../ui/avatar"
import Marquee from '../ui/Marquee';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation();
  const { user, logout, token } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  const [marketData, setMarketData] = useState<any>(null);
  const location = useLocation();

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
    const interval = setInterval(fetchMarket, 60000);
    return () => clearInterval(interval);
  }, []);

  const toggleLang = () => {
    const newLang = i18n.language === 'bn' ? 'en' : 'bn';
    i18n.changeLanguage(newLang);
  };

  const navItems = [
    { name: t('buy'), path: '/buy' },
    { name: t('swap'), path: '/swap' },
    { name: t('wallet'), path: '/wallet' },
    { name: t('orders'), path: '/orders' },
    { name: t('referral'), path: '/referral' },
    { name: t('sellers'), path: '/seller' },
    { name: 'Balance', path: '/balance' },
    { name: 'TX Log', path: '/txlog' },
  ];

  const secondaryNav = [
    { name: 'Payout', path: '/payout' },
    { name: 'FAQ', path: '/faq' },
    { name: 'Guide', path: '/guide' },
    { name: 'Terms', path: '/terms' },
    { name: 'Giveaway', path: '/giveaway' },
    { name: 'Order Status', path: '/order-status' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans selection:bg-white selection:text-black">
      {/* Top Marquee */}
      <div className="border-b border-white/10 bg-black py-1 overflow-hidden">
        <Marquee direction="left" duration="30s" className="text-[10px] uppercase tracking-[0.2em] font-mono text-white/50">
          <span className="mx-4">Fast Swaps ◈ Secure ◈ Automated Transactions</span>
          <span className="mx-4">System: Online ● Live Rates: ৳{marketData?.rates?.solana || '...'} (SOL) ◈ ৳{marketData?.rates?.ethereum || '...'} (ETH)</span>
          <span className="mx-4">Empowering the Decentralized Future ◈ No intermediaries ◈ Direct Settlement</span>
        </Marquee>
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-black/80 backdrop-blur-md px-4">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center space-x-2">
               <div className="w-8 h-8 bg-white rounded-none flex items-center justify-center">
                  <span className="text-black font-heading font-bold text-xl">M</span>
               </div>
            </Link>

            <nav className="hidden xl:flex items-center space-x-6 text-[10px] uppercase tracking-widest font-heading font-medium">
              <Link to="/" className={isActive('/') ? "text-white" : "text-white/40 transition-colors hover:text-white"}>Dashboard</Link>
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={isActive(item.path) ? "text-white" : "text-white/40 transition-colors hover:text-white"}
                >
                  {item.name}
                </Link>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={toggleLang} className="hover:bg-white/5 rounded-none h-8 text-[10px] tracking-widest">
              {i18n.language === 'bn' ? 'EN' : 'বাং'}
            </Button>

            {token ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-none border border-white/10 p-0">
                    <Avatar className="h-full w-full rounded-none">
                      <AvatarFallback className="bg-white text-black rounded-none text-xs">{user?.username?.[0]?.toUpperCase() || 'U'}</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56 bg-black border-white/10 rounded-none" align="end">
                  <DropdownMenuLabel className="font-heading uppercase tracking-widest text-[10px] text-white/50">Account</DropdownMenuLabel>
                  <DropdownMenuSeparator className="bg-white/10" />
                  <div className="px-2 py-1.5">
                    <p className="text-xs font-medium text-white">{user?.username}</p>
                    <p className="text-[10px] text-white/40 mt-0.5 font-mono">ID: {user?.telegram_id || 'N/A'}</p>
                  </div>
                  <DropdownMenuSeparator className="bg-white/10" />
                  <DropdownMenuItem asChild className="text-[10px] uppercase tracking-wider focus:bg-white focus:text-black rounded-none">
                      <Link to="/wallet">Personal Wallet</Link>
                  </DropdownMenuItem>
                  {!user?.telegram_id && (
                    <DropdownMenuItem asChild className="text-[10px] uppercase tracking-wider focus:bg-white focus:text-black rounded-none">
                      <Link to="/link-telegram">Link Telegram</Link>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator className="bg-white/10 xl:hidden" />
                  {/* Secondary items for small screens in dropdown */}
                  <div className="xl:hidden">
                    {secondaryNav.map(item => (
                       <DropdownMenuItem key={item.path} asChild className="text-[10px] uppercase tracking-wider focus:bg-white focus:text-black rounded-none">
                        <Link to={item.path}>{item.name}</Link>
                      </DropdownMenuItem>
                    ))}
                  </div>
                  <DropdownMenuSeparator className="bg-white/10" />
                  <DropdownMenuItem onClick={logout} className="text-[10px] uppercase tracking-wider text-red-500 focus:bg-red-500 focus:text-white rounded-none">
                    <LogOut className="mr-2 h-3 w-3" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex gap-2">
                <Button asChild variant="ghost" className="h-8 text-[10px] uppercase tracking-widest rounded-none hover:bg-white/5 px-3">
                  <Link to="/login">{t('login')}</Link>
                </Button>
                <Button asChild className="h-8 text-[10px] uppercase tracking-widest rounded-none bg-white text-black hover:bg-white/90 px-3">
                  <Link to="/register">{t('register') || 'Register'}</Link>
                </Button>
              </div>
            )}

            <Button variant="ghost" size="icon" className="xl:hidden text-white hover:bg-white/5" onClick={() => setIsMenuOpen(!isMenuOpen)}>
              {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <main className="container py-12 flex-1">
          {children}
        </main>
      </div>

      {/* Footer Marquee */}
      <div className="border-t border-white/10 bg-black py-4 overflow-hidden">
        <Marquee direction="right" duration="50s" className="text-[10px] uppercase tracking-[0.3em] font-mono text-white/20">
          <span className="mx-8">Non-custodial infrastructure ◇ Mouno Web v1.0.4 ◇ Decentralized Future ◇</span>
          <span className="mx-8">Available 24/7 ◇ Multi-Chain Support ◇ Secure Liquidity ◇</span>
          <span className="mx-8">Direct On-Chain Settlement ◇ User-coordinated Interface ◇</span>
        </Marquee>
      </div>

      <footer className="border-t border-white/10 bg-black py-8">
        <div className="container flex flex-col md:flex-row items-center justify-between gap-6">
           <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-white/10 flex items-center justify-center">
                 <span className="text-[10px] font-bold">M</span>
              </div>
              <span className="text-[10px] uppercase tracking-[0.2em] text-white/40">Mouno Web OS · 2024</span>
           </div>

           <div className="flex flex-wrap justify-center gap-x-8 gap-y-4 text-[10px] uppercase tracking-widest text-white/30">
              {secondaryNav.map(item => (
                <Link key={item.path} to={item.path} className="hover:text-white transition-colors">{item.name}</Link>
              ))}
              <Link to="/support" className="hover:text-white transition-colors">Support</Link>
           </div>
        </div>
      </footer>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-40 bg-black xl:hidden animate-in fade-in slide-in-from-top duration-300">
          <div className="container h-full overflow-y-auto flex flex-col gap-8 pt-24 px-8 pb-12">
            <Link to="/" onClick={() => setIsMenuOpen(false)} className="flex items-center justify-between text-2xl font-heading font-bold uppercase tracking-tighter">
              Dashboard
              <ChevronRight className="text-white/20" />
            </Link>
            {[...navItems, ...secondaryNav, { name: 'Support', path: '/support' }].map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center justify-between text-xl font-heading font-bold uppercase tracking-tighter text-white/40"
              >
                {item.name}
                <ChevronRight className="text-white/10" />
              </Link>
            ))}
            {!token && (
              <div className="flex flex-col gap-4 pt-8 border-t border-white/10">
                <Button asChild className="w-full bg-white text-black h-12 rounded-none uppercase tracking-widest font-bold">
                  <Link to="/login" onClick={() => setIsMenuOpen(false)}>{t('login')}</Link>
                </Button>
                <Button asChild variant="outline" className="w-full border-white/20 text-white h-12 rounded-none uppercase tracking-widest">
                  <Link to="/register" onClick={() => setIsMenuOpen(false)}>{t('register')}</Link>
                </Button>
              </div>
            )}
            <div className="mt-auto">
               <div className="flex items-center gap-2 text-white/20">
                  <Monitor size={14} />
                  <span className="text-[10px] uppercase tracking-widest">System v1.0.4</span>
               </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;
