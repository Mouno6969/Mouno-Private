import React, { useEffect, useState } from 'react';
import { cn } from '../../lib/utils';

interface FreshnessProps {
  /** When the data was last successfully updated. */
  updatedAt: Date | number | string | null | undefined;
  /** Seconds after which the data is considered stale (default 120s). */
  staleAfter?: number;
  /** Optional prefix label, e.g. "Prices". */
  label?: string;
  className?: string;
}

function toDate(value: Date | number | string): Date | null {
  const d = value instanceof Date ? value : new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

function ago(seconds: number): string {
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${Math.round(seconds)}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

/**
 * Compact "Prices last updated 2m ago" indicator with a live dot that turns
 * from success → warning once the data crosses the stale threshold. Self-updates
 * every 15s. Pairs a color with text so it stays color-blind safe.
 */
export const Freshness: React.FC<FreshnessProps> = ({
  updatedAt,
  staleAfter = 120,
  label = 'Updated',
  className,
}) => {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = window.setInterval(() => setTick((n) => n + 1), 15_000);
    return () => window.clearInterval(id);
  }, []);

  const date = updatedAt == null ? null : toDate(updatedAt);
  if (!date) {
    return (
      <span className={cn('inline-flex items-center gap-1.5 text-[10px] text-muted-foreground', className)}>
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50" />
        {label} —
      </span>
    );
  }

  const seconds = Math.max(0, (Date.now() - date.getTime()) / 1000);
  const stale = seconds > staleAfter;

  return (
    <span
      className={cn('inline-flex items-center gap-1.5 text-[10px] tabular-nums', stale ? 'text-warning' : 'text-muted-foreground', className)}
      title={date.toLocaleString()}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', stale ? 'bg-warning' : 'bg-success animate-pulse')} />
      {label} {ago(seconds)}
    </span>
  );
};

export default Freshness;
