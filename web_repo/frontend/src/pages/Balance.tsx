import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Coins, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { NETWORK_LIST, NetworkLogo } from '../constants/networks';



const Balance: React.FC = () => {
  const { token } = useAuth();
  const [balances, setBalances] = useState<Record<string, string | number> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchBalance = () => {
    setLoading(true);
    setError('');
    fetch(`${process.env.REACT_APP_API_URL || ''}/api/balance`, { headers: token ? { 'Authorization': `Bearer ${token}` } : {} })
      .then(r => r.json())
      .then(d => {
        if (d.balances) {
          setBalances(d.balances);
        } else {
          setError(d.message || 'Failed to load balances');
        }
      })
      .catch((err: Error) => setError(err?.message || 'Failed to connect to server'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchBalance(); }, []);

  // Surface async fetch errors into render so the ErrorBoundary can catch them.
  if (error) throw new Error(error);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Coins className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Balance</h1>
            <p className="text-muted-foreground text-sm">Live crypto balance across all networks</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={fetchBalance} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {loading && !balances && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {balances && (
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle className="text-lg">Network Balances</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {NETWORK_LIST.map((net) => (
                <div key={net.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                  <div className="flex items-center gap-3">
                    <NetworkLogo id={net.id} size={24} />
                    <span className="text-sm font-medium">{net.name} {net.asset}</span>
                  </div>
                  <Badge variant="outline" className="font-mono text-sm">
                    {balances[net.id] !== undefined ? String(balances[net.id]) : 'N/A'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Balance;
