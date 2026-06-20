import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../context/AuthContext';
import { Users, DollarSign, Wallet, Gift } from 'lucide-react';
import { apiClient } from '../lib/apiClient';
import { PageHeader, StatCard, TexturePanel, CopyButton } from '../components/common';

interface ReferralStats {
  referral_count?: number;
  total_earned?: number;
  balance?: number;
}

const Referral: React.FC = () => {
  const { t } = useTranslation();
  const { token, user } = useAuth();
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [code, setCode] = useState('');
  const [, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await apiClient.get<{ stats: ReferralStats; code: string }>('/api/referral', { silent: true });
        setStats(res.data.stats);
        setCode(res.data.code);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [token]);

  const refLink = `https://t.me/Automatedcryptobuybot?start=ref_${code}`;

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
      <PageHeader icon={<Gift className="h-7 w-7" />} eyebrow="Earn" title={t('referral')} description="Invite friends and earn on every order they make." />

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label={t('referral')} icon={<Users className="h-4 w-4" />} value={stats?.referral_count ?? 0} />
        <StatCard label={t('earnings')} icon={<DollarSign className="h-4 w-4" />} value={`$${stats?.total_earned?.toFixed(2) || '0.00'}`} />
        <StatCard label="Balance" icon={<Wallet className="h-4 w-4" />} value={`$${stats?.balance?.toFixed(2) || '0.00'}`} />
      </div>

      <TexturePanel variant="primary" glow accentTop>
        <div className="p-5 sm:p-6 space-y-4">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">{t('referral_link')}</h2>
            <p className="text-sm text-muted-foreground">Share this link to earn commissions on every order your friends make.</p>
          </div>
          <div className="flex gap-2">
            <Input value={refLink} readOnly className="font-mono text-xs" />
            <CopyButton value={refLink} label="Copy referral link" withText className="px-3 rounded-md border border-border shrink-0" />
          </div>
          <Button className="w-full" variant="outline">{t('withdraw')}</Button>
        </div>
      </TexturePanel>
    </div>
  );
};

export default Referral;
