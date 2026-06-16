import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import {
  LogOut,
  Languages,
  Home,
  ShoppingCart,
  RefreshCw,
  Wallet,
  Menu,
  X,
  Search,
  ChevronRight,
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
import { NAV_GROUPS, ALL_NAV_ITEMS } from './navConfig';
import NotificationBell from './NotificationBell';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation();
  const { user, logout, token } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const searchRef = React.useRef<HTMLInputElement>(null);
  const location = useLocation();
  const navigate = useNavigate();

  React.useEffect(() => {
    setIsMenuOpen(false);
    setQuery('');
  }, [location.pathname]);

  React.useEffect(() => {
    document.documentElement.lang = i18n.language === 'bn' ? 'bn' : 'en';
  }, [i18n.language]);

  // Press "/" anywhere (outside a field) to focus the sidebar search.
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (e.key === '/' && tag !== 'INPUT' && tag !== 'TEXTAREA') {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const toggleLang = () => {
    i18n.changeLanguage(i18n.language === 'bn' ? 'en' : 'bn');
  };

  // Treat "/" and "/dashboard" as the same route (dashboard aliasing).
  const isActive = (path: string) => {
    const normalized = location.pathname.replace(/\/+$/, '') || '/';
    if (path === '/') return normalized === '/' || normalized === '/dashboard';
    return normalized === path;
  };

  // Live nav search: match dashboard + every nav item by its translated label.
  const searchResults = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    const items = [
      { labelKey: 'nav_dashboard', path: '/', icon: <Home className="h-4 w-4" /> },
      ...ALL_NAV_ITEMS,
    ];
    return items.filter((i) => t(i.labelKey).toLowerCase().includes(q)).slice(0, 6);
  }, [query, t]);

  const goToResult = (path: string) => {
    setQuery('');
    searchRef.current?.blur();
    navigate(path);
  };

  // Resolve a human title for the current route for the header.
  const currentTitle = (() => {
    if (location.pathname === '/' || location.pathname === '/dashboard') {
      return t('nav_dashboard');
    }
    const match = ALL_NAV_ITEMS.find((i) => i.path === location.pathname);
    if (match) return t(match.labelKey);
    const seg = location.pathname.replace('/', '').replace(/-/g, ' ');
    return seg ? seg.charAt(0).toUpperCase() + seg.slice(1) : t('nav_dashboard');
  })();

  const initial = user?.username?.[0]?.toUpperCase() || 'G';

  return (
    <div className="min-h-screen text-foreground">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-xl focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:shadow-lg"
      >
        {t('skip_to_content', 'Skip to content')}
      </a>

      {/* ── Desktop sidebar ── */}
      <aside className="hidden md:flex fixed inset-y-0 left-0 z-40 w-64 flex-col glass-strong border-r border-border/60">
        <div className="flex flex-col gap-5 p-4 h-full">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-3 rounded-2xl border border-border/60 bg-secondary/40 px-3 py-2.5">
            <img src="/logo.jpg" alt="Logo" className="h-9 w-9 rounded-xl object-cover ring-1 ring-primary/40" />
            <div className="min-w-0">
              <p className="text-sm font-bold leading-tight tracking-tight truncate">Mouno</p>
              <p className="text-[10px] font-mono uppercase tracking-[0.18em] text-muted-foreground">BGC Crypto</p>
            </div>
          </Link>

          {/* Search */}
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-[1.25rem] h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              ref={searchRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && searchResults.length > 0) goToResult(searchResults[0].path);
                if (e.key === 'Escape') {
                  setQuery('');
                  searchRef.current?.blur();
                }
              }}
              placeholder={t('search', 'Search') as string}
              className="h-10 w-full rounded-xl border border-border/60 bg-secondary/40 pl-9 pr-10 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label={t('search', 'Search') as string}
            />
            <kbd className="pointer-events-none absolute right-2.5 top-[1.25rem] hidden -translate-y-1/2 select-none rounded-md border border-border/60 bg-background/60 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground lg:inline-block">
              /
            </kbd>

            {query.trim() && (
              <div
                className="absolute left-0 right-0 top-full z-50 mt-2 overflow-hidden rounded-xl border border-border/60 bg-popover/95 shadow-xl backdrop-blur-xl"
                role="listbox"
              >
                {searchResults.length > 0 ? (
                  searchResults.map((item) => (
                    <button
                      key={item.path}
                      type="button"
                      role="option"
                      aria-selected={false}
                      onClick={() => goToResult(item.path)}
                      className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm text-foreground transition-colors hover:bg-secondary/60"
                    >
                      <span className="text-muted-foreground">{item.icon}</span>
                      {t(item.labelKey)}
                    </button>
                  ))
                ) : (
                  <p className="px-3 py-2.5 text-sm text-muted-foreground">{t('no_results', 'No results')}</p>
                )}
              </div>
            )}
          </div>

          {/* Nav */}
          <nav className="flex-1 overflow-y-auto scrollbar-none -mx-1 px-1 flex flex-col gap-5 pb-2">
            <NavLink to="/" icon={<Home className="h-[18px] w-[18px]" />} label={t('nav_dashboard')} active={isActive('/')} />

            {NAV_GROUPS.map((group) => (
              <div key={group.titleKey} className="flex flex-col gap-1">
                <h2 className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground/60">
                  {t(group.titleKey)}
                </h2>
                {group.items.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    icon={item.icon}
                    label={t(item.labelKey)}
                    active={isActive(item.path)}
                  />
                ))}
              </div>
            ))}
          </nav>

          {/* Bottom promo card */}
          <div className="rounded-2xl border border-primary/25 bg-primary/10 p-4">
            <p className="text-sm font-semibold">{t('link_telegram_title', 'Link Telegram')}</p>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {t('link_telegram_desc', 'Connect your account for instant order alerts.')}
            </p>
            <Button asChild size="sm" className="mt-3 w-full">
              <Link to={token ? '/link-telegram' : '/login'} className="flex items-center justify-center gap-1.5">
                {t('connect', 'Connect')} <ChevronRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </div>
      </aside>

      {/* ── Main column ── */}
      <div className="md:pl-64">
        {/* Header */}
        <header className="sticky top-0 z-30 border-b border-border/60 bg-background/70 backdrop-blur-xl">
          <div className="flex h-16 items-center justify-between gap-3 px-4 md:px-8">
            <div className="flex items-center gap-3 min-w-0">
              <Link to="/" className="md:hidden flex items-center gap-2 shrink-0" aria-label="Home">
                <img src="/logo.jpg" alt="Logo" className="h-8 w-8 rounded-xl object-cover ring-1 ring-primary/40" />
              </Link>
              <h1 className="text-lg md:text-xl font-bold tracking-tight truncate">{currentTitle}</h1>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={toggleLang}
                aria-label={t('aria_toggle_language')}
                className="gap-1.5 rounded-xl"
              >
                <Languages className="h-4 w-4" />
                <span className="text-xs font-mono">{i18n.language === 'bn' ? 'EN' : 'বাং'}</span>
              </Button>

              {token && <NotificationBell />}

              {token ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      aria-label={t('aria_account_menu')}
                      className="flex items-center gap-2 rounded-xl border border-border/60 bg-secondary/40 py-1 pl-1 pr-2.5 transition-colors hover:bg-secondary"
                    >
                      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground font-mono text-xs font-bold">
                        {initial}
                      </span>
                      <span className="hidden sm:inline text-sm font-medium max-w-[8rem] truncate">{user?.username}</span>
                    </button>
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

        {/* Content */}
        <main id="main-content" className="min-w-0 px-4 py-6 md:px-8 md:py-8 pb-24 md:pb-10">
          {children}
        </main>
      </div>

      {/* ── Mobile bottom nav ── */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-border/60 bg-background/80 backdrop-blur-xl"
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
        <div className="md:hidden fixed inset-0 z-[60] bg-background/95 backdrop-blur-xl overflow-y-auto">
          <div className="flex items-center justify-between h-16 px-4 border-b border-border/60 sticky top-0 bg-background/80 backdrop-blur">
            <span className="font-mono text-sm font-bold uppercase tracking-widest">{t('nav_more')}</span>
            <Button variant="ghost" size="icon" aria-label={t('aria_close_menu')} onClick={() => setIsMenuOpen(false)}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          <div className="px-4 py-6 flex flex-col gap-8 pb-28">
            {NAV_GROUPS.map((group) => (
              <div key={group.titleKey} className="flex flex-col gap-2">
                <h2 className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground/60">
                  {t(group.titleKey)}
                </h2>
                <div className="grid grid-cols-2 gap-2">
                  {group.items.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setIsMenuOpen(false)}
                      className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm font-medium transition-colors ${
                        isActive(item.path)
                          ? 'border-primary/30 bg-primary/15 text-primary'
                          : 'border-border/60 bg-secondary/30 text-foreground hover:bg-secondary'
                      }`}
                      aria-current={isActive(item.path) ? 'page' : undefined}
                    >
                      <span className={isActive(item.path) ? 'text-primary' : 'text-muted-foreground'}>{item.icon}</span>
                      {t(item.labelKey)}
                    </Link>
                  ))}
                </div>
              </div>
            ))}

            {!token && (
              <div className="flex flex-col gap-2 pt-2 border-t border-border/60">
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

interface NavLinkProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
}

const NavLink: React.FC<NavLinkProps> = ({ to, icon, label, active }) => (
  <Link
    to={to}
    className={`group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
      active
        ? 'bg-primary/15 text-primary ring-1 ring-inset ring-primary/25'
        : 'text-muted-foreground hover:bg-secondary/60 hover:text-foreground'
    }`}
    aria-current={active ? 'page' : undefined}
  >
    <span className={active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}>{icon}</span>
    {label}
  </Link>
);

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
