import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Gift, Clock, Users, Loader2, Ticket } from 'lucide-react';
import { NETWORK_MAP, NetworkLogo } from '../constants/networks';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

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



const Giveaway: React.FC = () => {
  const { token } = useAuth();
  const [giveaways, setGiveaways] = useState<GiveawaySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [code, setCode] = useState('');
  const [wallet, setWallet] = useState('');
  const [redeeming, setRedeeming] = useState(false);

  useEffect(() => {
    fetch(`${process.env.REACT_APP_API_URL || ''}/api/giveaways`)
      .then(r => r.json())
      .then(d => setGiveaways(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleRedeem = async () => {
    if (!code.trim() || !wallet.trim()) {
      toast.error('Please enter both the giveaway code and your wallet address');
      return;
    }
    setRedeeming(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/gift/redeem`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ code: code.trim(), wallet: wallet.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message || 'Giveaway reward claimed successfully!');
        setCode('');
        setWallet('');
      } else {
        toast.error(data.message || 'Could not redeem this giveaway code');
      }
    } catch (err) {
      toast.error('Failed to connect to server');
    } finally {
      setRedeeming(false);
    }
  };

  const botUsername = process.env.REACT_APP_BOT_USERNAME || 'CryptoBGCbot';

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Gift className="h-6 w-6 text-primary" />
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight">Giveaways</h1>
      </div>
      <p className="text-muted-foreground">Active giveaway sessions — redeem your giveaway code below to receive your reward instantly.</p>

      {/* Redeem giveaway code */}
      <Card className="border-primary/20">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Ticket className="h-5 w-5 text-primary" /> Redeem Giveaway Code
          </CardTitle>
          <CardDescription>
            Enter the giveaway code you received and the wallet address where you want the reward sent.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {token ? (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Giveaway code</label>
                <Input
                  placeholder="ABC12345"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Receiving wallet address</label>
                <Input
                  placeholder="Enter your wallet address"
                  value={wallet}
                  onChange={(e) => setWallet(e.target.value)}
                />
              </div>
              <Button className="w-full" onClick={handleRedeem} disabled={redeeming}>
                {redeeming ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Processing...
                  </>
                ) : (
                  'Claim Reward'
                )}
              </Button>
            </>
          ) : (
            <div className="text-sm text-muted-foreground">
              <p className="mb-3">Please log in to redeem a giveaway code on the website.</p>
              <Button asChild variant="outline" className="w-full">
                <Link to="/login">Log in to redeem</Link>
              </Button>
            </div>
          )}

          <div className="pt-2 border-t border-border/50">
            <p className="text-xs text-muted-foreground mb-2">Prefer Telegram? Redeem your giveaway code directly in our bot.</p>
            <Button asChild variant="secondary" className="w-full">
              <a
                href={`https://t.me/${botUsername}?start=giveaway_redeem`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Redeem on Telegram Bot
              </a>
            </Button>
          </div>
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
