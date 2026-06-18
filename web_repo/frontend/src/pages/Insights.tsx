import React from 'react';
import { useTranslation } from 'react-i18next';
import useSWR from 'swr';
import {
  LineChart,
  TrendingUp,
  TrendingDown,
  Flame,
  RefreshCw,
  Activity,
  Globe,
  Gauge,
  Coins,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { ErrorState } from '../components/ui/states';

// ─────────────────────────────────────────────────────────────────────────────
// Public market-data APIs (free, no key, CORS-enabled). These are intentionally
// fetched directly from the client with dedicated fetchers rather than the app's
// backend apiClient, since the backend doesn't expose market-insights routes.
// ─────────────────────────────────────────────────────────────────────────────

const CG = 'https://api.coingecko.com/api/v3';
const REFRESH = 60_000; // 60s — keep modest to respect CoinGecko free-tier limits.

const jsonFetcher = async (url: string) => {
  const res = await fetch(url, {
    headers: { accept: 'application/json' },
    signal: AbortSignal.timeout(15_000),
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
};

// ── Types ──
interface MarketCoin {
  id: string;
  symbol: string;
  name: string;
  image: string;
  current_price: number;
  market_cap: number;
  total_volume: number;
  market_cap_rank: number;
  price_change_percentage_24h: number;
}

interface TrendingCoin {
  item: {
    id: string;
    name: string;
    symbol: string;
    small: string;
    market_cap_rank: number;
    data?: { price?: number; price_change_percentage_24h?: { usd?: number } };
  };
}

interface GlobalData {
  data: {
    total_market_cap: { usd: number };
    total_volume: { usd: number };
    market_cap_percentage: { btc: number; eth: number };
    market_cap_change_percentage_24h_usd: number;
    active_cryptocurrencies: number;
  };
}

interface FngData {
  data: { value: string; value_classification: string; timestamp: string }[];
}

// ── Formatters ──
const fmtUsd = (n: number, max = 2) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: max })}`;

const fmtCompact = (n: number) => {
  const v = Number(n || 0);
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
  return fmtUsd(v);
};

const fmtPrice = (n: number) => {
  const v = Number(n || 0);
  if (v >= 1) return fmtUsd(v, 2);
  return `$${v.toLocaleString(undefined, { maximumFractionDigits: 6 })}`;
};

const fmtPct = (n: number) => `${n >= 0 ? '+' : ''}${Number(n || 0).toFixed(2)}%`;

// ── Shared bits ──
const ChangeBadge: React.FC<{ value?: number }> = ({ value }) => {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return <span className="text-xs text-muted-foreground">—</span>;
  }
  const up = value >= 0;
  return (
    <span
      className={`inline-flex items-center gap-1 font-mono text-sm font-semibold ${
        up ? 'text-success' : 'text-destructive'
      }`}
    >
      {up ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
      {fmtPct(value)}
    </span>
  );
};

const StatCard: React.FC<{
  label: string;
  value: React.ReactNode;
  icon: React.ReactNode;
  sub?: React.ReactNode;
  loading?: boolean;
}> = ({ label, value, icon, sub, loading }) => (
  <Card className="border-primary/10 bg-card/50 backdrop-blur">
    <CardContent className="p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        <span className="text-primary">{icon}</span>
      </div>
      {loading ? (
        <Skeleton className="mt-2 h-7 w-28" />
      ) : (
        <p className="mt-1 text-2xl font-extrabold tracking-tight">{value}</p>
      )}
      {sub && <div className="mt-1">{sub}</div>}
    </CardContent>
  </Card>
);

const TokenRow: React.FC<{ rank: number; coin: MarketCoin }> = ({ rank, coin }) => (
  <div className="flex items-center justify-between gap-3 rounded-lg p-3 transition-colors hover:bg-muted/40">
    <div className="flex min-w-0 items-center gap-3">
      <span className="w-4 shrink-0 text-center font-mono text-xs text-muted-foreground">{rank}</span>
      <img
        src={coin.image || '/placeholder.svg'}
        alt={coin.name}
        width={28}
        height={28}
        loading="lazy"
        className="h-7 w-7 shrink-0 rounded-full"
      />
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold">{coin.name}</p>
        <p className="font-mono text-xs uppercase text-muted-foreground">{coin.symbol}</p>
      </div>
    </div>
    <div className="text-right">
      <p className="font-mono text-sm font-semibold">{fmtPrice(coin.current_price)}</p>
      <ChangeBadge value={coin.price_change_percentage_24h} />
    </div>
  </div>
);

// ── Fear & Greed gauge ──
const sentimentColor = (v: number) => {
  if (v >= 55) return 'text-success';
  if (v >= 45) return 'text-warning';
  if (v >= 25) return 'text-warning';
  return 'text-destructive';
};
const sentimentBar = (v: number) => {
  if (v >= 55) return 'bg-success';
  if (v >= 45) return 'bg-warning';
  if (v >= 25) return 'bg-warning';
  return 'bg-destructive';
};

const Insights: React.FC = () => {
  const { t } = useTranslation();

  const markets = useSWR<MarketCoin[]>(
    `${CG}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&price_change_percentage=24h`,
    jsonFetcher,
    { refreshInterval: REFRESH },
  );
  const trending = useSWR<{ coins: TrendingCoin[] }>(`${CG}/search/trending`, jsonFetcher, {
    refreshInterval: REFRESH,
  });
  const global = useSWR<GlobalData>(`${CG}/global`, jsonFetcher, {
    refreshInterval: REFRESH,
  });
  const fng = useSWR<FngData>('https://api.alternative.me/fng/?limit=1', jsonFetcher, {
    refreshInterval: REFRESH,
  });

  const refreshAll = () => {
    markets.mutate();
    trending.mutate();
    global.mutate();
    fng.mutate();
  };

  const refreshing =
    markets.isValidating || trending.isValidating || global.isValidating || fng.isValidating;

  const coins = React.useMemo(
    () => (Array.isArray(markets.data) ? markets.data : []),
    [markets.data],
  );
  const { gainers, losers } = React.useMemo(() => {
    const movers = coins.filter((c) => Number.isFinite(c.price_change_percentage_24h));
    return {
      gainers: [...movers]
        .sort((a, b) => b.price_change_percentage_24h - a.price_change_percentage_24h)
        .slice(0, 8),
      losers: [...movers]
        .sort((a, b) => a.price_change_percentage_24h - b.price_change_percentage_24h)
        .slice(0, 8),
    };
  }, [coins]);

  const g = global.data?.data;
  const fngEntry = fng.data?.data?.[0];
  const fngParsed = fngEntry ? Number(fngEntry.value) : NaN;
  const fngValue = Number.isFinite(fngParsed) ? fngParsed : null;

  const trendingCoins = React.useMemo(
    () => (trending.data?.coins ?? []).slice(0, 8),
    [trending.data],
  );

  const hardError = markets.error && coins.length === 0;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/10 p-2">
            <LineChart className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">
              {t('nav_insights', 'Market Insights')}
            </h1>
            <p className="text-sm text-muted-foreground">
              {t('insights_subtitle', 'Trending tokens, movers, sentiment & on-chain metrics')}
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={refreshAll} disabled={refreshing}>
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} aria-hidden="true" />
          {t('refresh', 'Refresh')}
        </Button>
      </div>

      {hardError ? (
        <Card className="border-destructive/30">
          <CardContent className="p-0">
            <ErrorState
              title={t('insights_error', "Couldn't load market data")}
              description={t('insights_error_desc', 'The market data provider is unreachable or rate-limited. Try again shortly.')}
              onRetry={refreshAll}
              retryLabel={t('retry', 'Retry')}
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Global market metrics */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard
              label={t('total_market_cap', 'Total Market Cap')}
              icon={<Globe className="h-4 w-4" />}
              loading={!g}
              value={g ? fmtCompact(g.total_market_cap.usd) : '—'}
              sub={g ? <ChangeBadge value={g.market_cap_change_percentage_24h_usd} /> : null}
            />
            <StatCard
              label={t('volume_24h', '24h Volume')}
              icon={<Activity className="h-4 w-4" />}
              loading={!g}
              value={g ? fmtCompact(g.total_volume.usd) : '—'}
            />
            <StatCard
              label={t('btc_dominance', 'BTC Dominance')}
              icon={<Coins className="h-4 w-4" />}
              loading={!g}
              value={g ? `${g.market_cap_percentage.btc.toFixed(1)}%` : '—'}
              sub={
                g ? (
                  <span className="text-xs text-muted-foreground">
                    ETH {g.market_cap_percentage.eth.toFixed(1)}%
                  </span>
                ) : null
              }
            />
            <StatCard
              label={t('active_coins', 'Active Coins')}
              icon={<Gauge className="h-4 w-4" />}
              loading={!g}
              value={g ? g.active_cryptocurrencies.toLocaleString() : '—'}
            />
          </div>

          {/* Sentiment + Trending */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* Market sentiment (Fear & Greed) */}
            <Card className="border-primary/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Gauge className="h-5 w-5 text-primary" /> {t('market_sentiment', 'Market Sentiment')}
                </CardTitle>
                <CardDescription>{t('fear_greed', 'Crypto Fear & Greed Index')}</CardDescription>
              </CardHeader>
              <CardContent>
                {fngValue == null ? (
                  <div className="space-y-3">
                    <Skeleton className="mx-auto h-16 w-24" />
                    <Skeleton className="h-3 w-full" />
                  </div>
                ) : (
                  <div className="space-y-4 text-center">
                    <div>
                      <p className={`text-6xl font-black tabular-nums ${sentimentColor(fngValue)}`}>
                        {fngValue}
                      </p>
                      <p className={`text-sm font-bold uppercase tracking-wide ${sentimentColor(fngValue)}`}>
                        {fngEntry?.value_classification}
                      </p>
                    </div>
                    <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className={`h-full rounded-full transition-all ${sentimentBar(fngValue)}`}
                        style={{ width: `${fngValue}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] font-mono uppercase text-muted-foreground">
                      <span>{t('fear', 'Fear')}</span>
                      <span>{t('neutral', 'Neutral')}</span>
                      <span>{t('greed', 'Greed')}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Trending tokens */}
            <Card className="border-primary/10 lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Flame className="h-5 w-5 text-warning" /> {t('trending_tokens', 'Trending Tokens')}
                </CardTitle>
                <CardDescription>{t('trending_desc', 'Most searched coins right now')}</CardDescription>
              </CardHeader>
              <CardContent>
                {trending.isLoading && trendingCoins.length === 0 ? (
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {Array.from({ length: 6 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {trendingCoins.map((c, i) => {
                      const change = c.item.data?.price_change_percentage_24h?.usd;
                      return (
                        <div
                          key={c.item.id}
                          className="flex items-center justify-between gap-2 rounded-lg bg-muted/30 p-2.5"
                        >
                          <div className="flex min-w-0 items-center gap-2.5">
                            <span className="font-mono text-xs text-muted-foreground">#{i + 1}</span>
                            <img
                              src={c.item.small || '/placeholder.svg'}
                              alt={c.item.name}
                              width={24}
                              height={24}
                              loading="lazy"
                              className="h-6 w-6 rounded-full"
                            />
                            <div className="min-w-0">
                              <p className="truncate text-sm font-semibold">{c.item.name}</p>
                              <p className="font-mono text-[10px] uppercase text-muted-foreground">
                                {c.item.symbol}
                              </p>
                            </div>
                          </div>
                          {c.item.market_cap_rank ? (
                            <Badge variant="outline" className="shrink-0 font-mono text-[10px]">
                              #{c.item.market_cap_rank}
                            </Badge>
                          ) : (
                            <ChangeBadge value={change} />
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Gainers + Losers */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Card className="border-primary/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <TrendingUp className="h-5 w-5 text-success" /> {t('top_gainers', 'Top Gainers')}
                </CardTitle>
                <CardDescription>{t('gainers_desc', 'Biggest 24h price increases (top 100 by cap)')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-1">
                {markets.isLoading && gainers.length === 0
                  ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)
                  : gainers.map((c, i) => <TokenRow key={c.id} rank={i + 1} coin={c} />)}
              </CardContent>
            </Card>

            <Card className="border-primary/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <TrendingDown className="h-5 w-5 text-destructive" /> {t('top_losers', 'Top Losers')}
                </CardTitle>
                <CardDescription>{t('losers_desc', 'Biggest 24h price drops (top 100 by cap)')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-1">
                {markets.isLoading && losers.length === 0
                  ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)
                  : losers.map((c, i) => <TokenRow key={c.id} rank={i + 1} coin={c} />)}
              </CardContent>
            </Card>
          </div>

          <p className="text-center text-xs text-muted-foreground">
            {t('insights_credit', 'Data from CoinGecko & Alternative.me · refreshes every 60s')}
          </p>
        </>
      )}
    </div>
  );
};

export default Insights;
