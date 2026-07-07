import React, { useState } from 'react';

interface SwapAssetLogoProps {
  src?: string | null;
  symbol?: string;
  name?: string;
  size?: number;
  className?: string;
}

/** Renders a chain or token logo from LI.FI, with a symbol fallback badge. */
export const SwapAssetLogo: React.FC<SwapAssetLogoProps> = ({
  src,
  symbol,
  name,
  size = 24,
  className = '',
}) => {
  const [failed, setFailed] = useState(false);
  const label = (symbol || name || '?').toUpperCase();

  if (src && !failed) {
    return (
      <img
        src={src}
        alt={name || symbol || 'asset'}
        width={size}
        height={size}
        className={`rounded-full object-cover bg-muted shrink-0 ${className}`}
        loading="lazy"
        onError={() => setFailed(true)}
      />
    );
  }

  return (
    <span
      className={`inline-flex items-center justify-center rounded-full bg-muted font-bold text-muted-foreground shrink-0 ${className}`}
      style={{ width: size, height: size, fontSize: Math.max(8, size * 0.34) }}
      title={name || symbol}
    >
      {label.slice(0, 3)}
    </span>
  );
};