import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { TOKEN_LIST, TOKEN_MAP } from '../../constants/tokens';

interface TokenSelectProps {
  value: string;
  onChange: (symbol: string) => void;
  className?: string;
  exclude?: string;
}

export const TokenLogo: React.FC<{ symbol: string; size?: number; className?: string }> = ({ symbol, size = 20, className = '' }) => {
  const token = TOKEN_MAP[symbol];
  if (!token) return <span className={className}>🔗</span>;
  return (
    <img
      src={token.logo}
      alt={token.name}
      width={size}
      height={size}
      className={`rounded-full inline-block ${className}`}
      loading="lazy"
    />
  );
};

const TokenSelect: React.FC<TokenSelectProps> = ({ value, onChange, className = '', exclude }) => {
  const options = TOKEN_LIST.filter((t) => t.symbol !== exclude);
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className={`h-12 rounded-xl bg-card border-muted font-bold ${className}`}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((token) => (
          <SelectItem key={token.symbol} value={token.symbol}>
            <span className="flex items-center gap-2">
              <TokenLogo symbol={token.symbol} size={18} />
              <span className="font-bold">{token.symbol}</span>
              <span className="text-muted-foreground text-xs font-normal">{token.name}</span>
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default TokenSelect;
