import React from 'react';

interface MarqueeProps {
  children: React.ReactNode;
  speed?: number;
  /** Only pauses on true mouse hover (fine pointer). Touch never pauses the scroll. */
  pauseOnHover?: boolean;
  className?: string;
  containerClassName?: string;
}

const Marquee: React.FC<MarqueeProps> = ({
  children,
  speed = 20,
  pauseOnHover = false,
  className = '',
  containerClassName = 'bg-secondary/40 border-y border-border py-1',
}) => {
  const pauseClass = pauseOnHover
    ? '[@media(hover:hover)_and_(pointer:fine)]:hover:[animation-play-state:paused]'
    : '';

  return (
    <div className={`overflow-hidden select-none ${containerClassName} ${className}`}>
      <div
        className={`flex w-max animate-marquee pointer-events-none ${pauseClass}`}
        style={{ animationDuration: `${speed}s` }}
      >
        <div className="flex shrink-0 items-center gap-4">{children}</div>
        <div className="flex shrink-0 items-center gap-4" aria-hidden="true">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Marquee;