import React from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ScrollText, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { NetworkLogo, NETWORK_MAP } from '../constants/networks';
import { useTxLog } from '../lib/hooks';
import { SkeletonListRow } from '../components/ui/skeleton';
import { EmptyState, ErrorState } from '../components/ui/states';

const TxLog: React.FC = () => {
  const { token } = useAuth();
  const { data: txs, error, isLoading, isValidating, mutate } = useTxLog(Boolean(token));

  const shortWallet = (w: string) => (w ? `${w.slice(0, 6)}...${w.slice(-4)}` : 'N/A');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <ScrollText className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">TX Log</h1>
            <p className="text-muted-foreground text-sm">Complete transaction history</p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => mutate()}
          disabled={isValidating}
          aria-label="Refresh transaction log"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isValidating ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonListRow key={i} />
          ))}
        </div>
      ) : error ? (
        <Card className="border-destructive/30">
          <CardContent className="p-0">
            <ErrorState
              title="Couldn't load transactions"
              description="We couldn't reach the server to fetch your transaction history."
              onRetry={() => mutate()}
            />
          </CardContent>
        </Card>
      ) : txs.length === 0 ? (
        <Card>
          <CardContent className="p-0">
            <EmptyState
              icon={<ScrollText className="h-6 w-6" aria-hidden="true" />}
              title="No transactions yet"
              description="Your completed and pending transactions will appear here."
            />
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {txs.map((tx) => (
            <Card key={tx.trx_id} className="border-primary/10">
              <CardContent className="p-4">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-3">
                    <NetworkLogo id={tx.network} size={28} />
                    <div>
                      <div className="font-semibold text-sm">{NETWORK_MAP[tx.network]?.name || tx.network}</div>
                      <div className="text-xs text-muted-foreground">{tx.created_at?.slice(0, 16)}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono font-bold">
                      {tx.amount_crypto} {NETWORK_MAP[tx.network]?.asset || ''}
                    </div>
                    <div className="text-xs text-muted-foreground">{tx.source}</div>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between flex-wrap gap-2 text-xs">
                  <span className="font-mono text-muted-foreground">Wallet: {shortWallet(tx.wallet)}</span>
                  {tx.order_id && <span className="font-mono text-muted-foreground">{tx.order_id}</span>}
                  <Badge variant={tx.status === 'completed' ? 'default' : 'destructive'} className="text-[10px]">
                    {tx.status}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default TxLog;
