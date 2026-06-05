import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { BookOpen } from 'lucide-react';
import { NetworkLogo } from '../constants/networks';

const Guide: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-primary/10 rounded-lg">
          <BookOpen className="h-6 w-6 text-primary" />
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight">User Guide</h1>
      </div>

      <Card className="border-primary/10">
        <CardHeader><CardTitle className="text-lg">১. কী করা যাবে</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>• bKash দিয়ে ক্রিপ্টো কেনা (Buy)</p>
          <p>• Gift Code / Giveaway Code দিয়ে ক্রিপ্টো নেওয়া</p>
          <p>• Cross-chain Swap/Bridge করা</p>
          <p>• নিজের encrypted wallet দিয়ে crypto পাঠানো</p>
          <p>• Balance দেখা, TX Log, Order Status চেক করা</p>
          <p>• Referral link শেয়ার করে earnings জমানো ও Payout নেওয়া</p>
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader><CardTitle className="text-lg">২. Supported Networks</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
            <div className="p-2 rounded bg-muted/30 flex items-center gap-2"><NetworkLogo id="solana" size={18} /> Solana — USDC</div>
            <div className="p-2 rounded bg-muted/30 flex items-center gap-2"><NetworkLogo id="trc20" size={18} /> Tron (TRC20) — USDT</div>
            <div className="p-2 rounded bg-muted/30 flex items-center gap-2"><NetworkLogo id="polygon" size={18} /> Polygon — USDC</div>
            <div className="p-2 rounded bg-muted/30 flex items-center gap-2"><NetworkLogo id="bsc" size={18} /> BSC (BNB) — USDT</div>
            <div className="p-2 rounded bg-muted/30 flex items-center gap-2"><NetworkLogo id="ton" size={18} /> TON — USDT</div>
            <div className="p-2 rounded bg-muted/30 flex items-center gap-2"><NetworkLogo id="avalanche" size={18} /> Avalanche — USDT</div>
            <div className="p-2 rounded bg-muted/30 flex items-center gap-2"><NetworkLogo id="ethereum" size={18} /> Ethereum — USDT / USDC</div>
            <div className="p-2 rounded bg-muted/30 flex items-center gap-2"><NetworkLogo id="base" size={18} /> Base — USDC</div>
          </div>
          <p className="text-xs text-destructive mt-3">⚠️ ভুল network বা ভুল wallet-এ পাঠালে transaction ফিরিয়ে আনা যায় না।</p>
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader><CardTitle className="text-lg">৩. bKash দিয়ে কেনার ধাপ</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p><strong>১)</strong> Buy পেজে যান → Network বেছে নিন</p>
          <p><strong>২)</strong> আপনার receiving wallet address দিন</p>
          <p><strong>৩)</strong> BDT amount লিখুন → crypto amount দেখুন</p>
          <p><strong>৪)</strong> bKash number-এ exact amount পাঠান</p>
          <p><strong>৫)</strong> bKash TrxID লিখে Submit করুন</p>
          <p><strong>৬)</strong> TrxID verify হলে crypto automatically আপনার wallet-এ পৌঁছে যাবে</p>
          <p className="text-xs text-yellow-500">💡 Order ID ও TrxID সংরক্ষণ করুন। Order Status পেজে যেকোনো সময় চেক করতে পারবেন।</p>
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader><CardTitle className="text-lg">৪. Personal Wallet Setup</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p><strong>১)</strong> Wallet পেজে যান → Setup Wallet</p>
          <p><strong>২)</strong> Network বেছে নিন</p>
          <p><strong>৩)</strong> Private key দিন — সার্ভারে encrypted অবস্থায় সংরক্ষিত হবে</p>
          <p><strong>৪)</strong> শক্তিশালী password দিন — এই password দিয়ে wallet unlock হবে</p>
          <p><strong>৫)</strong> Setup complete হলে wallet address দেখাবে</p>
          <p className="text-xs text-destructive">⚠️ Password ভুলে গেলে key recover করা যাবে না।</p>
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader><CardTitle className="text-lg">৫. Crypto পাঠানো (Send)</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p><strong>১)</strong> Wallet পেজে যান → Send</p>
          <p><strong>২)</strong> Destination wallet address দিন</p>
          <p><strong>৩)</strong> Amount লিখুন</p>
          <p><strong>৪)</strong> Password দিন</p>
          <p><strong>৫)</strong> Confirm করুন — transaction hash পাবেন</p>
          <p className="text-xs text-destructive">⚠️ Blockchain transaction irreversible। Address ও amount পাঠানোর আগে অবশ্যই মিলিয়ে নিন।</p>
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader><CardTitle className="text-lg">৬. Gas Fee / Network Fee</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>Token পাঠাতে network fee লাগে। Wallet-এ token ছাড়াও native gas token রাখতে হবে:</p>
          <div className="grid grid-cols-2 gap-1 mt-2 text-xs">
            <span>Solana → SOL</span><span>Polygon → MATIC</span>
            <span>BSC → BNB</span><span>Avalanche → AVAX</span>
            <span>Ethereum → ETH</span><span>Base → ETH</span>
            <span>Tron → TRX/Energy</span><span>TON → TON</span>
          </div>
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader><CardTitle className="text-lg">৭. Security Rules</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>• Private key, seed phrase বা wallet password কাউকে দেবেন না</p>
          <p>• Support/admin কখনো private key বা seed phrase চাইবে না</p>
          <p>• Public wallet address share করা যায়, কিন্তু private key share করা যাবে না</p>
          <p>• Password শক্তিশালী রাখুন এবং আলাদা জায়গায় সংরক্ষণ করুন</p>
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader><CardTitle className="text-lg">৮. Common Problems</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>• <strong>Wrong password:</strong> সঠিক password দিন। ভুলে গেলে key recover হবে না।</p>
          <p>• <strong>Insufficient gas:</strong> Native gas token top up করুন।</p>
          <p>• <strong>Invalid wallet:</strong> Selected network অনুযায়ী wallet address দিন।</p>
          <p>• <strong>Send failed:</strong> Hash না এলে duplicate send করার আগে support-এ verify করুন।</p>
          <p>• <strong>Pending order:</strong> Order ID/TrxID সংরক্ষণ করুন এবং Order Status পেজে চেক করুন।</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default Guide;
