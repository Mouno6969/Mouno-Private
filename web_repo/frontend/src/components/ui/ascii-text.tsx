import React, { useState, useEffect } from 'react';
import { cn } from '../../lib/utils';

interface ASCIITextProps {
  text: string;
  className?: string;
  animationDelay?: number;
  blockSize?: number;
  glitch?: boolean;
}

const fontMap: Record<string, string[]> = {
  'A': [
    '  AAA  ',
    ' A   A ',
    ' AAAAA ',
    ' A   A ',
    ' A   A '
  ],
  'B': [
    ' BBBB  ',
    ' B   B ',
    ' BBBB  ',
    ' B   B ',
    ' BBBB  '
  ],
  'C': [
    '  CCC  ',
    ' C     ',
    ' C     ',
    ' C     ',
    '  CCC  '
  ],
  'D': [
    ' DDDD  ',
    ' D   D ',
    ' D   D ',
    ' D   D ',
    ' DDDD  '
  ],
  'E': [
    ' EEEEE ',
    ' E     ',
    ' EEEE  ',
    ' E     ',
    ' EEEEE '
  ],
  'F': [
    ' FFFFF ',
    ' F     ',
    ' FFFF  ',
    ' F     ',
    ' F     '
  ],
  'G': [
    '  GGGG ',
    ' G     ',
    ' G  GG ',
    ' G   G ',
    '  GGG  '
  ],
  'H': [
    ' H   H ',
    ' H   H ',
    ' HHHHH ',
    ' H   H ',
    ' H   H '
  ],
  'I': [
    '  III  ',
    '   I   ',
    '   I   ',
    '   I   ',
    '  III  '
  ],
  'J': [
    '  JJJJ ',
    '     J ',
    '     J ',
    ' J   J ',
    '  JJJ  '
  ],
  'K': [
    ' K   K ',
    ' K  K  ',
    ' KKK   ',
    ' K  K  ',
    ' K   K '
  ],
  'L': [
    ' L     ',
    ' L     ',
    ' L     ',
    ' L     ',
    ' LLLLL '
  ],
  'M': [
    ' M   M ',
    ' MM MM ',
    ' M M M ',
    ' M   M ',
    ' M   M '
  ],
  'N': [
    ' N   N ',
    ' NN  N ',
    ' N N N ',
    ' N  NN ',
    ' N   N '
  ],
  'O': [
    '  OOO  ',
    ' O   O ',
    ' O   O ',
    ' O   O ',
    '  OOO  '
  ],
  'P': [
    ' PPPP  ',
    ' P   P ',
    ' PPPP  ',
    ' P     ',
    ' P     '
  ],
  'Q': [
    '  QQQ  ',
    ' Q   Q ',
    ' Q   Q ',
    ' Q  Q  ',
    '  QQ Q '
  ],
  'R': [
    ' RRRR  ',
    ' R   R ',
    ' RRRR  ',
    ' R  R  ',
    ' R   R '
  ],
  'S': [
    '  SSS  ',
    ' S     ',
    '  SSS  ',
    '     S ',
    '  SSS  '
  ],
  'T': [
    ' TTTTT ',
    '   T   ',
    '   T   ',
    '   T   ',
    '   T   '
  ],
  'U': [
    ' U   U ',
    ' U   U ',
    ' U   U ',
    ' U   U ',
    '  UUU  '
  ],
  'V': [
    ' V   V ',
    ' V   V ',
    ' V   V ',
    '  V V  ',
    '   V   '
  ],
  'W': [
    ' W   W ',
    ' W   W ',
    ' W W W ',
    ' WW WW ',
    ' W   W '
  ],
  'X': [
    ' X   X ',
    '  X X  ',
    '   X   ',
    '  X X  ',
    ' X   X '
  ],
  'Y': [
    ' Y   Y ',
    '  Y Y  ',
    '   Y   ',
    '   Y   ',
    '   Y   '
  ],
  'Z': [
    ' ZZZZZ ',
    '    Z  ',
    '   Z   ',
    '  Z    ',
    ' ZZZZZ '
  ],
  ' ': [
    '       ',
    '       ',
    '       ',
    '       ',
    '       '
  ],
  '.': [
    '       ',
    '       ',
    '       ',
    '       ',
    '   .   '
  ],
};

export const ASCIIText: React.FC<ASCIITextProps> = ({
  text,
  className,
  animationDelay = 100,
  blockSize = 2,
  glitch = false
}) => {
  const [displayText, setDisplayText] = useState('');
  const [isAnimating, setIsAnimating] = useState(true);

  useEffect(() => {
    let index = 0;
    setIsAnimating(true);

    const interval = setInterval(() => {
      if (index <= text.length) {
        setDisplayText(text.substring(0, index));
        index++;
      } else {
        setIsAnimating(false);
        clearInterval(interval);
      }
    }, animationDelay);

    return () => clearInterval(interval);
  }, [text, animationDelay]);

  const renderASCIIChar = (char: string) => {
    const lines = fontMap[char.toUpperCase()] || fontMap[' '];
    return (
      <div key={char} className="inline-block">
        {lines.map((line, idx) => (
          <div
            key={idx}
            className={cn(
              'font-mono text-[0.5rem] leading-none tracking-tighter',
              glitch && isAnimating && 'animate-pulse',
              className
            )}
            style={{
              letterSpacing: '0.05em',
              lineHeight: '0.8',
            }}
          >
            {line.split('').map((pixel, pidx) => (
              <span
                key={pidx}
                className={cn(
                  'inline-block w-[0.3em] h-[0.4em]',
                  pixel === char.toUpperCase() || pixel === '.' || pixel === ' '
                    ? 'bg-current'
                    : 'bg-transparent'
                )}
                style={{
                  opacity: pixel === ' ' ? 0 : 1,
                }}
              />
            ))}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="inline-block font-mono">
      {displayText.split('').map((char, idx) => (
        <span
          key={idx}
          className={cn(
            'inline-block transition-all duration-300',
            glitch && idx === displayText.length - 1 && 'animate-pulse'
          )}
        >
          {renderASCIIChar(char)}
        </span>
      ))}
      {isAnimating && (
        <span className="inline-block ml-0.5 animate-pulse">█</span>
      )}
    </div>
  );
};

export default ASCIIText;
