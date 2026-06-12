import * as React from 'react';
import { Loader2 } from 'lucide-react';
import { Button, type ButtonProps } from './button';
import { cn } from '../../lib/utils';

export interface AsyncButtonProps extends ButtonProps {
  /** When true, shows a spinner and disables the button to prevent double-submit. */
  loading?: boolean;
  /** Optional label shown next to the spinner while loading. */
  loadingText?: React.ReactNode;
}

/**
 * Button that handles async actions: while `loading` it shows a spinner and is
 * disabled so the user cannot double-submit (Buy, Swap, Payout, etc).
 */
const AsyncButton = React.forwardRef<HTMLButtonElement, AsyncButtonProps>(
  ({ loading = false, loadingText, disabled, children, className, ...props }, ref) => {
    return (
      <Button
        ref={ref}
        disabled={disabled || loading}
        aria-busy={loading}
        className={cn(className)}
        {...props}
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            {loadingText ?? children}
          </>
        ) : (
          children
        )}
      </Button>
    );
  }
);
AsyncButton.displayName = 'AsyncButton';

export { AsyncButton };
export default AsyncButton;
