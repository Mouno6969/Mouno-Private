import React from 'react';
import { Skeleton } from '../ui/skeleton';
import { Card, CardContent } from '../ui/card';
import { cn } from '../../lib/utils';

interface LoadingSkeletonProps {
  /** Preset shape to render. */
  variant?: 'list' | 'cards' | 'table' | 'stat';
  /** Number of repeated rows/cards. */
  rows?: number;
  className?: string;
}

/** Standard loading placeholders so every page's loading state looks the same. */
export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  variant = 'list',
  rows = 5,
  className,
}) => {
  if (variant === 'stat') {
    return (
      <div className={cn('grid gap-4 sm:grid-cols-2 lg:grid-cols-3', className)}>
        {Array.from({ length: rows }).map((_, i) => (
          <Card key={i} className="bg-card/50">
            <CardContent className="p-5 space-y-3">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-7 w-28" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (variant === 'cards') {
    return (
      <div className={cn('grid gap-4 sm:grid-cols-2 lg:grid-cols-3', className)}>
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-2xl" />
        ))}
      </div>
    );
  }

  if (variant === 'table') {
    return (
      <div className={cn('space-y-2', className)}>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-9 w-9 rounded-full shrink-0" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-16 shrink-0" />
          </div>
        ))}
      </div>
    );
  }

  // list
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full rounded-xl" />
      ))}
    </div>
  );
};

export default LoadingSkeleton;
