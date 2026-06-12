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
