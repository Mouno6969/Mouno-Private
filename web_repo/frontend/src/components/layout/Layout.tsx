import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  ShoppingCart,
  RefreshCw,
  Wallet,
  History,
  MessageSquare,
  LogOut,
  Menu,
  User,
  Store,
  Gift,
  Coins,
  HelpCircle,
  ShieldAlert,
  ScrollText,
  Search,
  Banknote,
  BookOpen,
  Languages,
  Home,
  Sparkles
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

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation();
  const { user, logout, token } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  const location = useLocation();

  // Close the mobile menu whenever the route changes so navigation always works
  React.useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

  const toggleLang = () => {
    const newLang = i18n.language === 'bn' ? 'en' : 'bn';
    i18n.changeLanguage(newLang);
  };

  const navItems = [
    { name: t('buy'), icon: <ShoppingCart className="h-4 w-4" />, path: '/buy' },
    { name: t('swap'), icon: <RefreshCw className="h-4 w-4" />, path: '/swap' },
    { name: t('wallet'), icon: <Wallet className="h-4 w-4" />, path: '/wallet' },
    { name: t('orders'), icon: <History className="h-4 w-4" />, path: '/orders' },
    { name: t('referral'), icon: <User className="h-4 w-4" />, path: '/referral' },
    { name: t('gift'), icon: <User className="h-4 w-4" />, path: '/gift' },
    { name: t('sellers'), icon: <Store className="h-4 w-4" />, path: '/seller' },
    { name: t('support'), icon: <MessageSquare className="h-4 w-4" />, path: '/support' },
    { name: 'Giveaway', icon: <Gift className="h-4 w-4" />, path: '/giveaway' },
    { name: 'Balance', icon: <Coins className="h-4 w-4" />, path: '/balance' },
    { name: 'TX Log', icon: <ScrollText className="h-4 w-4" />, path: '/txlog' },
    { name: 'Order Status', icon: <Search className="h-4 w-4" />, path: '/order-status' },
    { name: 'Payout', icon: <Banknote className="h-4 w-4" />, path: '/payout' },
    { name: 'FAQ', icon: <HelpCircle className="h-4 w-4" />, path: '/faq' },
    { name: 'Guide', icon: <BookOpen className="h-4 w-4" />, path: '/guide' },
    { name: 'Terms', icon: <ShieldAlert className="h-4 w-4" />, path: '/terms' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4">
        <div className="container flex h-16 items-center justify-between gap-3">
          <div className="flex items-center gap-2 shrink-0">
            <Link to="/" className="flex items-center space-x-2">
              <img src="/logo.jpg" alt="Logo" className="h-8 w-8 rounded-none object-cover border border-white" />
            </Link>
          </div>

          {/* Horizontal scrollable nav (visible on all sizes) */}
          <nav className="flex-1 min-w-0 flex items-center gap-2 overflow-x-auto scrollbar-none text-[11px] uppercase tracking-widest font-mono py-2">
            <Link
              to="/"
              className={
                isActive('/')
                  ? "shrink-0 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-foreground"
                  : "shrink-0 px-2 py-1 text-muted-foreground transition-colors hover:text-primary"
              }
            >
              Dashboard
            </Link>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={
                  isActive(item.path)
                    ? "shrink-0 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-foreground"
                    : "shrink-0 px-2 py-1 text-muted-foreground transition-colors hover:text-primary"
                }
              >
                {item.name}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2 shrink-0">
            <Button variant="ghost" size="sm" onClick={toggleLang} className="rounded-none gap-1 px-2 border border-white/10 hover:border-white">
              <Languages className="h-4 w-4" />
              <span className="text-xs font-mono">{i18n.language === 'bn' ? 'EN' : 'বাং'}</span>
            </Button>

            {token ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-none border border-white/10 p-0">
                    <div className="h-full w-full bg-white/10 flex items-center justify-center font-mono text-xs">
                      {user?.username?.[0]?.toUpperCase() || 'U'}
                    </div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">{user?.username}</p>
                      <p className="text-xs leading-none text-muted-foreground">User ID: {user?.telegram_id || 'N/A'}</p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {!user?.telegram_id && (
                    <DropdownMenuItem asChild>
                      <Link to="/link-telegram">Link Telegram</Link>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="hidden sm:flex gap-2">
                <Button asChild variant="ghost" size="sm">
                  <Link to="/login">{t('login')}</Link>
                </Button>
                <Button asChild size="sm">
                  <Link to="/register">{t('register') || 'Register'}</Link>
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex-1">
        <main className="container py-6 md:py-10 pb-24 md:pb-10">
          {children}
        </main>
      </div>

      {/* Bottom Navigation Bar */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="container flex items-center justify-around h-16 px-4">
          <Link to="/" onClick={() => setIsMenuOpen(false)} className={`flex flex-col items-center justify-center gap-1 min-h-11 min-w-11 px-2 ${isActive('/') ? 'text-primary' : 'text-muted-foreground'}`}>
            <Home className="h-5 w-5" />
            <span className="text-[10px] font-medium">Home</span>
          </Link>
          <Link
            to={token ? '/wallet' : '/login'}
            onClick={() => setIsMenuOpen(false)}
            className={`flex flex-col items-center justify-center gap-1 min-h-11 min-w-11 px-2 ${isActive('/wallet') || isActive('/login') ? 'text-primary' : 'text-muted-foreground'}`}
          >
            <User className="h-5 w-5" />
            <span className="text-[10px] font-medium">Account</span>
          </Link>
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className={`flex flex-col items-center justify-center gap-1 min-h-11 min-w-11 px-2 ${isMenuOpen ? 'text-primary' : 'text-muted-foreground'}`}
          >
            <Menu className="h-5 w-5" />
            <span className="text-[10px] font-medium">Menu</span>
          </button>
          <Link to="/support" onClick={() => setIsMenuOpen(false)} className={`flex flex-col items-center justify-center gap-1 min-h-11 min-w-11 px-2 ${isActive('/support') ? 'text-primary' : 'text-muted-foreground'}`}>
            <Sparkles className="h-5 w-5" />
            <span className="text-[10px] font-medium">Support</span>
          </Link>
        </div>
      </nav>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-40 bg-background overflow-y-auto pb-24">
          <div className="container flex flex-col gap-6 pt-20">
            <Link to="/" onClick={() => setIsMenuOpen(false)} className="flex items-center gap-4 text-lg font-medium">
              <LayoutDashboard className="h-5 w-5 text-primary" />
              Dashboard
            </Link>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center gap-4 text-lg font-medium text-muted-foreground"
              >
                <span className="text-primary">{item.icon}</span>
                {item.name}
              </Link>
            ))}
            {!token && (
              <div className="flex flex-col gap-2 pt-4 border-t">
                <Button asChild className="w-full">
                  <Link to="/login" onClick={() => setIsMenuOpen(false)}>{t('login')}</Link>
                </Button>
                <Button asChild variant="outline" className="w-full">
                  <Link to="/register" onClick={() => setIsMenuOpen(false)}>{t('register') || 'Register'}</Link>
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;
