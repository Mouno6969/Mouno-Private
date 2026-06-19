import React, { useEffect, useState } from 'react';

interface RelativeTimeProps {
  /** ISO string, epoch ms, or Date. */
  value: string | number | Date | null | undefined;
  className?: string;
}

function toDate(value: string | number | Date): Date | null {
  const d = value instanceof Date ? value : new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

function relative(from: Date, now: Date): string {
  const secs = Math.round((now.getTime() - from.getTime()) / 1000);
  const abs = Math.abs(secs);
  const fmt = (n: number, unit: Intl.RelativeTimeFormatUnit) =>
    new Intl.RelativeTimeFormat('en', { numeric: 'auto' }).format(-Math.sign(secs) * Math.round(n), unit);

  if (abs < 45) return 'just now';
  if (abs < 3600) return fmt(abs / 60, 'minute');
  if (abs < 86400) return fmt(abs / 3600, 'hour');
  if (abs < 2592000) return fmt(abs / 86400, 'day');
  if (abs < 31536000) return fmt(abs / 2592000, 'month');
  return fmt(abs / 31536000, 'year');
}

/**
 * Renders a human-readable relative time ("2 minutes ago") that self-updates
 * every 30s, with the full localized date/time available on hover (title attr).
 */
export const RelativeTime: React.FC<RelativeTimeProps> = ({ value, className }) => {
  const [, setTick] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => setTick((n) => n + 1), 30_000);
    return () => window.clearInterval(id);
  }, []);

  if (value == null) return <span className={className}>—</span>;
  const date = toDate(value);
  if (!date) return <span className={className}>—</span>;

  return (
    <time dateTime={date.toISOString()} title={date.toLocaleString()} className={className}>
      {relative(date, new Date())}
    </time>
  );
};

export default RelativeTime;
