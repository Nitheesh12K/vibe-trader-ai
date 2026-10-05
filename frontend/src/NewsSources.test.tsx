import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { NewsSources, safeNewsUrl } from './components/assistant/NewsSources';
import { NewsResult } from './types/market';

export const fixtureNews: NewsResult = {
  status: 'OK', provider: 'ollama_local', query: 'NIFTY news', checked_at: '2026-10-04T12:00:00Z',
  cache_hit: false, context_reused: false, retrieval_ms: 14, max_age_hours: 72, rejected_results: 0,
  notice: 'Search excerpts only.', summary: 'Evidence summary [1].', possible_market_implications: 'Could affect sentiment.',
  articles: [{ title: 'NIFTY outlook', publisher: 'CNBC TV18', url: 'https://www.cnbctv18.com/market/nifty.htm',
    published_at: '2026-10-04T04:08:29Z', retrieved_at: '2026-10-04T12:00:00Z', snippet: 'Analysts watch RBI.', provider: 'ollama_local', evidence_type: 'SEARCH_EXCERPT' }],
};

describe('NewsSources', () => {
  it('shows original links and separate publication and retrieval times', () => {
    render(<NewsSources news={fixtureNews} />);
    const link = screen.getByRole('link', { name: '[1] NIFTY outlook' });
    expect(link).toHaveAttribute('href', fixtureNews.articles[0].url);
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(screen.getByText('CNBC TV18')).toBeInTheDocument();
    expect(screen.getByText('2026-10-04T04:08:29Z')).toHaveAttribute('datetime', '2026-10-04T04:08:29Z');
    expect(screen.getByText('2026-10-04T12:00:00Z')).toBeInTheDocument();
    expect(screen.getByText(/full article not independently verified/)).toBeInTheDocument();
  });
  it('labels cached evidence without changing the retrieval time', () => {
    render(<NewsSources news={{ ...fixtureNews, cache_hit: true }} />);
    expect(screen.getByText(/Cached evidence; original retrieval times retained/)).toBeInTheDocument();
    expect(screen.getByText(fixtureNews.articles[0].retrieved_at)).toBeInTheDocument();
  });
  it.each(['javascript:alert(1)', 'https://127.0.0.1/admin', 'https://cnbctv18.com.evil.test/a', 'https://user:secret@cnbctv18.com/a', 'http://cnbctv18.com/a'])('rejects unsafe source %s', url => {
    expect(safeNewsUrl(url)).toBeUndefined();
  });
  it('renders malicious headline as text with no executable markup', () => {
    const { container } = render(<NewsSources news={{ ...fixtureNews, articles: [{ ...fixtureNews.articles[0], title: '<script>alert(1)</script>', url: 'javascript:alert(1)' }] }} />);
    expect(container.querySelector('script')).toBeNull();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.getByText(/<script>alert/)).toBeInTheDocument();
  });
  it.each([
    ['NO_RECENT_NEWS', 'No recent verified news'], ['PROVIDER_ERROR', 'News provider unavailable'], ['CLARIFICATION', 'News topic needed'],
  ] as const)('displays %s status', (status, label) => {
    render(<NewsSources news={{ ...fixtureNews, status, articles: [] }} />);
    expect(screen.getByText(new RegExp(label))).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.getByText(/No verified recent evidence available/)).toBeInTheDocument();
    expect(screen.queryByText(/New search evidence/)).not.toBeInTheDocument();
  });
});
