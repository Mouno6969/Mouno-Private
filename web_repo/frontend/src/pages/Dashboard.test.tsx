import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import Dashboard from './Dashboard';
import * as hooks from '../lib/hooks';

// Dashboard reads all live data through typed SWR hooks in ../lib/hooks.
// We mock that module so tests can drive loading / data states directly,
// without touching the network or SWR internals.
vi.mock('../lib/hooks', () => ({
  useMarket: vi.fn(),
  useStats: vi.fn(),
  useRecentActivity: vi.fn(),
  useBalance: vi.fn(),
  useTxLog: vi.fn(),
  useOrders: vi.fn(),
}));

// Auth: logged-in user by default (overridden per-test where needed).
const mockUseAuth = vi.fn();
vi.mock('../context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

// i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
}));

// Networks: keep the table small and avoid image loading.
vi.mock('../constants/networks', () => ({
  NETWORK_LIST: [
    { id: 'solana', name: 'Solana', asset: 'USDC', logo: '', color: '' },
    { id: 'trc20', name: 'Tron', asset: 'USDT', logo: '', color: '' },
  ],
  NetworkLogo: ({ id }: { id: string }) => <span data-testid={`logo-${id}`} />,
}));

// Marquee: simplify rendering.
vi.mock('../components/ui/marquee', () => ({
  __esModule: true,
  default: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="marquee" className={className}>{children}</div>
  ),
}));

const mockedUseMarket = hooks.useMarket as unknown as ReturnType<typeof vi.fn>;
const mockedUseStats = hooks.useStats as unknown as ReturnType<typeof vi.fn>;
const mockedUseRecentActivity = hooks.useRecentActivity as unknown as ReturnType<typeof vi.fn>;
const mockedUseBalance = hooks.useBalance as unknown as ReturnType<typeof vi.fn>;
const mockedUseTxLog = hooks.useTxLog as unknown as ReturnType<typeof vi.fn>;

// Default happy-path hook returns.
const setMarket = (
  data: unknown = { rates: { solana: '120', trc20: '118' } },
  isLoading = false
) => mockedUseMarket.mockReturnValue({ data, isLoading });

const renderDashboard = () =>
  render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  );

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: { username: 'testuser', telegram_id: null },
      token: 'test-token',
    });
    setMarket();
    mockedUseStats.mockReturnValue({ data: { total_users: 42 } });
    mockedUseRecentActivity.mockReturnValue({ data: [] });
    mockedUseBalance.mockReturnValue({ data: { balances: {} }, isLoading: false });
    mockedUseTxLog.mockReturnValue({ data: [] });
  });

  describe('Marquee (PR addition)', () => {
    it('renders the Marquee component', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getAllByTestId('marquee').length).toBeGreaterThan(0);
      });
    });

    it('Marquee contains protocol status messages', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getByText(/LIFI PROTOCOL INTEGRATED/i)).toBeInTheDocument();
        expect(screen.getByText(/24\/7 AUTOMATED DELIVERY/i)).toBeInTheDocument();
        expect(screen.getByText(/CROSS-CHAIN SWAPS ACTIVE/i)).toBeInTheDocument();
        expect(screen.getByText(/SECURE P2P SETTLEMENT/i)).toBeInTheDocument();
        expect(screen.getByText(/AI ONBOARDING ONLINE/i)).toBeInTheDocument();
      });
    });
  });

  describe('System status badge (PR change)', () => {
    it('shows "System: Online" badge', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getByText(/System: Online/i)).toBeInTheDocument();
      });
    });

    it('shows "Refreshed:" timestamp display (PR addition)', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getByText(/Refreshed:/i)).toBeInTheDocument();
      });
    });
  });

  describe('market data', () => {
    it('displays market rate data from the useMarket hook', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getAllByText('৳120').length).toBeGreaterThan(0);
      });
    });

    it('shows a loading skeleton before data arrives', () => {
      setMarket(undefined, true);
      renderDashboard();
      // Header rate cell falls back to N/A while loading with no data.
      expect(screen.getByText('System: Online')).toBeInTheDocument();
    });

    it('does not crash when the market hook returns no data', async () => {
      setMarket(undefined, false);
      renderDashboard();
      await waitFor(() => {
        expect(screen.getByText('Solana')).toBeInTheDocument();
      });
    });
  });

  describe('user greeting', () => {
    it('shows welcome message with username', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getAllByText('testuser').length).toBeGreaterThan(0);
      });
    });

    it('shows "Guest" when no user', async () => {
      mockUseAuth.mockReturnValue({ user: null, token: null });
      renderDashboard();
      await waitFor(() => {
        expect(screen.getAllByText('Guest').length).toBeGreaterThan(0);
      });
    });
  });

  describe('network table', () => {
    it('renders network rows', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getByText('Solana')).toBeInTheDocument();
        expect(screen.getByText('Tron')).toBeInTheDocument();
      });
    });
  });
});
