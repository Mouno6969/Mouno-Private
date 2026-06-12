import React from 'react';
import { cn } from '../../lib/utils';

/**
 * Base skeleton block with a shimmer sweep. Compose these to mirror the shape
 * of whatever is loading (cards, rows, table cells, etc).
 */
export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => {
  return (
    <div
      aria-hidden="true"
      className={cn('skeleton-shimmer rounded-md', className)}
      {...props}
    />
  );
};

/** A single text line skeleton. */
export const SkeletonText: React.FC<{ className?: string }> = ({ className }) => (
  <Skeleton className={cn('h-4 w-full', className)} />
);

/** Skeleton for a stat/summary card used on the dashboard. */
export const SkeletonStatCard: React.FC = () => (
  <div className="rounded-lg border border-primary/10 bg-card/50 p-3 sm:p-4">
    <div className="flex items-center gap-2.5">
      <Skeleton className="h-8 w-8 shrink-0 rounded-lg" />
      <div className="min-w-0 flex-1 space-y-2">
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-5 w-2/3" />
      </div>
    </div>
  </div>
);

/** Skeleton row for list-style cards (tx log, orders, balances). */
export const SkeletonListRow: React.FC<{ className?: string }> = ({ className }) => (
  <div
    className={cn(
      'flex items-center justify-between gap-3 rounded-lg border border-primary/10 bg-card/50 p-4',
      className
    )}
  >
    <div className="flex items-center gap-3">
      <Skeleton className="h-7 w-7 rounded-full" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-3 w-20" />
      </div>
    </div>
    <div className="space-y-2 text-right">
      <Skeleton className="ml-auto h-4 w-20" />
      <Skeleton className="ml-auto h-3 w-12" />
    </div>
  </div>
);

/** Skeleton for a table with the given number of rows/columns. */
export const SkeletonTableRows: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 5,
  cols = 4,
}) => (
  <>
    {Array.from({ length: rows }).map((_, r) => (
      <tr key={r} className="border-muted/50">
        {Array.from({ length: cols }).map((_, c) => (
          <td key={c} className="px-4 py-3.5">
            <Skeleton className="h-4 w-full max-w-[120px]" />
          </td>
        ))}
      </tr>
    ))}
  </>
);

export default Skeleton;
