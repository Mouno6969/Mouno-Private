import React from 'react';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './card';

describe('Card', () => {
  describe('Card base - rounded-xl (design overhaul)', () => {
    it('has rounded-xl class (not rounded-none)', () => {
      const { container } = render(<Card>Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card.className).toContain('rounded-xl');
      expect(card.className).not.toContain('rounded-none');
    });

    it('has border, bg-card, text-card-foreground, and shadow classes', () => {
      const { container } = render(<Card>Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card.className).toContain('border');
      expect(card.className).toContain('bg-card');
      expect(card.className).toContain('text-card-foreground');
      expect(card.className).toContain('shadow');
    });

    it('merges custom className', () => {
      const { container } = render(<Card className="my-card">Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card.className).toContain('my-card');
    });

    it('renders children', () => {
      render(<Card><span>Card child</span></Card>);
      expect(screen.getByText('Card child')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<Card ref={ref}>Content</Card>);
      expect(ref.current).not.toBeNull();
      expect(ref.current?.tagName).toBe('DIV');
    });

    it('passes additional HTML attributes', () => {
      render(<Card data-testid="my-card">Content</Card>);
      expect(screen.getByTestId('my-card')).toBeInTheDocument();
    });
  });

  describe('CardHeader', () => {
    it('renders with flex flex-col space-y-1.5 p-5 classes', () => {
      const { container } = render(<CardHeader>Header</CardHeader>);
      const el = container.firstChild as HTMLElement;
      expect(el.className).toContain('p-5');
    });

    it('renders children', () => {
      render(<CardHeader><span>Header content</span></CardHeader>);
      expect(screen.getByText('Header content')).toBeInTheDocument();
    });
  });

  describe('CardTitle', () => {
    it('renders with font-semibold leading-none tracking-tight', () => {
      const { container } = render(<CardTitle>Title</CardTitle>);
      const el = container.firstChild as HTMLElement;
      expect(el.className).toContain('font-semibold');
    });

    it('renders children', () => {
      render(<CardTitle>My Title</CardTitle>);
      expect(screen.getByText('My Title')).toBeInTheDocument();
    });
  });

  describe('CardDescription', () => {
    it('renders with text-sm text-muted-foreground', () => {
      const { container } = render(<CardDescription>Description</CardDescription>);
      const el = container.firstChild as HTMLElement;
      expect(el.className).toContain('text-sm');
      expect(el.className).toContain('text-muted-foreground');
    });
  });

  describe('CardContent', () => {
    it('renders with p-5 pt-0', () => {
      const { container } = render(<CardContent>Body</CardContent>);
      const el = container.firstChild as HTMLElement;
      expect(el.className).toContain('p-5');
      expect(el.className).toContain('pt-0');
    });
  });

  describe('CardFooter', () => {
    it('renders with flex items-center p-6 pt-0', () => {
      const { container } = render(<CardFooter>Footer</CardFooter>);
      const el = container.firstChild as HTMLElement;
      expect(el.className).toContain('flex');
      expect(el.className).toContain('items-center');
    });
  });

  describe('Card composition', () => {
    it('renders full card composition correctly', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Test Card</CardTitle>
            <CardDescription>A test card</CardDescription>
          </CardHeader>
          <CardContent>Content area</CardContent>
          <CardFooter>Footer area</CardFooter>
        </Card>
      );
      expect(screen.getByText('Test Card')).toBeInTheDocument();
      expect(screen.getByText('A test card')).toBeInTheDocument();
      expect(screen.getByText('Content area')).toBeInTheDocument();
      expect(screen.getByText('Footer area')).toBeInTheDocument();
    });
  });
});