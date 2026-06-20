import React, { useEffect, useRef, useState } from 'react';
import { cn } from '../../lib/utils';

interface FlashValueProps {
  /** The numeric value driving the flash (compared to its previous value). */
  value: number | null | undefined;
  children: React.ReactNode;
  className?: string;
  /** Flash duration in ms. */
  duration?: number;
  /** Wrapper element — use "div" when wrapping block children (e.g. a <p>). */
  as?: 'span' | 'div';
}

/**
 * Wraps a live value and briefly flashes a subtle success/destructive tint
 * when the value increases/decreases — a "live ticker" feel for prices and
 * rates. Respects prefers-reduced-motion (no flash when reduced).
 */
export const FlashValue: React.FC<FlashValueProps> = ({
  value,
  children,
  className,
  duration = 700,
  as: Tag = 'span',
}) => {
  const prev = useRef<number | null | undefined>(value);
  const [flash, setFlash] = useState<'up' | 'down' | null>(null);

  useEffect(() => {
    const reduce =
      typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    const isNum = (n: unknown): n is number => typeof n === 'number' && Number.isFinite(n);
    const shouldFlash =
      !reduce && isNum(value) && isNum(prev.current) && value !== prev.current;

    if (shouldFlash) {
      setFlash((value as number) > (prev.current as number) ? 'up' : 'down');
    }
    // Only remember finite values so a transient null/NaN can't poison the
    // next comparison (which would otherwise fire a spurious flash).
    if (isNum(value)) prev.current = value;

    if (!shouldFlash) return;
    const id = window.setTimeout(() => setFlash(null), duration);
    return () => window.clearTimeout(id);
  }, [value, duration]);

  return (
    <Tag
      className={cn(
        'rounded transition-colors duration-300',
        flash === 'up' && 'bg-success/20',
        flash === 'down' && 'bg-destructive/20',
        className
      )}
    >
      {children}
    </Tag>
  );
};

export default FlashValue;
