import React, { useState, useRef, useEffect } from 'react';
import { Check, Copy } from 'lucide-react';
import { cn } from '../../lib/utils';

interface CopyButtonProps {
  /** The text written to the clipboard. */
  value: string;
  /** Accessible label / tooltip (e.g. "Copy wallet address"). */
  label?: string;
  className?: string;
  /** Show a small "Copied!" text label next to the icon. */
  withText?: boolean;
}

/**
 * Icon button that copies `value` and shows a transient checkmark + "Copied!"
 * confirmation. Used for wallet addresses, order IDs, bKash numbers, etc.
 */
export const CopyButton: React.FC<CopyButtonProps> = ({ value, label = 'Copy', className, withText = false }) => {
  const [copied, setCopied] = useState(false);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  const handleCopy = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked — silently ignore */
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={copied ? 'Copied' : label}
      title={label}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        className,
      )}
    >
      {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
      {withText && (
        <span className={cn('text-xs', copied && 'text-success')}>{copied ? 'Copied!' : 'Copy'}</span>
      )}
    </button>
  );
};

export default CopyButton;
