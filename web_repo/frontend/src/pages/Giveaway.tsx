import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Gift, Clock, Users, Loader2, Ticket } from 'lucide-react';
import { PageHeader, RelativeTime } from '../components/common';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { NETWORK_MAP, NetworkLogo } from '../constants/networks';
import { apiClient, getErrorMessage } from '../lib/apiClient';

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



const botUsername = 'Automatedcryptobuybot';

const Giveaway: React.FC = () => {
  const { token } = useAuth();
  const [giveaways, setGiveaways] = useState<GiveawaySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [code, setCode] = useState('');
  const [wallet, setWallet] = useState('');
  const [redeeming, setRedeeming] = useState(false);

  useEffect(() => {
    apiClient
      .get<GiveawaySession[]>('/api/giveaways', { silent: true })
      .then(r => setGiveaways(Array.isArray(r.data) ? r.data : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleRedeem = async () => {
    if (!code || !wallet) {
      toast.error('Please enter both code and wallet address');
      return;
    }
    setRedeeming(true);
    try {
      const res = await apiClient.post<{ message: string }>(
        '/api/gift/redeem',
        { code, wallet },
        { silent: true }
      );
      toast.success(res.data.message);
      setCode('');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to connect to server'));
    } finally {
      setRedeeming(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader icon={<Gift className="h-7 w-7" />} eyebrow="Win" title="Giveaways" description="Active giveaway sessions — claim codes on the Gift Codes page." />

      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Ticket className="h-5 w-5 text-primary" /> Redeem Giveaway Code
          </CardTitle>
          <CardDescription>Enter a giveaway code to claim your reward directly to your wallet.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {token ? (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Giveaway Code</label>
                <Input
                  placeholder="ABC12345"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Wallet Address</label>
                <Input
                  placeholder="Enter your receiving address"
                  value={wallet}
                  onChange={(e) => setWallet(e.target.value)}
                />
              </div>
              <Button className="w-full" onClick={handleRedeem} disabled={redeeming}>
                {redeeming ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" /> Processing...
                  </>
                ) : (
                  'Claim Reward'
                )}
              </Button>
            </>
          ) : (
            <Button asChild className="w-full">
              <Link to="/login">Log in to redeem</Link>
            </Button>
          )}
          <a
            href={`https://t.me/${botUsername}?start=giveaway_redeem`}
            target="_blank"
            rel="noopener noreferrer"
            className="block"
          >
            <Button variant="outline" className="w-full">
              Redeem on Telegram Bot
            </Button>
          </a>
        </CardContent>
      </Card>

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
                    <NetworkLogo id={g.network} size={20} className="mr-1" /> {NETWORK_MAP[g.network]?.name || g.network} Giveaway
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
                    <RelativeTime value={g.expires_at} className="font-bold text-xs" />
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
