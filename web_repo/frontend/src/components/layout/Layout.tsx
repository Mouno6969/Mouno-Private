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
  ChevronDown,
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
  const [expandedGroups, setExpandedGroups] = React.useState<Record<string, boolean>>({});
  const searchRef = React.useRef<HTMLInputElement>(null);
  const contentRef = React.useRef<HTMLDivElement>(null);
  const location = useLocation();
  const navigate = useNavigate();

  // Subtle per-navigation fade
  React.useEffect(() => {
    const el = contentRef.current;
    if (!el) return;
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return;
    // Guard against environments without the Web Animations API (e.g. jsdom in
    // tests, or older browsers) so the page render never throws.
    if (typeof el.animate !== 'function') return;
    el.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 200, easing: 'ease-out' });
  }, [location.pathname]);

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

  // Auto-expand the group that contains the current route
  React.useEffect(() => {
    const currentGroup = NAV_GROUPS.find(g => g.items.some(i => i.path === location.pathname));
    if (currentGroup) {
      setExpandedGroups(prev => ({ ...prev, [currentGroup.titleKey]: true }));
    }
  }, [location.pathname]);

  const toggleLang = () => {
    i18n.changeLanguage(i18n.language === 'bn' ? 'en' : 'bn');
  };

  const toggleGroup = (key: string) => {
    setExpandedGroups(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const isActive = (path: string) => {
    const normalized = location.pathname.replace(/\/+$/, '') || '/';
    if (path === '/') return normalized === '/' || normalized === '/dashboard';
    return normalized === path;
  };

  // Live nav search
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
      <aside className="hidden md:flex fixed inset-y-0 left-0 z-40 w-60 flex-col bg-card/95 border-r border-border/70">
        <div className="flex flex-col gap-4 p-4 h-full">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2.5 px-2 py-2">
            <img src="/logo.jpg" alt="Logo" className="h-8 w-8 rounded-lg object-cover" />
            <div className="min-w-0">
              <p className="text-sm font-bold leading-tight tracking-tight truncate">BGC</p>
              <p className="text-[10px] text-muted-foreground">BGC Crypto</p>
            </div>
          </Link>

          {/* Search */}
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
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
              className="h-9 w-full rounded-lg border border-border/70 bg-muted/40 pl-8 pr-9 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label={t('search', 'Search') as string}
            />
            <kbd className="pointer-events-none absolute right-2.5 top-1/2 hidden -translate-y-1/2 select-none rounded border border-border/60 bg-background/60 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground lg:inline-block">
              /
            </kbd>

            {query.trim() && (
              <div
                className="absolute left-0 right-0 top-full z-50 mt-1.5 overflow-hidden rounded-lg border border-border/70 bg-popover shadow-lg"
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
                      className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm text-foreground transition-colors hover:bg-muted/60"
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
          <nav className="flex-1 overflow-y-auto scrollbar-none -mx-1 px-1 flex flex-col gap-1 pb-2">
            <NavLink to="/" icon={<Home className="h-4 w-4" />} label={t('nav_dashboard')} active={isActive('/')} />

            {NAV_GROUPS.map((group) => {
              const hasActiveChild = group.items.some(i => isActive(i.path));
              // Default to open when a child is active, but an explicit toggle
              // (stored in expandedGroups) always wins — so the active group can
              // still be collapsed.
              const isExpanded = expandedGroups[group.titleKey] ?? hasActiveChild;
              return (
                <div key={group.titleKey} className="flex flex-col">
                  <button
                    type="button"
                    onClick={() => toggleGroup(group.titleKey)}
                    aria-expanded={isExpanded}
                    className="flex items-center justify-between px-3 py-2 text-[11px] font-semibold tracking-wide text-muted-foreground/70 hover:text-muted-foreground transition-colors"
                  >
                    {t(group.titleKey)}
                    <ChevronDown className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-0' : '-rotate-90'}`} />
                  </button>
                  {isExpanded && (
                    <div className="flex flex-col gap-0.5 mb-2">
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
                  )}
                </div>
              );
            })}
          </nav>

          {/* Bottom promo card */}
          <div className="rounded-lg border border-primary/20 bg-primary/5 p-3.5">
            <p className="text-sm font-medium">{t('link_telegram_title', 'Link Telegram')}</p>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {t('link_telegram_desc', 'Connect your account for instant order alerts.')}
            </p>
            <Button asChild size="sm" className="mt-2.5 w-full h-8">
              <Link to={token ? '/link-telegram' : '/login'} className="flex items-center justify-center gap-1.5 text-xs">
                {t('connect', 'Connect')} <ChevronRight className="h-3 w-3" />
              </Link>
            </Button>
          </div>
        </div>
      </aside>

      {/* ── Main column ── */}
      <div className="md:pl-60">
        {/* Header */}
        <header className="sticky top-0 z-30 border-b border-border/60 bg-background/85 backdrop-blur-lg">
          <div className="flex h-14 items-center justify-between gap-3 px-4 md:px-6">
            <div className="flex items-center gap-3 min-w-0">
              <Link to="/" className="md:hidden flex items-center gap-2 shrink-0" aria-label="Home">
                <img src="/logo.jpg" alt="Logo" className="h-7 w-7 rounded-lg object-cover" />
              </Link>
              <h1 className="text-base md:text-lg font-semibold tracking-tight truncate">{currentTitle}</h1>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleLang}
                aria-label={t('aria_toggle_language')}
                className="gap-1.5 h-8 px-2.5"
              >
                <Languages className="h-3.5 w-3.5" />
                <span className="text-xs font-mono">{i18n.language === 'bn' ? 'EN' : 'বাং'}</span>
              </Button>

              {token && <NotificationBell />}

              {token ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      aria-label={t('aria_account_menu')}
                      className="flex items-center gap-2 rounded-lg border border-border/70 bg-muted/40 py-1 pl-1 pr-2.5 transition-colors hover:bg-muted"
                    >
                      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground text-xs font-bold">
                        {initial}
                      </span>
                      <span className="hidden sm:inline text-sm font-medium max-w-[8rem] truncate">{user?.username}</span>
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-52" align="end" forceMount>
                    <DropdownMenuLabel className="font-normal">
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">{user?.username}</p>
                        <p className="text-xs leading-none text-muted-foreground">User ID: {user?.telegram_id || 'N/A'}</p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {!user?.telegram_id && (
                      <DropdownMenuItem asChild>
                        <Link to="/link-telegram">{t('connect_telegram', 'Link Telegram')}</Link>
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>{t('logout', 'Log out')}</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <div className="hidden sm:flex gap-2">
                  <Button asChild variant="ghost" size="sm" className="h-8">
                    <Link to="/login">{t('login')}</Link>
                  </Button>
                  <Button asChild size="sm" className="h-8">
                    <Link to="/register">{t('register') || 'Register'}</Link>
                  </Button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <main
          id="main-content"
          className="min-w-0 px-4 py-6 md:px-6 md:py-8 pb-[calc(5rem+env(safe-area-inset-bottom))] md:pb-8"
        >
          <div ref={contentRef} className="mx-auto w-full max-w-6xl">
            {children}
          </div>
        </main>
      </div>

      {/* ── Mobile bottom nav ── */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-border/60 bg-background/90 backdrop-blur-lg pb-[env(safe-area-inset-bottom)]"
        aria-label="Primary"
      >
        <div className="flex items-center justify-around h-14 px-2">
          <BottomLink to="/" label={t('nav_home')} active={isActive('/')} icon={<Home className="h-5 w-5" />} />
          <BottomLink to="/buy" label={t('buy')} active={isActive('/buy')} icon={<ShoppingCart className="h-5 w-5" />} />
          <BottomLink to="/swap" label={t('swap')} active={isActive('/swap')} icon={<RefreshCw className="h-5 w-5" />} />
          <BottomLink to="/wallet" label={t('nav_wallet')} active={isActive('/wallet')} icon={<Wallet className="h-5 w-5" />} />
          <button
            type="button"
            onClick={() => setIsMenuOpen((v) => !v)}
            aria-label={t('nav_more')}
            aria-expanded={isMenuOpen}
            className={`flex flex-col items-center justify-center gap-0.5 min-h-11 min-w-11 px-2 ${
              isMenuOpen ? 'text-primary' : 'text-muted-foreground'
            }`}
          >
            <Menu className="h-5 w-5" />
            <span className="text-[10px] font-medium">{t('nav_more')}</span>
          </button>
        </div>
      </nav>

      {/* ── Mobile "More" sheet ── */}
      {isMenuOpen && (
        <div className="md:hidden fixed inset-0 z-[60] bg-background/98 backdrop-blur-sm overflow-y-auto">
          <div className="flex items-center justify-between h-14 px-4 border-b border-border/60 sticky top-0 bg-background/90 backdrop-blur">
            <span className="text-sm font-semibold">{t('nav_more')}</span>
            <Button variant="ghost" size="icon" aria-label={t('aria_close_menu')} onClick={() => setIsMenuOpen(false)}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          <div className="px-4 py-5 flex flex-col gap-6 pb-28">
            {NAV_GROUPS.map((group) => (
              <div key={group.titleKey} className="flex flex-col gap-2">
                <h2 className="text-[11px] font-semibold tracking-wide text-muted-foreground/70 px-1">
                  {t(group.titleKey)}
                </h2>
                <div className="grid grid-cols-2 gap-2">
                  {group.items.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setIsMenuOpen(false)}
                      className={`flex items-center gap-2.5 rounded-lg border px-3.5 py-2.5 text-sm font-medium transition-colors ${
                        isActive(item.path)
                          ? 'border-primary/30 bg-primary/10 text-primary'
                          : 'border-border/60 bg-muted/30 text-foreground hover:bg-muted/60'
                      }`}
                      aria-current={isActive(item.path) ? 'page' : undefined}
                    >
                      <span className={`shrink-0 ${isActive(item.path) ? 'text-primary' : 'text-muted-foreground'}`}>{item.icon}</span>
                      <span className="truncate">{t(item.labelKey)}</span>
                    </Link>
                  ))}
                </div>
              </div>
            ))}

            {!token && (
              <div className="flex flex-col gap-2 pt-3 border-t border-border/60">
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
    className={`group flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      active
        ? 'bg-primary/10 text-primary'
        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
    }`}
    aria-current={active ? 'page' : undefined}
  >
    <span className={`shrink-0 ${active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}`}>{icon}</span>
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
    className={`flex flex-col items-center justify-center gap-0.5 min-h-11 min-w-11 px-2 ${
      active ? 'text-primary' : 'text-muted-foreground'
    }`}
    aria-current={active ? 'page' : undefined}
  >
    {icon}
    <span className="text-[10px] font-medium">{label}</span>
  </Link>
);

export default Layout;
