import React from 'react';
import { cn } from '../../lib/utils';

type Variant = 'primary' | 'success' | 'plain';
type Texture = 'dots' | 'dots-fine' | 'none';

interface TexturePanelProps {
  children: React.ReactNode;
  className?: string;
  /** Accent color family for border tint. */
  variant?: Variant;
  /** Background dot texture density. */
  texture?: Texture;
  /** Add a soft top glow bloom behind the content. */
  glow?: boolean;
  /** Add the slow CRT scanline sweep. (disabled in new design) */
  scanline?: boolean;
  /** Add the slow aurora hue-drift backdrop. */
  aurora?: boolean;
  /** Gradient hairline accent along the top edge. */
  accentTop?: boolean;
  /** Use the stronger glass surface. */
  strong?: boolean;
}

/**
 * A clean panel surface with optional subtle accent effects.
 * Toned down from the original "Apex" treatment for better readability.
 */
export const TexturePanel: React.FC<TexturePanelProps> = ({
  children,
  className,
  variant = 'primary',
  texture = 'none',
  glow = false,
  scanline = false,
  aurora = false,
  accentTop = false,
  strong = false,
}) => {
  const borderTint =
    variant === 'success' ? 'border-success/25' : variant === 'plain' ? 'border-border' : 'border-primary/20';

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl border',
        strong ? 'glass-strong' : 'glass-panel',
        borderTint,
        accentTop && 'accent-top',
        className,
      )}
    >
      {aurora && <div className="aurora" aria-hidden="true" />}
      {glow && (
        <div
          className="absolute -top-20 left-1/2 -translate-x-1/2 h-32 w-[20rem] max-w-[100%] pointer-events-none glow-primary"
          aria-hidden="true"
        />
      )}
      <div className="relative">{children}</div>
    </div>
  );
};

export default TexturePanel;
