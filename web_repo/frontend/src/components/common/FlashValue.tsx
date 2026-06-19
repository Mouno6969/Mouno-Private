import React, { useEffect, useRef, useState } from 'react';
import { cn } from '../../lib/utils';

interface FlashValueProps {
  /** The numeric value driving the flash (compared to its previous value). */
  value: number | null | undefined;
  children: React.ReactNode;
  className?: string;
  /** Flash duration in ms. */
  duration?: number;
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
}) => {
  const prev = useRef<number | null | undefined>(value);
  const [flash, setFlash] = useState<'up' | 'down' | null>(null);

  useEffect(() => {
    const reduce =
      typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    if (
      !reduce &&
      typeof value === 'number' &&
      typeof prev.current === 'number' &&
      value !== prev.current
    ) {
      setFlash(value > prev.current ? 'up' : 'down');
      const id = window.setTimeout(() => setFlash(null), duration);
      prev.current = value;
      return () => window.clearTimeout(id);
    }
    prev.current = value;
  }, [value, duration]);

  return (
    <span
      className={cn(
        'rounded transition-colors duration-300',
        flash === 'up' && 'bg-success/20',
        flash === 'down' && 'bg-destructive/20',
        className
      )}
    >
      {children}
    </span>
  );
};

export default FlashValue;
