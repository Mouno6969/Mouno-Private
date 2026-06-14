// Shared API payload types for the Mouno web app.
//
// These mirror the JSON shapes returned by the Flask backend (web_repo/api).
// Keep them in sync with the backend response bodies. Where the backend can
// return either a bare value or a `{ message }` error object, the page/hook is
// responsible for narrowing.

/** Network identifiers used across market, balance and tx endpoints. */
export type NetworkId = string;

/** GET /api/me */
export interface MeResponse {
  username: string;
  telegram_id: string | null;
  created_at?: string;
  telegram_stats?: TelegramStats | null;
}

/** POST /api/login */
export interface LoginResponse {
  username: string;
  token: string;
  telegram_id: string | null;
}

export interface TelegramStats {
  [key: string]: unknown;
}

/** GET /api/market */
export interface MarketResponse {
  rates: Record<NetworkId, number>;
  // Present in some deployments; the UI treats these as optional.
  changes?: Record<NetworkId, number>;
  market_caps?: Record<NetworkId, number>;
  bKash?: string;
  support?: string;
}

/** GET /api/stats */
export interface GlobalStats {
  total_orders: number;
  completed_orders: number;
  total_volume_bdt: number;
  total_users: number;
  new_users_today: number;
}

/** GET /api/recent-activity (array) */
export interface ActivityEntry {
  trx_id: string;
  amount_crypto: number | string;
  network: NetworkId;
  wallet: string;
  status: string;
  created_at: string;
}

/** GET /api/balance */
export interface BalanceResponse {
  balances: Record<NetworkId, string | number>;
  evm_address?: string;
  message?: string;
}

/** GET /api/txlog (array) */
export interface TxEntry {
  trx_id: string;
  amount_bdt: number;
  amount_crypto: number;
  network: NetworkId;
  wallet: string;
  status: string;
  created_at: string;
  order_id: string | null;
  source: string;
}

/** GET /api/orders */
export interface OrderEntry {
  trx_id: string;
  order_id: string | null;
  amount_bdt: number;
  amount_usdc: number;
  network: NetworkId;
  wallet: string;
  status?: string;
  created_at: string;
}

export interface OrdersResponse {
  completed: OrderEntry[];
  pending: OrderEntry[];
}

/** GET /api/portfolio/overview (inside ApiEnvelope.data) */
export interface PortfolioHolding {
  asset: string;
  network: NetworkId;
  label: string | null;
  address: string | null;
  amount: number;
  usd_value: number;
  pct: number;
}

export interface PortfolioOverview {
  net_worth_usd: number;
  change_24h_pct: number | null;
  holdings: PortfolioHolding[];
  alerts_triggered: number[];
}

/** Price alert record (GET /api/price-alerts) */
export interface PriceAlert {
  id: number;
  symbol: string;
  chain: string | null;
  direction: 'above' | 'below';
  target_price: number;
  status: string;
  triggered_at: string | null;
  created_at: string;
}

/** GET /api/analytics/summary (inside ApiEnvelope.data) */
export interface AnalyticsSummary {
  period: string;
  total_volume: number;
  prev_volume: number;
  volume_change_pct: number | null;
  tx_count: number;
  spend_by_asset: { asset: string; usd_value: number }[];
  spend_by_network: { network: NetworkId; usd_value: number }[];
  top_recipients: { address: string; count: number }[];
}

/** Notification record (GET /api/notifications) */
export type NotificationType = 'price_alert' | 'bonus' | 'large_tx' | 'info';

export interface AppNotification {
  id: number;
  type: NotificationType;
  title: string;
  body: string | null;
  read: boolean;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface NotificationsResponse {
  notifications: AppNotification[];
  unread: number;
}

/** Generic wrapped backend response: { ok, message, data }. */
export interface ApiEnvelope<T> {
  ok?: boolean;
  message?: string;
  data?: T;
}

/** Standard error body returned by many endpoints. */
export interface ApiErrorBody {
  message?: string;
  error?: string;
}
