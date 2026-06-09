import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { HelpCircle } from 'lucide-react';
import { AnimatedText } from '../components/ui/animated-text';

const faqs = [
  {
    q: 'How do I buy crypto?',
    a: 'Choose Buy, select a network, enter your receiving wallet, enter the BDT amount, pay the exact bKash amount, then submit your TrxID.'
  },
  {
    q: 'Which networks are supported?',
    a: 'Solana USDC, Polygon USDC, BSC USDT, Avalanche USDT, Ethereum USDT/USDC, Base USDC, Tron USDT, and TON. Always send the correct wallet for the selected network.'
  },
  {
    q: 'How long does delivery take?',
    a: 'Most verified orders are delivered within a few minutes. Delivery can take longer if bKash notice is delayed, the TrxID is wrong, stock is low, or the network/RPC is busy.'
  },
  {
    q: 'What should I check before payment?',
    a: 'Confirm the selected network, wallet address, BDT amount, and bKash number before sending payment. Wrong network or wrong wallet transfers cannot be reversed.'
  },
  {
    q: 'What if my order is pending?',
    a: 'Save your Order ID and TrxID. Check your Order History page. If needed, admin will manually verify the payment.'
  },
  {
    q: 'How do gift codes work?',
    a: 'Enter your gift code and wallet address on the Gift Codes page. The system validates the code and sends the crypto to your wallet automatically.'
  },
  {
    q: 'Where can I get help?',
    a: 'Use AI Support for quick guidance or contact the support team via Telegram. Never share private keys, seed phrases, or wallet passwords.'
  },
];

const FAQ: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-primary/10 rounded-lg">
          <HelpCircle className="h-6 w-6 text-primary" />
        </div>
        <AnimatedText
          text="FAQ"
          speed={80}
          className="text-3xl font-extrabold tracking-tight"
        />
      </div>
      <p className="text-muted-foreground">Frequently asked questions about our services.</p>

      <div className="space-y-4">
        {faqs.map((faq, i) => (
          <Card key={i} className="border-primary/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-semibold">{i + 1}. {faq.q}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{faq.a}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default FAQ;
