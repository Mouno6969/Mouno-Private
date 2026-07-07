import React from 'react';
import { chainLogoUri, type LifiChain } from '../../constants/swapChains';
import { SwapAssetLogo } from './SwapAssetLogo';

export const ChainLogo: React.FC<{
  chain?: LifiChain | null;
  size?: number;
  className?: string;
}> = ({ chain, size = 24, className = '' }) => (
  <SwapAssetLogo
    src={chainLogoUri(chain)}
    symbol={chain?.coin || chain?.key}
    name={chain?.name}
    size={size}
    className={className}
  />
);