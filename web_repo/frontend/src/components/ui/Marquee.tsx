import React from 'react';
import { cn } from '../../lib/utils';

interface MarqueeProps {
  children: React.ReactNode;
  direction?: 'left' | 'right';
  pauseOnHover?: boolean;
  className?: string;
  duration?: string;
}

const Marquee: React.FC<MarqueeProps> = ({
  children,
  direction = 'left',
  pauseOnHover = false,
  className,
  duration = '40s',
}) => {
  return (
    <div
      className={cn(
        'group flex overflow-hidden p-2 [--duration:40s]',
        className
      )}
      style={{ '--duration': duration } as React.CSSProperties}
    >
      <div
        className={cn(
          'flex shrink-0 justify-around gap-4 min-w-full',
          direction === 'left' ? 'animate-marquee' : 'animate-marquee-reverse',
          pauseOnHover && 'group-hover:[animation-play-state:paused]'
        )}
      >
        {children}
        {children}
      </div>
      <div
        className={cn(
          'flex shrink-0 justify-around gap-4 min-w-full',
          direction === 'left' ? 'animate-marquee' : 'animate-marquee-reverse',
          pauseOnHover && 'group-hover:[animation-play-state:paused]'
        )}
        aria-hidden="true"
      >
        {children}
        {children}
      </div>
    </div>
  );
};

export default Marquee;
