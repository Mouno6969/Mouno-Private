import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuth } from '../context/AuthContext';
import { Store, CheckCircle2, Clock, Package, History, Users, ShoppingBag, Zap, Send, ArrowRight, Loader2, Shield } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../components/ui/badge';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import { PageHeader, StatCard, TexturePanel, CopyButton } from '../components/common';
import { NetworkLogo, NETWORK_MAP } from '../constants/networks';

interface SellerStatus {
  status?: string;
  display_name?: string;
  bkash_number?: string;
  sms_token?: string;
}
interface SellerInventory {
  rates?: { network: string; rate: number }[];
  wallets?: { network: string; wallet_address: string }[];
}
interface SellerOrder {
  order_id?: string;
  trx_id?: string;
  status?: string;
  amount_bdt?: number;
  amount_crypto?: number;
  network?: string;
  wallet?: string;
}

const Seller: React.FC = () => {
  const { t } = useTranslation();
  const { token, user } = useAuth();
  const [status, setStatus] = useState<SellerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);

  const [showInventory, setShowInventory] = useState(false);
  const [showOrders, setShowOrders] = useState(false);
  const [inventory, setInventory] = useState<SellerInventory | null>(null);
  const [sellerOrders, setSellerOrders] = useState<SellerOrder[]>([]);

  const [formData, setFormData] = useState({
    display_name: '',
    bkash_number: '',
    support_contact: ''
  });

  useEffect(() => {
    if (token && user?.telegram_id) {
      fetchStatus();
    } else {
      setLoading(false);
    }
  }, [token, user]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (showInventory && !inventory && token) {
      apiClient.get<SellerInventory>('/api/seller/inventory', { silent: true })
        .then(r => setInventory(r.data)).catch(() => {});
    }
  }, [showInventory, inventory, token]);

  useEffect(() => {
    if (showOrders && sellerOrders.length === 0 && token) {
      apiClient.get<SellerOrder[] | { orders: SellerOrder[] }>('/api/seller/orders', { silent: true })
        .then(r => setSellerOrders(Array.isArray(r.data) ? r.data : r.data.orders || [])).catch(() => {});
    }
  }, [showOrders, sellerOrders.length, token]);

  const fetchStatus = async () => {
    try {
      const res = await apiClient.get<SellerStatus>('/api/seller/status', { silent: true });
      setStatus(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    setApplying(true);
    try {
      const res = await apiClient.post<{ message: string }>('/api/seller/apply', formData, { silent: true });
      toast.success(res.data.message);
      fetchStatus();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to submit application'));
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // ─── Telegram Not Linked Gate ───
  if (!user?.telegram_id) {
    return (
      <div className="max-w-lg mx-auto space-y-6 animate-in fade-in duration-300">
        <PageHeader
          icon={<Store className="h-7 w-7" />}
          eyebrow="Marketplace"
          title="Seller Portal"
          description="Join our marketplace and start selling crypto."
        />
        <TexturePanel variant="primary" glow accentTop>
          <div className="p-8 text-center space-y-4">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
              <Send className="h-8 w-8 text-primary" />
            </div>
            <h2 className="text-xl font-bold">{t('connect_telegram')}</h2>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              To become a seller, you must link your Telegram account. This is required for order notifications and security.
            </p>
            <Button onClick={() => window.open('https://t.me/Automatedcryptobuybot', '_blank')} className="mt-4">
              Open Bot to Connect <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </TexturePanel>
      </div>
    );
  }

  // ─── Approved Seller Dashboard ───
  if (status?.status === 'approved') {
    return (
      <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-300">
        <PageHeader
          icon={<Store className="h-7 w-7" />}
          eyebrow="Marketplace"
          title="Seller Dashboard"
          description={`Welcome back, ${status.display_name}!`}
        />

        {/* Status Banner */}
        <TexturePanel variant="success" accentTop>
          <div className="p-5 sm:p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-success/10 rounded-xl">
                <CheckCircle2 className="h-8 w-8 text-success" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-lg font-bold tracking-tight">Seller Account Active</h2>
                <p className="text-sm text-muted-foreground">Your marketplace account is verified and operational.</p>
              </div>
              <Badge variant="success" className="shrink-0">Approved</Badge>
            </div>
          </div>
        </TexturePanel>

        {/* Seller Info Cards */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="border-primary/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">bKash Number</p>
                  <p className="text-lg font-bold font-mono mt-1">{status.bkash_number}</p>
                </div>
                <CopyButton value={status.bkash_number || ''} label="Copy bKash number" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-primary/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">Forwarder Token</p>
                  <p className="text-sm font-mono mt-1 truncate max-w-[200px]">{status.sms_token}</p>
                </div>
                <CopyButton value={status.sms_token || ''} label="Copy token" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Cards */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="group transition-all hover:border-primary/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Package className="h-5 w-5 text-primary" /> Manage Inventory
              </CardTitle>
              <CardDescription>Update your rates and stock for different networks.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full font-semibold" onClick={() => setShowInventory(!showInventory)}>
                {showInventory ? 'Hide Inventory' : 'Open Inventory'}
              </Button>
            </CardContent>
          </Card>
          <Card className="group transition-all hover:border-primary/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <History className="h-5 w-5 text-primary" /> Order History
              </CardTitle>
              <CardDescription>View and manage orders from your customers.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full font-semibold" onClick={() => setShowOrders(!showOrders)}>
                {showOrders ? 'Hide Orders' : 'View Orders'}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Inventory Panel */}
        {showInventory && (
          <Card className="border-primary/10 animate-in slide-in-from-top-2 duration-200">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Package className="h-5 w-5 text-primary" /> Inventory
              </CardTitle>
            </CardHeader>
            <CardContent>
              {inventory ? (
                <div className="space-y-6">
                  <div>
                    <h4 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3">Custom Rates</h4>
                    {inventory.rates?.length ? (
                      <div className="space-y-2">
                        {inventory.rates.map((r, i) => (
                          <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40">
                            <div className="flex items-center gap-2">
                              <NetworkLogo id={r.network} size={20} />
                              <span className="text-sm font-medium">{NETWORK_MAP[r.network]?.name || r.network}</span>
                            </div>
                            <Badge variant="outline" className="font-mono">৳{r.rate}</Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No custom rates set.</p>
                    )}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3">Wallets</h4>
                    {inventory.wallets?.length ? (
                      <div className="space-y-2">
                        {inventory.wallets.map((w, i) => (
                          <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40">
                            <div className="flex items-center gap-2">
                              <NetworkLogo id={w.network} size={20} />
                              <span className="text-sm font-medium">{NETWORK_MAP[w.network]?.name || w.network}</span>
                            </div>
                            <span className="font-mono text-xs text-muted-foreground truncate max-w-[200px]">{w.wallet_address}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No wallets configured.</p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex justify-center py-6">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Orders Panel */}
        {showOrders && (
          <Card className="border-primary/10 animate-in slide-in-from-top-2 duration-200">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <History className="h-5 w-5 text-primary" /> Recent Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              {sellerOrders.length > 0 ? (
                <div className="space-y-3">
                  {sellerOrders.map((order, i) => (
                    <div key={i} className="p-4 rounded-lg bg-muted/30 ring-1 ring-inset ring-border/40 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-sm">{order.order_id || order.trx_id}</span>
                        <Badge variant={order.status === 'completed' ? 'success' : 'secondary'}>{order.status}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">৳{order.amount_bdt} → {order.amount_crypto} {order.network?.toUpperCase()}</span>
                        {order.network && <NetworkLogo id={order.network} size={18} />}
                      </div>
                      {order.wallet && (
                        <div className="text-xs font-mono text-muted-foreground truncate">{order.wallet}</div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-6">No orders yet.</p>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // ─── Pending Application ───
  if (status?.status === 'pending') {
    return (
      <div className="max-w-lg mx-auto space-y-6 animate-in fade-in duration-300">
        <PageHeader
          icon={<Store className="h-7 w-7" />}
          eyebrow="Marketplace"
          title="Seller Portal"
        />
        <TexturePanel variant="primary" accentTop>
          <div className="p-8 text-center space-y-4">
            <div className="w-16 h-16 bg-warning/10 rounded-full flex items-center justify-center mx-auto">
              <Clock className="h-8 w-8 text-warning" />
            </div>
            <h2 className="text-xl font-bold">Application Pending</h2>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              Your application to become a seller is currently being reviewed by our team.
              We will notify you on Telegram once it is approved.
            </p>
            <Badge variant="warning" className="mt-2">Under Review</Badge>
          </div>
        </TexturePanel>
      </div>
    );
  }

  // ─── Application Form (default state) ───
  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in duration-300">
      <PageHeader
        icon={<Store className="h-7 w-7" />}
        eyebrow="Marketplace"
        title="Seller Portal"
        description="Join our marketplace and start selling crypto to thousands of users."
      />

      {/* Hero Banner */}
      <TexturePanel variant="primary" glow accentTop>
        <div className="p-6 sm:p-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-4">
              <h2 className="text-2xl font-extrabold tracking-tight">Start Earning Today</h2>
              <ul className="space-y-2">
                {[
                  'Set your own rates',
                  'Automated order matching',
                  'Real-time notifications via Telegram',
                  'Full inventory management',
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                    <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-xl border border-border/50 bg-card/50 text-center">
                <Users className="h-5 w-5 text-primary mx-auto mb-1" />
                <p className="text-lg font-bold">24</p>
                <p className="text-[10px] text-muted-foreground">Active Sellers</p>
              </div>
              <div className="p-4 rounded-xl border border-border/50 bg-card/50 text-center">
                <ShoppingBag className="h-5 w-5 text-primary mx-auto mb-1" />
                <p className="text-lg font-bold">12.5K+</p>
                <p className="text-[10px] text-muted-foreground">Orders Fulfilled</p>
              </div>
              <div className="p-4 rounded-xl border border-border/50 bg-card/50 text-center col-span-2">
                <Zap className="h-5 w-5 text-primary mx-auto mb-1" />
                <p className="text-lg font-bold">&lt;2 min</p>
                <p className="text-[10px] text-muted-foreground">Avg. Response Time</p>
              </div>
            </div>
          </div>
        </div>
      </TexturePanel>

      {/* Application Form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2">
          <Card className="border-primary/10 shadow-xl overflow-hidden">
            <CardHeader className="bg-muted/30">
              <CardTitle className="text-lg">Application Form</CardTitle>
              <CardDescription>Fill in your details to apply as a seller on our platform.</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <form onSubmit={handleApply} className="space-y-5">
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground">{t('seller_name', 'Display Name')}</Label>
                  <div className="relative">
                    <Store className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      required
                      placeholder="e.g. My Crypto Shop"
                      className="pl-10"
                      value={formData.display_name}
                      onChange={e => setFormData({ ...formData, display_name: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground">{t('seller_bkash', 'bKash Number')}</Label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-muted-foreground text-sm font-mono">+880</span>
                    <Input
                      required
                      placeholder="1XXXXXXXXX"
                      className="pl-14 font-mono"
                      value={formData.bkash_number}
                      onChange={e => setFormData({ ...formData, bkash_number: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground">{t('seller_support', 'Support Contact (Telegram)')}</Label>
                  <div className="relative">
                    <Send className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      required
                      placeholder="@telegram_username"
                      className="pl-10"
                      value={formData.support_contact}
                      onChange={e => setFormData({ ...formData, support_contact: e.target.value })}
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full h-12 text-base font-bold rounded-xl shadow-lg shadow-primary/20"
                  disabled={applying}
                >
                  {applying ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Submitting...
                    </>
                  ) : (
                    <>
                      Submit Application <ArrowRight className="ml-2 h-5 w-5" />
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Requirements Sidebar */}
        <div className="space-y-4">
          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Shield className="h-4 w-4 text-primary" /> Requirements
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { label: 'Telegram account linked', met: !!user?.telegram_id },
                { label: 'Valid bKash number', met: false },
                { label: 'Active for 7+ days', met: false },
              ].map((req, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg bg-muted/30">
                  <div className={`h-5 w-5 rounded-full flex items-center justify-center shrink-0 ${req.met ? 'bg-success/20 text-success' : 'bg-muted text-muted-foreground'}`}>
                    <CheckCircle2 className="h-3 w-3" />
                  </div>
                  <span className="text-xs font-medium">{req.label}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-sm font-bold">Seller Benefits</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs text-muted-foreground">
              <p>• Set your own exchange rates</p>
              <p>• Receive instant Telegram notifications</p>
              <p>• Automated payment verification</p>
              <p>• Full order management dashboard</p>
              <p>• Priority support from admin team</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Seller;
