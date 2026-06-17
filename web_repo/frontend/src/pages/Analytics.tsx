import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { BarChart3, TrendingUp, TrendingDown, Users, Loader2 } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { NetworkLogo, NETWORK_MAP } from '../constants/networks';
import { SkeletonText } from '../components/ui/skeleton';
import { EmptyState, ErrorState } from '../components/ui/states';
import { useAuth } from '../context/AuthContext';
import { useAnalytics } from '../lib/hooks';

const PIE_COLORS = ['#ffffff', '#9ca3af', '#22c55e', '#3b82f6', '#eab308', '#ef4444', '#06b6d4', '#a3a3a3'];

const fmtUsd = (n: number) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const shortAddr = (w: string) => (w && w.length > 12 ? `${w.slice(0, 6)}...${w.slice(-4)}` : w || 'N/A');

const Analytics: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const isLoggedIn = Boolean(token);

  const [period, setPeriod] = useState('month');
  const { data: res, error, isLoading, mutate } = useAnalytics(period, isLoggedIn);
  const data = res?.data;

  const periods: { key: string; label: string }[] = [
    { key: 'week', label: t('period_week', 'Week') },
    { key: 'month', label: t('period_month', 'Month') },
    { key: 'quarter', label: t('period_quarter', 'Quarter') },
    { key: 'year', label: t('period_year', 'Year') },
    { key: 'all', label: t('period_all', 'All') },
  ];

  const assetData = (data?.spend_by_asset ?? []).map((d) => ({ name: d.asset, value: d.usd_value }));
  const networkData = (data?.spend_by_network ?? []).map((d) => ({
    name: NETWORK_MAP[d.network]?.name || d.network,
    value: d.usd_value,
  }));

  const change = data?.volume_change_pct;
  const hasChange = typeof change === 'number' && Number.isFinite(change);
  const isUp = hasChange && (change as number) >= 0;

  const tooltipStyle = {
    background: 'hsl(var(--popover))',
    border: '1px solid hsl(var(--border))',
    borderRadius: 0,
    color: 'hsl(var(--popover-foreground))',
  };

  const hasData = (data?.tx_count ?? 0) > 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <BarChart3 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">{t('nav_analytics', 'Analytics')}</h1>
            <p className="text-muted-foreground text-sm">{t('analytics_subtitle', 'Your spending and transaction insights')}</p>
          </div>
        </div>
        <div className="flex items-center gap-1 flex-wrap">
          {periods.map((p) => (
            <Button
              key={p.key}
              variant={period === p.key ? 'default' : 'outline'}
              size="sm"
              onClick={() => setPeriod(p.key)}
            >
              {p.label}
            </Button>
          ))}
        </div>
      </div>

      {!isLoggedIn ? (
        <Card>
          <CardContent className="p-0">
            <EmptyState
              icon={<BarChart3 className="h-6 w-6" aria-hidden="true" />}
              title={t('login_required', 'Please log in')}
              description={t('analytics_login_desc', 'Log in to view your transaction analytics.')}
            />
          </CardContent>
        </Card>
      ) : error ? (
        <Card className="border-destructive/30">
          <CardContent className="p-0">
            <ErrorState
              title={t('analytics_error', "Couldn't load analytics")}
              description={t('analytics_error_desc', 'We could not reach the server.')}
              onRetry={() => mutate()}
              retryLabel={t('retry', 'Retry')}
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Volume summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="border-primary/10 bg-card/50 backdrop-blur">
              <CardContent className="p-5">
                <p className="text-sm font-medium text-muted-foreground">{t('total_volume', 'Total Volume')}</p>
                {isLoading && !data ? (
                  <SkeletonText className="mt-2 h-8 w-32" />
                ) : (
                  <p className="text-2xl font-extrabold tracking-tight mt-1">{fmtUsd(data?.total_volume ?? 0)}</p>
                )}
              </CardContent>
            </Card>
            <Card className="border-primary/10 bg-card/50 backdrop-blur">
              <CardContent className="p-5">
                <p className="text-sm font-medium text-muted-foreground">{t('transactions', 'Transactions')}</p>
                {isLoading && !data ? (
                  <SkeletonText className="mt-2 h-8 w-16" />
                ) : (
                  <p className="text-2xl font-extrabold tracking-tight mt-1">{data?.tx_count ?? 0}</p>
                )}
              </CardContent>
            </Card>
            <Card className="border-primary/10 bg-card/50 backdrop-blur">
              <CardContent className="p-5">
                <p className="text-sm font-medium text-muted-foreground">{t('vs_previous', 'vs Previous Period')}</p>
                {isLoading && !data ? (
                  <SkeletonText className="mt-2 h-8 w-24" />
                ) : hasChange ? (
                  <p className={`text-2xl font-extrabold tracking-tight mt-1 flex items-center gap-2 ${isUp ? 'text-success' : 'text-destructive'}`}>
                    {isUp ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                    {isUp ? '+' : ''}{(change as number).toFixed(1)}%
                  </p>
                ) : (
                  <p className="text-base text-muted-foreground mt-2">{t('no_comparison', 'No prior data')}</p>
                )}
              </CardContent>
            </Card>
          </div>

          {!hasData ? (
            <Card>
              <CardContent className="p-0">
                <EmptyState
                  icon={<BarChart3 className="h-6 w-6" aria-hidden="true" />}
                  title={t('no_analytics', 'No transactions in this period')}
                  description={t('no_analytics_desc', 'Try a longer time range to see your spending breakdown.')}
                />
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Spend by asset */}
                <Card className="border-primary/10">
                  <CardHeader>
                    <CardTitle className="text-lg">{t('spend_by_asset', 'Spend by Asset')}</CardTitle>
                    <CardDescription>{t('spend_by_asset_desc', 'Total volume grouped by asset')}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={assetData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                          <XAxis dataKey="name" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                          <YAxis tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                          <Tooltip cursor={{ fill: 'hsl(var(--muted) / 0.3)' }} formatter={(v) => fmtUsd(Number(v))} contentStyle={tooltipStyle} />
                          <Bar dataKey="value" radius={[2, 2, 0, 0]}>
                            {assetData.map((_, i) => (
                              <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Spend by network */}
                <Card className="border-primary/10">
                  <CardHeader>
                    <CardTitle className="text-lg">{t('spend_by_network', 'Spend by Network')}</CardTitle>
                    <CardDescription>{t('spend_by_network_desc', 'Share of volume per network')}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={networkData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} stroke="hsl(var(--background))">
                            {networkData.map((_, i) => (
                              <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(v) => fmtUsd(Number(v))} contentStyle={tooltipStyle} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Top recipients */}
              <Card className="border-primary/10">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Users className="h-5 w-5 text-primary" /> {t('top_recipients', 'Top Recipients')}
                  </CardTitle>
                  <CardDescription>{t('top_recipients_desc', 'Addresses you transact with most')}</CardDescription>
                </CardHeader>
                <CardContent>
                  {(data?.top_recipients ?? []).length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-4">{t('no_recipients', 'No recipient data yet.')}</p>
                  ) : (
                    <div className="space-y-2">
                      {(data?.top_recipients ?? []).map((r, i) => (
                        <div key={r.address} className="flex items-center justify-between gap-2 p-3 rounded-lg bg-muted/30">
                          <div className="flex items-center gap-3 min-w-0">
                            <span className="font-mono text-xs text-muted-foreground w-5">{i + 1}</span>
                            <span className="font-mono text-sm truncate">{shortAddr(r.address)}</span>
                          </div>
                          <span className="text-sm font-semibold shrink-0">
                            {r.count} {r.count === 1 ? t('tx_singular', 'tx') : t('tx_plural', 'txs')}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default Analytics;
