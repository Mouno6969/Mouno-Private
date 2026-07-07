type EthereumProvider = {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on?: (event: string, handler: (...args: unknown[]) => void) => void;
  removeListener?: (event: string, handler: (...args: unknown[]) => void) => void;
  isMetaMask?: boolean;
};

declare global {
  interface Window {
    ethereum?: EthereumProvider;
  }
}

export function hasInjectedWallet(): boolean {
  return typeof window !== 'undefined' && Boolean(window.ethereum?.request);
}

export async function connectEvmWallet(): Promise<string> {
  if (!hasInjectedWallet()) {
    throw new Error('No Web3 wallet found. Install MetaMask or another browser wallet.');
  }
  const accounts = (await window.ethereum!.request({
    method: 'eth_requestAccounts',
  })) as string[];
  const address = accounts?.[0];
  if (!address) {
    throw new Error('No wallet account selected.');
  }
  return address;
}

export async function getConnectedEvmAddress(): Promise<string | null> {
  if (!hasInjectedWallet()) return null;
  try {
    const accounts = (await window.ethereum!.request({
      method: 'eth_accounts',
    })) as string[];
    return accounts?.[0] ?? null;
  } catch {
    return null;
  }
}

function toHexChainId(chainId: number | string): string {
  const numeric = Number(chainId);
  if (!Number.isFinite(numeric) || numeric <= 0) {
    throw new Error('Invalid chain id for wallet switch.');
  }
  return `0x${numeric.toString(16)}`;
}

export async function switchEvmChain(chainId: number | string): Promise<void> {
  if (!hasInjectedWallet()) {
    throw new Error('No Web3 wallet found.');
  }
  const hexChainId = toHexChainId(chainId);
  try {
    await window.ethereum!.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: hexChainId }],
    });
  } catch (err: unknown) {
    const code = (err as { code?: number })?.code;
    if (code === 4902) {
      throw new Error('Add this network in your wallet, then try again.');
    }
    throw err;
  }
}

export async function sendEvmTransaction(tx: {
  from?: string;
  to: string;
  data?: string;
  value?: string;
}): Promise<string> {
  if (!hasInjectedWallet()) {
    throw new Error('No Web3 wallet found.');
  }
  const hash = (await window.ethereum!.request({
    method: 'eth_sendTransaction',
    params: [
      {
        from: tx.from,
        to: tx.to,
        data: tx.data || '0x',
        value: tx.value || '0x0',
      },
    ],
  })) as string;
  if (!hash) {
    throw new Error('Wallet did not return a transaction hash.');
  }
  return hash;
}

export function onAccountsChanged(handler: (accounts: string[]) => void): () => void {
  const provider = window.ethereum;
  if (!provider?.on) return () => {};
  const wrapped = (accounts: unknown) => handler(Array.isArray(accounts) ? (accounts as string[]) : []);
  provider.on('accountsChanged', wrapped);
  return () => provider.removeListener?.('accountsChanged', wrapped);
}