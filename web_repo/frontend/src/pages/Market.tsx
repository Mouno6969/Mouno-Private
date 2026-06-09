import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import {
  Store,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  Smartphone,
  Info,
  MessageCircle,
  Loader2,
  CreditCard,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { NETWORK_MAP, NetworkLogo } from '../constants/networks';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

interface SellerNetwork {
  network: string;
  rate: number;
}

interface MarketSeller {
  seller_id: string;
  display_name: string;
  support_contact: string;
  bkash_number: string;
  networks: SellerNetwork[];
}

const Market: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const [sellers, setSellers] = useState<MarketSeller[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSeller, setSelectedSeller] = useState<MarketSeller | null>(null);

  // Order form state
  const [network, setNetwork] = useState('');
  const [wallet, setWallet] = useState('');
  const [bdtAmount, setBdtAmount] = useState('');
  const [trxId, setTrxId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<any>(null);

  useEffect(() => {
    const fetchSellers = async () => {
      try {
        const res = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/sellers`);
        const data = await res.json();
        setSellers(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchSellers();
  }, []);

  const selectSeller = (seller: MarketSeller) => {
    setSelectedSeller(seller);
    setNetwork(seller.networks[0]?.network || '');
    setWallet('');
    setBdtAmount('');
    setTrxId('');
  };

  const currentRate = selectedSeller?.networks.find((n) => n.network === network)?.rate || 0;
  const cryptoAmount = bdtAmount && currentRate ? (parseFloat(bdtAmount) / currentRate).toFixed(6) : '0';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSeller) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/seller/order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          seller_id: selectedSeller.seller_id,
          network,
          wallet,
          amount_bdt: bdtAmount,
          trx_id: trxId,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setSuccess(data);
      } else {
        toast.error(data.message || 'Failed to place order');
      }
    } catch (err) {
      toast.error('Failed to connect to server');
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20 animate-in zoom-in duration-300">
        <div className="w-24 h-24 bg-green-500/20 text-green-500 rounded-full flex items-center justify-center mx-auto mb-8">
          <CheckCircle className="h-12 w-12" />
        </div>
        <h2 className="text-4xl font-extrabold mb-4 tracking-tight">Seller Order Placed!</h2>
        <Card className="mb-8 border-green-500/30 bg-green-500/5">
          <CardContent className="py-6">
            <p className="text-muted-foreground mb-2 text-sm uppercase font-bold tracking-widest">Your Order ID</p>
            <p className="text-2xl sm:text-3xl font-mono font-black text-primary break-all">{success.order_id}</p>
          </CardContent>
        </Card>
        <p className="text-muted-foreground mb-8 text-lg text-pretty">
          The seller will verify your bKash payment and deliver{' '}
          <span className="font-mono font-bold text-primary">{success.amount_crypto}</span> to your wallet.
          Track it in the <Link to="/order-status" className="text-primary underline">Order Status</Link> section.
        </p>
        <Button size="lg" onClick={() => { setSuccess(null); setSelectedSeller(null); }} className="rounded-full px-10">
          Back to Marketplace
        </Button>
      </div>
    );
  }

  // ── Order form for a selected seller ──
  if (selectedSeller) {
    if (!token) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
          <Store className="h-12 w-12 text-primary" />
          <h2 className="text-2xl font-bold">{t('login')} Required</h2>
          <p className="text-muted-foreground text-center max-w-md text-pretty">
            You need an account to place an order with a seller.
          </p>
          <div className="flex gap-2">
            <Button asChild><Link to="/login">{t('login')}</Link></Button>
            <Button asChild variant="outline"><Link to="/register">{t('register')}</Link></Button>
          </div>
        </div>
      );
    }

    return (
      <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
        <section className="space-y-1">
          <button
            onClick={() => setSelectedSeller(null)}
            className="flex items-center gap-1 text-xs uppercase tracking-widest font-mono text-muted-foreground hover:text-primary transition-colors mb-2"
          >
            <ArrowLeft className="h-3 w-3" /> {t('market')}
          </button>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Store className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">{selectedSeller.display_name}</h1>
          </div>
          <p className="text-muted-foreground">Place a bKash order with this seller.</p>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit}>
              <Card className="shadow-xl border-primary/10 overflow-hidden">
                <CardHeader className="bg-muted/30">
                  <CardTitle className="text-lg">Seller Order Details</CardTitle>
                  <CardDescription>Select network and specify amounts</CardDescription>
                </CardHeader>
                <CardContent className="pt-6 space-y-8">
                  <div className="space-y-4">
                    <Label className="text-xs uppercase tracking-wider text-muted-foreground">{t('network')}</Label>
                    <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
                      {selectedSeller.networks.map((n) => (
                        <button
                          key={n.network}
                          type="button"
                          onClick={() => setNetwork(n.network)}
                          className={`p-3 rounded-xl border flex flex-col items-center gap-2 transition-all relative ${
                            network === n.network
                              ? 'border-primary bg-primary/10 text-primary ring-1 ring-primary'
                              : 'border-muted bg-card hover:border-primary/50'
                          }`}
                        >
                          <NetworkLogo id={n.network} size={28} />
                          <span className="text-[10px] font-black uppercase tracking-tighter">
                            {NETWORK_MAP[n.network]?.name || n.network}
                          </span>
                          <span className="text-[9px] font-mono text-muted-foreground">৳{n.rate}</span>
                          {network === n.network && (
                            <div className="absolute -top-1 -right-1 bg-primary text-primary-foreground rounded-full p-0.5">
                              <CheckCircle className="h-3 w-3" />
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <Label htmlFor="bdt" className="text-xs uppercase tracking-wider text-muted-foreground">{t('bdt_amount')}</Label>
                      <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground font-bold font-mono">৳</span>
                        <Input
                          id="bdt"
                          type="number"
                          className="pl-10 h-14 text-xl font-bold font-mono bg-muted/20"
                          placeholder="e.g. 1000"
                          value={bdtAmount}
                          onChange={(e) => setBdtAmount(e.target.value)}
                          required
                        />
                      </div>
                      <p className="text-[10px] text-muted-foreground italic">Seller rate: ৳{currentRate || '...'}</p>
                    </div>

                    <div className="space-y-3">
                      <Label className="text-xs uppercase tracking-wider text-muted-foreground">{t('crypto_amount')} (Receive)</Label>
                      <div className="h-14 flex items-center justify-between px-4 rounded-md border bg-primary/5 border-primary/20">
                        <span className="text-2xl font-black font-mono text-primary">{cryptoAmount}</span>
                        <Badge variant="outline" className="font-mono bg-primary/10 border-primary/30">
                          {NETWORK_MAP[network]?.asset || ''}
                        </Badge>
                      </div>
                    </div>
                  </div>

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
                      Pay the seller&apos;s bKash number below, not the platform number. Crypto transactions are irreversible.
                    </AlertDescription>
                  </Alert>

                  <div className="space-y-6 pt-4 border-t">
                    <div className="flex flex-col items-center gap-4 bg-muted/50 p-6 rounded-2xl border border-dashed">
                      <div className="flex items-center gap-2 text-sm font-bold text-muted-foreground">
                        <Smartphone className="h-4 w-4" /> {t('send_bdt')} Seller bKash Number
                      </div>
                      <div className="text-3xl font-black font-mono tracking-widest text-primary flex items-center gap-3">
                        {selectedSeller.bkash_number}
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground"
                          onClick={() => { navigator.clipboard.writeText(selectedSeller.bkash_number); toast.success(t('copy_success')); }}
                        >
                          <CreditCard className="h-4 w-4" />
                        </Button>
                      </div>
                      <Badge variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20">Personal (Send Money)</Badge>
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
                  <Button
                    type="submit"
                    disabled={submitting || !wallet || !trxId || !bdtAmount || !network}
                    className="w-full h-14 text-lg font-bold rounded-xl shadow-lg shadow-primary/20"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Placing Order...
                      </>
                    ) : (
                      <>
                        Place Seller Order <ArrowRight className="ml-2 h-5 w-5" />
                      </>
                    )}
                  </Button>
                </CardFooter>
              </Card>
            </form>
          </div>

          <div className="space-y-6">
            <Card className="border-primary/10">
              <CardHeader>
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <Info className="h-4 w-4 text-primary" /> How it works
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { step: 1, text: 'Pick a network this seller supports and enter the BDT amount.' },
                  { step: 2, text: "Send the money via bKash to the seller's number shown in the form." },
                  { step: 3, text: 'Copy the TrxID from the bKash confirmation message.' },
                  { step: 4, text: 'Submit the order. The seller verifies and delivers your crypto.' },
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
                <CardDescription className="text-[10px] uppercase font-bold text-muted-foreground tracking-widest">Seller Support</CardDescription>
                <CardTitle className="text-lg font-black text-primary flex items-center gap-2">
                  <MessageCircle className="h-4 w-4" /> {selectedSeller.support_contact}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">Contact the seller directly on Telegram for order help.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  // ── Marketplace listing ──
  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
      <section className="space-y-1">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Store className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">{t('market')}</h1>
        </div>
        <p className="text-muted-foreground text-pretty">
          Buy crypto directly from verified sellers. Each seller sets their own rates and supported networks.
        </p>
      </section>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-muted-foreground gap-2">
          <Loader2 className="h-5 w-5 animate-spin" /> Loading sellers...
        </div>
      ) : sellers.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center space-y-3">
            <Store className="h-10 w-10 text-muted-foreground mx-auto" />
            <p className="font-bold">No active sellers right now</p>
            <p className="text-sm text-muted-foreground">
              Check back later, or buy directly from the platform on the{' '}
              <Link to="/buy" className="text-primary underline">Buy</Link> page.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sellers.map((seller) => (
            <Card key={seller.seller_id} className="border-primary/10 hover:border-primary/40 transition-colors flex flex-col">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center font-black text-primary font-mono">
                    {seller.display_name?.[0]?.toUpperCase() || 'S'}
                  </div>
                  <div className="min-w-0">
                    <CardTitle className="text-base truncate">{seller.display_name}</CardTitle>
                    <CardDescription className="text-xs font-mono truncate">{seller.support_contact}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 space-y-3">
                <p className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground">Networks &amp; Rates</p>
                <div className="flex flex-wrap gap-2">
                  {seller.networks.map((n) => (
                    <Badge key={n.network} variant="outline" className="font-mono gap-1.5 py-1 border-primary/20 bg-primary/5">
                      <NetworkLogo id={n.network} size={14} />
                      {NETWORK_MAP[n.network]?.name || n.network} ৳{n.rate}
                    </Badge>
                  ))}
                </div>
              </CardContent>
              <CardFooter>
                <Button className="w-full font-bold" onClick={() => selectSeller(seller)}>
                  Buy from this Seller <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default Market;
