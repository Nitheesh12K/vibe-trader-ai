import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MarketAssistantChat } from './components/assistant/MarketAssistantChat';
import { api } from './services/api';
import { NewsResult } from './types/market';

vi.mock('./services/api', () => ({
  api: {
    getAssistantStatus: vi.fn(),
    sendAssistantChat: vi.fn(),
    getAssistantChatHistory: vi.fn(),
    clearAssistantChatHistory: vi.fn(),
  },
}));

describe('MarketAssistantChat Component', () => {
  const newsFixture: NewsResult = {
    status: 'OK', provider: 'ollama_local', query: 'NIFTY news', checked_at: '2026-10-04T12:00:00Z',
    cache_hit: false, context_reused: false, retrieval_ms: 10, max_age_hours: 72, rejected_results: 0,
    notice: 'Search excerpts only.', summary: '', possible_market_implications: '',
    articles: [{ title: 'NIFTY outlook', publisher: 'CNBC TV18', url: 'https://www.cnbctv18.com/market/nifty.htm', published_at: '2026-10-04T04:08:29Z', retrieved_at: '2026-10-04T12:00:00Z', snippet: 'RBI policy outlook.', provider: 'ollama_local', evidence_type: 'SEARCH_EXCERPT' }],
  };
  it.each([
    ['Latest NIFTY news', '**Evidence summary (AI)**\nRBI policy outlook [1].', 'english'],
    ['NIFTY latest news sollunga', '**News surukkam (AI)**\nRBI policy paththi analysts paakuraanga [1].', 'tanglish'],
  ])('renders news response and source cards for %s', async (message, content, language) => {
    vi.mocked(api.sendAssistantChat).mockResolvedValue({ message_id: 'news-msg', session_id: 'test', role: 'assistant', content, news: newsFixture,
      sources: [{ tool_name: 'NewsTool', summary: 'News evidence', data_points: {} }], model_name: 'qwen3-local:latest', is_fallback: false, detected_language: language, detected_intent: 'NEWS_CURRENT', disclaimer: 'Advisory only.', created_at: '2026-10-04T12:00:00Z' });
    render(<MarketAssistantChat />);
    fireEvent.click(await screen.findByTitle('Open AI Market Copilot'));
    fireEvent.change(screen.getByPlaceholderText(/Ask about price, indicators/i), { target: { value: message } });
    fireEvent.click(screen.getByTitle('Send message'));
    expect(screen.getByText(message)).toBeInTheDocument();
    expect(await screen.findByRole('link', { name: '[1] NIFTY outlook' })).toHaveAttribute('href', newsFixture.articles[0].url);
    expect(screen.queryByText('Retrieved Grounding Sources (1)')).not.toBeInTheDocument();
    expect(screen.getByText(language === 'english' ? 'Evidence summary (AI)' : 'News surukkam (AI)')).toHaveProperty('tagName', 'STRONG');
  });
  it('shows news loading while the chat can still close and reopen', async () => {
    vi.mocked(api.sendAssistantChat).mockImplementation(() => new Promise(() => {}));
    render(<MarketAssistantChat />);
    fireEvent.click(await screen.findByTitle('Open AI Market Copilot'));
    fireEvent.change(screen.getByPlaceholderText(/Ask about price, indicators/i), { target: { value: 'What is the latest NIFTY news?' } });
    fireEvent.click(screen.getByTitle('Send message'));
    expect(screen.getByText('Checking recent news...')).toBeInTheDocument();
    expect(screen.queryByText('Analyzing market data...')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTitle('Close'));
    fireEvent.click(screen.getByTitle('Open AI Market Copilot'));
    expect(screen.getByText('Checking recent news...')).toBeInTheDocument();
    expect(api.sendAssistantChat).toHaveBeenCalledTimes(1);
  });
  it('restores news sources and fallback label from conversation history', async () => {
    vi.mocked(api.getAssistantChatHistory).mockResolvedValue([{ message_id: 'old-news', session_id: 'test', role: 'assistant', content: 'Retrieved headlines only.', news: { ...newsFixture, cache_hit: true }, sources: [], model_name: 'DETERMINISTIC_FALLBACK', is_fallback: true, created_at: '2026-10-04T12:00:00Z' }]);
    render(<MarketAssistantChat />);
    fireEvent.click(await screen.findByTitle('Open AI Market Copilot'));
    expect(await screen.findByRole('link', { name: '[1] NIFTY outlook' })).toBeInTheDocument();
    expect(screen.getByText(/Fallback response/)).toBeInTheDocument();
    expect(screen.getByText(/Cached evidence; original retrieval times retained/)).toBeInTheDocument();
  });
  it('uses neutral loading for coding questions and prevents duplicate sends', async () => {
    vi.mocked(api.sendAssistantChat).mockImplementation(() => new Promise(() => {}));
    render(<MarketAssistantChat />);
    fireEvent.click(await screen.findByTitle('Open AI Market Copilot'));
    const input = screen.getByPlaceholderText(/Ask about price, indicators/i);
    fireEvent.change(input, { target: { value: 'Write Python code' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(api.sendAssistantChat).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Write Python code')).toBeInTheDocument();
    expect(screen.getByText('Preparing response...')).toBeInTheDocument();
    expect(screen.queryByText('Analyzing market data...')).not.toBeInTheDocument();
  });

  it('shows a retry after failure and closes reliably', async () => {
    vi.mocked(api.sendAssistantChat).mockRejectedValue(new Error('Service unavailable'));
    render(<MarketAssistantChat />);
    fireEvent.click(await screen.findByTitle('Open AI Market Copilot'));
    fireEvent.change(screen.getByPlaceholderText(/Ask about price, indicators/i), { target: { value: 'Hello' } });
    fireEvent.click(screen.getByTitle('Send message'));
    expect(await screen.findByText('Service unavailable')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Retry Last Message'));
    await waitFor(() => expect(api.sendAssistantChat).toHaveBeenCalledTimes(2));
    fireEvent.click(screen.getByTitle('Close'));
    expect(screen.getByTitle('Open AI Market Copilot')).toBeInTheDocument();
  });
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(api.getAssistantStatus).mockResolvedValue({
      status: 'ONLINE',
      active_model: 'qwen3-local:latest',
      available_models: ['qwen3-local:latest'],
      host: 'http://127.0.0.1:11434',
      available_tools: ['MarketDataTool', 'TechnicalIndicatorsTool', 'PaperPortfolioTool'],
      paper_trading_mode: true,
      disclaimer: 'Advisory-only. Zero real order execution.',
    });

    vi.mocked(api.getAssistantChatHistory).mockResolvedValue([]);
  });

  it('renders the floating AI Market Copilot button initially', async () => {
    render(<MarketAssistantChat currentInstrument={{ symbol: 'RELIANCE', name: 'Reliance Industries', market: 'NSE', category: 'Energy', last_price: 2950, change: 10, change_percent: 0.34, high_24h: 2960, low_24h: 2940, volume: '1.2M', currency_symbol: '₹', is_mock: false }} />);

    const openButton = await screen.findByTitle('Open AI Market Copilot');
    expect(openButton).toBeInTheDocument();
    expect(screen.getByText('AI Market Copilot')).toBeInTheDocument();
  });

  it('opens the chat window when floating button is clicked', async () => {
    render(<MarketAssistantChat currentInstrument={{ symbol: 'RELIANCE', name: 'Reliance', market: 'NSE', category: 'Energy', last_price: 2950, change: 10, change_percent: 0.34, high_24h: 2960, low_24h: 2940, volume: '1.2M', currency_symbol: '₹', is_mock: false }} />);

    const openButton = await screen.findByTitle('Open AI Market Copilot');
    fireEvent.click(openButton);

    expect(screen.getByText('Welcome to Vibe Market Copilot')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask about price, indicators/i)).toBeInTheDocument();
    expect(screen.getAllByText(/RELIANCE/).length).toBeGreaterThanOrEqual(1);
  });

  it('sends user message and displays grounded assistant response with sources', async () => {
    vi.mocked(api.sendAssistantChat).mockResolvedValue({
      message_id: 'msg-asst-101',
      session_id: 'test-sess',
      role: 'assistant',
      content: 'RELIANCE is trading at ₹2956.64 with RSI at 48.26 indicating neutral momentum.',
      sources: [
        {
          tool_name: 'MarketDataTool',
          symbol: 'RELIANCE',
          summary: 'RELIANCE latest close: 2956.64',
          data_points: { close: 2956.64 },
        },
      ],
      model_name: 'qwen3-local:latest',
      is_fallback: false,
      disclaimer: 'Advisory only. Zero real order execution.',
      created_at: new Date().toISOString(),
    });

    render(<MarketAssistantChat currentInstrument={{ symbol: 'RELIANCE', name: 'Reliance', market: 'NSE', category: 'Energy', last_price: 2950, change: 10, change_percent: 0.34, high_24h: 2960, low_24h: 2940, volume: '1.2M', currency_symbol: '₹', is_mock: false }} />);

    // Open chat
    const openButton = await screen.findByTitle('Open AI Market Copilot');
    fireEvent.click(openButton);

    const input = screen.getByPlaceholderText(/Ask about price, indicators/i);
    fireEvent.change(input, { target: { value: 'What is the RSI on RELIANCE?' } });

    const sendBtn = screen.getByTitle('Send message');
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText('What is the RSI on RELIANCE?')).toBeInTheDocument();
      expect(screen.getByText(/RELIANCE is trading at ₹2956.64/)).toBeInTheDocument();
      expect(screen.getByText(/Retrieved Grounding Sources \(1\)/)).toBeInTheDocument();
    });
  });

  it('triggers quick prompt when clicked', async () => {
    vi.mocked(api.sendAssistantChat).mockResolvedValue({
      message_id: 'msg-asst-102',
      session_id: 'test-sess',
      role: 'assistant',
      content: 'Your virtual paper portfolio equity is ₹100,000.00 with 0 open positions.',
      sources: [],
      model_name: 'DETERMINISTIC_FALLBACK',
      is_fallback: true,
      disclaimer: 'Advisory only.',
      created_at: new Date().toISOString(),
    });

    render(<MarketAssistantChat />);

    const openButton = await screen.findByTitle('Open AI Market Copilot');
    fireEvent.click(openButton);

    const quickPromptBtn = screen.getByText(/What is my paper portfolio equity\?/i);
    fireEvent.click(quickPromptBtn);

    await waitFor(() => {
      expect(api.sendAssistantChat).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'What is my paper portfolio equity?',
        })
      );
    });
  });
});
