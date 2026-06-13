import React from 'react';
import { render, screen } from '@testing-library/react';
import Marquee from './marquee';

describe('Marquee', () => {
  it('renders children content', () => {
    render(<Marquee><span>Hello World</span></Marquee>);
    // Two animated tracks, each rendering the children twice, for a seamless loop.
    expect(screen.getAllByText('Hello World')).toHaveLength(4);
  });

  it('renders children multiple times for continuous scroll effect', () => {
    render(
      <Marquee>
        <span>Item A</span>
        <span>Item B</span>
      </Marquee>
    );
    expect(screen.getAllByText('Item A')).toHaveLength(4);
    expect(screen.getAllByText('Item B')).toHaveLength(4);
  });

  it('applies default speed of 20s as animationDuration', () => {
    const { container } = render(<Marquee><span>test</span></Marquee>);
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.style.animationDuration).toBe('20s');
  });

  it('applies custom speed prop as animationDuration', () => {
    const { container } = render(<Marquee speed={45}><span>test</span></Marquee>);
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.style.animationDuration).toBe('45s');
  });

  it('adds hover:pause class when pauseOnHover is true (default)', () => {
    const { container } = render(<Marquee><span>test</span></Marquee>);
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.className).toContain('hover:[animation-play-state:paused]');
  });

  it('omits hover:pause class when pauseOnHover is false', () => {
    const { container } = render(<Marquee pauseOnHover={false}><span>test</span></Marquee>);
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.className).not.toContain('hover:[animation-play-state:paused]');
  });

  it('applies custom className to outer wrapper', () => {
    const { container } = render(<Marquee className="custom-class"><span>test</span></Marquee>);
    const outer = container.firstChild as HTMLElement;
    expect(outer.className).toContain('custom-class');
  });

  it('outer wrapper has overflow-hidden and select-none classes', () => {
    const { container } = render(<Marquee><span>test</span></Marquee>);
    const outer = container.firstChild as HTMLElement;
    expect(outer.className).toContain('overflow-hidden');
    expect(outer.className).toContain('select-none');
  });

  it('inner scroller has animate-marquee class', () => {
    const { container } = render(<Marquee><span>test</span></Marquee>);
    const inner = container.querySelector('.animate-marquee');
    expect(inner).toBeInTheDocument();
  });

  it('renders with speed=0 without crashing (edge case)', () => {
    const { container } = render(<Marquee speed={0}><span>zero</span></Marquee>);
    const inner = container.querySelector('.animate-marquee') as HTMLElement;
    expect(inner.style.animationDuration).toBe('0s');
  });
});
