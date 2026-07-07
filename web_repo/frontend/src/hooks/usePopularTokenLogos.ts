import { useEffect, useState } from 'react';
import { apiClient } from '../lib/apiClient';
import { popularTokensForChain } from '../constants/swapTokens';

/** Fetch LI.FI logoURI for each popular token on a chain. */
export function usePopularTokenLogos(chainId: string): Record<string, string> {
  const [logos, setLogos] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!chainId) {
      setLogos({});
      return;
    }

    let cancelled = false;
    const popular = popularTokensForChain(chainId);

    (async () => {
      const results = await Promise.all(
        popular.map(async (token) => {
          try {
            const res = await apiClient.get<{ logoURI?: string }>('/api/swap/token', {
              params: { chain: chainId, token: token.address },
              silent: true,
            });
            return [token.address, res.data.logoURI || ''] as const;
          } catch {
            return [token.address, ''] as const;
          }
        }),
      );

      if (!cancelled) {
        const next: Record<string, string> = {};
        for (const [address, uri] of results) {
          if (uri) next[address] = uri;
        }
        setLogos(next);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [chainId]);

  return logos;
}