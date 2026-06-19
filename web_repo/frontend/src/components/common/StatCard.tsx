import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Skeleton } from '../ui/skeleton';
import { cn } from '../../lib/utils';

interface StatCardProps {
  label: string;
  value: React.ReactNode;
  icon?: React.ReactNode;
  /** Secondary line under the value (e.g. a PriceChange or sub-label). */
  sub?: React.ReactNode;
  loading?: boolean;
  className?: string;
}

/** Consistent metric tile used across dashboards (Portfolio, Analytics, etc). */
export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  sub,
  loading,
  className,
}) => (
  <Card className={cn('bg-card/50 backdrop-blur', className)}>
    <CardContent className="p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide font-medium text-muted-foreground">{label}</p>
        {icon && <span className="text-primary">{icon}</span>}
      </div>
      {loading ? (
        <Skeleton className="mt-2 h-7 w-28" />
      ) : (
        <p className="num mt-1 text-2xl font-extrabold tracking-tight text-foreground">{value}</p>
      )}
      {sub && <div className="mt-1">{sub}</div>}
    </CardContent>
  </Card>
);

export default StatCard;
