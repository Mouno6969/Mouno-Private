import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Gift, Clock, Users, Loader2 } from 'lucide-react';

interface GiveawaySession {
  session_id: string;
  network: string;
  base_amount: number;
  recipient_count: number;
  early_bonus_count: number;
  early_bonus_amount: number;
  claimed_count: number;
  remaining: number;
  expires_at: string;
  created_at: string;
}

const NETWORK_NAMES: Record<string, string> = {
  solana: 'Solana USDC', trc20: 'Tron USDT', polygon: 'Polygon USDC',
  bsc: 'BSC USDT', ton: 'TON', avalanche: 'Avalanche USDT',
  ethereum: 'ETH USDT', ethereum_usdc: 'ETH USDC', base: 'Base USDC',
};

const NETWORK_ICONS: Record<string, string> = {
  solana: '🪐', trc20: '🔋', polygon: '🟣', bsc: '🟡', ton: '💎',
  avalanche: '🔺', ethereum: '🔹', ethereum_usdc: '🔹', base: '🔵',
};

const Giveaway: React.FC = () => {
  const [giveaways, setGiveaways] = useState<GiveawaySession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/giveaways')
      .then(r => r.json())
      .then(d => setGiveaways(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Gift className="h-6 w-6 text-primary" />
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight">Giveaways</h1>
      </div>
      <p className="text-muted-foreground">Active giveaway sessions — claim codes on the Gift Codes page.</p>

      {loading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {!loading && giveaways.length === 0 && (
        <Card className="border-primary/10">
          <CardContent className="py-12 text-center text-muted-foreground">
            No active giveaways right now. Check back later!
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {giveaways.map((g) => {
          const expired = new Date(g.expires_at) < new Date();
          const full = g.remaining <= 0;
          return (
            <Card key={g.session_id} className={`border-primary/10 ${expired || full ? 'opacity-60' : ''}`}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    {NETWORK_ICONS[g.network] || '🎁'} {NETWORK_NAMES[g.network] || g.network} Giveaway
                  </CardTitle>
                  <Badge variant={expired ? 'destructive' : full ? 'secondary' : 'default'}>
                    {expired ? 'Expired' : full ? 'Fully Claimed' : 'Active'}
                  </Badge>
                </div>
                <CardDescription>Session: {g.session_id}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground text-xs">Amount per claim</p>
                    <p className="font-bold">{g.base_amount}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs flex items-center gap-1"><Users className="h-3 w-3" /> Claims</p>
                    <p className="font-bold">{g.claimed_count} / {g.recipient_count}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Remaining</p>
                    <p className="font-bold">{g.remaining}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs flex items-center gap-1"><Clock className="h-3 w-3" /> Expires</p>
                    <p className="font-bold text-xs">{new Date(g.expires_at).toLocaleString()}</p>
                  </div>
                </div>
                {g.early_bonus_count > 0 && g.early_bonus_amount > 0 && (
                  <div className="mt-3 p-2 bg-primary/5 rounded text-xs">
                    🎯 First {g.early_bonus_count} claimers get +{g.early_bonus_amount} bonus!
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default Giveaway;
