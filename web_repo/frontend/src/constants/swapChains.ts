/** Map LI.FI chain keys to NetworkLogo ids (see constants/networks.tsx). */
export const CHAIN_KEY_TO_LOGO: Record<string, string> = {
  eth: 'ethereum',
  pol: 'polygon',
  bsc: 'bsc',
  bas: 'base',
  ava: 'avalanche',
  sol: 'solana',
  arb: 'ethereum',
  opt: 'ethereum',
  btc: 'ethereum',
  era: 'ethereum',
  lna: 'ethereum',
  scl: 'ethereum',
  bls: 'ethereum',
  dai: 'polygon',
};

/** Popular networks shown by default (LI.FI chain keys, in display order). */
export const FEATURED_CHAIN_KEYS = [
  'eth',
  'pol',
  'bsc',
  'bas',
  'arb',
  'opt',
  'ava',
  'sol',
  'btc',
  'era',
  'lna',
  'scl',
  'bls',
  'dai',
] as const;

export interface LifiChain {
  id: number | string;
  key?: string;
  name?: string;
  coin?: string;
  chainType?: string;
}

export function chainLogoId(chain: LifiChain): string {
  const key = String(chain.key || '').toLowerCase();
  return CHAIN_KEY_TO_LOGO[key] || 'ethereum';
}

/** Full label for headers and summaries — always includes the network name. */
export function chainLabel(chain: LifiChain): string {
  const name = chain.name || chain.key || String(chain.id);
  const coin = chain.coin;
  if (!coin || coin.toUpperCase() === name.toUpperCase()) return name;
  return `${name} (${coin})`;
}

/** Network-only label for dropdowns (no token/coin tickers). */
export function chainSelectLabel(chain: LifiChain): string {
  return chain.name || chain.key || String(chain.id);
}

function featuredRank(chain: LifiChain): number {
  const key = String(chain.key || '').toLowerCase();
  const id = String(chain.id);
  const idx = FEATURED_CHAIN_KEYS.findIndex((k) => k === key || k === id);
  return idx === -1 ? 999 : idx;
}

/** Supported networks for the swap UI (popular/mainnet only). */
export function prepareSwapChains(chains: LifiChain[]): LifiChain[] {
  const valid = chains.filter((c) => c.id != null && (c.name || c.key));
  const featured = valid
    .filter((c) => featuredRank(c) < 999)
    .sort((a, b) => featuredRank(a) - featuredRank(b));
  return featured.length > 0 ? featured : valid.slice(0, 14);
}

export function featuredSwapChains(chains: LifiChain[]): LifiChain[] {
  return prepareSwapChains(chains);
}

export type ChainEcosystem = 'EVM' | 'SVM' | 'UTXO';

const SVM_CHAIN_IDS = new Set(['1151111081099710', 'sol', 'solana', 'sol-mainnet']);
const UTXO_CHAIN_IDS = new Set(['20000000000001', 'btc', 'bitcoin']);

/** Classify a LI.FI chain as EVM, SVM (Solana), or UTXO (Bitcoin). */
export function chainEcosystem(chainId: string): ChainEcosystem {
  const cid = String(chainId || '').trim().toLowerCase();
  if (SVM_CHAIN_IDS.has(cid)) return 'SVM';
  if (UTXO_CHAIN_IDS.has(cid)) return 'UTXO';
  return 'EVM';
}