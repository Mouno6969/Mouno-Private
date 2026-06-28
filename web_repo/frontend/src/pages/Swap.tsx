import React, { useState } from 'react';
import { toast } from 'sonner';
import { RefreshCw, Settings, Info, ArrowDown, Zap, ShieldCheck, Loader2, Globe, Clock, CheckCircle } from 'lucide-react';
import { FlashValue } from '../components/common';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { NetworkLogo } from '../constants/networks';
import { apiClient, getErrorMessage } from '../lib/apiClient';

interface SwapQuote {
  summary?: {
    to_amount?: string;
    to_symbol?: string;
    gas_usd?: string;
    route?: string;
  };
}

interface RecentSwap {
  from_amount: string;
  from_symbol: string;
  from_network: string;
  to_amount: string;
  to_symbol: string;
  to_network: string;
  time: string;
}

const Swap: React.FC = () => {
  const [fromChain, setFromChain] = useState('1'); // Ethereum
  const [toChain, setToChain] = useState('137'); // Polygon
  const [fromToken] = useState('0x0000000000000000000000000000000000000000'); // ETH
  const [toToken] = useState('0x2791bca1f2de4661ed88a30c99a7a9449aa84174'); // USDC
  const [amount, setAmount] = useState('');
  const [quote, setQuote] = useState<SwapQuote | null>(null);
  const [loading, setLoading] = useState(false);
  const [slippage] = useState('0.5');

  // Mock recent swaps for display
  const [recentSwaps] = useState<RecentSwap[]>([
    { from_amount: '1.5', from_symbol: 'ETH', from_network: 'ethereum', to_amount: '4,089', to_symbol: 'USDC', to_network: 'polygon', time: '2 min ago' },
    { from_amount: '500', from_symbol: 'USDC', from_network: 'polygon', to_amount: '0.18', to_symbol: 'ETH', to_network: 'ethereum', time: '15 min ago' },
  ]);

  const getQuote = async () => {
    if (!amount) return;
    setLoading(true);
    try {
      const res = await apiClient.get<SwapQuote>('/api/swap/quote', {
        params: { fromChain, toChain, fromToken, toToken, amount },
        silent: true,
      });
      setQuote(res.data);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to get quote'));
    } finally {
      setLoading(false);
    }
  };

  const chains = [
    { id: '1', name: 'Ethereum', symbol: 'ETH', networkId: 'ethereum', price: 2750 },
    { id: '56', name: 'BSC', symbol: 'BNB', networkId: 'bsc', price: 580 },
    { id: '137', name: 'Polygon', symbol: 'POL', networkId: 'polygon', price: 1 },
    { id: '8453', name: 'Base', symbol: 'ETH', networkId: 'base', price: 2750 },
    { id: '43114', name: 'Avalanche', symbol: 'AVAX', networkId: 'avalanche', price: 35 },
    { id: '1151111081099710', name: 'Solana', symbol: 'SOL', networkId: 'solana', price: 145 },
  ];

  const fromChainData = chains.find(c => c.id === fromChain);
  const toChainData = chains.find(c => c.id === toChain);
  const usdValue = amount ? (parseFloat(amount) * (fromChainData?.price || 0)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00';

  // Protocol logos data
  const protocols = [
    { name: 'Hop', color: 'text-purple-400' },
    { name: 'Stargate', color: 'text-blue-400' },
    { name: 'Across', color: 'text-green-400' },
    { name: 'Uniswap', color: 'text-pink-400' },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-5 sm:space-y-8 px-1 sm:px-0 animate-in fade-in duration-500">
      {/* Page Header */}
      <section className="space-y-1 text-center md:text-left">
        <div className="flex items-center justify-center md:justify-start gap-3">
          <div className="p-2.5 bg-primary/10 rounded-xl border border-primary/20">
            <RefreshCw className="h-7 w-7 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Cross-Chain Bridge</h1>
            <p className="text-xs sm:text-sm text-muted-foreground">Transfer assets between 20+ networks with deep liquidity. Best rates aggregated from multiple protocols.</p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 sm:gap-8 items-start">
        {/* Main Swap Card */}
        <div className="lg:col-span-3">
          <Card className="shadow-2xl border-primary/10 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/50 via-primary to-primary/50" />
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-7">
              <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Swap Interface</CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[9px] px-2 py-0.5 border-primary/20 text-primary">
                  Slippage: {slippage}%
                </Badge>
                <Button variant="ghost" size="icon" aria-label="Swap settings" className="h-8 w-8 text-muted-foreground hover:text-primary">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* From Block */}
              <div className="relative overflow-hidden rounded-2xl glass-panel p-5 transition-all focus-within:border-primary/40 focus-within:shadow-[0_0_30px_-10px_hsl(var(--primary)/0.35)]">
                <div className="absolute inset-0 dot-matrix-fine dot-matrix-fade opacity-40 pointer-events-none" aria-hidden="true" />
                <div className="relative flex justify-between items-center mb-2">
                  <span className="text-xs font-bold uppercase text-muted-foreground tracking-tighter">You Pay</span>
                </div>
                <div className="relative flex items-center gap-4">
                  <div className="flex-1">
                    <Input
                      type="number"
                      placeholder="0.0"
                      className="num border-none bg-transparent text-3xl font-black p-0 h-auto focus-visible:ring-0 placeholder:text-muted-foreground/30"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                    />
                    {amount && (
                      <p className="text-xs text-muted-foreground mt-1 font-mono">~${usdValue} USD</p>
                    )}
                  </div>
                  <Select value={fromChain} onValueChange={setFromChain}>
                    <SelectTrigger className="w-[110px] sm:w-[140px] h-10 sm:h-12 rounded-xl bg-card border-muted font-bold text-sm shrink-0">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {chains.map(chain => (
                        <SelectItem key={chain.id} value={chain.id}>
                          <NetworkLogo id={chain.networkId} size={16} className="mr-2" /> {chain.symbol}
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
                  aria-label="Reverse swap direction"
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
              <div className="relative overflow-hidden rounded-2xl glass-panel p-5 transition-all">
                <div className="absolute inset-0 dot-matrix-primary dot-matrix-fade opacity-30 pointer-events-none" aria-hidden="true" />
                <div className="relative flex justify-between items-center mb-2">
                  <span className="text-xs font-bold uppercase text-muted-foreground tracking-tighter">You Receive (Estimated)</span>
                </div>
                <div className="relative flex items-center gap-4">
                  <div className="flex-1">
                    <FlashValue value={quote?.summary?.to_amount ? Number(quote.summary.to_amount) : undefined} as="div" className="w-full">
                      <div className="num text-3xl font-black text-primary drop-shadow-[0_0_16px_hsl(var(--primary)/0.3)]">
                        {quote ? quote.summary?.to_amount : '0.0'}
                      </div>
                    </FlashValue>
                    {quote?.summary?.to_amount && (
                      <p className="text-xs text-muted-foreground mt-1 font-mono">~${quote.summary.to_amount} USD</p>
                    )}
                  </div>
                  <Select value={toChain} onValueChange={setToChain}>
                    <SelectTrigger className="w-[110px] sm:w-[140px] h-10 sm:h-12 rounded-xl bg-card border-muted font-bold text-sm shrink-0">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {chains.map(chain => (
                        <SelectItem key={chain.id} value={chain.id}>
                          <NetworkLogo id={chain.networkId} size={16} className="mr-2" /> {chain.symbol}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Quote Details */}
              {quote && (
                <div className="p-4 rounded-xl border border-dashed border-muted space-y-3 animate-in slide-in-from-top-2 duration-300">
                  <div className="flex justify-between text-[11px] font-bold uppercase text-muted-foreground tracking-widest">
                    <span>Best Price Across</span>
                    <Badge variant="outline" className="h-4 px-1.5 text-[8px] bg-primary/5 border-primary/20 text-primary">LI.FI PROTOCOL</Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Exchange Rate</span>
                    <span className="font-mono font-bold">1 {fromChainData?.symbol} ≈ {quote.summary?.to_amount} {quote.summary?.to_symbol}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Gas Fees</span>
                    <span className="font-mono text-warning font-bold">${quote.summary?.gas_usd}</span>
                  </div>
                  {/* Route Visualization */}
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Route</span>
                    <div className="flex items-center gap-1.5">
                      <NetworkLogo id={fromChainData?.networkId || ''} size={14} />
                      <span className="text-[10px] text-muted-foreground">→</span>
                      <span className="text-[10px] font-medium text-primary">Stargate</span>
                      <span className="text-[10px] text-muted-foreground">→</span>
                      <NetworkLogo id={toChainData?.networkId || ''} size={14} />
                    </div>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Slippage</span>
                    <span className="font-mono font-bold">{slippage}%</span>
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
                <Button className="w-full h-14 rounded-2xl bg-success text-success-foreground hover:bg-success/90 font-black text-lg transition-all group">
                  Execute Swap In-Bot <RefreshCw className="ml-2 h-5 w-5 group-hover:rotate-180 transition-transform duration-500" />
                </Button>
                <p className="text-center text-[10px] uppercase font-bold text-muted-foreground tracking-widest">Powered by Li.Fi Aggregator</p>
              </div>
            )}
          </Card>
        </div>

        {/* Right Sidebar */}
        <div className="lg:col-span-2 space-y-5">
          {/* Routing Info */}
          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" /> Routing Info
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-muted-foreground leading-relaxed">
                We aggregate liquidity from multiple bridges and DEXs to ensure you get the maximum output for your cross-chain transfer.
              </p>
              <div className="p-3 rounded-xl bg-muted/30 border border-muted flex items-start gap-3">
                <ShieldCheck className="h-5 w-5 text-success shrink-0" />
                <div>
                  <p className="text-xs font-bold mb-0.5">Secure & Audited</p>
                  <p className="text-[10px] text-muted-foreground leading-tight">All integrated protocols are audited and battle-tested.</p>
                </div>
              </div>
              {/* Protocol Logos */}
              <div className="grid grid-cols-4 gap-2">
                {protocols.map((proto) => (
                  <div key={proto.name} className="flex flex-col items-center gap-1 p-2 rounded-lg bg-muted/20 border border-border/40">
                    <div className={`w-6 h-6 rounded-full bg-muted/50 flex items-center justify-center text-[8px] font-bold ${proto.color}`}>
                      {proto.name.charAt(0)}
                    </div>
                    <span className="text-[9px] text-muted-foreground font-medium">{proto.name}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Supported Chains */}
          <Card className="border-primary/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Globe className="h-4 w-4 text-primary" /> Supported Chains
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-2 sm:gap-3">
                {chains.map((chain) => (
                  <div key={chain.id} className="flex flex-col items-center gap-1.5 p-2.5 rounded-xl bg-muted/20 border border-border/40 hover:border-primary/30 transition-colors">
                    <NetworkLogo id={chain.networkId} size={24} />
                    <span className="text-[10px] font-medium text-muted-foreground">{chain.name}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Info Alert */}
          <Alert className="bg-info/5 border-info/10">
            <Info className="h-4 w-4 text-info" />
            <AlertDescription className="text-xs text-muted-foreground">
              Cross-chain swaps can take anywhere from 2 to 20 minutes depending on the network congestion and destination chain.
            </AlertDescription>
          </Alert>

          {/* Recent Swaps */}
          <Card className="border-primary/10">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <Clock className="h-4 w-4 text-primary" /> Recent Swaps
                </CardTitle>
                <span className="text-[10px] text-primary font-medium cursor-pointer hover:underline">View All</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-2.5">
              {recentSwaps.map((swap, i) => (
                <div key={i} className="flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 rounded-lg bg-muted/20 border border-border/40">
                  <div className="flex items-center gap-1 sm:gap-1.5 flex-1 min-w-0 overflow-hidden">
                    <NetworkLogo id={swap.from_network} size={14} />
                    <span className="text-[10px] sm:text-xs font-bold truncate">{swap.from_amount} {swap.from_symbol}</span>
                    <span className="text-muted-foreground text-[9px] sm:text-[10px] shrink-0">→</span>
                    <NetworkLogo id={swap.to_network} size={14} />
                    <span className="text-[10px] sm:text-xs font-bold truncate">{swap.to_amount} {swap.to_symbol}</span>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <span className="text-[8px] sm:text-[9px] text-muted-foreground">{swap.time}</span>
                    <CheckCircle className="h-3 w-3 sm:h-3.5 sm:w-3.5 text-success" />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Swap;
