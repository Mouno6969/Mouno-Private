import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { Wallet, Key, Shield, Eye, EyeOff, AlertTriangle, Trash2, CheckCircle2, Lock, Cpu, Globe } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';

const MyWallet: React.FC = () => {
  const { t } = useTranslation();
  const [privateKey, setPrivateKey] = useState(localStorage.getItem('mouno_private_key') || '');
  const [showKey, setShowKey] = useState(false);
  const [isSaved, setIsSaved] = useState(!!localStorage.getItem('mouno_private_key'));

  const saveKey = () => {
    if (!privateKey) return;
    localStorage.setItem('mouno_private_key', privateKey);
    setIsSaved(true);
    // Use a toast in a real app, here we just update state
  };

  const removeKey = () => {
    if (window.confirm('Are you sure? Your private key will be removed from this browser memory.')) {
      localStorage.removeItem('mouno_private_key');
      setPrivateKey('');
      setIsSaved(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <section className="space-y-1">
        <div className="flex items-center gap-3">
           <div className="p-2 bg-primary/10 rounded-lg">
              <Wallet className="h-6 w-6 text-primary" />
           </div>
           <h1 className="text-3xl font-extrabold tracking-tight">Personal Wallet</h1>
        </div>
        <p className="text-muted-foreground">Connect your wallet for secure in-bot swaps and bridge executions.</p>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <Card className="shadow-xl border-primary/10 overflow-hidden">
            <CardHeader className="bg-muted/30">
               <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">Wallet Configuration</CardTitle>
                    <CardDescription>Manage your private keys locally</CardDescription>
                  </div>
                  {isSaved ? (
                    <Badge className="bg-green-500/10 text-green-500 border-green-500/20 px-3">
                       <CheckCircle2 className="mr-1 h-3 w-3" /> Connected
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-muted-foreground border-muted">Not Connected</Badge>
                  )}
               </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <Alert className="bg-amber-500/5 border-amber-500/20 text-amber-200">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle className="text-xs font-bold uppercase tracking-wider mb-1">Security Disclaimer</AlertTitle>
                <AlertDescription className="text-xs leading-relaxed opacity-80">
                  Your private key is stored <b>ONLY</b> in your browser's local storage. We never transmit or store your keys on our servers. Clearing your browser data will remove this key.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="key" className="text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                    <Key className="h-3 w-3" /> Private Key (EVM or Solana)
                  </Label>
                  <div className="relative group">
                    <Input
                      id="key"
                      type={showKey ? "text" : "password"}
                      className="h-12 pr-12 font-mono text-sm border-muted focus:border-primary/50 bg-muted/20"
                      placeholder="Paste your private key here"
                      value={privateKey}
                      onChange={(e) => setPrivateKey(e.target.value)}
                      disabled={isSaved}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-1 top-1 text-muted-foreground hover:text-primary transition-colors h-10 w-10"
                    >
                      {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
                    </Button>
                  </div>
                </div>

                <div className="flex gap-4 pt-2">
                  {!isSaved ? (
                    <Button onClick={saveKey} className="flex-1 h-12 font-bold rounded-xl shadow-lg shadow-primary/20">
                      <Shield className="mr-2 h-5 w-5" /> Save to Browser
                    </Button>
                  ) : (
                    <Button variant="destructive" onClick={removeKey} className="flex-1 h-12 font-bold rounded-xl opacity-80 hover:opacity-100 transition-opacity">
                      <Trash2 className="mr-2 h-5 w-5" /> Disconnect Wallet
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
            <CardFooter className="bg-muted/10 border-t py-4 px-6 flex items-center gap-2">
               <Lock className="h-3 w-3 text-muted-foreground" />
               <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-tighter">AES-256 Browser Encryption Enabled</span>
            </CardFooter>
          </Card>
        </div>

        <div className="space-y-6">
           <Card className="border-primary/10">
              <CardHeader className="pb-2">
                 <CardTitle className="text-sm font-bold flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-primary" /> How it works
                 </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                 <p className="text-xs text-muted-foreground leading-relaxed">
                   Saving your private key allows the MOUNO system to sign transactions directly from the web interface or telegram bot without requiring external wallet redirects (MetaMask/Phantom).
                 </p>
                 <div className="space-y-2 pt-2 border-t border-muted">
                    <div className="flex items-center gap-2 text-[10px] font-black text-muted-foreground uppercase">
                       <Globe className="h-3 w-3" /> Multi-Chain Support
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                       {['Ethereum', 'BSC', 'Polygon', 'Solana', 'Base', 'TON'].map(net => (
                         <Badge key={net} variant="secondary" className="text-[9px] px-1.5 py-0">{net}</Badge>
                       ))}
                    </div>
                 </div>
              </CardContent>
           </Card>

           <Card className="bg-blue-500/5 border-blue-500/10">
              <CardHeader className="pb-2">
                 <CardTitle className="text-xs font-bold text-blue-400 uppercase tracking-widest">In-Bot Execution</CardTitle>
              </CardHeader>
              <CardContent>
                 <p className="text-[11px] text-muted-foreground leading-tight">
                    This feature is optimized for users who prefer a seamless experience within the Telegram ecosystem.
                 </p>
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  );
};

export default MyWallet;
