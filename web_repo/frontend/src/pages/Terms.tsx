import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ShieldAlert } from 'lucide-react';
import { NetworkLogo } from '../constants/networks';
import { PageHeader } from '../components/common';

const Terms: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader icon={<ShieldAlert className="h-7 w-7" />} eyebrow="Legal" title="Terms & Risk Warning" />

      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="text-lg">Important Guidelines</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <ul className="list-disc list-inside space-y-3">
            <li><strong>Always choose the correct network.</strong> Selecting the wrong network for your wallet address will result in permanent loss of funds.</li>
            <li><strong>Wrong wallet/network transfers cannot be reversed.</strong> Double-check your wallet address before confirming any transaction.</li>
            <li><strong>Keep enough native gas tokens</strong> for personal wallet sends. Solana needs SOL, Polygon needs MATIC, BSC needs BNB, Tron needs TRX, TON needs TON, and Ethereum/Base need ETH.</li>
            <li><strong>Payments may require manual review</strong> if bKash notification data is delayed or mismatched with your order. Save your Order ID and TrxID.</li>
            <li><strong>Contact support</strong> if a payment is stuck or you encounter any issues. Do not retry payments without checking order status first.</li>
            <li><strong>Never share private keys, seed phrases, or wallet passwords</strong> with anyone, including support staff.</li>
            <li><strong>Rates are dynamic</strong> and may change between the time you view them and when payment is confirmed.</li>
            <li><strong>Gift codes and giveaway codes</strong> have expiration dates. Expired codes cannot be redeemed.</li>
          </ul>
        </CardContent>
      </Card>

      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="text-lg">Supported Networks</CardTitle>
        </CardHeader>
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
        </CardContent>
      </Card>
    </div>
  );
};

export default Terms;
