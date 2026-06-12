import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import Layout from './Layout';

// Mock AuthContext
const mockLogout = vi.fn();
const mockUseAuth = vi.fn();

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock react-i18next — return the key so we can assert on stable strings.
const mockChangeLanguage = vi.fn();
const mockI18n = {
  language: 'en',
  changeLanguage: mockChangeLanguage,
};

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: mockI18n,
  }),
}));

const renderLayout = (children = <div>Page content</div>) =>
  render(
    <MemoryRouter>
      <Layout>{children}</Layout>
    </MemoryRouter>
  );

describe('Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockI18n.language = 'en';
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      logout: mockLogout,
    });
  });

  describe('logo image', () => {
    it('renders the logo image with rounded-none + border-white', () => {
      renderLayout();
      const logo = screen.getByAltText('Logo');
      expect(logo.className).toContain('rounded-none');
      expect(logo.className).not.toContain('rounded-full');
      expect(logo.className).toContain('border-white');
    });

    it('logo links to /', () => {
      renderLayout();
      const logoLink = screen.getByAltText('Logo').closest('a');
      expect(logoLink).toHaveAttribute('href', '/');
    });
  });

  describe('grouped sidebar navigation', () => {
    it('renders the four nav group headings', () => {
      renderLayout();
      expect(screen.getAllByText('nav_trade').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('nav_wallet').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('nav_rewards').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('nav_help').length).toBeGreaterThanOrEqual(1);
    });

    it('renders a sidebar dashboard link to /', () => {
      const { container } = renderLayout();
      const aside = container.querySelector('aside') as HTMLElement;
      expect(aside).not.toBeNull();
      const dash = within(aside).getByText('nav_dashboard').closest('a');
      expect(dash).toHaveAttribute('href', '/');
    });

    it('renders trade links in the sidebar', () => {
      const { container } = renderLayout();
      const aside = container.querySelector('aside') as HTMLElement;
      expect(within(aside).getByText('buy').closest('a')).toHaveAttribute('href', '/buy');
      expect(within(aside).getByText('swap').closest('a')).toHaveAttribute('href', '/swap');
    });
  });

  describe('language toggle button', () => {
    it('shows "বাং" when language is en', () => {
      mockI18n.language = 'en';
      renderLayout();
      expect(screen.getByText('বাং')).toBeInTheDocument();
    });

    it('shows "EN" when language is bn', () => {
      mockI18n.language = 'bn';
      renderLayout();
      expect(screen.getByText('EN')).toBeInTheDocument();
    });

    it('toggles language to bn when current language is en', () => {
      mockI18n.language = 'en';
      renderLayout();
      fireEvent.click(screen.getByText('বাং').closest('button')!);
      expect(mockChangeLanguage).toHaveBeenCalledWith('bn');
    });

    it('toggles language to en when current language is bn', () => {
      mockI18n.language = 'bn';
      renderLayout();
      fireEvent.click(screen.getByText('EN').closest('button')!);
      expect(mockChangeLanguage).toHaveBeenCalledWith('en');
    });

    it('lang button has rounded-none and border classes', () => {
      renderLayout();
      const langBtn = screen.getByText('বাং').closest('button') as HTMLElement;
      expect(langBtn.className).toContain('rounded-none');
      expect(langBtn.className).toContain('border');
    });
  });

  describe('unauthenticated state', () => {
    it('shows Login and Register buttons when not logged in', () => {
      renderLayout();
      expect(screen.getByText('login')).toBeInTheDocument();
      expect(screen.getByText(/register/i)).toBeInTheDocument();
    });

    it('does not show user avatar when no token', () => {
      renderLayout();
      expect(screen.queryByText('U')).not.toBeInTheDocument();
    });
  });

  describe('authenticated state', () => {
    it('shows user initial when logged in', () => {
      mockUseAuth.mockReturnValue({
        user: { username: 'testuser', telegram_id: null },
        token: 'fake-token',
        logout: mockLogout,
      });
      renderLayout();
      expect(screen.getByText('T')).toBeInTheDocument();
    });

    it('shows "U" as fallback when username is empty', () => {
      mockUseAuth.mockReturnValue({
        user: { username: '', telegram_id: null },
        token: 'fake-token',
        logout: mockLogout,
      });
      renderLayout();
      expect(screen.getByText('U')).toBeInTheDocument();
    });

    it('does not show Login/Register when logged in', () => {
      mockUseAuth.mockReturnValue({
        user: { username: 'alice', telegram_id: null },
        token: 'abc123',
        logout: mockLogout,
      });
      renderLayout();
      expect(screen.queryByText('login')).not.toBeInTheDocument();
    });

    it('user initial button has rounded-none class', () => {
      mockUseAuth.mockReturnValue({
        user: { username: 'alice', telegram_id: null },
        token: 'abc123',
        logout: mockLogout,
      });
      renderLayout();
      const btn = screen.getByText('A').closest('button') as HTMLElement;
      expect(btn.className).toContain('rounded-none');
    });
  });

  describe('mobile "More" sheet', () => {
    it('is hidden initially', () => {
      const { container } = renderLayout();
      expect(container.querySelector('.fixed.inset-0')).not.toBeInTheDocument();
    });

    it('opens when the More button is clicked', () => {
      renderLayout();
      const moreBtn = screen.getByLabelText('nav_more');
      fireEvent.click(moreBtn);
      // The sheet shows grouped headings (now duplicated: sidebar + sheet).
      expect(screen.getAllByText('nav_trade').length).toBeGreaterThan(1);
    });
  });

  describe('children rendering', () => {
    it('renders children inside main', () => {
      renderLayout(<div data-testid="child-content">Hello Child</div>);
      expect(screen.getByTestId('child-content')).toBeInTheDocument();
    });
  });

  describe('user dropdown (authenticated)', () => {
    it('renders the account trigger when logged in', () => {
      mockUseAuth.mockReturnValue({
        user: { username: 'alice', telegram_id: '12345' },
        token: 'abc123',
        logout: mockLogout,
      });
      renderLayout();
      const userBtn = screen.getByText('A').closest('button') as HTMLButtonElement;
      expect(userBtn).toHaveAttribute('aria-label', 'Account menu');
    });
  });
});
