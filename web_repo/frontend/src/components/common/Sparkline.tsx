import React, { useId } from 'react';
import { cn } from '../../lib/utils';

interface SparklineProps {
  /** Ordered series of values (oldest → newest). */
  data: number[];
  width?: number;
  height?: number;
  /** Force a color; otherwise derived from trend (last vs first). */
  trend?: 'up' | 'down' | 'auto';
  /** Fill the area under the line. */
  area?: boolean;
  className?: string;
  'aria-label'?: string;
}

/**
 * Lightweight inline SVG sparkline — no chart library overhead, sized for
 * table rows and cards. Color follows the trend using semantic tokens
 * (success/destructive) so it stays on-theme. Renders nothing for <2 points.
 */
export const Sparkline: React.FC<SparklineProps> = ({
  data,
  width = 72,
  height = 24,
  trend = 'auto',
  area = true,
  className,
  'aria-label': ariaLabel,
}) => {
  const gradientId = useId();
  // Drop non-finite points (CoinGecko occasionally returns null/NaN for thin
  // coins); an interior NaN would otherwise yield a malformed, invisible path.
  const series = (data ?? []).filter((v) => Number.isFinite(v));
  if (series.length < 2) {
    return <span className={cn('inline-block', className)} style={{ width, height }} aria-hidden="true" />;
  }

  const min = Math.min(...series);
  const max = Math.max(...series);
  const range = max - min || 1;
  const stepX = width / (series.length - 1);
  const pad = 2;
  const usableH = height - pad * 2;

  const points = series.map((v, i) => {
    const x = i * stepX;
    const y = pad + usableH - ((v - min) / range) * usableH;
    return [x, y] as const;
  });

  const line = points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ');
  const fill = `${line} L${width},${height} L0,${height} Z`;

  const dir = trend === 'auto' ? (series[series.length - 1] >= series[0] ? 'up' : 'down') : trend;
  const stroke = dir === 'up' ? 'hsl(var(--success))' : 'hsl(var(--destructive))';

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={cn('overflow-visible', className)}
      role="img"
      aria-label={ariaLabel ?? `${dir === 'up' ? 'Upward' : 'Downward'} trend`}
      preserveAspectRatio="none"
    >
      {area && (
        <>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={stroke} stopOpacity="0.25" />
              <stop offset="100%" stopColor={stroke} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={fill} fill={`url(#${gradientId})`} />
        </>
      )}
      <path d={line} fill="none" stroke={stroke} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
};

export default Sparkline;
