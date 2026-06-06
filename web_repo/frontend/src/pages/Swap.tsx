import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { RefreshCw, ArrowRight, Settings, Info, ArrowDown, ChevronDown, Zap, ShieldCheck, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { NetworkLogo } from '../constants/networks';

const Swap: React.FC = () => {
  const { t } = useTranslation();
  const [fromChain, setFromChain] = useState('1'); // Ethereum
  const [toChain, setToChain] = useState('137'); // Polygon
  const [fromToken, setFromToken] = useState('0x0000000000000000000000000000000000000000'); // ETH
  const [toToken, setToToken] = useState('0x2791bca1f2de4661ed88a30c99a7a9449aa84174'); // USDC
  const [amount, setAmount] = useState('');
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const getQuote = async () => {
    if (!amount) return;
    setLoading(true);
    try {
      const res = await axios.get(`/api/swap/quote`, {
        params: { fromChain, toChain, fromToken, toToken, amount }
      });
      setQuote(res.data);
    } catch (err) {
      console.error(err);
      alert('Failed to get quote');
    } finally {
      setLoading(false);
    }
  };

  const chains = [
    { id: '1', name: 'Ethereum', symbol: 'ETH', networkId: 'ethereum' },
    { id: '56', name: 'BSC', symbol: 'BNB', networkId: 'bsc' },
    { id: '137', name: 'Polygon', symbol: 'POL', networkId: 'polygon' },
    { id: '8453', name: 'Base', symbol: 'ETH', networkId: 'base' },
    { id: '43114', name: 'Avalanche', symbol: 'AVAX', networkId: 'avalanche' },
    { id: '1151111081099710', name: 'Solana', symbol: 'SOL', networkId: 'solana' },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in duration-700">
      <section className="space-y-4">
        <div className="flex items-center gap-2 text-white/40">
           <RefreshCw size={14} />
           <span className="text-[10px] uppercase tracking-[0.3em] font-mono">Module ◈ Bridge_Swap</span>
        </div>
        <h1 className="text-5xl font-heading font-bold tracking-tighter uppercase">Cross-Chain <span className="text-white/40">Liquidity</span></h1>
        <p className="text-white/40 text-lg max-w-2xl font-medium tracking-tight">Aggregate deep liquidity across 20+ chains. Permissionless settlement.</p>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
        <div className="lg:col-span-8">
          <div className="border border-white/10 p-1 bg-white/5 space-y-1">
            {/* From Block */}
            <div className="bg-black p-8 border border-white/5">
                <div className="flex justify-between items-center mb-6">
                   <span className="text-[10px] font-bold uppercase text-white/40 tracking-[0.2em]">01 ◈ Source Allocation</span>
                   <Badge variant="outline" className="font-mono text-[9px] border-white/5">BAL: 0.00</Badge>
                </div>
                <div className="flex flex-col sm:flex-row items-center gap-6">
                  <Input
                    type="number"
                    placeholder="0.00"
                    className="border-none bg-transparent text-5xl font-bold p-0 h-auto focus-visible:ring-0 placeholder:text-white/10 font-mono"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                  />
                  <Select value={fromChain} onValueChange={setFromChain}>
                    <SelectTrigger className="w-full sm:w-[180px] h-14 rounded-none bg-white text-black font-bold uppercase tracking-widest text-[11px] border-none">
                       <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-black border-white/10 rounded-none">
                      {chains.map(chain => (
                        <SelectItem key={chain.id} value={chain.id} className="text-white focus:bg-white focus:text-black rounded-none">
                          <div className="flex items-center gap-2">
                             <NetworkLogo id={chain.networkId} size={16} /> <span>{chain.symbol}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
            </div>

            {/* Reverse Icon */}
            <div className="flex justify-center -my-6 z-10 relative">
                <button
                  className="bg-white text-black h-12 w-12 flex items-center justify-center hover:scale-110 transition-transform active:scale-95"
                  onClick={() => {
                    const temp = fromChain;
                    setFromChain(toChain);
                    setToChain(temp);
                  }}
                >
                  <ArrowDown className="h-5 w-5" />
                </button>
            </div>

            {/* To Block */}
            <div className="bg-black p-8 border border-white/5">
                <div className="flex justify-between items-center mb-6">
                   <span className="text-[10px] font-bold uppercase text-white/40 tracking-[0.2em]">02 ◈ Target Settlement (EST)</span>
                </div>
                <div className="flex flex-col sm:flex-row items-center gap-6">
                  <div className="text-5xl font-bold w-full text-white/20 font-mono">
                    {quote ? quote.summary?.to_amount : '0.00'}
                  </div>
                  <Select value={toChain} onValueChange={setToChain}>
                    <SelectTrigger className="w-full sm:w-[180px] h-14 rounded-none border border-white/10 bg-black text-white font-bold uppercase tracking-widest text-[11px] hover:bg-white/5">
                       <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-black border-white/10 rounded-none">
                       {chains.map(chain => (
                        <SelectItem key={chain.id} value={chain.id} className="text-white focus:bg-white focus:text-black rounded-none">
                          <div className="flex items-center gap-2">
                             <NetworkLogo id={chain.networkId} size={16} /> <span>{chain.symbol}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
            </div>

            {quote && (
                <div className="p-8 border-t border-white/10 bg-black space-y-4 animate-in slide-in-from-top-2 duration-300">
                   <div className="flex justify-between items-center text-[10px] uppercase font-bold tracking-[0.2em] text-white/40">
                      <span>Rate Optimization</span>
                      <Badge variant="outline" className="text-[8px] border-white/10">LI.FI v2.4</Badge>
                   </div>
                   <div className="grid grid-cols-2 gap-8">
                      <div className="space-y-1">
                         <p className="text-[10px] text-white/20 uppercase tracking-widest">Exchange Rate</p>
                         <p className="text-sm font-mono font-bold">1 {chains.find(c => c.id === fromChain)?.symbol} ≈ {quote.summary?.to_amount} {quote.summary?.to_symbol}</p>
                      </div>
                      <div className="space-y-1 text-right">
                         <p className="text-[10px] text-white/20 uppercase tracking-widest">Est. Gas Fees</p>
                         <p className="text-sm font-mono font-bold text-white">${quote.summary?.gas_usd}</p>
                      </div>
                   </div>
                </div>
            )}

            <div className="p-8 pt-4">
                {!quote ? (
                   <Button
                    onClick={getQuote}
                    disabled={loading || !amount}
                    className="w-full h-16 text-[11px] uppercase tracking-[0.3em]"
                   >
                    {loading ? (
                        <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Fetching Routes...
                        </>
                    ) : (
                        <>Get Quotation</>
                    )}
                   </Button>
                ) : (
                   <div className="space-y-4">
                      <Button className="w-full h-16 text-[11px] bg-white text-black hover:bg-white/90 uppercase tracking-[0.3em]">
                        Initialize Swap <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                      <p className="text-center text-[9px] uppercase font-bold text-white/20 tracking-[0.4em]">Settlement via Li.Fi Hub</p>
                   </div>
                )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-12">
           <div className="space-y-6">
              <h4 className="text-[11px] font-heading font-bold uppercase tracking-[0.2em] border-b border-white/10 pb-4">Routing Protocol</h4>
              <div className="space-y-6">
                 <p className="text-xs text-white/40 leading-relaxed font-medium">
                   Our smart router aggregates liquidity from 30+ DEXs and 15+ bridges to ensure minimal slippage and optimal gas efficiency for your cross-chain journey.
                 </p>
                 <div className="p-6 border border-white/10 flex items-start gap-4">
                    <ShieldCheck className="h-4 w-4 text-white/40 shrink-0 mt-1" />
                    <div className="space-y-1">
                       <p className="text-[10px] font-bold uppercase tracking-widest">Atomic Execution</p>
                       <p className="text-[10px] text-white/30 leading-tight">All swaps are executed via non-custodial smart contracts, ensuring user control throughout the process.</p>
                    </div>
                 </div>
              </div>
           </div>

           <Alert className="bg-white/5 border-white/10 text-white/40 rounded-none">
              <AlertDescription className="text-[10px] uppercase tracking-widest font-medium">
                 Average Settlement Time: 3-8 Minutes
              </AlertDescription>
           </Alert>
        </div>
      </div>
    </div>
  );
};

export default Swap;
