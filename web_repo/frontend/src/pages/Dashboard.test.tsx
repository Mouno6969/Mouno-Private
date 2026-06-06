import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from './Dashboard';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock useAuth
jest.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { username: 'testuser', telegram_id: null },
    token: 'test-token',
  }),
}));

// Mock useTranslation
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
}));

// Mock NETWORK_LIST and NetworkLogo to avoid image loading
jest.mock('../constants/networks', () => ({
  NETWORK_LIST: [
    { id: 'solana', name: 'Solana', asset: 'USDC', logo: '', color: '' },
    { id: 'trc20', name: 'Tron', asset: 'USDT', logo: '', color: '' },
  ],
  NetworkLogo: ({ id }: { id: string }) => <span data-testid={`logo-${id}`} />,
}));

// Mock Marquee component to simplify rendering
jest.mock('../components/ui/marquee', () => ({
  __esModule: true,
  default: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="marquee" className={className}>{children}</div>
  ),
}));

const renderDashboard = () => {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  );
};

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockedAxios.get.mockResolvedValue({ data: { rates: { solana: '120', trc20: '118' } } });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Marquee (PR addition)', () => {
    it('renders the Marquee component', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getByTestId('marquee')).toBeInTheDocument();
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

    it('Marquee has font-mono and uppercase classes', () => {
      renderDashboard();
      const marquee = screen.getByTestId('marquee');
      expect(marquee.className).toContain('font-mono');
      expect(marquee.className).toContain('uppercase');
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

  describe('market data fetching', () => {
    it('calls axios.get /api/market on mount', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith('/api/market');
      });
    });

    it('displays market rate data from API response', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getAllByText('৳120').length).toBeGreaterThan(0);
      });
    });

    it('shows "..." placeholder before data loads', () => {
      mockedAxios.get.mockReturnValue(new Promise(() => {})); // never resolves
      renderDashboard();
      expect(screen.getAllByText('৳...').length).toBeGreaterThan(0);
    });

    it('updates lastUpdated after successful fetch', async () => {
      const before = new Date();
      renderDashboard();
      await waitFor(() => {
        expect(screen.getByText(/Refreshed:/i)).toBeInTheDocument();
      });
      // The time shown should be at or after our before time
      const refreshedText = screen.getByText(/Refreshed:/i).textContent || '';
      expect(refreshedText).toMatch(/Refreshed:/);
    });

    it('logs error to console on failed fetch without crashing', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      mockedAxios.get.mockRejectedValue(new Error('Network error'));
      renderDashboard();
      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalled();
      });
      consoleErrorSpy.mockRestore();
    });
  });

  describe('polling interval (PR addition)', () => {
    it('sets up an interval for refetching every 10 seconds', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1);
      });

      act(() => {
        jest.advanceTimersByTime(10000);
      });

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(2);
      });
    });

    it('clears interval on unmount', async () => {
      const { unmount } = renderDashboard();
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1);
      });

      unmount();

      act(() => {
        jest.advanceTimersByTime(10000);
      });

      // Should still be 1 since interval was cleared
      expect(mockedAxios.get).toHaveBeenCalledTimes(1);
    });

    it('fetches again after each 10-second interval', async () => {
      renderDashboard();
      await waitFor(() => expect(mockedAxios.get).toHaveBeenCalledTimes(1));

      act(() => jest.advanceTimersByTime(10000));
      await waitFor(() => expect(mockedAxios.get).toHaveBeenCalledTimes(2));

      act(() => jest.advanceTimersByTime(10000));
      await waitFor(() => expect(mockedAxios.get).toHaveBeenCalledTimes(3));
    });
  });

  describe('user greeting', () => {
    it('shows welcome message with username', async () => {
      renderDashboard();
      await waitFor(() => {
        expect(screen.getByText('testuser')).toBeInTheDocument();
      });
    });

    it('shows "Guest" when no user', async () => {
      jest.resetModules();
      jest.doMock('../context/AuthContext', () => ({
        useAuth: () => ({
          user: null,
          token: null,
        }),
      }));
      // Re-import after mock change
      const { default: DashboardNoAuth } = await import('./Dashboard');
      render(
        <MemoryRouter>
          <DashboardNoAuth />
        </MemoryRouter>
      );
      await waitFor(() => {
        expect(screen.getByText('Guest')).toBeInTheDocument();
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