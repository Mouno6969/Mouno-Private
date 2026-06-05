import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../context/AuthContext';
import { Copy, Users, DollarSign, Wallet } from 'lucide-react';
import { toast } from 'sonner';

const Referral: React.FC = () => {
  const { t } = useTranslation();
  const { token, user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, [token]);

  const fetchStats = async () => {
    try {
      const res = await fetch('http://localhost:5001/api/referral', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setStats(data.stats);
        setCode(data.code);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const copyLink = () => {
    const link = `https://t.me/Automatedcryptobuybot?start=ref_${code}`;
    navigator.clipboard.writeText(link);
    toast.success(t('copy_success'));
  };

  if (!user?.telegram_id) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <h2 className="text-2xl font-bold">{t('connect_telegram')}</h2>
        <p className="text-muted-foreground text-center max-w-md">
          To use the referral system, you must link your Telegram account.
          This allows us to track your referrals across the bot and website.
        </p>
        <Button onClick={() => window.open('https://t.me/Automatedcryptobuybot', '_blank')}>
          Open Bot to Connect
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('referral')}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.referral_count || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('earnings')}</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${stats?.total_earned?.toFixed(2) || '0.00'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Balance</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${stats?.balance?.toFixed(2) || '0.00'}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('referral_link')}</CardTitle>
          <CardDescription>Share this link to earn commissions on every order your friends make.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input value={`https://t.me/Automatedcryptobuybot?start=ref_${code}`} readOnly />
            <Button size="icon" onClick={copyLink}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
          <Button className="w-full" variant="outline">{t('withdraw')}</Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default Referral;
