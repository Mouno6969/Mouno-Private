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
  Globe,
  Menu,
  X,
  User
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
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar"

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation();
  const { user, logout, token } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  const location = useLocation();

  const toggleLang = () => {
    const newLang = i18n.language === 'bn' ? 'en' : 'bn';
    i18n.changeLanguage(newLang);
  };

  const navItems = [
    { name: t('buy'), icon: <ShoppingCart className="h-4 w-4" />, path: '/buy' },
    { name: t('swap'), icon: <RefreshCw className="h-4 w-4" />, path: '/swap' },
    { name: t('wallet'), icon: <Wallet className="h-4 w-4" />, path: '/wallet' },
    { name: t('orders'), icon: <History className="h-4 w-4" />, path: '/orders' },
    { name: t('support'), icon: <MessageSquare className="h-4 w-4" />, path: '/support' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Link to="/" className="flex items-center space-x-2">
              <img src="/logo.jpg" alt="Logo" className="h-8 w-8 rounded-full object-cover border border-primary" />
            </Link>
          </div>

          <div className="hidden md:flex items-center space-x-6 text-sm font-medium">
            <Link to="/" className={isActive('/') ? "text-primary" : "text-muted-foreground transition-colors hover:text-primary"}>Dashboard</Link>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={isActive(item.path) ? "text-primary" : "text-muted-foreground transition-colors hover:text-primary"}
              >
                {item.name}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={toggleLang} className="rounded-full">
              <Globe className="h-5 w-5" />
              <span className="sr-only">Toggle language</span>
            </Button>

            {token ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="" alt={user?.username} />
                      <AvatarFallback className="bg-primary/20 text-primary">{user?.username?.[0]?.toUpperCase() || 'U'}</AvatarFallback>
                    </Avatar>
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
                  <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex gap-2">
                <Button asChild variant="ghost" size="sm">
                  <Link to="/login">{t('login')}</Link>
                </Button>
                <Button asChild size="sm">
                  <Link to="/register">{t('register') || 'Register'}</Link>
                </Button>
              </div>
            )}

            <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setIsMenuOpen(!isMenuOpen)}>
              {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </header>

      <div className="flex-1">
        <main className="container py-6 md:py-10">
          {children}
        </main>
      </div>

      <footer className="border-t py-6 md:px-8 md:py-0">
        <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
        </div>
      </footer>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-40 bg-background md:hidden">
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
