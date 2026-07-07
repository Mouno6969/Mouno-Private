// Central API client for the BGC Crypto web app.
//
// A single axios instance is shared across the whole app. It is responsible
// for:
//   * Resolving the API base URL once (from Vite env), instead of repeating
//     `import.meta.env.VITE_API_URL || ''` in every file.
//   * Injecting the auth token (Bearer) on every request from a single place.
//   * Surfacing errors as user-facing toasts via sonner.
//   * Detecting the "stale backend served index.html instead of JSON" case and
//     turning it into a clear, actionable error.
//
// SECURITY NOTE: the auth token is stored in localStorage (see TOKEN_KEY).
// This is readable by any JS running on the page, so it carries an XSS risk.
// Moving to an httpOnly cookie would require backend changes; until then we at
// least centralize all token access here so it is never scattered or logged.

import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios';
import { toast } from 'sonner';

// Allow callers to opt out of the automatic error toast on a per-request basis
// (e.g. forms that render their own inline error). Declared via module
// augmentation so `apiClient.get(url, { silent: true })` type-checks.
declare module 'axios' {
  export interface AxiosRequestConfig {
    silent?: boolean;
  }
}

export const TOKEN_KEY = 'token';

/**
 * Resolve the API base URL once. In dev, leaving VITE_API_URL unset lets the
 * Vite proxy forward `/api` to Flask. In production the SPA is served from the
 * same origin as the API, so an empty base (relative URLs) is correct.
 */
export const API_BASE = (
  import.meta.env.VITE_API_URL || ''
).replace(/\/$/, '');

/** Thrown when the backend replies with HTML (stale/missing route) not JSON. */
export class ApiUnavailableError extends Error {
  constructor(path: string) {
    super(
      `The server does not recognize ${path} yet. The website backend is likely running an old version - please restart/redeploy the server.`
    );
    this.name = 'ApiUnavailableError';
  }
}

// ─── Token helpers (single source of truth) ──────────────────────────────────

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* ignore storage failures (private mode, etc.) */
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

// ─── Axios instance ──────────────────────────────────────────────────────────

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach the auth token (if any) to every outgoing request.
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken();
  if (token) {
    const headers = AxiosHeaders.from(config.headers);
    headers.set('Authorization', `Bearer ${token}`);
    config.headers = headers;
  }
  return config;
});

/**
 * Extract a human-friendly message from an axios error / backend error body.
 */
export function getErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (error instanceof ApiUnavailableError) return error.message;
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: string; error?: string } | undefined;
    if (data?.message) return data.message;
    if (data?.error) return data.error;
    if (error.code === 'ERR_NETWORK') return 'Cannot reach the server. Check your connection.';
    if (error.message) return error.message;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

// Surface errors as toasts and normalize the stale-backend HTML case.
apiClient.interceptors.response.use(
  (response) => {
    // The backend's catch-all route can serve index.html (HTML) for unknown
    // API routes when running an old build. Detect that and fail loudly.
    const contentType = String(response.headers?.['content-type'] || '');
    if (contentType.includes('text/html')) {
      const err = new ApiUnavailableError(response.config?.url || 'this endpoint');
      // Throwing here rejects the promise to the caller but bypasses the
      // onRejected handler below, so emit the toast explicitly (unless the
      // caller opted out via `silent`) to match the regular error path.
      if (!response.config?.silent) {
        toast.error(err.message);
      }
      throw err;
    }
    return response;
  },
  (error: AxiosError) => {
    // 401 → token is invalid/expired. Clear it; AuthContext listens for this.
    if (error.response?.status === 401) {
      clearToken();
      window.dispatchEvent(new Event('auth:unauthorized'));
    }

    // Only auto-toast when the caller hasn't opted out via `silent`.
    const silent = error.config?.silent;
    if (!silent) {
      toast.error(getErrorMessage(error));
    }
    return Promise.reject(error);
  }
);

// ─── SWR fetcher ─────────────────────────────────────────────────────────────

/**
 * Default SWR fetcher: GET a path and return the parsed JSON body.
 * Errors propagate to SWR's `error` so components can render error states.
 */
export async function fetcher<T = unknown>(path: string): Promise<T> {
  // Background polling renders its own error/empty states via SWR's `error`,
  // so suppress the global toast to avoid flooding the UI with duplicate
  // error toasts on every failed poll + retry.
  const res = await apiClient.get<T>(path, { silent: true });
  return res.data;
}

export default apiClient;
