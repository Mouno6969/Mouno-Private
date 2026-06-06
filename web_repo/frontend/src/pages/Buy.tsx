import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ShoppingCart, Smartphone, CheckCircle, TrendingUp, ArrowRight, CreditCard, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';

const Buy: React.FC = () => {
  const { t } = useTranslation();
  const networks = NETWORK_LIST;

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
        <div className="w-20 h-20 bg-white text-black flex items-center justify-center mx-auto mb-8">
          <CheckCircle className="h-10 w-10" />
        </div>
        <h2 className="text-4xl font-heading font-bold mb-4 uppercase tracking-tighter">Order Received</h2>
        <div className="mb-8 border border-white/10 bg-white/5 p-12">
            <p className="text-white/40 mb-2 text-[10px] uppercase font-bold tracking-[0.2em]">Transaction ID</p>
            <p className="text-5xl font-mono font-bold text-white">{success}</p>
        </div>
        <p className="text-white/40 mb-8 text-sm font-medium leading-relaxed max-w-md mx-auto">
          Your order is being processed by the Mouno OS automation layer. Status will be updated in real-time.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" onClick={() => setSuccess(null)} className="px-10">
              New Transaction
            </Button>
            <Button asChild variant="outline" size="lg" className="px-10">
                <Link to="/orders">View Orders</Link>
            </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in duration-700">
      <section className="space-y-4">
        <div className="flex items-center gap-2 text-white/40">
           <ShoppingCart size={14} />
           <span className="text-[10px] uppercase tracking-[0.3em] font-mono">Module ◈ Buy_Crypto</span>
        </div>
        <h1 className="text-5xl font-heading font-bold tracking-tighter uppercase">Digital <span className="text-white/40">Settlement</span></h1>
        <p className="text-white/40 text-lg max-w-2xl font-medium tracking-tight">Acquire digital assets via local fiat rails. Secured by Mouno infrastructure.</p>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
        <div className="lg:col-span-8 space-y-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Network Selection */}
            <div className="space-y-4">
              <Label className="text-[10px] uppercase tracking-[0.2em] text-white/40 font-bold font-heading">01 ◈ Select Network</Label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {networks.map((net) => (
                  <button
                    key={net.id}
                    type="button"
                    onClick={() => handleNetworkChange(net.id)}
                    className={`p-6 border flex flex-col items-center gap-4 transition-all relative ${
                      selectedNetwork === net.id
                      ? 'border-white bg-white text-black'
                      : 'border-white/10 bg-black text-white hover:border-white/30'
                    }`}
                  >
                    <div className={selectedNetwork === net.id ? 'grayscale-0' : 'grayscale'}>
                        <NetworkLogo id={net.id} size={32} />
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-widest">{net.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Amounts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
              <div className="space-y-4">
                <Label htmlFor="bdt" className="text-[10px] uppercase tracking-[0.2em] text-white/40 font-bold font-heading">02 ◈ Fiat Amount (BDT)</Label>
                <div className="relative">
                  <span className="absolute left-6 top-1/2 -translate-y-1/2 text-white/20 font-bold font-mono text-xl">৳</span>
                  <Input
                    id="bdt"
                    type="number"
                    className="pl-12 h-16 text-2xl font-bold font-mono bg-white/5 border-white/10 rounded-none focus:ring-white focus:border-white"
                    placeholder="500.00"
                    value={bdtAmount}
                    onChange={(e) => handleBdtChange(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="space-y-4">
                <Label className="text-[10px] uppercase tracking-[0.2em] text-white/40 font-bold font-heading">03 ◈ You Receive (EST)</Label>
                <div className="h-16 flex items-center justify-between px-6 bg-white text-black font-bold">
                  <span className="text-2xl font-mono">{cryptoAmount}</span>
                  <span className="text-xs tracking-widest font-heading uppercase">
                    {networks.find(n => n.id === selectedNetwork)?.asset}
                  </span>
                </div>
              </div>
            </div>

            {/* Wallet Address */}
            <div className="space-y-4 pt-4">
              <Label htmlFor="wallet" className="text-[10px] uppercase tracking-[0.2em] text-white/40 font-bold font-heading">04 ◈ Destination Address</Label>
              <Input
                id="wallet"
                className="h-14 font-mono bg-white/5 border-white/10 rounded-none text-sm px-6"
                placeholder="Connect destination wallet"
                value={wallet}
                onChange={(e) => setWallet(e.target.value)}
                required
              />
              <Alert className="bg-white/5 border-white/10 text-white/60 rounded-none py-3">
                <AlertDescription className="text-[10px] uppercase tracking-wider font-medium">
                  Verify destination address. On-chain settlements are finalized upon execution.
                </AlertDescription>
              </Alert>
            </div>

            {/* Payment Section */}
            <div className="space-y-6 pt-12 border-t border-white/10">
               <div className="space-y-4">
                  <Label className="text-[10px] uppercase tracking-[0.2em] text-white/40 font-bold font-heading">05 ◈ Settlement Provider</Label>
                  <div className="border border-white/10 p-8 flex flex-col items-center gap-6 bg-black">
                      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.3em] text-white/40">
                         <Smartphone size={12} /> bKash Automation
                      </div>
                      <div className="text-4xl font-bold font-mono tracking-tighter text-white flex items-center gap-6">
                         {marketData?.bKash || '01XXXXXXXXX'}
                         <button type="button" className="text-white/20 hover:text-white transition-colors" onClick={() => navigator.clipboard.writeText(marketData?.bKash)}>
                            <CreditCard size={20} />
                         </button>
                      </div>
                      <Badge variant="outline" className="border-white/20 text-white/40">Manual Verification Active</Badge>
                  </div>
               </div>

               <div className="space-y-4">
                  <Label htmlFor="trxid" className="text-[10px] uppercase tracking-[0.2em] text-white/40 font-bold font-heading">06 ◈ Proof of Transaction (TRXID)</Label>
                  <Input
                    id="trxid"
                    className="h-14 font-mono uppercase bg-white/5 border-white/10 rounded-none px-6"
                    placeholder="Enter system identifier"
                    value={trxId}
                    onChange={(e) => setTrxId(e.target.value)}
                    required
                  />
               </div>
            </div>

            <Button type="submit" disabled={loading || !wallet || !trxId || !bdtAmount} className="w-full h-16 text-sm font-bold uppercase tracking-[0.2em]">
              {loading ? (
                 <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Finalizing...
                 </>
              ) : (
                <>
                  Initialize Order <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </form>
        </div>

        {/* Sidebar info */}
        <div className="lg:col-span-4 space-y-12">
           <div className="space-y-6">
              <h4 className="text-[11px] font-heading font-bold uppercase tracking-[0.2em] border-b border-white/10 pb-4">Protocol Specs</h4>
              <div className="space-y-6">
                 {[
                   { step: "01", title: "Allocation", desc: "Select target network and define fiat expenditure." },
                   { step: "02", title: "Transfer", desc: "Execute payment via bKash to the designated provider." },
                   { step: "03", title: "Proof", desc: "Input the transaction identifier for system matching." },
                   { step: "04", title: "Settlement", desc: "Assets are dispatched to your destination wallet." }
                 ].map((i) => (
                   <div key={i.step} className="flex gap-6 items-start">
                      <span className="text-[10px] font-mono text-white/20 font-bold">{i.step}</span>
                      <div className="space-y-1">
                         <h5 className="text-[10px] uppercase font-bold tracking-widest">{i.title}</h5>
                         <p className="text-[11px] text-white/40 leading-relaxed font-medium">{i.desc}</p>
                      </div>
                   </div>
                 ))}
              </div>
           </div>

           <div className="border border-white/10 p-8 space-y-2">
              <span className="text-[10px] uppercase font-bold text-white/40 tracking-[0.2em]">Market Signal</span>
              <p className="text-3xl font-bold font-mono">৳{marketData?.rates?.[selectedNetwork] || '0.00'}</p>
              <div className="flex items-center gap-2 text-[10px] text-white/20 font-bold uppercase tracking-widest pt-2">
                 <TrendingUp size={12} /> Optimization: Enabled
              </div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default Buy;
