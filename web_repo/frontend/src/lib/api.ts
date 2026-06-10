// Shared API helpers.
//
// The backend serves the React SPA from a catch-all route. If the running
// server process is outdated (missing a newly added API route), a fetch to
// that route can come back as HTML (index.html) instead of JSON. Parsing it
// with res.json() throws and the UI silently shows an empty/blank state.
// safeJson() detects that case and raises a clear, actionable error instead.

export const API_BASE = (process.env.REACT_APP_API_URL || window.location.origin).replace(/\/$/, '');

export class ApiUnavailableError extends Error {
  constructor(path: string) {
    super(
      `The server does not recognize ${path} yet. The website backend is likely running an old version - please restart/redeploy the server.`
    );
    this.name = 'ApiUnavailableError';
  }
}

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
