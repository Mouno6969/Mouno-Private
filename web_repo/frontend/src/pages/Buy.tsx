import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { ShoppingCart, Smartphone, CheckCircle, Info, TrendingUp, ArrowRight, ShieldCheck, CreditCard } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';

const Buy: React.FC = () => {
  const { t } = useTranslation();
  const [networks] = useState([
    { id: 'solana', name: 'Solana', asset: 'USDC', icon: '🪐' },
    { id: 'trc20', name: 'Tron', asset: 'USDT', icon: '🔋' },
    { id: 'polygon', name: 'Polygon', asset: 'USDC', icon: '🟣' },
    { id: 'bsc', name: 'BSC', asset: 'USDT', icon: '🟡' },
    { id: 'ton', name: 'TON', asset: 'USDT', icon: '💎' },
  ]);

  const [selectedNetwork, setSelectedNetwork] = useState('solana');
  const [bdtAmount, setBdtAmount] = useState('');
  const [cryptoAmount, setCryptoAmount] = useState('0');
  const [wallet, setWallet] = useState('');
  const [trxId, setTrxId] = useState('');
  const [marketData, setMarketData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const fetchMarket = async () => {
      try {
        const res = await axios.get('/api/market');
        setMarketData(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchMarket();
  }, []);

  const handleBdtChange = (val: string) => {
    setBdtAmount(val);
    const rate = marketData?.rates?.[selectedNetwork] || 137;
    const crypto = val ? (parseFloat(val) / rate).toFixed(2) : '0';
    setCryptoAmount(crypto);
  };

  const handleNetworkChange = (id: string) => {
    setSelectedNetwork(id);
    const rate = marketData?.rates?.[id] || 137;
    const crypto = bdtAmount ? (parseFloat(bdtAmount) / rate).toFixed(2) : '0';
    setCryptoAmount(crypto);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post('/api/buy', {
        amount_bdt: bdtAmount,
        network: selectedNetwork,
        wallet,
        trx_id: trxId
      });
      setSuccess(res.data.order_id);
      setBdtAmount('');
      setCryptoAmount('0');
      setWallet('');
      setTrxId('');
    } catch (err) {
      console.error(err);
      alert('Failed to submit order');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20 animate-in zoom-in duration-300">
        <div className="w-24 h-24 bg-green-500/20 text-green-500 rounded-full flex items-center justify-center mx-auto mb-8">
          <CheckCircle className="h-12 w-12" />
        </div>
        <h2 className="text-4xl font-extrabold mb-4 tracking-tight">Order Received!</h2>
        <Card className="mb-8 border-green-500/30 bg-green-500/5">
          <CardContent className="py-6">
            <p className="text-muted-foreground mb-2 text-sm uppercase font-bold tracking-widest">Your Order ID</p>
            <p className="text-4xl font-mono font-black text-primary">{success}</p>
          </CardContent>
        </Card>
        <p className="text-muted-foreground mb-8 text-lg">
          Your order is being processed automatically. You can track the status in the <Link to="/orders" className="text-primary underline">Orders</Link> section.
        </p>
        <Button size="lg" onClick={() => setSuccess(null)} className="rounded-full px-10">
          Place Another Order
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
      <section className="space-y-1">
        <div className="flex items-center gap-3">
           <div className="p-2 bg-primary/10 rounded-lg">
              <ShoppingCart className="h-6 w-6 text-primary" />
           </div>
           <h1 className="text-3xl font-extrabold tracking-tight">{t('buy')} Crypto</h1>
        </div>
        <p className="text-muted-foreground">Follow these simple steps to purchase stablecoins with bKash.</p>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <div className="lg:col-span-2 space-y-6">
          <Card className="shadow-xl border-primary/10 overflow-hidden">
            <CardHeader className="bg-muted/30">
               <CardTitle className="text-lg">Order Details</CardTitle>
               <CardDescription>Select network and specify amounts</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-8">
              {/* Network Selection */}
              <div className="space-y-4">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">{t('network')}</Label>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  {networks.map((net) => (
                    <button
                      key={net.id}
                      type="button"
                      onClick={() => handleNetworkChange(net.id)}
                      className={`p-3 rounded-xl border flex flex-col items-center gap-2 transition-all relative group ${
                        selectedNetwork === net.id
                        ? 'border-primary bg-primary/10 text-primary ring-1 ring-primary'
                        : 'border-muted bg-card hover:border-primary/50'
                      }`}
                    >
                      <span className="text-2xl">{net.icon}</span>
                      <span className="text-[10px] font-black uppercase tracking-tighter">{net.name}</span>
                      {selectedNetwork === net.id && (
                        <div className="absolute -top-1 -right-1 bg-primary text-primary-foreground rounded-full p-0.5">
                           <CheckCircle className="h-3 w-3" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Amounts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <Label htmlFor="bdt" className="text-xs uppercase tracking-wider text-muted-foreground">{t('bdt_amount')}</Label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground font-bold font-mono">৳</span>
                    <Input
                      id="bdt"
                      type="number"
                      className="pl-10 h-14 text-xl font-bold font-mono bg-muted/20"
                      placeholder="Min 500"
                      value={bdtAmount}
                      onChange={(e) => handleBdtChange(e.target.value)}
                      required
                    />
                  </div>
                  <p className="text-[10px] text-muted-foreground italic">Approx. rate: ৳{marketData?.rates?.[selectedNetwork] || '...'}</p>
                </div>

                <div className="space-y-3">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground">{t('crypto_amount')} (Receive)</Label>
                  <div className="h-14 flex items-center justify-between px-4 rounded-md border bg-primary/5 border-primary/20">
                    <span className="text-2xl font-black font-mono text-primary">{cryptoAmount}</span>
                    <Badge variant="outline" className="font-mono bg-primary/10 border-primary/30">
                      {networks.find(n => n.id === selectedNetwork)?.asset}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Wallet Address */}
              <div className="space-y-3">
                <Label htmlFor="wallet" className="text-xs uppercase tracking-wider text-muted-foreground">{t('wallet_address')}</Label>
                <div className="relative">
                   <ShieldCheck className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                   <Input
                    id="wallet"
                    className="pl-10 h-12 font-mono"
                    placeholder="Enter your receive address"
                    value={wallet}
                    onChange={(e) => setWallet(e.target.value)}
                    required
                  />
                </div>
              </div>

              <Alert className="bg-amber-500/5 border-amber-500/20 text-amber-200">
                <Info className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  Double-check your wallet address. Crypto transactions are irreversible.
                </AlertDescription>
              </Alert>

              <div className="space-y-6 pt-4 border-t">
                 <div className="flex flex-col items-center gap-4 bg-muted/50 p-6 rounded-2xl border border-dashed">
                    <div className="flex items-center gap-2 text-sm font-bold text-muted-foreground">
                       <Smartphone className="h-4 w-4" /> {t('send_bdt')} to this bKash Number
                    </div>
                    <div className="text-3xl font-black font-mono tracking-widest text-primary flex items-center gap-3">
                       {marketData?.bKash || '01XXXXXXXXX'}
                       <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" onClick={() => navigator.clipboard.writeText(marketData?.bKash)}>
                          <CreditCard className="h-4 w-4" />
                       </Button>
                    </div>
                    <Badge variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20">Personal (Send Money / Cash In)</Badge>
                 </div>

                 <div className="space-y-3">
                    <Label htmlFor="trxid" className="text-xs uppercase tracking-wider text-muted-foreground">{t('trx_id')}</Label>
                    <Input
                      id="trxid"
                      className="h-12 font-mono uppercase"
                      placeholder="e.g. BMA1234567"
                      value={trxId}
                      onChange={(e) => setTrxId(e.target.value)}
                      required
                    />
                 </div>
              </div>
            </CardContent>
            <CardFooter className="bg-muted/20 p-6">
              <Button type="submit" disabled={loading} onClick={handleSubmit} className="w-full h-14 text-lg font-bold rounded-xl shadow-lg shadow-primary/20">
                {loading ? (
                   <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Processing Order...
                   </>
                ) : (
                  <>
                    Complete Purchase <ArrowRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
           <Card className="border-primary/10">
              <CardHeader>
                 <CardTitle className="text-sm font-bold flex items-center gap-2">
                    <Info className="h-4 w-4 text-primary" /> {t('how_to_buy')}
                 </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                 {[
                   { step: 1, text: "Select your network and enter the amount you want to pay." },
                   { step: 2, text: "Send the money via bKash to the provided number." },
                   { step: 3, text: "Copy the TrxID from the bKash confirmation message." },
                   { step: 4, text: "Enter TrxID and your wallet address, then submit." }
                 ].map((i) => (
                   <div key={i.step} className="flex gap-3 items-start">
                      <div className="h-5 w-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                         {i.step}
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">{i.text}</p>
                   </div>
                 ))}
              </CardContent>
           </Card>

           <Card className="bg-primary/5 border-primary/20">
              <CardHeader className="pb-2">
                 <CardDescription className="text-[10px] uppercase font-bold text-muted-foreground tracking-widest">Live Exchange Rate</CardDescription>
                 <CardTitle className="text-2xl font-black text-primary">৳{marketData?.rates?.[selectedNetwork] || '...'}</CardTitle>
              </CardHeader>
              <CardContent>
                 <div className="flex items-center gap-1 text-[10px] text-green-500 font-bold uppercase">
                    <TrendingUp className="h-3 w-3" /> Best rate in Bangladesh
                 </div>
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  );
};

// Help helper
const Loader2 = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
);

const Link = ({ to, children, className }: any) => (
  <a href={to} className={className}>{children}</a>
);

export default Buy;
