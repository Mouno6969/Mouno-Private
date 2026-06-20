import React from 'react';
import { Badge } from '../ui/badge';

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'success' | 'warning' | 'info' | 'outline';

/**
 * Maps domain status strings to a consistent semantic Badge variant so every
 * page renders the same status the same way.
 */
const STATUS_VARIANT: Record<string, BadgeVariant> = {
  // success-ish
  completed: 'success',
  complete: 'success',
  success: 'success',
  paid: 'success',
  resolved: 'success',
  active: 'success',
  online: 'success',
  approved: 'success',
  confirmed: 'success',
  sent: 'success',
  filled: 'success',
  // pending / warning
  pending: 'warning',
  processing: 'warning',
  open: 'warning',
  waiting: 'warning',
  waiting_payment: 'warning',
  paused: 'warning',
  scheduled: 'warning',
  review: 'warning',
  // info / neutral live states
  triggered: 'info',
  partial: 'info',
  // error / destructive
  failed: 'destructive',
  error: 'destructive',
  cancelled: 'destructive',
  canceled: 'destructive',
  rejected: 'destructive',
  closed: 'destructive',
  expired: 'destructive',
  // info / neutral
  new: 'info',
  info: 'info',
  draft: 'secondary',
};

interface StatusBadgeProps {
  status: string;
  /** Optional display label (defaults to the status string, capitalized). */
  label?: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, className }) => {
  const key = String(status || '').toLowerCase().trim();
  const variant = STATUS_VARIANT[key] ?? 'secondary';
  // Default label: prettify snake_case (waiting_payment -> "Waiting payment").
  const pretty = status ? status.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase()) : '—';
  const text = label ?? pretty;
  return (
    <Badge variant={variant} className={className}>
      {text}
    </Badge>
  );
};

export default StatusBadge;
