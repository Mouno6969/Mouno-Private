import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Coins, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';
import { useBalance } from '../lib/hooks';
import { Skeleton, SkeletonListRow } from '../components/ui/skeleton';
import { ErrorState } from '../components/ui/states';
import { PageHeader, FlashValue, Freshness } from '../components/common';

const Balance: React.FC = () => {
  const { token } = useAuth();
  const { data, error, isLoading, isValidating, mutate } = useBalance(Boolean(token));

  const balances = data?.balances ?? null;
  // The backend can return a 200 with `{ message }` instead of balances.
  const messageError = !error && data && !data.balances ? data.message : undefined;

  // Track when fresh balance data actually arrived (for the live indicator).
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const lastRef = useRef<unknown>(null);
  useEffect(() => {
    if (data && data !== lastRef.current) {
      lastRef.current = data;
      setLastUpdated(new Date());
    }
  }, [data]);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader
        icon={<Coins className="h-7 w-7" />}
        eyebrow="Live"
        title="Balance"
        description="Live crypto balance across all networks"
        actions={
          <div className="flex items-center gap-3">
            {balances && <Freshness updatedAt={isValidating ? undefined : lastUpdated} label="Balances" />}
            <Button
              variant="outline"
              size="sm"
              onClick={() => mutate()}
              disabled={isValidating}
              aria-label="Refresh balances"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isValidating ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        }
      />

      {isLoading ? (
        <Card className="border-primary/10">
          <CardHeader>
            <Skeleton className="h-5 w-40" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <SkeletonListRow key={i} />
              ))}
            </div>
          </CardContent>
        </Card>
      ) : error ? (
        <ErrorState
          title="Couldn't load balances"
          description="We couldn't reach the server to fetch your balances."
          onRetry={() => mutate()}
        />
      ) : messageError ? (
        <ErrorState title="Balances unavailable" description={messageError} onRetry={() => mutate()} />
      ) : balances ? (
        <Card className="relative overflow-hidden glass-panel">
          <div className="absolute inset-0 dot-matrix-fine dot-matrix-fade-top opacity-50 pointer-events-none" aria-hidden="true" />
          <CardHeader className="relative">
            <CardTitle className="text-lg flex items-center gap-2">
              <span className="live-dot" /> Network Balances
            </CardTitle>
          </CardHeader>
          <CardContent className="relative">
            <div className="space-y-2">
              {NETWORK_LIST.map((net) => {
                const raw = balances[net.id];
                const has = raw !== undefined && raw !== null;
                return (
                  <div
                    key={net.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40 transition-colors hover:bg-muted/50"
                  >
                    <div className="flex items-center gap-3">
                      <NetworkLogo id={net.id} size={24} />
                      <span className="text-sm font-medium">
                        {net.name} {net.asset}
                      </span>
                    </div>
                    {has ? (
                      <FlashValue value={Number(raw)}>
                        <span className="num text-sm font-bold">{String(raw)}</span>
                      </FlashValue>
                    ) : (
                      <span className="text-sm text-muted-foreground">—</span>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
};

export default Balance;
