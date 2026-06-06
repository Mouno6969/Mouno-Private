import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Support from './Support';

// Mock fetch globally
global.fetch = jest.fn();
const mockedFetch = global.fetch as jest.MockedFunction<typeof fetch>;

// Mock AuthContext
const mockUseAuth = jest.fn();
jest.mock('../context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock i18n
const mockI18n = { language: 'en' };
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: mockI18n,
  }),
}));

// Mock Marquee to simplify rendering
jest.mock('../components/ui/marquee', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="marquee">{children}</div>
  ),
}));

// Mock ScrollArea from radix-ui
jest.mock('../components/ui/scroll-area', () => ({
  ScrollArea: React.forwardRef(({ children, className }: any, ref: any) => (
    <div ref={ref} className={className} data-testid="scroll-area">
      {children}
    </div>
  )),
}));

const renderSupport = () => {
  return render(
    <MemoryRouter>
      <Support />
    </MemoryRouter>
  );
};

describe('Support', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockI18n.language = 'en';
    mockUseAuth.mockReturnValue({ token: 'test-token' });
  });

  describe('initial messages (PR addition: system + welcome messages)', () => {
    it('shows the OS initialization system message', async () => {
      renderSupport();
      await waitFor(() => {
        expect(screen.getByText('>>> INITIALIZING MOUNO_OS v0.1...')).toBeInTheDocument();
      });
    });

    it('shows the connection established system message', async () => {
      renderSupport();
      await waitFor(() => {
        expect(screen.getByText('>>> CONNECTION ESTABLISHED VIA ENCRYPTED CHANNEL')).toBeInTheDocument();
      });
    });

    it('shows English welcome message when language is en', async () => {
      mockI18n.language = 'en';
      renderSupport();
      await waitFor(() => {
        expect(screen.getByText(
          'System Online. I am your AI Support assistant. How can I help you today?'
        )).toBeInTheDocument();
      });
    });

    it('shows Bengali welcome message when language is bn', async () => {
      mockI18n.language = 'bn';
      renderSupport();
      await waitFor(() => {
        expect(screen.getByText(
          'সিস্টেম অনলাইন। আমি আপনার AI সাপোর্ট অ্যাসিস্ট্যান্ট। কিভাবে সাহায্য করতে পারি?'
        )).toBeInTheDocument();
      });
    });

    it('does NOT wipe existing messages when language changes (conversation preservation)', async () => {
      const { rerender } = renderSupport();
      await waitFor(() => {
        expect(screen.getByText('>>> INITIALIZING MOUNO_OS v0.1...')).toBeInTheDocument();
      });

      // Simulate a user message being in the conversation (by simulating state having messages)
      // We test that the init effect respects `if (prev.length > 0) return prev`
      // After initial render, messages are > 0 so re-trigger should not reset
      mockI18n.language = 'bn';
      rerender(
        <MemoryRouter>
          <Support />
        </MemoryRouter>
      );

      // English init message should still be visible (not wiped)
      expect(screen.getByText('>>> INITIALIZING MOUNO_OS v0.1...')).toBeInTheDocument();
    });
  });

  describe('message rendering styles (PR change)', () => {
    it('system messages have low opacity muted style', async () => {
      renderSupport();
      await waitFor(() => {
        const sysMsg = screen.getByText('>>> INITIALIZING MOUNO_OS v0.1...').parentElement as HTMLElement;
        expect(sysMsg.className).toContain('opacity-50');
        expect(sysMsg.className).toContain('text-muted-foreground');
      });
    });

    it('assistant messages show ◈ prefix', async () => {
      renderSupport();
      await waitFor(() => {
        const prefixes = screen.getAllByText('◈');
        expect(prefixes.length).toBeGreaterThan(0);
      });
    });

    it('assistant message bubble has black background and white border', async () => {
      renderSupport();
      await waitFor(() => {
        // The assistant welcome message
        const msgEl = screen.getByText(
          'System Online. I am your AI Support assistant. How can I help you today?'
        ).closest('div.inline-block') as HTMLElement;
        expect(msgEl.className).toContain('bg-black');
        expect(msgEl.className).toContain('text-white');
      });
    });
  });

  describe('input and send form', () => {
    it('renders the command input with placeholder', () => {
      renderSupport();
      expect(screen.getByPlaceholderText('COMMAND_INPUT...')).toBeInTheDocument();
    });

    it('renders the send button', () => {
      renderSupport();
      expect(screen.getByRole('button', { name: '' })).toBeInTheDocument();
    });

    it('send button is disabled when input is empty', () => {
      renderSupport();
      const btn = screen.getByRole('button');
      expect(btn).toBeDisabled();
    });

    it('send button is enabled when input has text', async () => {
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'hello');
      const btn = screen.getByRole('button');
      expect(btn).not.toBeDisabled();
    });

    it('input has the > prefix symbol visible', () => {
      renderSupport();
      expect(screen.getByText('>')).toBeInTheDocument();
    });
  });

  describe('handleSend - success flow', () => {
    it('adds user message to the chat on submit', async () => {
      mockedFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ answer: 'Bot reply' }),
      } as Response);

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'my question');
      await userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(screen.getByText('my question')).toBeInTheDocument();
      });
    });

    it('clears input after send', async () => {
      mockedFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ answer: 'OK' }),
      } as Response);

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...') as HTMLInputElement;
      await userEvent.type(input, 'test');
      await userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });

    it('adds assistant reply message to chat on success', async () => {
      mockedFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ answer: 'Helpful answer from bot' }),
      } as Response);

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'question');
      await userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(screen.getByText('Helpful answer from bot')).toBeInTheDocument();
      });
    });

    it('sends fetch request to /api/ai/chat with correct payload', async () => {
      mockedFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ answer: 'OK' }),
      } as Response);

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'my question');
      await userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(mockedFetch).toHaveBeenCalledWith('/api/ai/chat', expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ question: 'my question' }),
        }));
      });
    });

    it('sends Authorization header with token', async () => {
      mockedFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ answer: 'OK' }),
      } as Response);

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(mockedFetch).toHaveBeenCalledWith('/api/ai/chat', expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        }));
      });
    });

    it('shows loading indicator while waiting for response', async () => {
      let resolveResponse: (value: Response) => void;
      mockedFetch.mockReturnValueOnce(
        new Promise<Response>((resolve) => { resolveResponse = resolve; })
      );

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'question');
      await userEvent.click(screen.getByRole('button'));

      expect(screen.getByText(/Computing response.../i)).toBeInTheDocument();

      // Resolve the promise
      act(() => {
        resolveResponse!({
          ok: true,
          json: async () => ({ answer: 'done' }),
        } as Response);
      });

      await waitFor(() => {
        expect(screen.queryByText(/Computing response.../i)).not.toBeInTheDocument();
      });
    });
  });

  describe('handleSend - error flows (PR change: new error messages)', () => {
    it('shows ERROR: UPLINK_FAILURE when response is not ok (PR change)', async () => {
      mockedFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ message: undefined, answer: undefined }),
      } as Response);

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(screen.getByText('ERROR: UPLINK_FAILURE')).toBeInTheDocument();
      });
    });

    it('shows CRITICAL_ERROR: NETWORK_OFFLINE on fetch exception (PR change)', async () => {
      mockedFetch.mockRejectedValueOnce(new Error('Network down'));

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(screen.getByText('CRITICAL_ERROR: NETWORK_OFFLINE')).toBeInTheDocument();
      });
    });

    it('uses data.message from error response when available', async () => {
      mockedFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ message: 'Service unavailable' }),
      } as Response);

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(screen.getByText('Service unavailable')).toBeInTheDocument();
      });
    });
  });

  describe('send button disabled states', () => {
    it('button is disabled when input is only whitespace', async () => {
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, '   ');
      const btn = screen.getByRole('button');
      expect(btn).toBeDisabled();
    });

    it('does not submit on empty input via keyboard Enter', async () => {
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      fireEvent.submit(input.closest('form')!);
      expect(mockedFetch).not.toHaveBeenCalled();
    });
  });

  describe('Marquee header (PR addition)', () => {
    it('renders the top Marquee with system status info', () => {
      renderSupport();
      expect(screen.getByTestId('marquee')).toBeInTheDocument();
      expect(screen.getByText(/AI SUPPORT SYSTEM v0\.1/i)).toBeInTheDocument();
    });
  });

  describe('sidebar content', () => {
    it('shows System Status section', () => {
      renderSupport();
      expect(screen.getByText('System Status')).toBeInTheDocument();
    });

    it('shows kernel version v0.1-prod', () => {
      renderSupport();
      expect(screen.getByText('v0.1-prod')).toBeInTheDocument();
    });

    it('shows AI Node ACTIVE status', () => {
      renderSupport();
      expect(screen.getByText('● ACTIVE')).toBeInTheDocument();
    });

    it('shows Security section with E2E encryption info', () => {
      renderSupport();
      expect(screen.getByText('E2E Encryption: ENABLED')).toBeInTheDocument();
    });
  });
});
