import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import Marquee from './marquee';

describe('Marquee', () => {
  it('renders children content twice for a seamless loop', () => {
    render(
      <Marquee>
        <span>Hello World</span>
      </Marquee>,
    );
    expect(screen.getAllByText('Hello World')).toHaveLength(2);
  });

  it('renders children multiple times for continuous scroll effect', () => {
    render(
      <Marquee>
        <span>Item A</span>
        <span>Item B</span>
      </Marquee>,
    );
    expect(screen.getAllByText('Item A')).toHaveLength(2);
    expect(screen.getAllByText('Item B')).toHaveLength(2);
  });

  it('applies default speed of 20s as animationDuration', () => {
    const { container } = render(
      <Marquee>
        <span>test</span>
      </Marquee>,
    );
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.style.animationDuration).toBe('20s');
  });

  it('applies custom speed prop as animationDuration', () => {
    const { container } = render(
      <Marquee speed={45}>
        <span>test</span>
      </Marquee>,
    );
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.style.animationDuration).toBe('45s');
  });

  it('does not pause on hover/touch by default', () => {
    const { container } = render(
      <Marquee>
        <span>test</span>
      </Marquee>,
    );
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.className).not.toContain('animation-play-state:paused');
  });

  it('adds fine-pointer hover pause class when pauseOnHover is true', () => {
    const { container } = render(
      <Marquee pauseOnHover>
        <span>test</span>
      </Marquee>,
    );
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.className).toContain('[@media(hover:hover)_and_(pointer:fine)]:hover:[animation-play-state:paused]');
  });

  it('applies custom className to outer wrapper', () => {
    const { container } = render(
      <Marquee className="custom-class">
        <span>test</span>
      </Marquee>,
    );
    const outer = container.firstChild as HTMLElement;
    expect(outer.className).toContain('custom-class');
  });

  it('outer wrapper has overflow-hidden and select-none classes', () => {
    const { container } = render(
      <Marquee>
        <span>test</span>
      </Marquee>,
    );
    const outer = container.firstChild as HTMLElement;
    expect(outer.className).toContain('overflow-hidden');
    expect(outer.className).toContain('select-none');
  });

  it('uses a single animated track', () => {
    const { container } = render(
      <Marquee>
        <span>test</span>
      </Marquee>,
    );
    expect(container.querySelectorAll('.animate-marquee')).toHaveLength(1);
  });

  it('animated track ignores pointer events so touch does not pause scroll', () => {
    const { container } = render(
      <Marquee>
        <span>test</span>
      </Marquee>,
    );
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.className).toContain('pointer-events-none');
  });

  it('renders with speed=0 without crashing (edge case)', () => {
    const { container } = render(
      <Marquee speed={0}>
        <span>zero</span>
      </Marquee>,
    );
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.style.animationDuration).toBe('0s');
  });
});