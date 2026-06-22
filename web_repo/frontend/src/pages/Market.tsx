import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { io, Socket } from 'socket.io-client';
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
  RefreshCw,
  Search,
  ArrowDownUp,
  BadgeCheck,
  X,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Freshness, PageHeader, CopyButton } from '../components/common';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { NETWORK_MAP, NetworkLogo } from '../constants/networks';
import { Skeleton } from '../components/ui/skeleton';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { API_BASE } from '../lib/api';
import { apiClient, getErrorMessage } from '../lib/apiClient';

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
  trades?: number;
}

type P2PSide = 'buy' | 'sell';
type SortKey = 'rate' | 'trades' | 'name';

const Market: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const [sellers, setSellers] = useState<MarketSeller[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedSeller, setSelectedSeller] = useState<MarketSeller | null>(null);

  // P2P controls
  const [side, setSide] = useState<P2PSide>('buy');
  const [sortKey, setSortKey] = useState<SortKey>('rate');
  const [search, setSearch] = useState('');
  const [networkFilter, setNetworkFilter] = useState('');
  const [contactSeller, setContactSeller] = useState<MarketSeller | null>(null);

  // Order form state
  const [network, setNetwork] = useState('');
  const [wallet, setWallet] = useState('');
  const [bdtAmount, setBdtAmount] = useState('');
  const [trxId, setTrxId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<{ order_id: string; amount_crypto: string } | null>(null);

  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [refreshing, setRefreshing] = useState(false);
  
  // Ref to keep selectedSeller up-to-date for the WebSocket handler
  const selectedSellerRef = useRef<MarketSeller | null>(null);
  useEffect(() => {
    selectedSellerRef.current = selectedSeller;
  }, [selectedSeller]);

  // Ref to keep network up-to-date for the WebSocket handler
  const networkRef = useRef<string>('');
  useEffect(() => {
    networkRef.current = network;
  }, [network]);

  const fetchSellers = async () => {
    try {
      const res = await apiClient.get<MarketSeller[]>('/api/sellers', { silent: true });
      setSellers(Array.isArray(res.data) ? res.data : []);
      setLoadError(null);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to fetch sellers:', err);
      setLoadError(getErrorMessage(err, 'Failed to connect to the server.'));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial load + WebSocket real-time updates
  useEffect(() => {
    fetchSellers();
    
    // Connect to WebSocket for real-time seller updates
    const socket: Socket = io(API_BASE, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    socket.on('connect', () => {
      console.log('[v0] WebSocket connected to marketplace');
    });

    socket.on('sellers_updated', (data: { sellers: MarketSeller[] }) => {
      const newSellers = Array.isArray(data.sellers) ? data.sellers : [];
      setSellers(newSellers);
      setLastRefresh(new Date());
      
      // Keep selectedSeller and network in sync using ref to avoid stale closure
      const current = selectedSellerRef.current;
      if (current) {
        const updatedSeller = newSellers.find(s => s.seller_id === current.seller_id);
        if (updatedSeller) {
          setSelectedSeller(updatedSeller);
          // Check if current network is still available in updated seller's networks
          const networkStillExists = updatedSeller.networks.some(n => n.network === networkRef.current);
          if (!networkStillExists) {
            // Reset network to first available or empty
            setNetwork(updatedSeller.networks[0]?.network || '');
          }
        } else {
          // Seller no longer available, clear selection and network
          setSelectedSeller(null);
          setNetwork('');
        }
      }
      
      console.log('[v0] Sellers updated via WebSocket:', newSellers.length);
    });

    socket.on('disconnect', () => {
      console.log('[v0] WebSocket disconnected');
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const handleManualRefresh = async () => {
    setRefreshing(true);
    await fetchSellers();
  };

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
      const res = await apiClient.post<{ order_id: string; amount_crypto: string }>(
        '/api/seller/order',
        {
          seller_id: selectedSeller.seller_id,
          network,
          wallet,
          amount_bdt: bdtAmount,
          trx_id: trxId,
        },
        { silent: true }
      );
      setSuccess(res.data);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to place order'));
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20 animate-in zoom-in duration-300">
        <div className="w-24 h-24 bg-success/15 text-success rounded-full flex items-center justify-center mx-auto mb-8">
          <CheckCircle className="h-12 w-12" />
        </div>
        <h2 className="text-4xl font-extrabold mb-4 tracking-tight">Seller Order Placed!</h2>
        <Card className="mb-8 border-success/30 bg-success/5">
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
          Back to P2P
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

                  <Alert className="bg-warning/5 border-warning/20 text-warning">
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
                          aria-label="Copy bKash number"
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

  // ── P2P listing ──
  // Networks present across all sellers — powers the network filter dropdown.
  const allNetworks = Array.from(
    new Set(sellers.flatMap((s) => s.networks.map((n) => n.network)))
  ).sort((a, b) => (NETWORK_MAP[a]?.name || a).localeCompare(NETWORK_MAP[b]?.name || b));

  // A seller's representative rate for the active side. For Buy, the cheapest
  // rate wins (you pay fewer BDT); for Sell, the highest rate wins (you receive
  // more BDT). When a network filter is set, use that network's rate only.
  const repRate = (s: MarketSeller): number | null => {
    const nets = networkFilter ? s.networks.filter((n) => n.network === networkFilter) : s.networks;
    if (nets.length === 0) return null;
    const rates = nets.map((n) => n.rate);
    return side === 'buy' ? Math.min(...rates) : Math.max(...rates);
  };

  const visibleSellers = sellers
    .filter((s) => (networkFilter ? s.networks.some((n) => n.network === networkFilter) : true))
    .filter((s) =>
      search.trim() ? s.display_name?.toLowerCase().includes(search.trim().toLowerCase()) : true
    )
    .sort((a, b) => {
      if (sortKey === 'name') return (a.display_name || '').localeCompare(b.display_name || '');
      if (sortKey === 'trades') return (b.trades ?? 0) - (a.trades ?? 0);
      // sortKey === 'rate' — best rate first (asc for buy, desc for sell)
      const ra = repRate(a);
      const rb = repRate(b);
      if (ra === null) return 1;
      if (rb === null) return -1;
      return side === 'buy' ? ra - rb : rb - ra;
    });

  const sortLabels: Record<SortKey, string> = {
    rate: 'Best rate',
    trades: 'Most trades',
    name: 'Name (A–Z)',
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500">
      <PageHeader
        icon={<Store className="h-6 w-6" />}
        eyebrow="Peer to Peer"
        title={t('market')}
        description={
          side === 'buy'
            ? 'Buy crypto directly from verified sellers. Each seller sets their own rates and supported networks.'
            : 'Sell your crypto to verified merchants. Pick a merchant, then contact them to arrange the payout.'
        }
        actions={
          <div className="flex items-center gap-3">
            <Freshness updatedAt={refreshing ? undefined : lastRefresh} label="Sellers" />
            <Button variant="outline" size="sm" onClick={handleManualRefresh} disabled={refreshing} aria-label="Refresh sellers">
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} /> Refresh
            </Button>
          </div>
        }
      />

      {/* Buy / Sell side toggle */}
      <div className="inline-flex rounded-lg border border-primary/20 bg-card p-1" role="tablist" aria-label="Buy or sell">
        {(['buy', 'sell'] as P2PSide[]).map((s) => (
          <button
            key={s}
            role="tab"
            aria-selected={side === s}
            onClick={() => setSide(s)}
            className={`px-6 py-2 rounded-md text-sm font-bold capitalize transition-colors ${
              side === s
                ? s === 'buy'
                  ? 'bg-success/15 text-success'
                  : 'bg-destructive/15 text-destructive'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Filters & sorting */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="relative flex-1 min-w-0">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search merchant name…"
            className="pl-9"
            aria-label="Search merchant name"
          />
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <NetworkLogo id={networkFilter} size={16} />
            <select
              value={networkFilter}
              onChange={(e) => setNetworkFilter(e.target.value)}
              aria-label="Filter by network"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm font-medium"
            >
              <option value="">All networks</option>
              {allNetworks.map((net) => (
                <option key={net} value={net}>
                  {NETWORK_MAP[net]?.name || net}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <ArrowDownUp className="h-4 w-4 text-muted-foreground" />
            <select
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value as SortKey)}
              aria-label="Sort sellers"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm font-medium"
            >
              {(Object.keys(sortLabels) as SortKey[]).map((k) => (
                <option key={k} value={k}>
                  {sortLabels[k]}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" aria-busy="true" aria-label="Loading sellers">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Card key={i} className="border-primary/10 flex flex-col">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div className="min-w-0 flex-1 space-y-2">
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 space-y-3">
                <Skeleton className="h-2.5 w-24" />
                <div className="flex flex-wrap gap-2">
                  <Skeleton className="h-7 w-28 rounded-full" />
                  <Skeleton className="h-7 w-24 rounded-full" />
                </div>
              </CardContent>
              <CardFooter>
                <Skeleton className="h-10 w-full rounded-md" />
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : loadError ? (
        <Card className="border-destructive/30">
          <CardContent className="py-16 text-center space-y-4">
            <Info className="h-10 w-10 text-destructive mx-auto" />
            <p className="font-bold">Could not load P2P</p>
            <p className="text-sm text-muted-foreground max-w-md mx-auto text-pretty">{loadError}</p>
            <Button variant="outline" onClick={handleManualRefresh} disabled={refreshing}>
              {refreshing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Try again
            </Button>
          </CardContent>
        </Card>
      ) : sellers.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center space-y-3">
            <Store className="h-10 w-10 text-muted-foreground mx-auto" />
            <p className="font-bold">No active merchants right now</p>
            <p className="text-sm text-muted-foreground">
              Check back later, or buy directly from the platform on the{' '}
              <Link to="/buy" className="text-primary underline">Buy</Link> page.
            </p>
          </CardContent>
        </Card>
      ) : visibleSellers.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center space-y-3">
            <Search className="h-10 w-10 text-muted-foreground mx-auto" />
            <p className="font-bold">No merchants match your filters</p>
            <p className="text-sm text-muted-foreground">Try a different network or clear the search.</p>
            <Button
              variant="outline"
              onClick={() => {
                setSearch('');
                setNetworkFilter('');
              }}
            >
              Clear filters
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {visibleSellers.map((seller) => {
            const shownNetworks = networkFilter
              ? seller.networks.filter((n) => n.network === networkFilter)
              : seller.networks;
            return (
              <Card key={seller.seller_id} className="border-primary/10 hover:border-primary/40 transition-colors flex flex-col">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center font-black text-primary font-mono">
                      {seller.display_name?.[0]?.toUpperCase() || 'S'}
                    </div>
                    <div className="min-w-0 flex-1">
                      <CardTitle className="text-base truncate flex items-center gap-1.5">
                        {seller.display_name}
                        <BadgeCheck className="h-4 w-4 text-primary shrink-0" aria-label="Verified merchant" />
                      </CardTitle>
                      <CardDescription className="text-xs font-mono truncate">{seller.support_contact}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 space-y-3">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <BadgeCheck className="h-3.5 w-3.5 text-success" />
                    <span className="font-semibold text-foreground">{seller.trades ?? 0}</span> completed trade{(seller.trades ?? 0) === 1 ? '' : 's'}
                  </div>
                  <p className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground">Networks &amp; Rates</p>
                  <div className="flex flex-wrap gap-2">
                    {shownNetworks.map((n) => (
                      <Badge key={n.network} variant="outline" className="font-mono gap-1.5 py-1 border-primary/20 bg-primary/5">
                        <NetworkLogo id={n.network} size={14} />
                        {NETWORK_MAP[n.network]?.name || n.network} ৳{n.rate}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
                <CardFooter>
                  {side === 'buy' ? (
                    <Button className="w-full font-bold" onClick={() => selectSeller(seller)}>
                      Buy from this Seller <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  ) : (
                    <Button
                      className="w-full font-bold bg-destructive hover:bg-destructive/90 text-destructive-foreground"
                      onClick={() => setContactSeller(seller)}
                    >
                      Sell to this Seller <MessageCircle className="ml-2 h-4 w-4" />
                    </Button>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}

      {/* Sell flow — contact the merchant to arrange the payout (no automated money flow) */}
      {contactSeller && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-in fade-in"
          onClick={() => setContactSeller(null)}
        >
          <Card className="w-full max-w-md border-primary/20" onClick={(e) => e.stopPropagation()}>
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <CardTitle className="flex items-center gap-2">
                    <MessageCircle className="h-5 w-5 text-destructive" /> Sell to {contactSeller.display_name}
                  </CardTitle>
                  <CardDescription>
                    Contact this merchant to agree on the amount and rate, then send your crypto and receive the payout.
                  </CardDescription>
                </div>
                <button
                  onClick={() => setContactSeller(null)}
                  className="text-muted-foreground hover:text-foreground"
                  aria-label="Close"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <p className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground">Their Rates</p>
                <div className="flex flex-wrap gap-2">
                  {contactSeller.networks.map((n) => (
                    <Badge key={n.network} variant="outline" className="font-mono gap-1.5 py-1 border-primary/20 bg-primary/5">
                      <NetworkLogo id={n.network} size={14} />
                      {NETWORK_MAP[n.network]?.name || n.network} ৳{n.rate}
                    </Badge>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between rounded-md border border-primary/15 bg-primary/5 px-3 py-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <MessageCircle className="h-4 w-4 text-primary shrink-0" />
                    <span className="text-sm font-mono truncate">{contactSeller.support_contact}</span>
                  </div>
                  <CopyButton value={contactSeller.support_contact ?? ''} />
                </div>
                {contactSeller.bkash_number ? (
                  <div className="flex items-center justify-between rounded-md border border-primary/15 bg-primary/5 px-3 py-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <Smartphone className="h-4 w-4 text-primary shrink-0" />
                      <span className="text-sm font-mono truncate">{contactSeller.bkash_number}</span>
                    </div>
                    <CopyButton value={contactSeller.bkash_number ?? ''} />
                  </div>
                ) : null}
              </div>
              <Alert>
                <ShieldCheck className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  Only send crypto after you have agreed terms with the merchant. Mouno does not hold funds for P2P sell
                  trades — payouts are arranged directly with the merchant.
                </AlertDescription>
              </Alert>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full" onClick={() => setContactSeller(null)}>
                Close
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Market;
