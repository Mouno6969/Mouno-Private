import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from './input';

describe('Input', () => {
  describe('styling - rounded-none (PR change)', () => {
    it('has rounded-none class (not rounded-md)', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('rounded-none');
      expect(input.className).not.toContain('rounded-md');
    });

    it('has border and border-input classes', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('border');
      expect(input.className).toContain('border-input');
    });

    it('has h-9 w-full classes', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('h-9');
      expect(input.className).toContain('w-full');
    });

    it('has focus-visible:ring-1 focus-visible:ring-ring classes', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('focus-visible:ring-1');
    });
  });

  describe('custom className', () => {
    it('merges custom className with default classes', () => {
      render(<Input className="custom-input" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('custom-input');
    });

    it('custom class can override via tailwind-merge', () => {
      render(<Input className="pl-7" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('pl-7');
    });
  });

  describe('type prop', () => {
    it('renders as text input by default', () => {
      render(<Input />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders as password input when type is password', () => {
      const { container } = render(<Input type="password" />);
      const input = container.querySelector('input') as HTMLInputElement;
      expect(input.type).toBe('password');
    });

    it('renders with specified type attribute', () => {
      const { container } = render(<Input type="email" />);
      const input = container.querySelector('input') as HTMLInputElement;
      expect(input.type).toBe('email');
    });
  });

  describe('disabled state', () => {
    it('is disabled when disabled prop is passed', () => {
      render(<Input disabled />);
      expect(screen.getByRole('textbox')).toBeDisabled();
    });

    it('has disabled:cursor-not-allowed class', () => {
      render(<Input disabled />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('disabled:cursor-not-allowed');
    });

    it('does not accept user input when disabled', async () => {
      render(<Input disabled placeholder="Enter text" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      await userEvent.type(input, 'hello');
      expect(input.value).toBe('');
    });
  });

  describe('placeholder', () => {
    it('renders with placeholder text', () => {
      render(<Input placeholder="Type here..." />);
      expect(screen.getByPlaceholderText('Type here...')).toBeInTheDocument();
    });
  });

  describe('ref forwarding', () => {
    it('forwards ref to the underlying input element', () => {
      const ref = React.createRef<HTMLInputElement>();
      render(<Input ref={ref} />);
      expect(ref.current).not.toBeNull();
      expect(ref.current?.tagName).toBe('INPUT');
    });
  });

  describe('user interactions', () => {
    it('accepts user typed input', async () => {
      render(<Input />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      await userEvent.type(input, 'hello world');
      expect(input.value).toBe('hello world');
    });

    it('calls onChange handler when value changes', async () => {
      const handleChange = jest.fn();
      render(<Input onChange={handleChange} />);
      await userEvent.type(screen.getByRole('textbox'), 'a');
      expect(handleChange).toHaveBeenCalled();
    });
  });

  describe('controlled value', () => {
    it('renders with controlled value', () => {
      render(<Input value="controlled" onChange={() => {}} />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('controlled');
    });
  });
});