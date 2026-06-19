import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '../../lib/utils';

interface PriceChangeProps {
  /** Percentage (or absolute) change value. Sign drives direction. */
  value: number | null | undefined;
  /** Render as a percentage (appends %). Defaults to true. */
  percent?: boolean;
  /** Decimal places. Defaults to 2. */
  decimals?: number;
  /** Show the trending arrow icon. Defaults to true. */
  icon?: boolean;
  /** Placeholder shown when value is null/undefined. */
  placeholder?: string;
  className?: string;
}

/**
 * Color-blind-safe gain/loss indicator: pairs the semantic color with BOTH a
 * directional arrow and a +/- sign, so meaning never relies on color alone.
 */
export const PriceChange: React.FC<PriceChangeProps> = ({
  value,
  percent = true,
  decimals = 2,
  icon = true,
  placeholder = '—',
  className,
}) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return <span className="text-xs text-muted-foreground">{placeholder}</span>;
  }
  const up = value >= 0;
  const Arrow = up ? TrendingUp : TrendingDown;
  return (
    <span
      className={cn(
        'num inline-flex items-center gap-1 font-medium',
        up ? 'text-success' : 'text-destructive',
        className
      )}
    >
      {icon && <Arrow className="h-3.5 w-3.5" aria-hidden="true" />}
      <span>
        {up ? '+' : '−'}
        {Math.abs(value).toFixed(decimals)}
        {percent ? '%' : ''}
      </span>
    </span>
  );
};

export default PriceChange;
