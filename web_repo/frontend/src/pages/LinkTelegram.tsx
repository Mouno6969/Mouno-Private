import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuth } from '../context/AuthContext';
import { Send, Link as LinkIcon, CheckCircle, Bell, Gift, Shield, ExternalLink, ArrowRight, Loader2, User } from 'lucide-react';
import { toast } from 'sonner';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import { PageHeader, TexturePanel } from '../components/common';

const LinkTelegram: React.FC = () => {
  const { t } = useTranslation();
  const { refreshUser } = useAuth();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code) return;

    setLoading(true);
    try {
      const res = await apiClient.post<{ message: string }>(
        '/api/link-telegram',
        { link_code: code },
        { silent: true }
      );
      toast.success(res.data.message);
      await refreshUser();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to connect to server'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-4 sm:space-y-6 px-1 sm:px-0 animate-in fade-in duration-300">
      <PageHeader
        icon={<LinkIcon className="h-7 w-7" />}
        eyebrow="Connect"
        title={t('connect_telegram', 'Link Telegram Account')}
        description="Sync your account with Telegram for order notifications and exclusive features."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 items-start">
        {/* Main Form */}
        <div className="lg:col-span-2">
          <TexturePanel variant="primary" accentTop glow>
            <div className="p-5 sm:p-6 space-y-6">
              {/* Visual Connection Diagram */}
              <div className="flex items-center justify-center gap-2 sm:gap-4 py-4 sm:py-6">
                <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-muted/50 border border-border/50 flex items-center justify-center shrink-0">
                  <User className="h-5 w-5 sm:h-7 sm:w-7 text-muted-foreground" />
                </div>
                <div className="flex items-center gap-0.5 sm:gap-1">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-primary/40" />
                  ))}
                </div>
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center shrink-0">
                  <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
                </div>
                <div className="flex items-center gap-0.5 sm:gap-1">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-primary/40" />
                  ))}
                </div>
                <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-[#229ED9]/10 border border-[#229ED9]/30 flex items-center justify-center shrink-0">
                  <Send className="h-5 w-5 sm:h-7 sm:w-7 text-[#229ED9]" />
                </div>
              </div>

              {/* Code Input */}
              <form onSubmit={handleLink} className="space-y-5">
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground">Enter Link Code</Label>
                  <Input
                    placeholder="A1B2C3D4"
                    value={code}
                    onChange={(e) => setCode(e.target.value.toUpperCase())}
                    className="h-12 sm:h-14 font-mono text-center text-xl sm:text-2xl tracking-[0.2em] sm:tracking-[0.3em] uppercase border-primary/20 focus-visible:border-primary"
                    maxLength={8}
                    required
                  />
                  <p className="text-xs text-muted-foreground text-center">Get this code from our Telegram bot</p>
                </div>

                <Button
                  type="submit"
                  className="w-full h-12 text-base font-bold rounded-xl shadow-lg shadow-primary/20"
                  disabled={loading || !code}
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Linking...
                    </>
                  ) : (
                    <>
                      <LinkIcon className="mr-2 h-5 w-5" /> Link My Account
                    </>
                  )}
                </Button>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t border-border/50" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-card px-2 text-muted-foreground">OR</span>
                  </div>
                </div>

                <a
                  href="https://t.me/Automatedcryptobuybot"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <Button type="button" variant="outline" className="w-full h-11 font-semibold">
                    <Send className="mr-2 h-4 w-4 text-[#229ED9]" />
                    Open Telegram Bot
                    <ExternalLink className="ml-2 h-3 w-3 text-muted-foreground" />
                  </Button>
                </a>
              </form>
            </div>
          </TexturePanel>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* How to Get Code */}
          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Send className="h-4 w-4 text-primary" /> How to Get Your Code
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { step: 1, text: 'Open our Telegram Bot', link: '@Automatedcryptobuybot' },
                { step: 2, text: 'Send the /link command' },
                { step: 3, text: 'Copy the 8-character code' },
                { step: 4, text: 'Paste it here and link' },
              ].map((item) => (
                <div key={item.step} className="flex gap-3 items-start">
                  <div className="h-5 w-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    {item.step}
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{item.text}</p>
                    {item.link && (
                      <a
                        href="https://t.me/Automatedcryptobuybot"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline"
                      >
                        {item.link}
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Benefits */}
          <Card className="border-primary/10">
            <CardHeader>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Gift className="h-4 w-4 text-primary" /> Link Benefits
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { icon: Bell, text: 'Instant order notifications' },
                { icon: Send, text: 'Buy crypto via Telegram' },
                { icon: Gift, text: 'Access giveaways & rewards' },
                { icon: Shield, text: 'Priority support channel' },
              ].map((benefit, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg bg-muted/30">
                  <div className="h-5 w-5 rounded-full bg-success/20 text-success flex items-center justify-center shrink-0">
                    <CheckCircle className="h-3 w-3" />
                  </div>
                  <span className="text-xs font-medium">{benefit.text}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default LinkTelegram;
