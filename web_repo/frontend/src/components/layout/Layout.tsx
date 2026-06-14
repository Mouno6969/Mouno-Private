import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import {
  LogOut,
  User,
  Languages,
  Home,
  ShoppingCart,
  RefreshCw,
  Wallet,
  Menu,
  X,
} from 'lucide-react';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { NAV_GROUPS } from './navConfig';
import NotificationBell from './NotificationBell';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation();
  const { user, logout, token } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  const location = useLocation();

  // Close the mobile "More" sheet whenever the route changes.
  React.useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

  // Keep the document language in sync with i18n for screen readers / SEO.
  React.useEffect(() => {
    document.documentElement.lang = i18n.language === 'bn' ? 'bn' : 'en';
  }, [i18n.language]);

  const toggleLang = () => {
    i18n.changeLanguage(i18n.language === 'bn' ? 'en' : 'bn');
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Skip link for keyboard / screen-reader users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:shadow-lg"
      >
        {t('skip_to_content', 'Skip to content')}
      </a>
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-16 items-center justify-between gap-3 px-4 md:px-6">
          <Link to="/" className="flex items-center gap-2 shrink-0" aria-label="Home">
            <img src="/logo.jpg" alt="Logo" className="h-8 w-8 rounded-none object-cover border border-white" />
            <span className="hidden sm:inline font-mono text-sm font-bold tracking-tight">BGC Crypto</span>
          </Link>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleLang}
              aria-label={t('aria_toggle_language')}
              className="rounded-none gap-1 px-2 border border-white/10 hover:border-white"
            >
              <Languages className="h-4 w-4" />
              <span className="text-xs font-mono">{i18n.language === 'bn' ? 'EN' : 'বাং'}</span>
            </Button>

            {token && <NotificationBell />}

            {token ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" aria-label={t('aria_account_menu')} className="relative h-8 w-8 rounded-none border border-white/10 p-0">
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

      <div className="flex">
        {/* ── Desktop grouped sidebar ── */}
        <aside className="hidden md:flex sticky top-16 h-[calc(100vh-4rem)] w-60 shrink-0 flex-col gap-6 overflow-y-auto border-r bg-background/60 px-3 py-6">
          <Link
            to="/"
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isActive('/') ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}
            aria-current={isActive('/') ? 'page' : undefined}
          >
            <Home className="h-4 w-4" />
            {t('nav_dashboard')}
          </Link>

          {NAV_GROUPS.map((group) => (
            <div key={group.titleKey} className="flex flex-col gap-1">
              <h2 className="px-3 pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
                {t(group.titleKey)}
              </h2>
              {group.items.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive(item.path)
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                  aria-current={isActive(item.path) ? 'page' : undefined}
                >
                  {item.icon}
                  {t(item.labelKey)}
                </Link>
              ))}
            </div>
          ))}
        </aside>

        {/* ── Main content ── */}
        <main id="main-content" className="flex-1 min-w-0 px-4 py-6 md:px-8 md:py-10 pb-24 md:pb-10">
          {children}
        </main>
      </div>

      {/* ── Mobile bottom nav ── */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80"
        aria-label="Primary"
      >
        <div className="flex items-center justify-around h-16 px-2">
          <BottomLink to="/" label={t('nav_home')} active={isActive('/')} icon={<Home className="h-5 w-5" />} />
          <BottomLink to="/buy" label={t('buy')} active={isActive('/buy')} icon={<ShoppingCart className="h-5 w-5" />} />
          <BottomLink to="/swap" label={t('swap')} active={isActive('/swap')} icon={<RefreshCw className="h-5 w-5" />} />
          <BottomLink to="/wallet" label={t('nav_wallet')} active={isActive('/wallet')} icon={<Wallet className="h-5 w-5" />} />
          <button
            type="button"
            onClick={() => setIsMenuOpen((v) => !v)}
            aria-label={t('nav_more')}
            aria-expanded={isMenuOpen}
            className={`flex flex-col items-center justify-center gap-1 min-h-11 min-w-11 px-2 ${
              isMenuOpen ? 'text-primary' : 'text-muted-foreground'
            }`}
          >
            <Menu className="h-5 w-5" />
            <span className="text-xs font-medium">{t('nav_more')}</span>
          </button>
        </div>
      </nav>

      {/* ── Mobile "More" grouped sheet ── */}
      {isMenuOpen && (
        <div className="md:hidden fixed inset-0 z-[60] bg-background overflow-y-auto">
          <div className="flex items-center justify-between h-16 px-4 border-b sticky top-0 bg-background/95 backdrop-blur">
            <span className="font-mono text-sm font-bold uppercase tracking-widest">{t('nav_more')}</span>
            <Button variant="ghost" size="icon" aria-label={t('aria_close_menu')} onClick={() => setIsMenuOpen(false)}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          <div className="px-4 py-6 flex flex-col gap-8 pb-28">
            {NAV_GROUPS.map((group) => (
              <div key={group.titleKey} className="flex flex-col gap-2">
                <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
                  {t(group.titleKey)}
                </h2>
                <div className="grid grid-cols-2 gap-2">
                  {group.items.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setIsMenuOpen(false)}
                      className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-sm font-medium transition-colors ${
                        isActive(item.path)
                          ? 'border-primary/30 bg-primary/10 text-primary'
                          : 'border-muted text-foreground hover:bg-muted'
                      }`}
                      aria-current={isActive(item.path) ? 'page' : undefined}
                    >
                      <span className="text-primary">{item.icon}</span>
                      {t(item.labelKey)}
                    </Link>
                  ))}
                </div>
              </div>
            ))}

            {!token && (
              <div className="flex flex-col gap-2 pt-2 border-t">
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

interface BottomLinkProps {
  to: string;
  label: string;
  active: boolean;
  icon: React.ReactNode;
}

const BottomLink: React.FC<BottomLinkProps> = ({ to, label, active, icon }) => (
  <Link
    to={to}
    className={`flex flex-col items-center justify-center gap-1 min-h-11 min-w-11 px-2 ${
      active ? 'text-primary' : 'text-muted-foreground'
    }`}
    aria-current={active ? 'page' : undefined}
  >
    {icon}
    <span className="text-xs font-medium">{label}</span>
  </Link>
);

export default Layout;
