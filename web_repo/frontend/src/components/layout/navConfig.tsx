import React from 'react';
import {
  ShoppingCart,
  RefreshCw,
  Sparkles,
  Store,
  History,
  Wallet,
  Layers,
  Coins,
  Banknote,
  PieChart,
  BarChart3,
  LineChart,
  ScrollText,
  Search,
  User,
  Gift,
  Wrench,
  Send,
  MessageSquare,
  LifeBuoy,
  HelpCircle,
  BookOpen,
  ShieldAlert,
} from 'lucide-react';

export interface NavItem {
  /** i18n key for the visible label */
  labelKey: string;
  icon: React.ReactNode;
  path: string;
}

export interface NavGroup {
  /** i18n key for the group heading */
  titleKey: string;
  items: NavItem[];
}

/**
 * Single source of truth for the app's navigation. Consumed by both the
 * desktop sidebar and the mobile "More" sheet so the two never drift apart.
 */
export const NAV_GROUPS: NavGroup[] = [
  {
    titleKey: 'nav_trade',
    items: [
      { labelKey: 'buy', icon: <ShoppingCart className="h-4 w-4" />, path: '/buy' },
      { labelKey: 'swap', icon: <RefreshCw className="h-4 w-4" />, path: '/swap' },
      { labelKey: 'smart_trading', icon: <Sparkles className="h-4 w-4" />, path: '/automation' },
      { labelKey: 'market', icon: <Store className="h-4 w-4" />, path: '/market' },
      { labelKey: 'orders', icon: <History className="h-4 w-4" />, path: '/orders' },
    ],
  },
  {
    titleKey: 'nav_wallet',
    items: [
      { labelKey: 'wallet', icon: <Wallet className="h-4 w-4" />, path: '/wallet' },
      { labelKey: 'nav_unified', icon: <Layers className="h-4 w-4" />, path: '/unified' },
      { labelKey: 'nav_portfolio', icon: <PieChart className="h-4 w-4" />, path: '/portfolio' },
      { labelKey: 'nav_balance', icon: <Coins className="h-4 w-4" />, path: '/balance' },
      { labelKey: 'nav_analytics', icon: <BarChart3 className="h-4 w-4" />, path: '/analytics' },
      { labelKey: 'nav_insights', icon: <LineChart className="h-4 w-4" />, path: '/insights' },
      { labelKey: 'nav_payout', icon: <Banknote className="h-4 w-4" />, path: '/payout' },
      { labelKey: 'nav_txlog', icon: <ScrollText className="h-4 w-4" />, path: '/txlog' },
      { labelKey: 'nav_order_status', icon: <Search className="h-4 w-4" />, path: '/order-status' },
    ],
  },
  {
    titleKey: 'nav_rewards',
    items: [
      { labelKey: 'referral', icon: <User className="h-4 w-4" />, path: '/referral' },
      { labelKey: 'gift', icon: <Gift className="h-4 w-4" />, path: '/gift' },
      { labelKey: 'nav_giveaway', icon: <Gift className="h-4 w-4" />, path: '/giveaway' },
      { labelKey: 'sellers', icon: <Store className="h-4 w-4" />, path: '/seller' },
      { labelKey: 'free_tools', icon: <Wrench className="h-4 w-4" />, path: '/tools' },
      { labelKey: 'forward_telegram', icon: <Send className="h-4 w-4" />, path: '/forward' },
    ],
  },
  {
    titleKey: 'nav_help',
    items: [
      { labelKey: 'support', icon: <MessageSquare className="h-4 w-4" />, path: '/support' },
      { labelKey: 'my_tickets', icon: <LifeBuoy className="h-4 w-4" />, path: '/tickets' },
      { labelKey: 'nav_faq', icon: <HelpCircle className="h-4 w-4" />, path: '/faq' },
      { labelKey: 'nav_guide', icon: <BookOpen className="h-4 w-4" />, path: '/guide' },
      { labelKey: 'nav_terms', icon: <ShieldAlert className="h-4 w-4" />, path: '/terms' },
    ],
  },
];

/** Flattened list of every nav item, useful for lookups. */
export const ALL_NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);
