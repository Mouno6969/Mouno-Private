// Common tradable assets used across the Swap experience (multi-leg swaps,
// limit orders and scheduled buys). Logos reuse the CoinGecko CDN already used
// elsewhere in the app.

export interface TokenInfo {
  symbol: string;
  name: string;
  logo: string;
}

export const TOKEN_LIST: TokenInfo[] = [
  {
    symbol: 'BTC',
    name: 'Bitcoin',
    logo: 'https://assets.coingecko.com/coins/images/1/small/bitcoin.png',
  },
  {
    symbol: 'ETH',
    name: 'Ethereum',
    logo: 'https://assets.coingecko.com/coins/images/279/small/ethereum.png',
  },
  {
    symbol: 'SOL',
    name: 'Solana',
    logo: 'https://assets.coingecko.com/coins/images/4128/small/solana.png',
  },
  {
    symbol: 'BNB',
    name: 'BNB',
    logo: 'https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png',
  },
  {
    symbol: 'USDT',
    name: 'Tether',
    logo: 'https://assets.coingecko.com/coins/images/325/small/Tether.png',
  },
  {
    symbol: 'USDC',
    name: 'USD Coin',
    logo: 'https://assets.coingecko.com/coins/images/6319/small/usdc.png',
  },
  {
    symbol: 'POL',
    name: 'Polygon',
    logo: 'https://assets.coingecko.com/coins/images/4713/small/polygon.png',
  },
  {
    symbol: 'AVAX',
    name: 'Avalanche',
    logo: 'https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png',
  },
  {
    symbol: 'TON',
    name: 'Toncoin',
    logo: 'https://assets.coingecko.com/coins/images/17980/small/ton_symbol.png',
  },
];

export const TOKEN_MAP: Record<string, TokenInfo> = Object.fromEntries(
  TOKEN_LIST.map((t) => [t.symbol, t])
);

// Rough indicative USD prices used for client-side estimates (limit order
// progress bars, schedule projections). These are illustrative defaults that
// get overridden by live market data when available.
export const TOKEN_PRICE_USD: Record<string, number> = {
  BTC: 67000,
  ETH: 3500,
  SOL: 150,
  BNB: 580,
  USDT: 1,
  USDC: 1,
  POL: 0.55,
  AVAX: 38,
  TON: 6.2,
};
