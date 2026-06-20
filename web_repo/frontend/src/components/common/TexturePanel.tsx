import React from 'react';
import { cn } from '../../lib/utils';

type Variant = 'primary' | 'success' | 'plain';
type Texture = 'dots' | 'dots-fine' | 'none';

interface TexturePanelProps {
  children: React.ReactNode;
  className?: string;
  /** Accent color family for glow + dot tint. */
  variant?: Variant;
  /** Background dot texture density. */
  texture?: Texture;
  /** Add a soft top glow bloom behind the content. */
  glow?: boolean;
  /** Add the slow CRT scanline sweep. */
  scanline?: boolean;
  /** Add the slow aurora hue-drift backdrop (showpiece surfaces only). */
  aurora?: boolean;
  /** Gradient hairline accent along the top edge. */
  accentTop?: boolean;
  /** Use the stronger glass surface. */
  strong?: boolean;
}

/**
 * The Apex "hero value" surface: a glass panel with an optional dot-matrix
 * backdrop, accent glow, scanline, and aurora — all theme-token driven and
 * reduced-motion safe (global CSS rule neutralizes the animations). Encapsulates
 * the recipe so the showpiece cards across the app stay consistent.
 */
export const TexturePanel: React.FC<TexturePanelProps> = ({
  children,
  className,
  variant = 'primary',
  texture = 'dots',
  glow = false,
  scanline = false,
  aurora = false,
  accentTop = false,
  strong = false,
}) => {
  const dotClass =
    texture === 'none'
      ? null
      : variant === 'primary' && texture === 'dots'
        ? 'dot-matrix-primary'
        : texture === 'dots-fine'
          ? 'dot-matrix-fine'
          : 'dot-matrix';

  const glowClass =
    variant === 'success' ? 'glow-success' : variant === 'plain' ? 'glow-primary' : 'glow-primary';

  const borderTint =
    variant === 'success' ? 'border-success/25' : variant === 'plain' ? 'border-border' : 'border-primary/20';

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-2xl border',
        strong ? 'glass-strong' : 'glass-panel',
        borderTint,
        accentTop && 'accent-top',
        className,
      )}
    >
      {aurora && <div className="aurora" aria-hidden="true" />}
      {dotClass && (
        <div className={cn('absolute inset-0 pointer-events-none opacity-60 dot-matrix-fade-top', dotClass)} aria-hidden="true" />
      )}
      {glow && (
        <div
          className={cn('absolute -top-20 left-1/2 -translate-x-1/2 h-40 w-[26rem] max-w-[120%] pointer-events-none', glowClass)}
          aria-hidden="true"
        />
      )}
      {scanline && <div className="scanline" aria-hidden="true" />}
      <div className="relative">{children}</div>
    </div>
  );
};

export default TexturePanel;
