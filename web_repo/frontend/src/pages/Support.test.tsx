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

const urlOf = (input: RequestInfo | URL): string =>
  typeof input === 'string' ? input : input instanceof URL ? input.toString() : (input as Request).url;

// Route fetch calls by URL. Session listing returns empty by default; the
// chat endpoint uses whatever `chatResponse` is configured for the test.
const setupFetch = (chatResponse?: Partial<Response> & { json?: () => Promise<any> }) => {
  mockedFetch.mockImplementation((input: RequestInfo | URL) => {
    const url = urlOf(input);
    if (url.includes('/api/ai/sessions')) {
      return Promise.resolve({ ok: true, json: async () => ({ sessions: [] }) } as Response);
    }
    if (url.includes('/api/ai/chat')) {
      if (chatResponse) return Promise.resolve(chatResponse as Response);
      return Promise.resolve({ ok: true, json: async () => ({ answer: 'OK' }) } as Response);
    }
    return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
  });
};

const chatCalls = () =>
  mockedFetch.mock.calls.filter(([input]) => urlOf(input as RequestInfo | URL).includes('/api/ai/chat'));

const sendButton = () => screen.getByRole('button', { name: 'send' });

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
    setupFetch();
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
  });

  describe('message rendering styles (PR change)', () => {
    it('system messages have low opacity muted style', async () => {
      renderSupport();
      await waitFor(() => {
        const sysMsg = screen.getByText('>>> INITIALIZING MOUNO_OS v0.1...') as HTMLElement;
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

    it('assistant message bubble has black background and white text', async () => {
      renderSupport();
      await waitFor(() => {
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
      expect(sendButton()).toBeInTheDocument();
    });

    it('send button is disabled when input is empty', () => {
      renderSupport();
      expect(sendButton()).toBeDisabled();
    });

    it('send button is enabled when input has text', async () => {
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'hello');
      expect(sendButton()).not.toBeDisabled();
    });

    it('input has the > prefix symbol visible', () => {
      renderSupport();
      expect(screen.getByText('>')).toBeInTheDocument();
    });
  });

  describe('handleSend - success flow', () => {
    it('adds user message to the chat on submit', async () => {
      setupFetch({ ok: true, json: async () => ({ answer: 'Bot reply' }) });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'my question');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(screen.getByText('my question')).toBeInTheDocument();
      });
    });

    it('clears input after send', async () => {
      setupFetch({ ok: true, json: async () => ({ answer: 'OK' }) });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...') as HTMLInputElement;
      await userEvent.type(input, 'test');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });

    it('adds assistant reply message to chat on success', async () => {
      setupFetch({ ok: true, json: async () => ({ answer: 'Helpful answer from bot' }) });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'question');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(screen.getByText('Helpful answer from bot')).toBeInTheDocument();
      });
    });

    it('sends fetch request to /api/ai/chat with question and session_id', async () => {
      setupFetch({ ok: true, json: async () => ({ answer: 'OK' }) });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'my question');
      await userEvent.click(sendButton());

      await waitFor(() => {
        const calls = chatCalls();
        expect(calls.length).toBe(1);
        const [, init] = calls[0];
        expect(init?.method).toBe('POST');
        expect(JSON.parse(init?.body as string)).toEqual({ question: 'my question', session_id: null });
      });
    });

    it('sends Authorization header with token', async () => {
      setupFetch({ ok: true, json: async () => ({ answer: 'OK' }) });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(sendButton());

      await waitFor(() => {
        const calls = chatCalls();
        expect(calls.length).toBe(1);
        const [, init] = calls[0];
        expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
      });
    });

    it('shows loading indicator while waiting for response', async () => {
      let resolveResponse: (value: Response) => void;
      mockedFetch.mockImplementation((input: RequestInfo | URL) => {
        const url = urlOf(input);
        if (url.includes('/api/ai/sessions')) {
          return Promise.resolve({ ok: true, json: async () => ({ sessions: [] }) } as Response);
        }
        return new Promise<Response>((resolve) => { resolveResponse = resolve; });
      });

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'question');
      await userEvent.click(sendButton());

      expect(screen.getByText(/Computing response.../i)).toBeInTheDocument();

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
    it('shows ERROR: UPLINK_FAILURE when response is not ok', async () => {
      setupFetch({ ok: false, json: async () => ({}) });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(screen.getByText('ERROR: UPLINK_FAILURE')).toBeInTheDocument();
      });
    });

    it('shows CRITICAL_ERROR: NETWORK_OFFLINE on fetch exception', async () => {
      mockedFetch.mockImplementation((input: RequestInfo | URL) => {
        const url = urlOf(input);
        if (url.includes('/api/ai/sessions')) {
          return Promise.resolve({ ok: true, json: async () => ({ sessions: [] }) } as Response);
        }
        return Promise.reject(new Error('Network down'));
      });

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(screen.getByText('CRITICAL_ERROR: NETWORK_OFFLINE')).toBeInTheDocument();
      });
    });

    it('uses data.message from error response when available', async () => {
      setupFetch({ ok: false, json: async () => ({ message: 'Service unavailable' }) });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(sendButton());

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
      expect(sendButton()).toBeDisabled();
    });

    it('does not call the chat endpoint on empty input via keyboard Enter', async () => {
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      fireEvent.submit(input.closest('form')!);
      expect(chatCalls().length).toBe(0);
    });
  });

  describe('Marquee header (PR addition)', () => {
    it('renders the top Marquee with system status info', () => {
      renderSupport();
      expect(screen.getByTestId('marquee')).toBeInTheDocument();
      expect(screen.getByText(/AI SUPPORT SYSTEM v0\.1/i)).toBeInTheDocument();
    });
  });

  describe('chat history sidebar (PR addition)', () => {
    it('shows the New Chat button', () => {
      renderSupport();
      expect(screen.getByRole('button', { name: /New Chat/i })).toBeInTheDocument();
    });

    it('shows the Chat History heading', () => {
      renderSupport();
      expect(screen.getByText('Chat History')).toBeInTheDocument();
    });

    it('shows an empty-history hint when there are no sessions', async () => {
      renderSupport();
      await waitFor(() => {
        expect(screen.getByText('No conversations yet.')).toBeInTheDocument();
      });
    });

    it('prompts login when there is no token', async () => {
      mockUseAuth.mockReturnValue({ token: null });
      renderSupport();
      await waitFor(() => {
        expect(screen.getByText('Log in to keep chat history.')).toBeInTheDocument();
      });
    });

    it('lists existing sessions returned by the API', async () => {
      mockedFetch.mockImplementation((input: RequestInfo | URL) => {
        const url = urlOf(input);
        if (url.includes('/api/ai/sessions')) {
          return Promise.resolve({ ok: true, json: async () => ({ sessions: [{ id: 1, title: 'My first chat' }] }) } as Response);
        }
        return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
      });
      renderSupport();
      await waitFor(() => {
        expect(screen.getByText('My first chat')).toBeInTheDocument();
      });
    });
  });

  describe('sidebar content', () => {
    it('shows System Status section', () => {
      renderSupport();
      expect(screen.getByText('System Status')).toBeInTheDocument();
    });

    it('shows AI Node ACTIVE status', () => {
      renderSupport();
      expect(screen.getByText('● ACTIVE')).toBeInTheDocument();
    });

    it('shows the E2E encryption ENABLED status', () => {
      renderSupport();
      expect(screen.getByText('ENABLED')).toBeInTheDocument();
    });
  });
});
