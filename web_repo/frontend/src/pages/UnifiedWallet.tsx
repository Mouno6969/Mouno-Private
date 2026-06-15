import React from 'react';
import { useTranslation } from 'react-i18next';
import { Layers, Wallet, Loader2, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { NetworkLogo, NETWORK_MAP } from '../constants/networks';
import { SkeletonText, SkeletonListRow } from '../components/ui/skeleton';
import { EmptyState, ErrorState } from '../components/ui/states';
import { useAuth } from '../context/AuthContext';
import { usePortfolio, useMarket } from '../lib/hooks';
import type { PortfolioHolding } from '../types/api';

// On-brand, monochrome-leaning palette (no purple) reused for the chain share bar.
const CHAIN_COLORS = ['#ffffff', '#22c55e', '#3b82f6', '#eab308', '#ef4444', '#06b6d4', '#9ca3af', '#a3a3a3'];

const fmtUsd = (n: number) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const fmtAmount = (n: number) =>
  Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 6 });

interface ChainGroup {
  network: string;
  name: string;
  usdTotal: number;
  holdings: PortfolioHolding[];
}

const UnifiedWallet: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const isLoggedIn = Boolean(token);

  const { data: portfolioRes, error, isLoading, isValidating, mutate } = usePortfolio(isLoggedIn);
  const { data: market } = useMarket();

  const overview = portfolioRes?.data;
  const netWorthUsd = overview?.net_worth_usd ?? 0;

  // Derive a USD->BDT rate from live stablecoin rates (USDT/USDC ~ $1), so the
  // total can be shown in BDT consistently with the Live Rates feature.
  const bdtPerUsd = React.useMemo(() => {
    const rates = Object.values(market?.rates ?? {}).filter((r) => Number.isFinite(r) && r > 0);
    if (rates.length === 0) return null;
    return rates.reduce((a, b) => a + b, 0) / rates.length;
  }, [market?.rates]);

  // Group funded holdings by chain and compute per-chain subtotals. Chains are
  // sorted by USD value (highest first); tokens within each chain likewise.
  const chainGroups = React.useMemo<ChainGroup[]>(() => {
    const funded = (overview?.holdings ?? []).filter((h) => h.usd_value > 0);
    const byChain = new Map<string, ChainGroup>();
    for (const h of funded) {
      const existing = byChain.get(h.network);
      if (existing) {
        existing.usdTotal += h.usd_value;
        existing.holdings.push(h);
      } else {
        byChain.set(h.network, {
          network: h.network,
          name: NETWORK_MAP[h.network]?.name || h.network,
          usdTotal: h.usd_value,
          holdings: [h],
        });
      }
    }
    const groups = Array.from(byChain.values());
    groups.forEach((g) => g.holdings.sort((a, b) => b.usd_value - a.usd_value));
    return groups.sort((a, b) => b.usdTotal - a.usdTotal);
  }, [overview?.holdings]);

  const hasFunds = chainGroups.length > 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Layers className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">{t('nav_unified', 'Unified Wallet')}</h1>
            <p className="text-muted-foreground text-sm">
              {t('unified_subtitle', 'All chain balances on one screen — no switching')}
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={() => mutate()} disabled={isValidating}>
          {isValidating ? <Loader2 className="h-4 w-4 animate-spin" /> : t('refresh', 'Refresh')}
        </Button>
      </div>

      {!isLoggedIn ? (
        <Card>
          <CardContent className="p-0">
            <EmptyState
              icon={<Wallet className="h-6 w-6" aria-hidden="true" />}
              title={t('login_required', 'Please log in')}
              description={t('unified_login_desc', 'Log in to see your balances across every chain in one place.')}
            />
          </CardContent>
        </Card>
      ) : error ? (
        <ErrorState
          title={t('unified_error', "Couldn't load balances")}
          description={t('unified_error_desc', 'We could not reach the server to value your wallets across chains.')}
          onRetry={() => mutate()}
          retryLabel={t('retry', 'Retry')}
        />
      ) : (
        <>
          {/* Total value hero */}
          <Card className="border-primary/10 bg-card/50 backdrop-blur">
            <CardContent className="p-6">
              <p className="text-sm font-medium text-muted-foreground">{t('total_value_all_chains', 'Total Value (All Chains)')}</p>
              {isLoading && !overview ? (
                <SkeletonText className="mt-2 h-10 w-48" />
              ) : (
                <>
                  <p className="text-4xl font-extrabold tracking-tight mt-1">{fmtUsd(netWorthUsd)}</p>
                  {bdtPerUsd ? (
                    <p className="text-sm text-muted-foreground mt-1 font-mono">
                      {'\u2248'} {'\u09F3'}{(netWorthUsd * bdtPerUsd).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </p>
                  ) : null}
                </>
              )}
              <p className="text-xs text-muted-foreground mt-3">
                {hasFunds
                  ? t('unified_chains_count', '{{count}} chains funded', { count: chainGroups.length })
                  : t('unified_no_funds_hint', 'No funded chains yet')}
              </p>

              {/* Chain share bar */}
              {hasFunds && netWorthUsd > 0 ? (
                <div className="mt-4">
                  <div className="flex h-3 w-full overflow-hidden rounded-full bg-muted">
                    {chainGroups.map((g, i) => (
                      <div
                        key={g.network}
                        className="h-full"
                        style={{
                          width: `${(g.usdTotal / netWorthUsd) * 100}%`,
                          backgroundColor: CHAIN_COLORS[i % CHAIN_COLORS.length],
                        }}
                        title={`${g.name}: ${fmtUsd(g.usdTotal)}`}
                      />
                    ))}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
                    {chainGroups.map((g, i) => (
                      <div key={g.network} className="flex items-center gap-1.5 text-xs">
                        <span
                          className="h-2.5 w-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: CHAIN_COLORS[i % CHAIN_COLORS.length] }}
                        />
                        <span className="font-medium">{g.name}</span>
                        <span className="text-muted-foreground">
                          {((g.usdTotal / netWorthUsd) * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>

          {/* Per-chain breakdown */}
          {isLoading && !overview ? (
            <Card className="border-primary/10">
              <CardHeader>
                <SkeletonText className="h-5 w-40" />
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <SkeletonListRow key={i} />
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : !hasFunds ? (
            <Card>
              <CardContent className="p-0">
                <EmptyState
                  icon={<Wallet className="h-6 w-6" aria-hidden="true" />}
                  title={t('no_holdings', 'No funded assets yet')}
                  description={t('unified_empty_desc', 'Add a wallet with a balance to see your unified balances across chains.')}
                />
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {chainGroups.map((g) => (
                <Card key={g.network} className="border-primary/10">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between gap-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <NetworkLogo id={g.network} size={22} />
                        {g.name}
                        <Badge variant="secondary" className="text-[10px]">
                          {t('unified_token_count', '{{count}} tokens', { count: g.holdings.length })}
                        </Badge>
                      </CardTitle>
                      <span className="font-mono font-semibold text-sm">{fmtUsd(g.usdTotal)}</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {g.holdings.map((h, i) => (
                        <div
                          key={`${h.network}-${h.address}-${h.asset}-${i}`}
                          className="flex items-center justify-between gap-3 p-3 rounded-lg bg-muted/30"
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <NetworkLogo id={h.network} size={20} />
                            <div className="min-w-0">
                              <div className="text-sm font-semibold truncate">{h.asset}</div>
                              {h.label ? (
                                <div className="text-xs text-muted-foreground truncate">{h.label}</div>
                              ) : null}
                            </div>
                          </div>
                          <div className="text-right shrink-0">
                            <div className="font-mono text-sm font-semibold">{fmtUsd(h.usd_value)}</div>
                            <div className="text-xs text-muted-foreground font-mono">
                              {fmtAmount(h.amount)} {h.asset}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <ChevronRight className="h-3 w-3" />
            {t('unified_credit', 'Aggregated from all your wallets · values update automatically')}
          </p>
        </>
      )}
    </div>
  );
};

export default UnifiedWallet;
