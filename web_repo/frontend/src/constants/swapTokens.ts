/** Popular swappable tokens per LI.FI chain id. */
export interface SwapTokenOption {
  address: string;
  symbol: string;
  name: string;
}

const NATIVE = (symbol: string, name: string): SwapTokenOption => ({
  address: 'native',
  symbol,
  name,
});

/** Curated popular tokens — shown after a network is selected. */
export const POPULAR_TOKENS_BY_CHAIN: Record<string, SwapTokenOption[]> = {
  '1': [
    NATIVE('ETH', 'Ethereum'),
    { address: '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', symbol: 'USDC', name: 'USD Coin' },
    { address: '0xdAC17F958D2ee523a2206206994597C13D831ec7', symbol: 'USDT', name: 'Tether USD' },
    { address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', symbol: 'WETH', name: 'Wrapped Ether' },
    { address: '0x6B175474E89094C44Da98b954EedeAC495271d0F', symbol: 'DAI', name: 'Dai Stablecoin' },
  ],
  '137': [
    NATIVE('POL', 'Polygon'),
    { address: '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359', symbol: 'USDC', name: 'USD Coin' },
    { address: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', symbol: 'USDT', name: 'Tether USD' },
    { address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', symbol: 'WETH', name: 'Wrapped Ether' },
  ],
  '56': [
    NATIVE('BNB', 'BNB'),
    { address: '0x55d398326f99059fF775485246999027B3197955', symbol: 'USDT', name: 'Tether USD' },
    { address: '0x8AC76a51cc950d9822D68b05e7934808d', symbol: 'USDC', name: 'USD Coin' },
    { address: '0x2170Ed0880ac9A755fd29B2688956BD959F933F8', symbol: 'ETH', name: 'Ethereum Token' },
  ],
  '8453': [
    NATIVE('ETH', 'Base'),
    { address: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', symbol: 'USDC', name: 'USD Coin' },
    { address: '0x4200000000000000000000000000000000000006', symbol: 'WETH', name: 'Wrapped Ether' },
    { address: '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb', symbol: 'DAI', name: 'Dai Stablecoin' },
  ],
  '42161': [
    NATIVE('ETH', 'Arbitrum'),
    { address: '0xaf88d065e77c8cC2239327C5EDb3A432268e5831', symbol: 'USDC', name: 'USD Coin' },
    { address: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9', symbol: 'USDT', name: 'Tether USD' },
    { address: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1', symbol: 'WETH', name: 'Wrapped Ether' },
    { address: '0x912CE59144191C1204E64559FE8253a0e49E6548', symbol: 'ARB', name: 'Arbitrum' },
  ],
  '10': [
    NATIVE('ETH', 'Optimism'),
    { address: '0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85', symbol: 'USDC', name: 'USD Coin' },
    { address: '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58', symbol: 'USDT', name: 'Tether USD' },
    { address: '0x4200000000000000000000000000000000000006', symbol: 'WETH', name: 'Wrapped Ether' },
    { address: '0x4200000000000000000000000000000000000042', symbol: 'OP', name: 'Optimism' },
  ],
  '43114': [
    NATIVE('AVAX', 'Avalanche'),
    { address: '0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E', symbol: 'USDC', name: 'USD Coin' },
    { address: '0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7', symbol: 'USDT', name: 'Tether USD' },
    { address: '0x49D5c2BdFfac6CE2BFdB7840F0c0A441e3Dba5D4', symbol: 'WETH', name: 'Wrapped Ether' },
  ],
  '1151111081099710': [
    NATIVE('SOL', 'Solana'),
    { address: 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', symbol: 'USDC', name: 'USD Coin' },
    { address: 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB', symbol: 'USDT', name: 'Tether USD' },
    { address: 'So11111111111111111111111111111111111111112', symbol: 'WSOL', name: 'Wrapped SOL' },
  ],
  '20000000000001': [
    NATIVE('BTC', 'Bitcoin'),
  ],
  '324': [
    NATIVE('ETH', 'zkSync Era'),
    { address: '0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4', symbol: 'USDC', name: 'USD Coin' },
    { address: '0x493257fD37EDB34451fE62EDf050D45a1C0a1923', symbol: 'USDT', name: 'Tether USD' },
  ],
  '59144': [
    NATIVE('ETH', 'Linea'),
    { address: '0x176211869cA2b568f2A7D4F94108100A03684965', symbol: 'USDC', name: 'USD Coin' },
    { address: '0xA219439258ca9da29E9Cc4cE5596924745e12B93', symbol: 'USDT', name: 'Tether USD' },
  ],
  '534352': [
    NATIVE('ETH', 'Scroll'),
    { address: '0x06eFdBFf2a14a7c8E15944D1F4A48F9F95F663A4', symbol: 'USDC', name: 'USD Coin' },
    { address: '0xf55BEC9cafDbE8730f096Aa55b6A4a7AFC4c2d0E', symbol: 'USDT', name: 'Tether USD' },
  ],
  '81457': [
    NATIVE('ETH', 'Blast'),
    { address: '0x4300000000000000000000000000000000000003', symbol: 'USDB', name: 'USDB' },
    { address: '0x4300000000000000000000000000000000000004', symbol: 'WETH', name: 'Wrapped Ether' },
  ],
  '100': [
    NATIVE('xDAI', 'Gnosis'),
    { address: '0xDDAfbb505ad214D7b80b1f830fcCc89B60fbA85', symbol: 'USDC', name: 'USD Coin' },
    { address: '0x4ECaBa5870353805a9F068101A40E0f32ed605C6', symbol: 'USDT', name: 'Tether USD' },
  ],
};

export function popularTokensForChain(chainId: string): SwapTokenOption[] {
  return POPULAR_TOKENS_BY_CHAIN[chainId] ?? [NATIVE('NATIVE', 'Native token')];
}

export function defaultFromToken(chainId: string): string {
  return popularTokensForChain(chainId)[0]?.address ?? 'native';
}

export function defaultToToken(chainId: string): string {
  const tokens = popularTokensForChain(chainId);
  const stable = tokens.find((t) => ['USDC', 'USDT'].includes(t.symbol));
  return stable?.address ?? tokens[0]?.address ?? 'native';
}

/** @deprecated use popularTokensForChain */
export function tokensForChain(chainId: string) {
  const tokens = popularTokensForChain(chainId);
  const stable = tokens.find((t) => ['USDC', 'USDT'].includes(t.symbol));
  return {
    native: tokens[0]?.address ?? 'native',
    stable: stable?.address ?? 'usdc',
    stableSymbol: stable?.symbol ?? 'USDC',
  };
}