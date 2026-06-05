import React from 'react';

export interface NetworkInfo {
  id: string;
  name: string;
  asset: string;
  logo: string;
  color: string;
}

export const NETWORK_LIST: NetworkInfo[] = [
  {
    id: 'solana',
    name: 'Solana',
    asset: 'USDC',
    logo: 'https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png',
    color: 'text-purple-400',
  },
  {
    id: 'trc20',
    name: 'Tron',
    asset: 'USDT',
    logo: 'https://s2.coinmarketcap.com/static/img/coins/64x64/1958.png',
    color: 'text-red-400',
  },
  {
    id: 'polygon',
    name: 'Polygon',
    asset: 'USDC',
    logo: 'https://assets.coingecko.com/coins/images/4713/small/polygon.png',
    color: 'text-indigo-400',
  },
  {
    id: 'bsc',
    name: 'BSC',
    asset: 'USDT',
    logo: 'https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png',
    color: 'text-yellow-400',
  },
  {
    id: 'ton',
    name: 'TON',
    asset: 'USDT',
    logo: 'https://assets.coingecko.com/coins/images/17980/small/ton_symbol.png',
    color: 'text-blue-400',
  },
  {
    id: 'avalanche',
    name: 'Avalanche',
    asset: 'USDT',
    logo: 'https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png',
    color: 'text-red-500',
  },
  {
    id: 'ethereum',
    name: 'ETH USDT',
    asset: 'USDT',
    logo: 'https://assets.coingecko.com/coins/images/279/small/ethereum.png',
    color: 'text-blue-500',
  },
  {
    id: 'ethereum_usdc',
    name: 'ETH USDC',
    asset: 'USDC',
    logo: 'https://assets.coingecko.com/coins/images/279/small/ethereum.png',
    color: 'text-blue-400',
  },
  {
    id: 'base',
    name: 'Base',
    asset: 'USDC',
    logo: 'https://assets.coingecko.com/asset_platforms/images/131/small/base.jpeg',
    color: 'text-blue-600',
  },
];

export const NETWORK_MAP: Record<string, NetworkInfo> = Object.fromEntries(
  NETWORK_LIST.map((n) => [n.id, n])
);

export const NetworkLogo: React.FC<{ id: string; size?: number; className?: string }> = ({ id, size = 24, className = '' }) => {
  const net = NETWORK_MAP[id];
  if (!net) return <span className={className}>🔗</span>;
  return (
    <img
      src={net.logo}
      alt={net.name}
      width={size}
      height={size}
      className={`rounded-full inline-block ${className}`}
      loading="lazy"
    />
  );
};
