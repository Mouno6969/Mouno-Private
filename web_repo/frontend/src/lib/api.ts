// Shared API helpers.
//
// This module is kept as a thin compatibility layer over the central
// `apiClient`. New code should import from `lib/apiClient` directly, but several
// pages still import { API_BASE, ApiUnavailableError, safeJson } from here.
//
// The backend serves the React SPA from a catch-all route. If the running
// server process is outdated (missing a newly added API route), a fetch to
// that route can come back as HTML (index.html) instead of JSON. Parsing it
// with res.json() throws and the UI silently shows an empty/blank state.
// safeJson() detects that case and raises a clear, actionable error instead.

import { API_BASE, ApiUnavailableError } from './apiClient';

export { API_BASE, ApiUnavailableError };

/**
 * Parse a fetch Response as JSON, but detect when the server replied with
 * HTML (stale backend without the route) and throw a clear error instead.
 */
export async function safeJson(res: Response, path: string): Promise<any> {
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('text/html')) {
    throw new ApiUnavailableError(path);
  }
  try {
    return await res.json();
  } catch {
    throw new ApiUnavailableError(path);
  }
}
