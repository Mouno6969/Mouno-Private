import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { History, Clock, CheckCircle, ExternalLink, Search } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../context/AuthContext';
import { useOrders } from '../lib/hooks';
import type { OrderEntry } from '../types';
import { SkeletonTableRows } from '../components/ui/skeleton';
import { ErrorState } from '../components/ui/states';

const StatusBadge = ({ status }: { status: string | null | undefined }) => {
  if (!status) {
    return <Badge variant="outline">Unknown</Badge>;
  }
  switch (status.toLowerCase()) {
    case 'completed':
      return <Badge variant="success">Completed</Badge>;
    case 'pending':
      return <Badge variant="warning">Pending</Badge>;
    case 'failed':
      return <Badge variant="destructive">Failed</Badge>;
    case 'waiting_payment':
      return <Badge variant="info">Waiting Payment</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
};

const Orders: React.FC = () => {
  const { t } = useTranslation();
  const { token } = useAuth();
  const { data, error, isLoading, mutate } = useOrders(Boolean(token));
  const [searchTerm, setSearchTerm] = useState('');

  const filteredCompleted = data.completed.filter(
    (order: OrderEntry) =>
      order.order_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.network?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      false
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-500">
      <section className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-3">
            <History className="text-primary h-8 w-8" /> {t('orders')}
          </h1>
          <p className="text-muted-foreground">View and track your previous crypto purchases.</p>
        </div>
        <div className="relative w-full md:w-64">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by Order ID..."
            className="pl-9"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search orders by ID or network"
          />
        </div>
      </section>

      {/* Pending Orders */}
      {data.pending.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-xl font-bold flex items-center gap-2 text-warning">
            <Clock className="h-5 w-5 animate-pulse" /> {t('pending_orders')}
          </h2>
          <div className="grid grid-cols-1 gap-4">
            {data.pending.map((order: OrderEntry) => (
              <Card key={order.trx_id} className="border-warning/20 bg-warning/5 overflow-hidden transition-all hover:border-warning/40">
                <CardContent className="p-4 md:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-warning/10 text-warning rounded-2xl flex items-center justify-center shrink-0 border border-warning/20">
                      <Clock size={24} />
                    </div>
                    <div>
                      <p className="font-mono font-bold text-lg">{order.order_id}</p>
                      <p className="text-xs text-muted-foreground">{new Date(order.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between md:justify-end gap-8 w-full md:w-auto border-t border-border/60 md:border-none pt-4 md:pt-0">
                    <div className="text-left md:text-right">
                      <p className="font-black text-xl text-warning">৳{order.amount_bdt}</p>
                      <p className="text-xs font-bold text-muted-foreground uppercase">{order.amount_usdc} USDC • {order.network}</p>
                    </div>
                    <StatusBadge status="pending" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Completed Orders */}
      <Card className="shadow-xl border-primary/10 overflow-hidden">
        <CardHeader className="bg-muted/30 pb-4">
          <CardTitle className="text-xl flex items-center gap-2 text-success">
            <CheckCircle className="h-5 w-5" /> {t('order_history')}
          </CardTitle>
          <CardDescription>A list of your successfully processed transactions.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? (
            <ErrorState
              title="Couldn't load orders"
              description="We couldn't reach the server to fetch your order history."
              onRetry={() => mutate()}
            />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/20 hover:bg-muted/20 border-muted/50">
                    <TableHead className="w-[150px] pl-6 font-semibold uppercase text-[10px] tracking-wider">Order ID</TableHead>
                    <TableHead className="font-semibold uppercase text-[10px] tracking-wider">Network</TableHead>
                    <TableHead className="font-semibold uppercase text-[10px] tracking-wider">Amount</TableHead>
                    <TableHead className="font-semibold uppercase text-[10px] tracking-wider text-center">Status</TableHead>
                    <TableHead className="font-semibold uppercase text-[10px] tracking-wider">Date</TableHead>
                    <TableHead className="text-right pr-6 font-semibold uppercase text-[10px] tracking-wider">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <SkeletonTableRows rows={5} cols={6} />
                  ) : filteredCompleted.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6}>
                        <div className="flex flex-col items-center justify-center py-16 text-center px-4">
                          <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mb-4">
                            <History className="h-8 w-8 text-muted-foreground opacity-20" />
                          </div>
                          <p className="text-muted-foreground font-medium">No completed orders found.</p>
                          <p className="text-xs text-muted-foreground/60 max-w-[200px] mt-1">
                            {searchTerm ? 'Try a different search term.' : 'Start trading to see your transaction history here.'}
                          </p>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredCompleted.map((order: OrderEntry) => (
                      <TableRow key={order.trx_id} className="group hover:bg-primary/5 transition-colors border-muted/30">
                        <TableCell className="p-4 pl-6 font-mono font-bold text-sm">{order.order_id}</TableCell>
                        <TableCell className="p-4 uppercase text-[10px] font-black">
                          <Badge variant="outline" className="font-mono border-primary/20 bg-primary/5 text-primary">{order.network}</Badge>
                        </TableCell>
                        <TableCell className="p-4">
                          <div className="font-bold text-base">৳{order.amount_bdt}</div>
                          <div className="text-[10px] font-medium text-muted-foreground uppercase">{order.amount_usdc} USDC</div>
                        </TableCell>
                        <TableCell className="p-4 text-center"><StatusBadge status={order.status} /></TableCell>
                        <TableCell className="p-4 text-xs font-medium text-muted-foreground">{new Date(order.created_at).toLocaleDateString()}</TableCell>
                        <TableCell className="p-4 text-right pr-6">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full"
                            aria-label={`View order ${order.order_id ?? ''}`}
                          >
                            <ExternalLink size={16} />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Orders;
