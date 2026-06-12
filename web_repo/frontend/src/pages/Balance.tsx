import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Coins, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';
import { useBalance } from '../lib/hooks';
import { Skeleton, SkeletonListRow } from '../components/ui/skeleton';
import { ErrorState } from '../components/ui/states';

const Balance: React.FC = () => {
  const { token } = useAuth();
  const { data, error, isLoading, isValidating, mutate } = useBalance(Boolean(token));

  const balances = data?.balances ?? null;
  // The backend can return a 200 with `{ message }` instead of balances.
  const messageError = !error && data && !data.balances ? data.message : undefined;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Coins className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Balance</h1>
            <p className="text-muted-foreground text-sm">Live crypto balance across all networks</p>
          </div>
        </div>
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
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle className="text-lg">Network Balances</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {NETWORK_LIST.map((net) => (
                <div key={net.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                  <div className="flex items-center gap-3">
                    <NetworkLogo id={net.id} size={24} />
                    <span className="text-sm font-medium">
                      {net.name} {net.asset}
                    </span>
                  </div>
                  <Badge variant="outline" className="font-mono text-sm">
                    {balances[net.id] !== undefined ? String(balances[net.id]) : 'N/A'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
};

export default Balance;
