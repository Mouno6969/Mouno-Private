import React from 'react';

interface MarqueeProps {
  children: React.ReactNode;
  speed?: number;
  pauseOnHover?: boolean;
  className?: string;
}

const Marquee: React.FC<MarqueeProps> = ({
  children,
  speed = 20,
  pauseOnHover = true,
  className = ""
}) => {
  return (
    <div className={`overflow-hidden flex bg-white/5 border-y border-white/10 py-1 select-none ${className}`}>
      <div
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
