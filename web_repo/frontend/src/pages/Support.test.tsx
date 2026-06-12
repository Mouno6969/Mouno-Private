import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import Support from './Support';
import { apiClient } from '../lib/apiClient';

// Mock the central API client. Support.tsx talks to the backend exclusively
// through apiClient (axios), so we drive responses by mocking get/post/delete.
vi.mock('../lib/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockedGet = apiClient.get as unknown as ReturnType<typeof vi.fn>;
const mockedPost = apiClient.post as unknown as ReturnType<typeof vi.fn>;
const mockedDelete = apiClient.delete as unknown as ReturnType<typeof vi.fn>;

// Mock AuthContext
const mockUseAuth = vi.fn();
vi.mock('../context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock i18n
const mockI18n = { language: 'en' };
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: mockI18n,
  }),
}));

// Mock Marquee to simplify rendering
vi.mock('../components/ui/marquee', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="marquee">{children}</div>
  ),
}));

// Route GET calls by URL. Session listing returns empty by default.
const setupGet = (sessions: Array<{ id: number; title: string }> = []) => {
  mockedGet.mockImplementation((url: string) => {
    if (url.includes('/api/ai/sessions')) {
      return Promise.resolve({ data: { sessions } });
    }
    return Promise.resolve({ data: {} });
  });
};

// Configure the chat POST response (or rejection).
const setupChat = (
  result: { data?: Record<string, unknown>; reject?: boolean } = { data: { answer: 'OK' } }
) => {
  mockedPost.mockImplementation((url: string) => {
    if (url.includes('/api/ai/chat')) {
      if (result.reject) return Promise.reject(new Error('Network down'));
      return Promise.resolve({ data: result.data ?? {} });
    }
    return Promise.resolve({ data: {} });
  });
};

const chatCalls = () =>
  mockedPost.mock.calls.filter(([url]) => String(url).includes('/api/ai/chat'));

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
    vi.clearAllMocks();
    mockI18n.language = 'en';
    mockUseAuth.mockReturnValue({ token: 'test-token' });
    setupGet();
    setupChat();
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
      setupChat({ data: { answer: 'Bot reply' } });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'my question');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(screen.getByText('my question')).toBeInTheDocument();
      });
    });

    it('clears input after send', async () => {
      setupChat({ data: { answer: 'OK' } });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...') as HTMLInputElement;
      await userEvent.type(input, 'test');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });

    it('adds assistant reply message to chat on success', async () => {
      setupChat({ data: { answer: 'Helpful answer from bot' } });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'question');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(screen.getByText('Helpful answer from bot')).toBeInTheDocument();
      });
    });

    it('posts to /api/ai/chat with question and session_id', async () => {
      setupChat({ data: { answer: 'OK' } });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'my question');
      await userEvent.click(sendButton());

      await waitFor(() => {
        const calls = chatCalls();
        expect(calls.length).toBe(1);
        const [, body] = calls[0];
        expect(body).toEqual({ question: 'my question', session_id: null });
      });
    });

    it('shows loading indicator while waiting for response', async () => {
      let resolveResponse: (value: { data: Record<string, unknown> }) => void;
      mockedPost.mockImplementation((url: string) => {
        if (url.includes('/api/ai/chat')) {
          return new Promise((resolve) => { resolveResponse = resolve; });
        }
        return Promise.resolve({ data: {} });
      });

      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'question');
      await userEvent.click(sendButton());

      expect(screen.getByText(/Computing response.../i)).toBeInTheDocument();

      act(() => {
        resolveResponse!({ data: { answer: 'done' } });
      });

      await waitFor(() => {
        expect(screen.queryByText(/Computing response.../i)).not.toBeInTheDocument();
      });
    });
  });

  describe('handleSend - error flows (PR change: new error messages)', () => {
    it('shows ERROR: UPLINK_FAILURE when a 2xx response has no answer', async () => {
      setupChat({ data: {} });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(screen.getByText('ERROR: UPLINK_FAILURE')).toBeInTheDocument();
      });
    });

    it('shows CRITICAL_ERROR: NETWORK_OFFLINE when the request rejects', async () => {
      setupChat({ reject: true });
      renderSupport();
      const input = screen.getByPlaceholderText('COMMAND_INPUT...');
      await userEvent.type(input, 'test');
      await userEvent.click(sendButton());

      await waitFor(() => {
        expect(screen.getByText('CRITICAL_ERROR: NETWORK_OFFLINE')).toBeInTheDocument();
      });
    });

    it('uses data.message when a 2xx response lacks an answer', async () => {
      setupChat({ data: { message: 'Service unavailable' } });
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
      setupGet([{ id: 1, title: 'My first chat' }]);
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
