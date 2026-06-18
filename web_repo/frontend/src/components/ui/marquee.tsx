import React from 'react';

interface MarqueeProps {
  children: React.ReactNode;
  speed?: number;
  pauseOnHover?: boolean;
  className?: string;
  containerClassName?: string;
}

const Marquee: React.FC<MarqueeProps> = ({
  children,
  speed = 20,
  pauseOnHover = true,
  className = "",
  containerClassName = "bg-secondary/40 border-y border-border py-1"
}) => {
  return (
    <div className={`overflow-hidden flex select-none ${containerClassName} ${className}`}>
      <div
        className={`flex min-w-full shrink-0 items-center justify-around gap-4 animate-marquee ${pauseOnHover ? 'hover:[animation-play-state:paused]' : ''}`}
        style={{ animationDuration: `${speed}s` }}
      >
        {children}
        {children}
      </div>
      <div
        aria-hidden="true"
        className={`flex min-w-full shrink-0 items-center justify-around gap-4 animate-marquee ${pauseOnHover ? 'hover:[animation-play-state:paused]' : ''}`}
        style={{ animationDuration: `${speed}s` }}
      >
        {children}
        {children}
      </div>
    </div>
  );
};

export default Marquee;
