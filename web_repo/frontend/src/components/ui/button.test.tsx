import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button, buttonVariants } from './button';

describe('Button', () => {
  describe('base styling - rounded-lg (design overhaul)', () => {
    it('has rounded-lg in the base class (not rounded-none)', () => {
      render(<Button>Click me</Button>);
      const btn = screen.getByRole('button', { name: 'Click me' });
      expect(btn.className).toContain('rounded-lg');
      expect(btn.className).not.toContain('rounded-none');
    });

    it('sm size uses rounded-md', () => {
      render(<Button size="sm">Small</Button>);
      const btn = screen.getByRole('button', { name: 'Small' });
      expect(btn.className).toContain('rounded-md');
    });

    it('lg size has rounded-lg', () => {
      render(<Button size="lg">Large</Button>);
      const btn = screen.getByRole('button', { name: 'Large' });
      expect(btn.className).toContain('rounded-lg');
    });
  });

  describe('variants', () => {
    it('renders default variant with primary background', () => {
      render(<Button variant="default">Default</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('bg-primary');
    });

    it('renders destructive variant', () => {
      render(<Button variant="destructive">Destructive</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('bg-destructive');
    });

    it('renders outline variant', () => {
      render(<Button variant="outline">Outline</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('border');
    });

    it('renders secondary variant', () => {
      render(<Button variant="secondary">Secondary</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('bg-secondary');
    });

    it('renders ghost variant', () => {
      render(<Button variant="ghost">Ghost</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('hover:bg-muted');
    });

    it('renders link variant', () => {
      render(<Button variant="link">Link</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('underline-offset-4');
    });
  });

  describe('sizes', () => {
    it('default size has h-9 px-4 py-2', () => {
      render(<Button size="default">Default</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('h-9');
    });

    it('sm size has h-8 and px-3', () => {
      render(<Button size="sm">Small</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('h-8');
      expect(btn.className).toContain('px-3');
    });

    it('lg size has h-11 and px-8', () => {
      render(<Button size="lg">Large</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('h-11');
      expect(btn.className).toContain('px-8');
    });

    it('icon size has h-9 w-9', () => {
      render(<Button size="icon">Icon</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('h-9');
      expect(btn.className).toContain('w-9');
    });
  });

  describe('disabled state', () => {
    it('is disabled when disabled prop is passed', () => {
      render(<Button disabled>Disabled</Button>);
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('has pointer-events-none class when disabled', () => {
      render(<Button disabled>Disabled</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('disabled:pointer-events-none');
    });

    it('does not fire onClick when disabled', async () => {
      const handleClick = vi.fn();
      render(<Button disabled onClick={handleClick}>Disabled</Button>);
      await userEvent.click(screen.getByRole('button'));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('asChild', () => {
    it('renders as a child element when asChild is true', () => {
      render(
        <Button asChild>
          <a href="/test">Link Button</a>
        </Button>
      );
      const link = screen.getByRole('link', { name: 'Link Button' });
      expect(link).toBeInTheDocument();
      expect(link.tagName).toBe('A');
    });
  });

  describe('custom className', () => {
    it('merges custom className with variant classes', () => {
      render(<Button className="my-custom-class">Custom</Button>);
      const btn = screen.getByRole('button');
      expect(btn.className).toContain('my-custom-class');
    });
  });

  describe('click interaction', () => {
    it('calls onClick handler when clicked', async () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click me</Button>);
      await userEvent.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('buttonVariants helper', () => {
    it('generates class string with rounded-lg for default', () => {
      const classes = buttonVariants({});
      expect(classes).toContain('rounded-lg');
    });

    it('generates class string with rounded-md for sm size', () => {
      const classes = buttonVariants({ size: 'sm' });
      expect(classes).toContain('rounded-md');
    });

    it('generates class string with rounded-lg for lg size', () => {
      const classes = buttonVariants({ size: 'lg' });
      expect(classes).toContain('rounded-lg');
    });
  });
});
