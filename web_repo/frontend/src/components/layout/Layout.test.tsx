import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from './Layout';

// Mock AuthContext
const mockLogout = jest.fn();
const mockUseAuth = jest.fn();

jest.mock('../../context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock react-i18next
const mockChangeLanguage = jest.fn();
const mockI18n = {
  language: 'en',
  changeLanguage: mockChangeLanguage,
};

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: mockI18n,
  }),
}));

const renderLayout = (children = <div>Page content</div>) => {
  return render(
    <MemoryRouter>
      <Layout>{children}</Layout>
    </MemoryRouter>
  );
};

describe('Layout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockI18n.language = 'en';
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      logout: mockLogout,
    });
  });

  describe('logo image', () => {
    it('renders the logo image with rounded-none class (PR change)', () => {
      renderLayout();
      const logo = screen.getByAltText('Logo');
      expect(logo.className).toContain('rounded-none');
      expect(logo.className).not.toContain('rounded-full');
    });

    it('renders logo with border-white class (PR change)', () => {
      renderLayout();
      const logo = screen.getByAltText('Logo');
      expect(logo.className).toContain('border-white');
    });

    it('logo links to /', () => {
      renderLayout();
      const logoLink = screen.getByAltText('Logo').closest('a');
      expect(logoLink).toHaveAttribute('href', '/');
    });
  });

  describe('navigation styling (PR change)', () => {
    it('nav container has text-xs uppercase tracking-widest font-mono classes', () => {
      const { container } = renderLayout();
      // Find the hidden md:flex nav div
      const navDiv = container.querySelector('.hidden.md\\:flex') as HTMLElement;
      expect(navDiv).not.toBeNull();
      expect(navDiv.className).toContain('text-xs');
      expect(navDiv.className).toContain('uppercase');
      expect(navDiv.className).toContain('tracking-widest');
      expect(navDiv.className).toContain('font-mono');
    });

    it('nav does NOT have text-sm font-medium classes (was changed)', () => {
      const { container } = renderLayout();
      const navDiv = container.querySelector('.hidden.md\\:flex') as HTMLElement;
      // It should now use text-xs instead of text-sm for the nav
      expect(navDiv.className).not.toContain('text-sm font-medium');
    });
  });

  describe('language toggle button (PR change)', () => {
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

    it('lang button has rounded-none and border classes (PR change)', () => {
      renderLayout();
      // Find button containing the language text
      const langBtn = screen.getByText('বাং').closest('button') as HTMLElement;
      expect(langBtn.className).toContain('rounded-none');
      expect(langBtn.className).toContain('border');
    });

    it('lang button span has font-mono class (PR change)', () => {
      renderLayout();
      const span = screen.getByText('বাং');
      expect(span.className).toContain('font-mono');
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
      // The user div (showing initial letter) should not be present
      expect(screen.queryByText('U')).not.toBeInTheDocument();
    });
  });

  describe('authenticated state (PR change - removed Avatar component)', () => {
    it('shows user initial in a div (not Avatar) when logged in', () => {
      mockUseAuth.mockReturnValue({
        user: { username: 'testuser', telegram_id: null },
        token: 'fake-token',
        logout: mockLogout,
      });
      renderLayout();
      // Shows first letter of username
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

    it('user initial button has rounded-none class (PR change)', () => {
      mockUseAuth.mockReturnValue({
        user: { username: 'alice', telegram_id: null },
        token: 'abc123',
        logout: mockLogout,
      });
      const { container } = renderLayout();
      // The trigger button wrapping the user initial
      const btn = screen.getByText('A').closest('button') as HTMLElement;
      expect(btn.className).toContain('rounded-none');
    });
  });

  describe('mobile menu', () => {
    it('mobile menu is hidden initially', () => {
      renderLayout();
      // The fixed inset-0 overlay should not be visible initially
      const { container } = render(
        <MemoryRouter>
          <Layout>child</Layout>
        </MemoryRouter>
      );
      expect(container.querySelector('.fixed.inset-0')).not.toBeInTheDocument();
    });

    it('opens mobile menu when hamburger button is clicked', () => {
      const { container } = render(
        <MemoryRouter>
          <Layout>child</Layout>
        </MemoryRouter>
      );
      // Find the menu toggle button (md:hidden)
      const menuBtn = container.querySelector('button.md\\:hidden') as HTMLButtonElement;
      if (menuBtn) {
        fireEvent.click(menuBtn);
        expect(container.querySelector('.fixed.inset-0')).toBeInTheDocument();
      }
    });
  });

  describe('children rendering', () => {
    it('renders children inside main', () => {
      renderLayout(<div data-testid="child-content">Hello Child</div>);
      expect(screen.getByTestId('child-content')).toBeInTheDocument();
    });
  });

  describe('user dropdown (authenticated)', () => {
    it('shows username in dropdown', async () => {
      mockUseAuth.mockReturnValue({
        user: { username: 'alice', telegram_id: '12345' },
        token: 'abc123',
        logout: mockLogout,
      });
      renderLayout();
      // Open dropdown
      const userBtn = screen.getByText('A').closest('button') as HTMLButtonElement;
      fireEvent.click(userBtn);
      expect(await screen.findByText('alice')).toBeInTheDocument();
    });
  });
});