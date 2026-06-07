import React from 'react';

// Brand marks are recreated for display purposes.
// All trademarks remain the property of their respective owners.

export const BkashLogo: React.FC<{ className?: string }> = ({ className }) => (
  <div className={`flex items-center gap-1.5 ${className || ''}`}>
    <svg
      viewBox="0 0 48 48"
      className="h-7 w-7"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M9 8 L24 19 L17 24 Z"
        fill="#E2136E"
      />
      <path
        d="M39 8 L24 19 L31 24 Z"
        fill="#E2136E"
        opacity="0.85"
      />
      <path
        d="M17 26 L31 26 L24 40 Z"
        fill="#E2136E"
      />
    </svg>
    <span className="font-extrabold text-lg tracking-tight" style={{ color: '#E2136E' }}>
      bKash
    </span>
  </div>
);

export const LifiLogo: React.FC<{ className?: string }> = ({ className }) => (
  <div className={`flex items-center gap-2 ${className || ''}`}>
    <svg
      viewBox="0 0 64 32"
      className="h-6 w-12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M16 16c0-5 4-9 9-9s9 4 9 9-4 9-9 9-9-4-9-9z M48 16c0-5-4-9-9-9s-9 4-9 9 4 9 9 9 9-4 9-9z"
        stroke="currentColor"
        strokeWidth="4"
        className="text-foreground"
        fill="none"
      />
    </svg>
    <span className="font-extrabold text-xl tracking-tighter text-foreground">
      LI.FI
    </span>
  </div>
);
