import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Gift, Clock, Users, Loader2, Ticket, Send, Star, ArrowRight, Sparkles } from 'lucide-react';
import { PageHeader, RelativeTime, TexturePanel } from '../components/common';
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
    <div className="max-w-5xl mx-auto space-y-4 sm:space-y-6 px-1 sm:px-0 animate-in fade-in duration-300">
      <PageHeader
        icon={<Gift className="h-7 w-7" />}
        eyebrow="Win"
        title="Giveaways"
        description="Active giveaway sessions — claim codes and win crypto rewards."
      />

      {/* Hero Banner */}
      <TexturePanel variant="success" glow accentTop>
        <div className="p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="p-4 bg-primary/10 rounded-2xl">
              <Sparkles className="h-10 w-10 text-primary" />
            </div>
            <div className="text-center sm:text-left">
              <h2 className="text-2xl font-extrabold tracking-tight">Claim Your Reward</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Enter a giveaway code to receive crypto directly to your wallet.
              </p>
            </div>
          </div>
        </div>
      </TexturePanel>

      {/* Redeem Section */}
      <Card className="border-primary/15 shadow-xl overflow-hidden">
        <CardHeader className="bg-muted/30">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Ticket className="h-5 w-5 text-primary" /> Redeem Giveaway Code
          </CardTitle>
          <CardDescription>Enter a giveaway code to claim your reward directly to your wallet.</CardDescription>
        </CardHeader>
        <CardContent className="p-5 sm:p-6 space-y-5">
          {token ? (
            <>
              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground">Giveaway Code</Label>
                  <div className="relative">
                    <Ticket className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="ABC12345"
                      value={code}
                      onChange={(e) => setCode(e.target.value.toUpperCase())}
                      className="pl-10 font-mono uppercase tracking-wider"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground">Wallet Address</Label>
                  <Input
                    placeholder="Enter your receiving address"
                    value={wallet}
                    onChange={(e) => setWallet(e.target.value)}
                    className="font-mono"
                  />
                </div>
              </div>
              <Button
                className="w-full h-11 font-bold rounded-xl shadow-lg shadow-primary/20"
                onClick={handleRedeem}
                disabled={redeeming || !code || !wallet}
              >
                {redeeming ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" /> Processing...
                  </>
                ) : (
                  <>
                    <Gift className="mr-2 h-4 w-4" /> Claim Reward
                  </>
                )}
              </Button>
            </>
          ) : (
            <Button asChild className="w-full h-11 font-bold rounded-xl">
              <Link to="/login">Log in to redeem <ArrowRight className="ml-2 h-4 w-4" /></Link>
            </Button>
          )}
          <a
            href={`https://t.me/${botUsername}?start=giveaway_redeem`}
            target="_blank"
            rel="noopener noreferrer"
            className="block"
          >
            <Button variant="outline" className="w-full h-11 font-semibold">
              <Send className="mr-2 h-4 w-4 text-[#229ED9]" /> Redeem on Telegram Bot
            </Button>
          </a>
        </CardContent>
      </Card>

      {/* Active Giveaways Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold tracking-tight">Active Giveaways</h2>
          {!loading && giveaways.filter(g => new Date(g.expires_at) >= new Date() && g.remaining > 0).length > 0 && (
            <Badge variant="success" className="gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" /> LIVE
            </Badge>
          )}
        </div>

        {loading && (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {!loading && giveaways.length === 0 && (
          <Card className="border-border/50">
            <CardContent className="py-12 text-center">
              <Gift className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground font-medium">No active giveaways right now.</p>
              <p className="text-xs text-muted-foreground mt-1">Check back soon for new giveaway sessions!</p>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {giveaways.map((g) => {
            const expired = new Date(g.expires_at) < new Date();
            const full = g.remaining <= 0;
            const progress = g.recipient_count > 0 ? (g.claimed_count / g.recipient_count) * 100 : 0;
            const remainingPct = 100 - progress;
            const isActive = !expired && !full;

            return (
              <Card
                key={g.session_id}
                className={`border-primary/10 transition-all ${isActive ? 'hover:border-primary/30 hover:shadow-lg' : 'opacity-60'}`}
              >
                <CardContent className="p-5 space-y-4">
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <NetworkLogo id={g.network} size={24} />
                      <span className="font-bold text-sm">{NETWORK_MAP[g.network]?.name || g.network} Giveaway</span>
                    </div>
                    <Badge variant={expired ? 'destructive' : full ? 'secondary' : 'success'}>
                      {expired ? 'Expired' : full ? 'Fully Claimed' : 'Active'}
                    </Badge>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{g.claimed_count} / {g.recipient_count} claimed</span>
                      <span className={isActive ? 'text-primary font-medium' : ''}>{remainingPct.toFixed(0)}% remaining</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <div className="text-center p-2 rounded-lg bg-muted/30">
                      <p className="text-[10px] text-muted-foreground">Per claim</p>
                      <p className="text-xs font-bold">{g.base_amount} {NETWORK_MAP[g.network]?.asset}</p>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-muted/30">
                      <p className="text-[10px] text-muted-foreground flex items-center justify-center gap-0.5"><Users className="h-2.5 w-2.5" /> Claims</p>
                      <p className="text-xs font-bold">{g.claimed_count}/{g.recipient_count}</p>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-muted/30">
                      <p className="text-[10px] text-muted-foreground">Left</p>
                      <p className="text-xs font-bold">{g.remaining}</p>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-muted/30">
                      <p className="text-[10px] text-muted-foreground flex items-center justify-center gap-0.5"><Clock className="h-2.5 w-2.5" /> Expires</p>
                      <RelativeTime value={g.expires_at} className="text-xs font-bold" />
                    </div>
                  </div>

                  {/* Early Bonus */}
                  {g.early_bonus_count > 0 && g.early_bonus_amount > 0 && (
                    <div className="flex items-center gap-2 p-2.5 bg-warning/5 border border-warning/20 rounded-lg">
                      <Star className="h-4 w-4 text-warning shrink-0" />
                      <span className="text-xs font-medium text-warning">
                        First {g.early_bonus_count} claimers get +{g.early_bonus_amount} bonus!
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Giveaway;
