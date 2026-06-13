import React from 'react';
import { SWRConfig } from 'swr';
import { fetcher } from './apiClient';

// Polling intervals (ms) used across the app for "live" data.
export const REFRESH_INTERVALS = {
  fast: 10_000, // market rates, live activity
  normal: 30_000, // balances, dashboard aggregates
  slow: 60_000, // orders / history
} as const;

/**
 * Global SWR provider.
 *
 * Important behaviors:
 *  - `fetcher` uses the central axios apiClient (auth + error toasts).
 *  - `refreshWhenHidden` is left at its default (false), so any `refreshInterval`
 *    set on a hook automatically PAUSES while the browser tab is backgrounded
 *    and resumes on focus. This replaces the old always-on setInterval polling.
 *  - `revalidateOnFocus` re-fetches when the user returns to the tab.
 */
export const AppSWRConfig: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <SWRConfig
      value={{
        fetcher,
        revalidateOnFocus: true,
        revalidateOnReconnect: true,
        shouldRetryOnError: true,
        errorRetryCount: 3,
        dedupingInterval: 5_000,
        // refreshWhenHidden defaults to false → background polling is paused.
      }}
    >
      {children}
    </SWRConfig>
  );
};
