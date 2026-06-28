import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Gift, ShieldCheck, AlertTriangle, CheckCircle, ArrowRight, TrendingUp, DollarSign } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';
import { PageHeader, StatCard, TexturePanel } from '../components/common';

const GiftCode: React.FC = () => {
  const { t } = useTranslation();
  const [code, setCode] = useState('');
  const [wallet, setWallet] = useState('');
  const [selectedNetwork, setSelectedNetwork] = useState('solana');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleRedeem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || !wallet) {
      toast.error('Please enter both code and wallet address');
      return;
    }

    setLoading(true);
    try {
      const res = await apiClient.post<{ message: string }>(
        '/api/gift/redeem',
        { code, wallet },
        { silent: true }
      );
      toast.success(res.data.message);
      setSuccess(true);
      setCode('');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to connect to server'));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20 animate-in zoom-in duration-300">
        <div className="w-24 h-24 bg-success/15 text-success rounded-full flex items-center justify-center mx-auto mb-8">
          <CheckCircle className="h-12 w-12" />
        </div>
        <h2 className="text-4xl font-extrabold mb-4 tracking-tight">Code Redeemed!</h2>
        <p className="text-muted-foreground mb-8 text-lg">
          Your gift code has been processed. The crypto will arrive in your wallet shortly.
        </p>
        <Button size="lg" onClick={() => setSuccess(false)} className="rounded-full px-10">
          Redeem Another Code
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-300">
      <PageHeader
        icon={<Gift className="h-7 w-7" />}
        eyebrow="Rewards"
        title={t('redeem_gift', 'Redeem Gift Code')}
        description="Enter your gift code to receive crypto instantly to your wallet."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Main Form */}
        <div className="lg:col-span-2">
          <TexturePanel variant="primary" accentTop glow>
            <form onSubmit={handleRedeem} className="p-5 sm:p-6 space-y-6">
              <div>
                <h2 className="text-lg font-semibold tracking-tight">Enter Your Code</h2>
                <p className="text-sm text-muted-foreground mt-1">Paste the gift code you received from a giveaway or promotion.</p>
              </div>

              {/* Code Input */}
              <div className="space-y-2">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">{t('enter_code', 'Gift Code')}</Label>
                <div className="relative">
                  <Gift className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                  <Input
                    placeholder="GIFT-XXXXXX"
                    className="pl-10 h-12 font-mono text-lg uppercase tracking-widest"
                    value={code}
                    onChange={(e) => setCode(e.target.value.toUpperCase())}
                    required
                  />
                </div>
              </div>

              {/* Wallet Address */}
              <div className="space-y-2">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">{t('wallet_address', 'Receiving Wallet Address')}</Label>
                <div className="relative">
                  <ShieldCheck className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                  <Input
                    placeholder="Enter your receiving address"
                    className="pl-10 h-12 font-mono"
                    value={wallet}
                    onChange={(e) => setWallet(e.target.value)}
                    required
                  />
                </div>
              </div>

              {/* Network Selector */}
              <div className="space-y-3">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Select Network</Label>
                <div className="grid grid-cols-4 sm:grid-cols-5 gap-2">
                  {NETWORK_LIST.slice(0, 5).map((net) => (
                    <button
                      key={net.id}
                      type="button"
                      onClick={() => setSelectedNetwork(net.id)}
                      className={`p-3 rounded-xl border flex flex-col items-center gap-2 transition-all relative ${
                        selectedNetwork === net.id
                          ? 'border-primary bg-primary/10 text-primary ring-1 ring-primary'
                          : 'border-border/50 bg-card/50 hover:border-primary/50'
                      }`}
                    >
                      <NetworkLogo id={net.id} size={24} />
                      <span className="text-[10px] font-bold uppercase tracking-tighter">{net.name}</span>
                      {selectedNetwork === net.id && (
                        <div className="absolute -top-1 -right-1 bg-primary text-primary-foreground rounded-full p-0.5">
                          <CheckCircle className="h-3 w-3" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Warning */}
              <Alert className="bg-warning/5 border-warning/20 text-warning">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  Double-check your wallet address and network. Crypto transfers are irreversible.
                </AlertDescription>
              </Alert>

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full h-12 text-base font-bold rounded-xl shadow-lg shadow-primary/20"
                disabled={loading || !code || !wallet}
              >
                {loading ? (
                  'Processing...'
                ) : (
                  <>
                    Redeem Code <ArrowRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </Button>
            </form>
          </TexturePanel>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* How It Works */}
          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Gift className="h-4 w-4 text-primary" /> How It Works
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { step: 1, text: 'Get a gift code from giveaways or promotions.' },
                { step: 2, text: 'Select the correct network for your wallet.' },
                { step: 3, text: 'Enter the code and your receiving address.' },
                { step: 4, text: 'Crypto is sent automatically after verification.' },
              ].map((item) => (
                <div key={item.step} className="flex gap-3 items-start">
                  <div className="h-5 w-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    {item.step}
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">{item.text}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Stats */}
          <Card className="border-primary/10">
            <CardContent className="p-4 space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <TrendingUp className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Codes Redeemed</p>
                  <p className="text-lg font-bold tracking-tight">2,847</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <DollarSign className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Total Distributed</p>
                  <p className="text-lg font-bold tracking-tight">$45,200</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Supported Networks */}
          <Card className="border-primary/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-bold">Supported Networks</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1.5">
                {NETWORK_LIST.slice(0, 5).map((net) => (
                  <div key={net.id} className="flex items-center gap-2 p-1.5 rounded bg-muted/30 text-xs">
                    <NetworkLogo id={net.id} size={16} />
                    <span>{net.name}</span>
                    <Badge variant="outline" className="ml-auto text-[9px] px-1.5">{net.asset}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default GiftCode;
