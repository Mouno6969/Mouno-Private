import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import { apiClient, getErrorMessage } from '../lib/apiClient';

const GiftCode: React.FC = () => {
  const { t } = useTranslation();
  const [code, setCode] = useState('');
  const [wallet, setWallet] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRedeem = async () => {
    if (!code || !wallet) {
      toast.error('Please enter both code and wallet address');
      return;
    }

    setLoading(true);
    try {
      const res = await apiClient.post<{ message: string }>(
        '/api/gift/redeem',
        { code, wallet },
        { silent: true }
      );
      toast.success(res.data.message);
      setCode('');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to connect to server'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>{t('redeem_gift')}</CardTitle>
          <CardDescription>Enter a valid gift code to receive crypto instantly to your wallet.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">{t('enter_code')}</label>
            <Input
              placeholder="GIFT-XXXXXX"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t('wallet_address')}</label>
            <Input
              placeholder="Enter your receiving address"
              value={wallet}
              onChange={(e) => setWallet(e.target.value)}
            />
          </div>
          <Button
            className="w-full"
            onClick={handleRedeem}
            disabled={loading}
          >
            {loading ? 'Processing...' : t('withdraw')}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default GiftCode;
