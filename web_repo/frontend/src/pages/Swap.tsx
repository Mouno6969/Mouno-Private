import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { RefreshCw, ArrowRight, Settings, Info, ArrowDown, ChevronDown, Zap, ShieldCheck } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';

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
    { id: '1', name: 'Ethereum', symbol: 'ETH', icon: '🔹' },
    { id: '56', name: 'BSC', symbol: 'BNB', icon: '🟡' },
    { id: '137', name: 'Polygon', symbol: 'POL', icon: '🟣' },
    { id: '8453', name: 'Base', symbol: 'ETH', icon: '🔵' },
    { id: '43114', name: 'Avalanche', symbol: 'AVAX', icon: '🔺' },
    { id: '1151111081099710', name: 'Solana', symbol: 'SOL', icon: '🪐' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <section className="space-y-1 text-center md:text-left">
        <div className="flex items-center justify-center md:justify-start gap-3">
           <div className="p-2 bg-primary/10 rounded-lg">
              <RefreshCw className="h-6 w-6 text-primary" />
           </div>
           <h1 className="text-3xl font-extrabold tracking-tight">Cross-Chain Bridge</h1>
        </div>
        <p className="text-muted-foreground">Transfer assets between 20+ networks with deep liquidity.</p>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
        <div className="lg:col-span-3">
          <Card className="shadow-2xl border-primary/10 relative overflow-hidden">
             <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/50 via-primary to-primary/50"></div>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-7">
              <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Swap Interface</CardTitle>
              <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                <Settings className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* From Block */}
              <div className="rounded-2xl bg-muted/40 p-5 border border-muted transition-all focus-within:border-primary/30">
                <div className="flex justify-between items-center mb-2">
                   <span className="text-xs font-bold uppercase text-muted-foreground tracking-tighter">You Pay</span>
                   <Badge variant="outline" className="text-[10px] font-mono">Bal: 0.00</Badge>
                </div>
                <div className="flex items-center gap-4">
                  <Input
                    type="number"
                    placeholder="0.0"
                    className="border-none bg-transparent text-3xl font-black p-0 h-auto focus-visible:ring-0 placeholder:text-muted-foreground/30"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                  />
                  <Select value={fromChain} onValueChange={setFromChain}>
                    <SelectTrigger className="w-[140px] h-12 rounded-xl bg-card border-muted font-bold">
                       <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {chains.map(chain => (
                        <SelectItem key={chain.id} value={chain.id}>
                          <span className="mr-2">{chain.icon}</span> {chain.symbol}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Reverse Icon */}
              <div className="flex justify-center -my-7 z-10 relative">
                <Button
                  variant="outline"
                  size="icon"
                  className="rounded-full h-10 w-10 border-muted bg-background shadow-lg hover:bg-primary/10 hover:text-primary hover:border-primary/50 transition-all group"
                  onClick={() => {
                    const temp = fromChain;
                    setFromChain(toChain);
                    setToChain(temp);
                  }}
                >
                  <ArrowDown className="h-5 w-5 group-hover:scale-110 transition-transform" />
                </Button>
              </div>

              {/* To Block */}
              <div className="rounded-2xl bg-muted/40 p-5 border border-muted transition-all">
                <div className="flex justify-between items-center mb-2">
                   <span className="text-xs font-bold uppercase text-muted-foreground tracking-tighter">You Receive (Estimated)</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-3xl font-black w-full text-primary/60 font-mono">
                    {quote ? quote.summary?.to_amount : '0.0'}
                  </div>
                  <Select value={toChain} onValueChange={setToChain}>
                    <SelectTrigger className="w-[140px] h-12 rounded-xl bg-card border-muted font-bold">
                       <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                       {chains.map(chain => (
                        <SelectItem key={chain.id} value={chain.id}>
                          <span className="mr-2">{chain.icon}</span> {chain.symbol}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {quote && (
                <div className="p-4 rounded-xl border border-dashed border-muted space-y-2 animate-in slide-in-from-top-2 duration-300">
                   <div className="flex justify-between text-[11px] font-bold uppercase text-muted-foreground tracking-widest">
                     <span>Best Price Across</span>
                     <Badge variant="outline" className="h-4 px-1 text-[8px] bg-primary/5 border-primary/20 text-primary">LI.FI PROTOCOL</Badge>
                   </div>
                   <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Exchange Rate</span>
                      <span className="font-mono font-bold">1 {chains.find(c => c.id === fromChain)?.symbol} ≈ <span>{quote.summary?.to_amount} {quote.summary?.to_symbol}</span></span>
                   </div>
                   <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Gas Fees</span>
                      <span className="font-mono text-amber-500 font-bold">${quote.summary?.gas_usd}</span>
                   </div>
                </div>
              )}
            </CardContent>
            <CardFooter className="pt-2">
              <Button
                onClick={getQuote}
                disabled={loading || !amount}
                className="w-full h-14 text-lg font-black rounded-2xl shadow-xl shadow-primary/20"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Calculating Best Route...
                  </>
                ) : (
                  <>Get Quote</>
                )}
              </Button>
            </CardFooter>

            {quote && (
               <div className="p-6 pt-0 space-y-4">
                  <Button className="w-full h-14 rounded-2xl bg-white text-black hover:bg-white/90 font-black text-lg transition-all group">
                    Execute Swap In-Bot <RefreshCw className="ml-2 h-5 w-5 group-hover:rotate-180 transition-transform duration-500" />
                  </Button>
                  <p className="text-center text-[10px] uppercase font-bold text-muted-foreground tracking-widest">Powered by Li.Fi Aggregator</p>
               </div>
            )}
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-6">
           <Card className="border-primary/10">
              <CardHeader>
                 <CardTitle className="text-sm font-bold flex items-center gap-2">
                    <Zap className="h-4 w-4 text-primary" /> Routing Info
                 </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                 <p className="text-xs text-muted-foreground leading-relaxed">
                   We aggregate liquidity from multiple bridges (Hop, Stargate, Across) and DEXs (Uniswap, PancakeSwap) to ensure you get the maximum output for your cross-chain transfer.
                 </p>
                 <div className="p-4 rounded-xl bg-muted/30 border border-muted flex items-start gap-3">
                    <ShieldCheck className="h-5 w-5 text-green-500 shrink-0" />
                    <div>
                       <p className="text-xs font-bold mb-1 uppercase tracking-tighter">Secure & Audited</p>
                       <p className="text-[10px] text-muted-foreground opacity-80 leading-tight">All bridge routes used are fully audited and battle-tested on-chain protocols.</p>
                    </div>
                 </div>
              </CardContent>
           </Card>

           <Alert className="bg-blue-500/5 border-blue-500/10">
              <Info className="h-4 w-4 text-blue-400" />
              <AlertDescription className="text-xs text-muted-foreground">
                 Cross-chain swaps can take anywhere from 2 to 20 minutes depending on the network congestion and destination chain.
              </AlertDescription>
           </Alert>
        </div>
      </div>
    </div>
  );
};

const Loader2 = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
);

export default Swap;
