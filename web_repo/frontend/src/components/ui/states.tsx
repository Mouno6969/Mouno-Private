import React from 'react';
import { Inbox, AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './button';
import { cn } from '../../lib/utils';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

/** Friendly placeholder for lists/sections that have no data yet. */
export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => (
  <div
    className={cn(
      'flex flex-col items-center justify-center gap-3 px-6 py-12 text-center',
      className
    )}
  >
    <div className="rounded-full bg-muted p-3 text-muted-foreground">
      {icon ?? <Inbox className="h-6 w-6" aria-hidden="true" />}
    </div>
    <div className="space-y-1">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      {description && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
    </div>
    {action}
  </div>
);

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  retrying?: boolean;
  /** Localized label for the retry button (defaults to English "Retry"). */
  retryLabel?: string;
  className?: string;
}

/** Error placeholder with an optional Retry action. */
export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  description = 'We could not load this data. Please try again.',
  onRetry,
  retrying = false,
  retryLabel = 'Retry',
  className,
}) => (
  <div
    role="alert"
    className={cn(
      'flex flex-col items-center justify-center gap-3 px-6 py-12 text-center',
      className
    )}
  >
    <div className="rounded-full bg-destructive/10 p-3 text-destructive">
      <AlertTriangle className="h-6 w-6" aria-hidden="true" />
    </div>
    <div className="space-y-1">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
    {onRetry && (
      <Button variant="outline" size="sm" onClick={onRetry} disabled={retrying}>
        <RefreshCw
          className={cn('h-4 w-4', retrying && 'animate-spin')}
          aria-hidden="true"
        />
        {retryLabel}
      </Button>
    )}
  </div>
);

export default EmptyState;
