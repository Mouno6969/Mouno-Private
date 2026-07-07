import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import {
  RefreshCw,
  Settings,
  Info,
  ArrowDown,
  Zap,
  ShieldCheck,
  Loader2,
  Globe,
  Clock,
  CheckCircle,
  Check,
  AlertCircle,
  Wallet,
  ExternalLink,
} from 'lucide-react';
import { FlashValue } from '../components/common';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { NetworkLogo } from '../constants/networks';
import {
  chainEcosystem,
  chainLabel,
  chainLogoId,
  chainSelectLabel,
  featuredSwapChains,
  prepareSwapChains,
  type ChainEcosystem,
  type LifiChain,
} from '../constants/swapChains';
import {
  defaultFromToken,
  defaultToToken,
  popularTokensForChain,
} from '../constants/swapTokens';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import {
  connectEvmWallet,
  getConnectedEvmAddress,
  hasInjectedWallet,
  onAccountsChanged,
  sendEvmTransaction,
  switchEvmChain,
} from '../lib/evmWallet';

interface TokenMeta {
  address?: string;
  symbol?: string;
  name?: string;
  decimals?: number;
  logoURI?: string;
  priceUSD?: string;
}

interface SwapQuoteSummary {
  from_symbol?: string;
  to_symbol?: string;
  to_amount?: string;
  to_min?: string;
  gas_usd?: string;
  fee_usd?: string;
  tool?: string;
  duration?: number;
  executable?: boolean;
  pricing_only?: boolean;
  execution_note?: string;
  approval_needed?: boolean;
  approval_address?: string;
  tx_to?: string;
  tx_value?: string;
  tx_data?: string;
  chain_id?: number | string;
}

interface SwapQuote {
  summary?: SwapQuoteSummary;
  action?: {
    fromToken?: { address?: string };
    fromAmount?: string;
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

function normalizeTokenAddress(value: string): string {
  return value.trim();
}

const EVM_ADDRESS_RE = /^0x[0-9a-fA-F]{40}$/;
const BTC_ADDRESS_RE = /^(bc1[02-9ac-hj-np-z]{6,87}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$/;
const SVM_ADDRESS_RE = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;

function isValidAddressForEcosystem(address: string, ecosystem: ChainEcosystem): boolean {
  const value = address.trim();
  if (!value) return false;
  if (ecosystem === 'EVM') return EVM_ADDRESS_RE.test(value);
  if (ecosystem === 'UTXO') return BTC_ADDRESS_RE.test(value);
  if (ecosystem === 'SVM') {
    return SVM_ADDRESS_RE.test(value) && !value.startsWith('bc1') && !value.startsWith('tb1');
  }
  return false;
}

function slippageDecimal(slippagePercent: string): number {
  const parsed = parseFloat(slippagePercent);
  if (!Number.isFinite(parsed) || parsed <= 0) return 0.005;
  return parsed / 100;
}

function useTokenLookup(chainId: string, tokenAddress: string) {
  const [meta, setMeta] = useState<TokenMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const address = normalizeTokenAddress(tokenAddress);
    if (!chainId || !address) {
      setMeta(null);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiClient.get<TokenMeta>('/api/swap/token', {
          params: { chain: chainId, token: address },
          silent: true,
        });
        if (!cancelled) {
          setMeta(res.data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setMeta(null);
          setError(getErrorMessage(err, 'Token not found on this network'));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 450);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [chainId, tokenAddress]);

  return { meta, loading, error };
}

const TokenPicker: React.FC<{
  chainId: string;
  value: string;
  onChange: (value: string) => void;
  meta: TokenMeta | null;
  loading: boolean;
  error: string | null;
}> = ({ chainId, value, onChange, meta, loading, error }) => {
  const popular = useMemo(() => popularTokensForChain(chainId), [chainId]);
  const [customMode, setCustomMode] = useState(false);

  useEffect(() => {
    setCustomMode(false);
  }, [chainId]);

  const selectedPopular = popular.find((t) => t.address === value);

  return (
    <div className="space-y-2">
      {!customMode ? (
        <>
          <div className="flex flex-wrap gap-1.5">
            {popular.map((token) => (
              <Button
                key={`${chainId}-${token.address}`}
                type="button"
                variant={value === token.address ? 'default' : 'outline'}
                size="sm"
                className="h-8 px-3 text-xs font-bold"
                onClick={() => onChange(token.address)}
              >
                {token.symbol}
              </Button>
            ))}
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 px-0 text-[11px] font-bold text-primary hover:text-primary"
            onClick={() => setCustomMode(true)}
          >
            Search by contract / mint address
          </Button>
          {selectedPopular && (
            <p className="text-[11px] text-muted-foreground">{selectedPopular.name}</p>
          )}
        </>
      ) : (
        <div className="space-y-2">
          <Input
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="0x… EVM contract, Solana mint, or native / usdc / usdt"
            className="font-mono text-xs h-10 bg-background/60"
            spellCheck={false}
            autoComplete="off"
            autoFocus
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 px-0 text-[11px] text-muted-foreground"
            onClick={() => {
              setCustomMode(false);
              onChange(popular[0]?.address ?? 'native');
            }}
          >
            ← Back to popular tokens
          </Button>
        </div>
      )}
      <div className="min-h-[1.25rem] flex items-center gap-1.5 text-[11px]">
        {loading && (
          <>
            <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
            <span className="text-muted-foreground">Verifying token…</span>
          </>
        )}
        {!loading && customMode && meta?.symbol && (
          <>
            <Check className="h-3 w-3 text-success" />
            <span className="font-bold text-foreground">{meta.symbol}</span>
            {meta.name && <span className="text-muted-foreground truncate">· {meta.name}</span>}
          </>
        )}
        {!loading && customMode && error && value.trim() && (
          <>
            <AlertCircle className="h-3 w-3 text-destructive shrink-0" />
            <span className="text-destructive truncate">{error}</span>
          </>
        )}
      </div>
    </div>
  );
};

const Swap: React.FC = () => {
  const [chains, setChains] = useState<LifiChain[]>([]);
  const [chainsLoading, setChainsLoading] = useState(true);
  const [fromChain, setFromChain] = useState('1');
  const [toChain, setToChain] = useState('137');
  const [fromToken, setFromToken] = useState(defaultFromToken('1'));
  const [toToken, setToToken] = useState(defaultToToken('137'));
  const [amount, setAmount] = useState('');
  const [quote, setQuote] = useState<SwapQuote | null>(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [connectingWallet, setConnectingWallet] = useState(false);
  const [slippage] = useState('0.5');
  const [connectedAddress, setConnectedAddress] = useState<string | null>(null);
  const [fromAddress, setFromAddress] = useState('');
  const [toAddress, setToAddress] = useState('');

  const supportedChains = useMemo(() => prepareSwapChains(chains), [chains]);
  const popularChains = useMemo(() => featuredSwapChains(chains), [chains]);

  const fromLookup = useTokenLookup(fromChain, fromToken);
  const toLookup = useTokenLookup(toChain, toToken);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await apiClient.get<LifiChain[]>('/api/swap/chains', { silent: true });
        if (!cancelled && Array.isArray(res.data) && res.data.length > 0) {
          setChains(res.data);
        }
      } catch {
        if (!cancelled) {
          setChains([
            { id: '1', key: 'eth', name: 'Ethereum', coin: 'ETH' },
            { id: '56', key: 'bsc', name: 'BSC', coin: 'BNB' },
            { id: '137', key: 'pol', name: 'Polygon', coin: 'POL' },
            { id: '8453', key: 'bas', name: 'Base', coin: 'ETH' },
            { id: '43114', key: 'ava', name: 'Avalanche', coin: 'AVAX' },
            { id: '1151111081099710', key: 'sol', name: 'Solana', coin: 'SOL' },
          ]);
        }
      } finally {
        if (!cancelled) setChainsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const findChain = useCallback(
    (id: string) => chains.find((c) => String(c.id) === id),
    [chains],
  );

  const fromChainData = findChain(fromChain);
  const toChainData = findChain(toChain);
  const fromEco = chainEcosystem(fromChain);
  const toEco = chainEcosystem(toChain);
  const evmSource = fromEco === 'EVM';

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const existing = await getConnectedEvmAddress();
      if (!cancelled && existing) setConnectedAddress(existing);
    })();
    const unsubscribe = onAccountsChanged((accounts) => {
      const next = accounts[0] ?? null;
      setConnectedAddress(next);
      if (next && evmSource) {
        setFromAddress(next);
        if (toEco === 'EVM') setToAddress(next);
      } else if (!next && evmSource) {
        setFromAddress('');
      }
    });
    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, [evmSource, toEco]);

  useEffect(() => {
    if (evmSource && connectedAddress) {
      setFromAddress(connectedAddress);
      if (toEco === 'EVM' && !toAddress) {
        setToAddress(connectedAddress);
      }
    }
  }, [connectedAddress, evmSource, toEco, toAddress]);

  const handleFromChainChange = (chainId: string) => {
    setFromChain(chainId);
    setFromToken(defaultFromToken(chainId));
    setQuote(null);
  };

  const handleToChainChange = (chainId: string) => {
    setToChain(chainId);
    setToToken(defaultToToken(chainId));
    setQuote(null);
  };

  const usdValue = useMemo(() => {
    const price = fromLookup.meta?.priceUSD ? Number(fromLookup.meta.priceUSD) : null;
    if (!amount || !price || Number.isNaN(price)) return null;
    return (parseFloat(amount) * price).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }, [amount, fromLookup.meta?.priceUSD]);

  const [recentSwaps] = useState<RecentSwap[]>([
    { from_amount: '1.5', from_symbol: 'ETH', from_network: 'ethereum', to_amount: '4,089', to_symbol: 'USDC', to_network: 'polygon', time: '2 min ago' },
    { from_amount: '500', from_symbol: 'USDC', from_network: 'polygon', to_amount: '0.18', to_symbol: 'ETH', to_network: 'ethereum', time: '15 min ago' },
  ]);

  const protocols = [
    { name: 'Hop', color: 'text-purple-400' },
    { name: 'Stargate', color: 'text-blue-400' },
    { name: 'Across', color: 'text-green-400' },
    { name: 'Uniswap', color: 'text-pink-400' },
  ];

  const canQuote =
    Boolean(amount) &&
    Boolean(normalizeTokenAddress(fromToken)) &&
    Boolean(normalizeTokenAddress(toToken)) &&
    !loading;

  const quoteParams = (withAddresses = false) => {
    const params: Record<string, string> = {
      fromChain,
      toChain,
      fromToken: normalizeTokenAddress(fromToken),
      toToken: normalizeTokenAddress(toToken),
      amount,
      slippage: String(slippageDecimal(slippage)),
    };
    if (withAddresses) {
      const from = fromAddress.trim();
      const to = toAddress.trim();
      if (from) params.fromAddress = from;
      if (to) params.toAddress = to;
    }
    return params;
  };

  const fetchQuote = async (withAddresses = false, options?: { updateLoading?: boolean }) => {
    if (!canQuote) return null;
    const updateLoading = options?.updateLoading ?? true;
    if (updateLoading) setLoading(true);
    if (!withAddresses) setQuote(null);
    try {
      const res = await apiClient.get<SwapQuote>('/api/swap/quote', {
        params: quoteParams(withAddresses),
        silent: true,
      });
      setQuote(res.data);
      return res.data;
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to get quote'));
      return null;
    } finally {
      if (updateLoading) setLoading(false);
    }
  };

  const getQuote = (withAddresses = false) => fetchQuote(withAddresses);

  const connectWallet = async () => {
    if (!hasInjectedWallet()) {
      toast.error('Install MetaMask or another browser wallet to swap from EVM networks.');
      return;
    }
    setConnectingWallet(true);
    try {
      const address = await connectEvmWallet();
      setConnectedAddress(address);
      setFromAddress(address);
      if (toEco === 'EVM') setToAddress(address);
      toast.success('Wallet connected');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not connect wallet'));
    } finally {
      setConnectingWallet(false);
    }
  };

  const openJumperSwap = async () => {
    const res = await apiClient.get<{ url: string }>('/api/swap/widget-url', {
      params: { ...quoteParams(true), withQuote: '0' },
      silent: true,
    });
    window.open(res.data.url, '_blank', 'noopener,noreferrer');
  };

  const executeSwap = async () => {
    if (!canQuote || !quote) return;

    const from = fromAddress.trim();
    const to = toAddress.trim();

    if (!from || !isValidAddressForEcosystem(from, fromEco)) {
      toast.error(
        evmSource
          ? 'Connect your wallet or enter a valid source address.'
          : 'Enter a valid source wallet address for this network.',
      );
      return;
    }
    if (!to || !isValidAddressForEcosystem(to, toEco)) {
      toast.error('Enter a valid receiving address on the destination network.');
      return;
    }

    setExecuting(true);
    try {
      const executableQuote = await fetchQuote(true, { updateLoading: false });
      if (!executableQuote?.summary) {
        toast.error('Could not refresh an executable quote. Check your addresses and try again.');
        return;
      }

      const summary = executableQuote.summary;
      const canExecuteInWallet =
        summary.executable &&
        evmSource &&
        hasInjectedWallet() &&
        summary.tx_to &&
        summary.tx_data;

      if (!canExecuteInWallet) {
        await openJumperSwap();
        toast.message('Opening Jumper to complete your swap in your wallet.');
        return;
      }

      const chainId = summary.chain_id ?? fromChain;
      await switchEvmChain(chainId);

      if (summary.approval_needed) {
        const fromTokenAddr = executableQuote.action?.fromToken?.address;
        const fromAmount = executableQuote.action?.fromAmount;
        if (!fromTokenAddr || !fromAmount) {
          throw new Error('Missing approval details for this swap.');
        }
        toast.message(`Approve ${summary.from_symbol || 'token'} in your wallet…`);
        const approvalRes = await apiClient.get<{ to?: string; data?: string }>('/api/swap/approval', {
          params: { chain: fromChain, token: fromTokenAddr, amount: fromAmount },
          silent: true,
        });
        if (!approvalRes.data.to || !approvalRes.data.data) {
          throw new Error('Could not prepare token approval.');
        }
        await sendEvmTransaction({
          from,
          to: approvalRes.data.to,
          data: approvalRes.data.data,
          value: '0x0',
        });
        toast.message('Approval sent. Waiting for confirmation…');
        await new Promise((resolve) => window.setTimeout(resolve, 12000));
      }

      toast.message('Confirm the swap in your wallet…');
      const hash = await sendEvmTransaction({
        from,
        to: summary.tx_to!,
        data: summary.tx_data,
        value: summary.tx_value || '0x0',
      });
      toast.success(`Swap submitted: ${hash.slice(0, 10)}…${hash.slice(-6)}`);
    } catch (err) {
      const message = getErrorMessage(err, 'Swap failed');
      if (message.toLowerCase().includes('user rejected') || message.toLowerCase().includes('denied')) {
        toast.error('Transaction cancelled in wallet.');
      } else {
        toast.error(message);
      }
    } finally {
      setExecuting(false);
    }
  };

  const reverseDirection = () => {
    setFromChain(toChain);
    setToChain(fromChain);
    setFromToken(toToken);
    setToToken(fromToken);
    setQuote(null);
  };

  const renderChainSelect = (value: string, onChange: (v: string) => void) => {
    const selected = findChain(value);
    return (
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full h-10 rounded-xl bg-card border-muted font-bold text-sm">
          <SelectValue placeholder={chainsLoading ? 'Loading…' : 'Select network'}>
            {selected ? (
              <span className="flex items-center gap-2 truncate">
                <NetworkLogo id={chainLogoId(selected)} size={16} />
                <span className="truncate">{chainSelectLabel(selected)}</span>
              </span>
            ) : null}
          </SelectValue>
        </SelectTrigger>
        <SelectContent className="max-h-72">
          {supportedChains.map((chain) => (
            <SelectItem key={String(chain.id)} value={String(chain.id)}>
              <NetworkLogo id={chainLogoId(chain)} size={16} className="mr-2" />
              {chainSelectLabel(chain)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  };

  return (
    <div className="max-w-5xl mx-auto space-y-5 sm:space-y-8 px-1 sm:px-0 animate-in fade-in duration-500">
      <section className="space-y-1 text-center md:text-left">
        <div className="flex items-center justify-center md:justify-start gap-3">
          <div className="p-2.5 bg-primary/10 rounded-xl border border-primary/20">
            <RefreshCw className="h-7 w-7 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Cross-Chain Swap</h1>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Pick a network, choose a popular token or search by contract address — cross-chain routes via LI.FI.
            </p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 sm:gap-8 items-start">
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
              {/* From */}
              <div className="relative overflow-hidden rounded-2xl glass-panel p-5 transition-all focus-within:border-primary/40 focus-within:shadow-[0_0_30px_-10px_hsl(var(--primary)/0.35)]">
                <div className="absolute inset-0 dot-matrix-fine dot-matrix-fade opacity-40 pointer-events-none" aria-hidden="true" />
                <div className="relative space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold uppercase text-muted-foreground tracking-tighter">You Pay</span>
                    {fromChainData && (
                      <span className="text-[10px] text-muted-foreground font-mono">{chainLabel(fromChainData)}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <Input
                        type="number"
                        placeholder="0.0"
                        className="num border-none bg-transparent text-3xl font-black p-0 h-auto focus-visible:ring-0 placeholder:text-muted-foreground/30"
                        value={amount}
                        onChange={(e) => { setAmount(e.target.value); setQuote(null); }}
                      />
                      {usdValue && <p className="text-xs text-muted-foreground mt-1 font-mono">~${usdValue} USD</p>}
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold uppercase text-muted-foreground">Network</span>
                      {renderChainSelect(fromChain, handleFromChainChange)}
                    </div>
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold uppercase text-muted-foreground">Token</span>
                      <TokenPicker
                        chainId={fromChain}
                        value={fromToken}
                        onChange={(v) => { setFromToken(v); setQuote(null); }}
                        meta={fromLookup.meta}
                        loading={fromLookup.loading}
                        error={fromLookup.error}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-center -my-5 z-10 relative">
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="Reverse swap direction"
                  className="rounded-full h-10 w-10 border-muted bg-background shadow-lg hover:bg-primary/10 hover:text-primary hover:border-primary/50 transition-all group"
                  onClick={reverseDirection}
                >
                  <ArrowDown className="h-5 w-5 group-hover:scale-110 transition-transform" />
                </Button>
              </div>

              {/* To */}
              <div className="relative overflow-hidden rounded-2xl glass-panel p-5 transition-all">
                <div className="absolute inset-0 dot-matrix-primary dot-matrix-fade opacity-30 pointer-events-none" aria-hidden="true" />
                <div className="relative space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold uppercase text-muted-foreground tracking-tighter">You Receive (Estimated)</span>
                    {toChainData && (
                      <span className="text-[10px] text-muted-foreground font-mono">{chainLabel(toChainData)}</span>
                    )}
                  </div>
                  <FlashValue value={quote?.summary?.to_amount ? Number(quote.summary.to_amount) : undefined} as="div" className="w-full">
                    <div className="num text-3xl font-black text-primary drop-shadow-[0_0_16px_hsl(var(--primary)/0.3)]">
                      {quote?.summary?.to_amount ?? '0.0'}
                      {quote?.summary?.to_symbol && (
                        <span className="text-lg ml-2 text-muted-foreground">{quote.summary.to_symbol}</span>
                      )}
                    </div>
                  </FlashValue>
                  <div className="space-y-3">
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold uppercase text-muted-foreground">Network</span>
                      {renderChainSelect(toChain, handleToChainChange)}
                    </div>
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold uppercase text-muted-foreground">Token</span>
                      <TokenPicker
                        chainId={toChain}
                        value={toToken}
                        onChange={(v) => { setToToken(v); setQuote(null); }}
                        meta={toLookup.meta}
                        loading={toLookup.loading}
                        error={toLookup.error}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl border border-border/60 bg-muted/10 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-bold uppercase text-muted-foreground tracking-widest">
                    Wallet &amp; addresses
                  </span>
                  {evmSource && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-7 text-[10px] font-bold"
                      onClick={connectWallet}
                      disabled={connectingWallet}
                    >
                      {connectingWallet ? (
                        <Loader2 className="h-3 w-3 animate-spin mr-1" />
                      ) : (
                        <Wallet className="h-3 w-3 mr-1" />
                      )}
                      {connectedAddress ? 'Reconnect' : 'Connect wallet'}
                    </Button>
                  )}
                </div>
                {evmSource ? (
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold uppercase text-muted-foreground">Source (you pay from)</span>
                    <Input
                      value={fromAddress}
                      onChange={(e) => { setFromAddress(e.target.value); setQuote(null); }}
                      placeholder={connectedAddress ? connectedAddress : 'Connect wallet or paste 0x address'}
                      className="font-mono text-xs h-10 bg-background/60"
                      spellCheck={false}
                    />
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold uppercase text-muted-foreground">
                      Source address ({fromChainData?.name || 'source network'})
                    </span>
                    <Input
                      value={fromAddress}
                      onChange={(e) => { setFromAddress(e.target.value); setQuote(null); }}
                      placeholder={fromEco === 'SVM' ? 'Solana wallet address' : 'Bitcoin address'}
                      className="font-mono text-xs h-10 bg-background/60"
                      spellCheck={false}
                    />
                  </div>
                )}
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold uppercase text-muted-foreground">
                    Receiving address ({toChainData?.name || 'destination'})
                  </span>
                  <Input
                    value={toAddress}
                    onChange={(e) => { setToAddress(e.target.value); setQuote(null); }}
                    placeholder={
                      toEco === 'EVM'
                        ? '0x… destination wallet'
                        : toEco === 'SVM'
                          ? 'Solana wallet address'
                          : 'Bitcoin address'
                    }
                    className="font-mono text-xs h-10 bg-background/60"
                    spellCheck={false}
                  />
                </div>
                <p className="text-[10px] text-muted-foreground leading-relaxed">
                  Quotes work without addresses. To execute, both source and destination addresses must match their networks.
                </p>
              </div>

              {quote && (
                <div className="p-4 rounded-xl border border-dashed border-muted space-y-3 animate-in slide-in-from-top-2 duration-300">
                  <div className="flex justify-between text-[11px] font-bold uppercase text-muted-foreground tracking-widest">
                    <span>Best Route</span>
                    <Badge variant="outline" className="h-4 px-1.5 text-[8px] bg-primary/5 border-primary/20 text-primary">
                      {quote.summary?.tool || 'LI.FI'}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Pair</span>
                    <span className="font-mono font-bold text-right">
                      {quote.summary?.from_symbol || fromLookup.meta?.symbol || '?'} → {quote.summary?.to_symbol || toLookup.meta?.symbol || '?'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Gas Fees</span>
                    <span className="font-mono text-warning font-bold">${quote.summary?.gas_usd ?? '0'}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Route</span>
                    <div className="flex items-center gap-1.5">
                      <NetworkLogo id={fromChainData ? chainLogoId(fromChainData) : 'ethereum'} size={14} />
                      <span className="text-[10px] text-muted-foreground">→</span>
                      <NetworkLogo id={toChainData ? chainLogoId(toChainData) : 'ethereum'} size={14} />
                    </div>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Slippage</span>
                    <span className="font-mono font-bold">{slippage}%</span>
                  </div>
                  {quote.summary?.executable ? (
                    <div className="flex items-center gap-1.5 text-[11px] text-success border-t border-border/50 pt-2">
                      <CheckCircle className="h-3.5 w-3.5 shrink-0" />
                      <span>Executable — ready to sign with your wallet</span>
                    </div>
                  ) : quote.summary?.pricing_only && quote.summary.execution_note ? (
                    <p className="text-[11px] text-muted-foreground border-t border-border/50 pt-2">
                      {quote.summary.execution_note}
                    </p>
                  ) : null}
                </div>
              )}
            </CardContent>
            <CardFooter className="pt-2">
              <Button
                onClick={() => getQuote(Boolean(fromAddress.trim() && toAddress.trim()))}
                disabled={!canQuote || loading}
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
                <Button
                  onClick={() => {
                    if (evmSource && !fromAddress.trim()) {
                      void connectWallet();
                      return;
                    }
                    void executeSwap();
                  }}
                  disabled={executing || loading}
                  className="w-full h-14 rounded-2xl bg-success text-success-foreground hover:bg-success/90 font-black text-lg transition-all group"
                >
                  {executing ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Processing…
                    </>
                  ) : evmSource && !fromAddress.trim() ? (
                    <>
                      <Wallet className="mr-2 h-5 w-5" />
                      Connect Wallet to Swap
                    </>
                  ) : quote.summary?.executable && evmSource ? (
                    <>
                      Execute Swap
                      <RefreshCw className="ml-2 h-5 w-5 group-hover:rotate-180 transition-transform duration-500" />
                    </>
                  ) : (
                    <>
                      Continue on Jumper
                      <ExternalLink className="ml-2 h-5 w-5" />
                    </>
                  )}
                </Button>
                <p className="text-center text-[10px] uppercase font-bold text-muted-foreground tracking-widest">
                  Powered by Li.Fi · {quote.summary?.executable ? 'Sign in wallet' : 'Opens jumper.exchange'}
                </p>
              </div>
            )}
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-5">
          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" /> How it works
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-muted-foreground leading-relaxed">
              <p>1. Select source and destination <strong className="text-foreground font-semibold">networks</strong> ({supportedChains.length} supported).</p>
              <p>2. Tap a <strong className="text-foreground font-semibold">popular token</strong> or use &quot;Search by contract / mint address&quot; for any other token.</p>
              <p>3. Enter amount and get a live cross-chain quote.</p>
              <div className="p-3 rounded-xl bg-muted/30 border border-muted flex items-start gap-3">
                <ShieldCheck className="h-5 w-5 text-success shrink-0" />
                <div>
                  <p className="text-xs font-bold mb-0.5 text-foreground">Any token, any chain</p>
                  <p className="text-[10px] leading-tight">Routes aggregate bridges and DEXs automatically. Unsupported or illiquid pairs will show a clear error.</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-primary/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Globe className="h-4 w-4 text-primary" /> Popular Networks
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-2 sm:gap-3">
                {popularChains.map((chain) => (
                  <div key={String(chain.id)} className="flex flex-col items-center gap-1.5 p-2.5 rounded-xl bg-muted/20 border border-border/40 hover:border-primary/30 transition-colors">
                    <NetworkLogo id={chainLogoId(chain)} size={24} />
                    <span className="text-[10px] font-medium text-muted-foreground text-center leading-tight">{chain.name}</span>
                  </div>
                ))}
              </div>

            </CardContent>
          </Card>

          <Alert className="bg-info/5 border-info/10">
            <Info className="h-4 w-4 text-info" />
            <AlertDescription className="text-xs text-muted-foreground">
              EVM tokens use 0x contract addresses. Solana uses base58 mint addresses. Bitcoin native swaps use <code>native</code> or <code>bitcoin</code>.
            </AlertDescription>
          </Alert>

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