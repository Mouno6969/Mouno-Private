// Typed SWR hooks for the Mouno web app.
//
// These wrap useSWR with the central fetcher (auth + error handling lives in
// apiClient) and the shared payload types, so pages get fully-typed live data
// with background-paused polling for free.

import useSWR, { type SWRConfiguration } from 'swr';
import { REFRESH_INTERVALS } from './swrConfig';
import type {
  MarketResponse,
  GlobalStats,
  ActivityEntry,
  BalanceResponse,
  TxEntry,
  OrdersResponse,
} from '../types';

/** Normalize endpoints that may return either an array or `{ data: [] }`. */
function asArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && Array.isArray((value as { data?: unknown }).data)) {
    return (value as { data: T[] }).data;
  }
  return [];
}

/** Live market rates (fast polling, pauses when tab hidden). */
export function useMarket(config?: SWRConfiguration<MarketResponse>) {
  return useSWR<MarketResponse>('/api/market', {
    refreshInterval: REFRESH_INTERVALS.fast,
    ...config,
  });
}

/** Global platform stats. */
export function useStats(config?: SWRConfiguration<GlobalStats>) {
  return useSWR<GlobalStats>('/api/stats', {
    refreshInterval: REFRESH_INTERVALS.normal,
    ...config,
  });
}

/** Public recent activity feed (already privacy-masked by the backend). */
export function useRecentActivity(config?: SWRConfiguration<ActivityEntry[]>) {
  const swr = useSWR<ActivityEntry[]>('/api/recent-activity', {
    refreshInterval: REFRESH_INTERVALS.fast,
    ...config,
  });
  return { ...swr, data: asArray<ActivityEntry>(swr.data) };
}

/** Authenticated wallet balances. Pass `enabled=false` to skip when logged out. */
export function useBalance(enabled = true, config?: SWRConfiguration<BalanceResponse>) {
  return useSWR<BalanceResponse>(enabled ? '/api/balance' : null, {
    refreshInterval: REFRESH_INTERVALS.normal,
    ...config,
  });
}

/** Authenticated transaction log. */
export function useTxLog(enabled = true, config?: SWRConfiguration<TxEntry[]>) {
  const swr = useSWR<TxEntry[]>(enabled ? '/api/txlog' : null, config);
  return { ...swr, data: asArray<TxEntry>(swr.data) };
}

/** Authenticated orders (active + pending). */
export function useOrders(enabled = true, config?: SWRConfiguration<OrdersResponse>) {
  return useSWR<OrdersResponse>(enabled ? '/api/orders' : null, config);
}
