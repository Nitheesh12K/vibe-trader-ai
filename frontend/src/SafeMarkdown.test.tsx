import { render, screen } from '@testing-library/react';
import React from 'react';
import { describe, it, expect } from 'vitest';
import { SafeMarkdown } from './components/assistant/SafeMarkdown';

describe('SafeMarkdown Component', () => {
  it('renders fenced code, tables, and ordered lists without interpreting code', () => {
    const { container } = render(<SafeMarkdown content={'```python\n# code **literal**\n```\n| Name | Value |\n| --- | --- |\n| RSI | **50** |\n1. First\n2. Second'} />);
    expect(container.querySelector('pre code')?.textContent).toBe('# code **literal**');
    expect(container.querySelectorAll('td')).toHaveLength(2);
    expect(container.querySelector('td strong')?.textContent).toBe('50');
    expect(container.querySelectorAll('ol li')).toHaveLength(2);
  });
  it('renders headings and bold text properly without raw symbols', () => {
    const md = `### Market Analysis for RELIANCE
The close price is **2956.64** and RSI is **48.26**.`;
    const { container } = render(<SafeMarkdown content={md} />);

    // Check heading rendered as h4
    const heading = screen.getByRole('heading', { level: 4 });
    expect(heading).toBeInTheDocument();
    expect(heading.textContent).toContain('Market Analysis for RELIANCE');

    // Check bold elements exist
    const bolds = container.querySelectorAll('strong');
    expect(bolds.length).toBe(2);
    expect(bolds[0].textContent).toBe('2956.64');
    expect(bolds[1].textContent).toBe('48.26');

    // Raw markdown tokens should NOT appear in text
    expect(container.textContent).not.toContain('###');
    expect(container.textContent).not.toContain('**2956.64**');
  });

  it('renders unordered lists properly', () => {
    const md = `- Item 1: First point
- Item 2: Second point`;
    const { container } = render(<SafeMarkdown content={md} />);

    const listItems = container.querySelectorAll('li');
    expect(listItems.length).toBe(2);
    expect(listItems[0].textContent).toContain('Item 1: First point');
    expect(listItems[1].textContent).toContain('Item 2: Second point');
  });

  it('renders inline code blocks safely', () => {
    const md = 'Deterministic signal is `BUY_CANDIDATE` with confidence `85%`.';
    const { container } = render(<SafeMarkdown content={md} />);

    const codes = container.querySelectorAll('code');
    expect(codes.length).toBe(2);
    expect(codes[0].textContent).toBe('BUY_CANDIDATE');
    expect(codes[1].textContent).toBe('85%');
  });

  it('renders blockquotes safely', () => {
    const md = '> [!NOTE] All trading is simulated paper trading.';
    const { container } = render(<SafeMarkdown content={md} />);

    expect(container.textContent).toContain('All trading is simulated paper trading.');
  });

  it('safely escapes HTML tags without executing them', () => {
    const xss = '<script>window.__pwned = true;</script><img src="x" onerror="alert(1)">';
    const { container } = render(<SafeMarkdown content={xss} />);

    // Scripts should not exist in DOM as active executable scripts
    const scripts = container.querySelectorAll('script');
    expect(scripts.length).toBe(0);

    // Text should be treated as text content
    expect(container.textContent).toContain('<script>');
  });
});
