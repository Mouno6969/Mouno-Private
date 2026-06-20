import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { PieChart as PieChartIcon, Wallet, Bell, Loader2, Trash2 } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { NetworkLogo, NETWORK_MAP } from '../constants/networks';
import { SkeletonText } from '../components/ui/skeleton';
import { EmptyState, ErrorState, PageHeader, StatCard, PriceChange, TexturePanel, FlashValue } from '../components/common';
import { useAuth } from '../context/AuthContext';
import { usePortfolio, usePriceAlerts } from '../lib/hooks';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import { toast } from 'sonner';

// On-brand, monochrome-leaning palette (no purple), reused for pie slices.
const PIE_COLORS = [
  'hsl(var(--primary))',
  'hsl(var(--info))',
  'hsl(var(--success))',
  'hsl(var(--warning))',
  'hsl(var(--destructive))',
  'hsl(258 70% 60%)',
  'hsl(var(--muted-foreground))',
  'hsl(var(--foreground) / 0.5)',
];

const fmtUsd = (n: number) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const Portfolio: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const isLoggedIn = Boolean(token);

  const { data: portfolioRes, error, isLoading, isValidating, mutate } = usePortfolio(isLoggedIn);
  const { data: alertsRes, mutate: mutateAlerts } = usePriceAlerts(isLoggedIn);

  const overview = portfolioRes?.data;
  const holdings = overview?.holdings ?? [];
  const alerts = alertsRes?.data?.alerts ?? [];

  const [symbol, setSymbol] = useState('');
  const [direction, setDirection] = useState<'below' | 'above'>('below');
  const [targetPrice, setTargetPrice] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const change = overview?.change_24h_pct;
  const hasChange = typeof change === 'number' && Number.isFinite(change);
  const isUp = hasChange && (change as number) >= 0;

  // Single source of truth: the pie chart and the breakdown list must show the
  // same rows (and stay color-synced), so derive both from positiveHoldings.
  const positiveHoldings = holdings.filter((h) => h.usd_value > 0);
  const chartData = positiveHoldings.map((h) => ({
    name: `${h.asset} (${NETWORK_MAP[h.network]?.name || h.network})`,
    value: h.usd_value,
  }));

  const createAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol.trim()) {
      toast.error(t('alert_symbol_required', 'Please enter an asset symbol (e.g. BTC).'));
      return;
    }
    const parsedTargetPrice = Number(targetPrice);
    if (!Number.isFinite(parsedTargetPrice) || parsedTargetPrice <= 0) {
      toast.error(t('alert_price_required', 'Enter a valid target price.'));
      return;
    }
    setSubmitting(true);
    try {
      const res = await apiClient.post<{ ok?: boolean; message?: string }>(
        '/api/price-alerts',
        { symbol: symbol.trim().toUpperCase(), direction, target_price: parsedTargetPrice },
        { silent: true },
      );
      if (res.data.ok) {
        toast.success(res.data.message || t('alert_created', 'Price alert created.'));
        setSymbol('');
        setTargetPrice('');
        mutateAlerts();
      } else {
        toast.error(res.data.message || 'Failed');
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to create alert'));
    } finally {
      setSubmitting(false);
    }
  };

  const cancelAlert = async (id: number) => {
    try {
      await apiClient.delete(`/api/price-alerts/${id}`, { silent: true });
      toast.success(t('alert_cancelled', 'Price alert cancelled.'));
      mutateAlerts();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to cancel alert'));
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        icon={<PieChartIcon className="h-7 w-7" />}
        title={t('nav_portfolio', 'Portfolio')}
        description={t('portfolio_subtitle', 'Your total net worth across all wallets')}
        actions={
          <Button variant="outline" size="sm" onClick={() => mutate()} disabled={isValidating}>
            {isValidating ? <Loader2 className="h-4 w-4 animate-spin" /> : t('refresh', 'Refresh')}
          </Button>
        }
      />

      {!isLoggedIn ? (
        <Card>
          <CardContent className="p-0">
            <EmptyState
              icon={<Wallet className="h-6 w-6" aria-hidden="true" />}
              title={t('login_required', 'Please log in')}
              description={t('portfolio_login_desc', 'Log in to view your portfolio and set price alerts.')}
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Net worth + 24h change */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <TexturePanel variant="primary" glow accentTop strong className="sm:col-span-1">
              <div className="p-5">
                <p className="label-eyebrow">{t('net_worth', 'Total Net Worth')}</p>
                {isLoading && !overview ? (
                  <div className="mt-2 h-9 w-40 animate-pulse rounded bg-muted/60" />
                ) : (
                  <FlashValue value={overview?.net_worth_usd ?? 0} as="div">
                    <p className="num mt-1 text-3xl font-extrabold tracking-tight drop-shadow-[0_0_18px_hsl(var(--primary)/0.35)]">
                      {fmtUsd(overview?.net_worth_usd ?? 0)}
                    </p>
                  </FlashValue>
                )}
              </div>
            </TexturePanel>
            <StatCard
              label={t('change_24h', '24h Change')}
              loading={isLoading && !overview}
              value={
                hasChange ? (
                  <PriceChange value={change as number} className="text-2xl" />
                ) : (
                  <span className="text-base font-normal text-muted-foreground">{t('change_pending', 'Tracking — available after 24h')}</span>
                )
              }
            />
          </div>

          {/* Holdings pie + breakdown */}
          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <PieChartIcon className="h-5 w-5 text-primary" /> {t('top_holdings', 'Top Holdings')}
              </CardTitle>
              <CardDescription>{t('holdings_desc', 'Breakdown of your assets by USD value')}</CardDescription>
            </CardHeader>
            <CardContent>
              {error ? (
                <ErrorState
                  title={t('portfolio_error', "Couldn't load portfolio")}
                  description={t('portfolio_error_desc', 'We could not reach the server to value your wallets.')}
                  onRetry={() => mutate()}
                  retryLabel={t('retry', 'Retry')}
                />
              ) : chartData.length === 0 ? (
                <EmptyState
                  icon={<Wallet className="h-6 w-6" aria-hidden="true" />}
                  title={t('no_holdings', 'No funded assets yet')}
                  description={t('no_holdings_desc', 'Add a wallet with a balance to see your portfolio breakdown.')}
                />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={2} stroke="hsl(var(--background))">
                          {chartData.map((_, i) => (
                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(v) => fmtUsd(Number(v))}
                          contentStyle={{ background: 'hsl(var(--popover))', border: '1px solid hsl(var(--border))', borderRadius: 12, color: 'hsl(var(--popover-foreground))' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-2">
                    {positiveHoldings.map((h, i) => (
                      <div key={`${h.network}-${h.address}-${i}`} className="flex items-center justify-between gap-2 text-sm">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                          <NetworkLogo id={h.network} size={18} />
                          <span className="font-medium truncate">{h.asset}</span>
                          <span className="text-xs text-muted-foreground truncate">{NETWORK_MAP[h.network]?.name || h.network}</span>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="font-mono font-semibold">{fmtUsd(h.usd_value)}</div>
                          <div className="text-[10px] text-muted-foreground">{h.pct.toFixed(1)}%</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Set price alert */}
          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" /> {t('set_price_alert', 'Set Price Alert')}
              </CardTitle>
              <CardDescription>{t('price_alert_desc', 'Get notified when an asset crosses your target (e.g. alert me if BTC drops below $60,000).')}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={createAlert} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
                <div className="space-y-2">
                  <Label>{t('asset_symbol', 'Asset')}</Label>
                  <Input placeholder="BTC" value={symbol} onChange={(e) => setSymbol(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>{t('direction', 'Condition')}</Label>
                  <select value={direction} onChange={(e) => setDirection(e.target.value as 'below' | 'above')} className="w-full h-10 rounded-md border bg-background px-3 text-sm">
                    <option value="below">{t('drops_below', 'Drops below')}</option>
                    <option value="above">{t('rises_above', 'Rises above')}</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>{t('target_price', 'Target price (USD)')}</Label>
                  <Input type="number" step="any" placeholder="60000" value={targetPrice} onChange={(e) => setTargetPrice(e.target.value)} />
                </div>
                <Button type="submit" disabled={submitting}>
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  {t('create_alert', 'Create')}
                </Button>
              </form>
              <p className="text-xs text-muted-foreground mt-3">
                {t('supported_assets', 'Supported for live pricing: BTC, ETH, BNB, MATIC, AVAX, SOL and stablecoins.')}
              </p>

              <div className="mt-5 space-y-2">
                {alerts.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">{t('no_alerts', 'No price alerts yet.')}</p>
                ) : (
                  alerts.map((a) => (
                    <div key={a.id} className="flex items-center justify-between gap-2 p-3 rounded-lg bg-muted/30">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="font-bold font-mono">{a.symbol}</span>
                        <span className="text-muted-foreground">
                          {a.direction === 'above' ? t('rises_above', 'Rises above') : t('drops_below', 'Drops below')} {fmtUsd(a.target_price)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={a.status === 'active' ? 'secondary' : 'default'} className="text-[10px]">
                          {a.status === 'active' ? t('active', 'Active') : t('triggered', 'Triggered')}
                        </Badge>
                        <Button variant="ghost" size="icon" aria-label="Cancel alert" onClick={() => cancelAlert(a.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default Portfolio;
