import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../context/AuthContext';
import { Store, CheckCircle2, Clock, XCircle, Package, History } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../components/ui/badge';

const Seller: React.FC = () => {
  const { t } = useTranslation();
  const { token, user } = useAuth();
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);

  const [showInventory, setShowInventory] = useState(false);
  const [showOrders, setShowOrders] = useState(false);
  const [inventory, setInventory] = useState<any>(null);
  const [sellerOrders, setSellerOrders] = useState<any[]>([]);

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
  }, [token, user]);

  useEffect(() => {
    if (showInventory && !inventory && token) {
      fetch(`${process.env.REACT_APP_API_URL || ''}/api/seller/inventory`, { headers: { 'Authorization': `Bearer ${token}` } })
        .then(r => r.json()).then(d => setInventory(d)).catch(() => {});
    }
  }, [showInventory, inventory, token]);

  useEffect(() => {
    if (showOrders && sellerOrders.length === 0 && token) {
      fetch(`${process.env.REACT_APP_API_URL || ''}/api/seller/orders`, { headers: { 'Authorization': `Bearer ${token}` } })
        .then(r => r.json()).then(d => setSellerOrders(Array.isArray(d) ? d : d.orders || [])).catch(() => {});
    }
  }, [showOrders, sellerOrders.length, token]);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/seller/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setStatus(data);
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
      const res = await fetch(`${process.env.REACT_APP_API_URL || ''}/api/seller/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message);
        fetchStatus();
      } else {
        toast.error(data.message);
      }
    } catch (err) {
      toast.error('Failed to submit application');
    } finally {
      setApplying(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  if (!user?.telegram_id) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <h2 className="text-2xl font-bold">{t('connect_telegram')}</h2>
        <p className="text-muted-foreground text-center max-w-md">
          To become a seller, you must link your Telegram account.
          This is required for order notifications and security.
        </p>
        <Button onClick={() => window.open('https://t.me/Automatedcryptobuybot', '_blank')}>
          Open Bot to Connect
        </Button>
      </div>
    );
  }

  if (status?.status === 'approved') {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <Card className="border-primary/50 bg-primary/5">
          <CardHeader>
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-8 w-8 text-primary" />
              <div>
                <CardTitle>Seller Account Active</CardTitle>
                <CardDescription>Welcome back, {status.display_name}!</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">bKash Number</p>
              <p className="font-medium">{status.bkash_number}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Forwarder Token</p>
              <code className="bg-muted px-2 py-1 rounded text-xs">{status.sms_token}</code>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
            <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><Package className="h-4 w-4" /> Manage Inventory</CardTitle></CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">Update your rates and stock for different networks.</p>
                    <Button variant="outline" className="w-full" onClick={() => setShowInventory(!showInventory)}>
                      {showInventory ? 'Hide Inventory' : 'Open Inventory'}
                    </Button>
                </CardContent>
            </Card>
            <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><History className="h-4 w-4" /> Order History</CardTitle></CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">View and manage orders from your customers.</p>
                    <Button variant="outline" className="w-full" onClick={() => setShowOrders(!showOrders)}>
                      {showOrders ? 'Hide Orders' : 'View Orders'}
                    </Button>
                </CardContent>
            </Card>
        </div>

        {showInventory && (
          <Card>
            <CardHeader><CardTitle>Inventory</CardTitle></CardHeader>
            <CardContent>
              {inventory ? (
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Rates</h4>
                    {inventory.rates?.length > 0 ? inventory.rates.map((r: any, i: number) => (
                      <div key={i} className="flex justify-between py-1 border-b text-sm">
                        <span className="font-mono">{r.network}</span>
                        <Badge variant="outline">৳{r.rate}</Badge>
                      </div>
                    )) : <p className="text-sm text-muted-foreground">No custom rates set.</p>}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Wallets</h4>
                    {inventory.wallets?.length > 0 ? inventory.wallets.map((w: any, i: number) => (
                      <div key={i} className="flex justify-between py-1 border-b text-sm">
                        <span className="font-mono">{w.network}</span>
                        <span className="font-mono text-xs truncate max-w-[200px]">{w.wallet_address}</span>
                      </div>
                    )) : <p className="text-sm text-muted-foreground">No wallets configured.</p>}
                  </div>
                </div>
              ) : <p className="text-sm text-muted-foreground">Loading...</p>}
            </CardContent>
          </Card>
        )}

        {showOrders && (
          <Card>
            <CardHeader><CardTitle>Recent Orders</CardTitle></CardHeader>
            <CardContent>
              {sellerOrders.length > 0 ? (
                <div className="space-y-3">
                  {sellerOrders.map((order: any, i: number) => (
                    <div key={i} className="p-3 border rounded-lg space-y-1">
                      <div className="flex justify-between">
                        <span className="font-mono font-bold">{order.order_id || order.trx_id}</span>
                        <Badge variant={order.status === 'completed' ? 'default' : 'secondary'}>{order.status}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        ৳{order.amount_bdt} → {order.amount_crypto} {order.network?.toUpperCase()}
                      </div>
                      {order.wallet && <div className="text-xs font-mono text-muted-foreground truncate">{order.wallet}</div>}
                    </div>
                  ))}
                </div>
              ) : <p className="text-sm text-muted-foreground">No orders yet.</p>}
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  if (status?.status === 'pending') {
    return (
      <Card className="max-w-md mx-auto">
        <CardHeader className="text-center">
          <Clock className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <CardTitle>Application Pending</CardTitle>
          <CardDescription>
            Your application to become a seller is currently being reviewed by our team.
            We will notify you on Telegram once it is approved.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="max-w-md mx-auto">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 mb-2">
            <Store className="h-5 w-5 text-primary" />
            <CardTitle>{t('apply_seller')}</CardTitle>
          </div>
          <CardDescription>
            Join our marketplace and start selling your crypto to thousands of users.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleApply} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('seller_name')}</label>
              <Input
                required
                placeholder="e.g. My Crypto Shop"
                value={formData.display_name}
                onChange={e => setFormData({...formData, display_name: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('seller_bkash')}</label>
              <Input
                required
                placeholder="01XXXXXXXXX"
                value={formData.bkash_number}
                onChange={e => setFormData({...formData, bkash_number: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('seller_support')}</label>
              <Input
                required
                placeholder="@username"
                value={formData.support_contact}
                onChange={e => setFormData({...formData, support_contact: e.target.value})}
              />
            </div>
            <Button type="submit" className="w-full" disabled={applying}>
              {applying ? 'Submitting...' : 'Submit Application'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default Seller;
