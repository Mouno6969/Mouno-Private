import React, { useState, useEffect } from 'react';

interface AnimatedTextProps {
  text: string;
  speed?: number;
  delay?: number;
  className?: string;
  containerClassName?: string;
}

/**
 * Animated Text Component
 * Displays text with character-by-character reveal animation
 * Styled to match the crypto platform aesthetic
 */
export const AnimatedText: React.FC<AnimatedTextProps> = ({
  text,
  speed = 50,
  delay = 0,
  className = '',
  containerClassName = '',
}) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    let charIndex = 0;

    const animate = () => {
      if (charIndex < text.length) {
        setDisplayedText(text.substring(0, charIndex + 1));
        charIndex++;
        timeoutId = setTimeout(animate, speed);
      } else {
        setIsComplete(true);
      }
    };

    if (delay > 0) {
      timeoutId = setTimeout(animate, delay);
    } else {
      animate();
    }

    return () => clearTimeout(timeoutId);
  }, [text, speed, delay]);

  return (
    <div className={containerClassName}>
      <span className={className}>
        {displayedText}
        {!isComplete && (
          <span className="animate-pulse ml-0.5">▌</span>
        )}
      </span>
    </div>
  );
};

interface GlitchTextProps {
  text: string;
  className?: string;
  containerClassName?: string;
}

/**
 * Glitch Text Component
 * Creates a cyberpunk-style glitch effect for text
 */
export const GlitchText: React.FC<GlitchTextProps> = ({
  text,
  className = '',
  containerClassName = '',
}) => {
  return (
    <div className={`relative inline-block ${containerClassName}`}>
      <span className={`relative ${className}`}>
        {text}
        <span
          className="absolute left-0 top-0 w-full h-full text-primary animate-[glitch_0.3s_ease-in-out_infinite]"
          style={{
            content: `"${text}"`,
            clipPath: 'polygon(0 0, 100% 0, 100% 45%, 0 58%)',
            transform: 'translate(-2px, 2px)',
            opacity: 0.8,
          }}
          aria-hidden="true"
        >
          {text}
        </span>
        <span
          className="absolute left-0 top-0 w-full h-full text-red-500 animate-[glitch_0.3s_ease-in-out_infinite_0.15s]"
          style={{
            content: `"${text}"`,
            clipPath: 'polygon(0 60%, 100% 30%, 100% 100%, 0 100%)',
            transform: 'translate(2px, -2px)',
            opacity: 0.8,
          }}
          aria-hidden="true"
        >
          {text}
        </span>
      </span>
    </div>
  );
};

interface TypewriterTextProps {
  lines: string[];
  speed?: number;
  lineDelay?: number;
  className?: string;
  containerClassName?: string;
}

/**
 * Typewriter Text Component
 * Displays multiple lines with typewriter effect
 * One line at a time
 */
export const TypewriterText: React.FC<TypewriterTextProps> = ({
  lines,
  speed = 40,
  lineDelay = 1500,
  className = '',
  containerClassName = '',
}) => {
  const [displayedLines, setDisplayedLines] = useState<string[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    if (currentLineIndex >= lines.length) return;

    let timeoutId: NodeJS.Timeout;
    let charIndex = 0;
    const currentLine = lines[currentLineIndex];

    const animate = () => {
      if (charIndex < currentLine.length) {
        setDisplayedText(currentLine.substring(0, charIndex + 1));
        charIndex++;
        timeoutId = setTimeout(animate, speed);
      } else {
        setDisplayedLines([...displayedLines, currentLine]);
        timeoutId = setTimeout(() => {
          setCurrentLineIndex(currentLineIndex + 1);
          setDisplayedText('');
        }, lineDelay);
      }
    };

    animate();
    return () => clearTimeout(timeoutId);
  }, [currentLineIndex, lines, speed, lineDelay, displayedLines]);

  return (
    <div className={containerClassName}>
      {displayedLines.map((line, idx) => (
        <div key={idx} className={className}>
          {line}
        </div>
      ))}
      {currentLineIndex < lines.length && (
        <div className={className}>
          {displayedText}
          <span className="animate-pulse">▌</span>
        </div>
      )}
    </div>
  );
};

export default AnimatedText;
