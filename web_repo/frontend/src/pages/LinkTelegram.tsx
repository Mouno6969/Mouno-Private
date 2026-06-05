import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../context/AuthContext';
import { Send, Link as LinkIcon } from 'lucide-react';
import { toast } from 'sonner';

const LinkTelegram: React.FC = () => {
  const { t } = useTranslation();
  const { token, refreshUser } = useAuth();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code) return;

    setLoading(true);
    try {
      const res = await fetch('http://localhost:5001/api/link-telegram', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ link_code: code })
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message);
        await refreshUser();
      } else {
        toast.error(data.message);
      }
    } catch (err) {
      toast.error('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 mb-2">
            <LinkIcon className="h-5 w-5 text-primary" />
            <CardTitle>{t('connect_telegram')}</CardTitle>
          </div>
          <CardDescription>
            Link your website account with your Telegram profile to sync orders and access exclusive features.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-muted/50 p-4 rounded-lg text-sm space-y-2">
             <p className="font-bold">How to get the code:</p>
             <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                <li>Open our Telegram Bot: <a href="https://t.me/Automatedcryptobuybot" target="_blank" className="text-primary underline">@Automatedcryptobuybot</a></li>
                <li>Send the command <code>/link</code> to the bot.</li>
                <li>Copy the 8-character code and paste it below.</li>
             </ol>
          </div>

          <form onSubmit={handleLink} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Link Code</label>
              <Input
                placeholder="e.g. A1B2C3D4"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                className="font-mono text-center text-lg tracking-widest"
                maxLength={8}
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading || !code}>
              {loading ? 'Linking...' : 'Link Account'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default LinkTelegram;
