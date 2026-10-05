import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Sparkles,
  Send,
  X,
  Minimize2,
  Maximize2,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Activity,
  Layers,
  Database,
  LineChart,
  Briefcase,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  ChatMessageResponse,
  ChatSourceItem,
  NewsResult,
  AssistantStatusResponse,
  InstrumentItem,
  MarketType,
} from '../../types/market';
import { SafeMarkdown } from './SafeMarkdown';
import { NewsSources } from './NewsSources';

interface MarketAssistantChatProps {
  currentInstrument?: InstrumentItem | null;
  timeframe?: string;
}

export const MarketAssistantChat: React.FC<MarketAssistantChatProps> = ({
  currentInstrument,
  timeframe = '1D',
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string>(() => {
    const saved = localStorage.getItem('vibe_assistant_session_id');
    if (saved) return saved;
    const newId = `sess-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 7)}`;
    localStorage.setItem('vibe_assistant_session_id', newId);
    return newId;
  });

  const [messages, setMessages] = useState<
    Array<{
      id: string;
      role: 'user' | 'assistant';
      content: string;
      sources?: ChatSourceItem[];
      news?: NewsResult | null;
      model_name?: string;
      is_fallback?: boolean;
      detected_language?: string;
      detected_intent?: string;
      routing_time_ms?: number;
      tool_latency_ms?: number;
      inference_latency_ms?: number;
      total_latency_ms?: number;
      created_at: string;
    }>
  >([]);

  const [inputText, setInputText] = useState<string>('');
  const [activeQuery, setActiveQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFailedQuery, setLastFailedQuery] = useState<string | null>(null);
  const [status, setStatus] = useState<AssistantStatusResponse | null>(null);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sendingRef = useRef(false);
  const conversationVersion = useRef(0);

  // Auto-scroll to bottom of message thread
  const scrollToBottom = () => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const getLoadingDetails = (query: string) => {
    const q = query.trim().toLowerCase();
    if (/\b(this news|that news|these headlines|intha news|indha news|this announcement|that announcement)\b/.test(q)) {
      return { title: 'Reviewing previous news...', subtitle: 'Checking the prior evidence and its freshness.' };
    }
    const newsWords = /\b(news|headlines|announcements?)\b/.test(q);
    const currentNews = /\b(latest|recent|today|current|now|innaiku|ippo)\b/.test(q);
    if ((newsWords && (currentNews || !/^(what is|define|how does|how do)\b/.test(q))) || /what.?s happening.*today/i.test(q)) {
      return { title: 'Checking recent news...', subtitle: 'Retrieving relevant sources and checking publication times.' };
    }

    // 1. Greeting
    if (/^(hi|hello|hey|vanakkam|good morning|good evening)/i.test(q) && q.split(/\s+/).length <= 4) {
      return {
        title: 'Greeting assistant...',
        subtitle: 'Preparing conversational response (0 tools invoked).',
      };
    }
    // 2. Educational
    if (
      /^(what is|what are|what does|explain|how does|how do|define|meaning of|concept of)/i.test(q) ||
      /(na enna|nu enna|epdi work aagum)/i.test(q)
    ) {
      return {
        title: 'Preparing explanation...',
        subtitle: 'Answering your question; live market data is requested only for analysis.',
      };
    }
    // 3. Portfolio
    if (/(portfolio|balance|equity|cash|pnl|profit|open positions)/i.test(q)) {
      return {
        title: 'Querying paper portfolio...',
        subtitle: 'Retrieving simulated account balance and open paper positions.',
      };
    }
    // 4. Risk
    if (/(risk|drawdown|emergency stop|daily loss limit|max risk)/i.test(q)) {
      return {
        title: 'Inspecting Risk Guardian...',
        subtitle: 'Retrieving safety ceilings, loss limit status, and account exposure.',
      };
    }
    // 5. Strategy
    if (/(strategy|signal|why buy|why sell)/i.test(q)) {
      return {
        title: 'Retrieving recorded strategy context...',
        subtitle: 'Looking for the saved signal and its original evidence.',
      };
    }
    // 6. Technical Analysis
    if (/(rsi|macd|ema|sma|atr|vwap|adx|bollinger|pattern|candlestick|support|resistance)/i.test(q)) {
      return {
        title: 'Computing technical indicators...',
        subtitle: 'Calculating requested indicators and chart patterns.',
      };
    }
    // Activity is provisional until the backend routes the request.
    return {
      title: 'Preparing response...',
      subtitle: 'Answering your question; relevant data is retrieved only when needed.',
    };
  };

  useEffect(() => {
    if (isOpen && !isMinimized) {
      scrollToBottom();
    }
  }, [messages, isOpen, isMinimized, loading]);

  // Load status and chat history on mount
  useEffect(() => {
    fetchStatus();
    loadHistory(sessionId);
  }, [sessionId]);

  const fetchStatus = async () => {
    try {
      const s = await api.getAssistantStatus();
      setStatus(s);
    } catch (e) {
      console.warn('Failed to fetch assistant status:', e);
    }
  };

  const loadHistory = async (sessId: string) => {
    const version = conversationVersion.current;
    try {
      const history = await api.getAssistantChatHistory(sessId);
      if (history && history.length > 0 && version === conversationVersion.current) {
        setMessages(
          history.map((h) => ({
            id: h.message_id,
            role: h.role as 'user' | 'assistant',
            content: h.content,
            sources: h.sources,
            news: h.news,
            model_name: h.model_name,
            is_fallback: h.is_fallback,
            detected_language: h.detected_language,
            detected_intent: h.detected_intent,
            routing_time_ms: h.routing_time_ms,
            tool_latency_ms: h.tool_latency_ms,
            inference_latency_ms: h.inference_latency_ms,
            total_latency_ms: h.total_latency_ms,
            created_at: h.created_at,
          }))
        );
      }
    } catch (e) {
      console.warn('Failed to load chat history:', e);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query || sendingRef.current) return;
    sendingRef.current = true;
    conversationVersion.current += 1;

    setError(null);
    setLastFailedQuery(null);
    setInputText('');
    setActiveQuery(query);

    const tempUserMsgId = `temp-user-${Date.now()}`;
    const userMsg = {
      id: tempUserMsgId,
      role: 'user' as const,
      content: query,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await api.sendAssistantChat({
        session_id: sessionId,
        message: query,
        symbol: currentInstrument?.symbol,
        market: currentInstrument?.market,
        timeframe: timeframe,
      });

      const asstMsg = {
        id: response.message_id,
        role: 'assistant' as const,
        content: response.content,
        sources: response.sources,
        news: response.news,
        model_name: response.model_name,
        is_fallback: response.is_fallback,
        detected_language: response.detected_language,
        detected_intent: response.detected_intent,
        routing_time_ms: response.routing_time_ms,
        tool_latency_ms: response.tool_latency_ms,
        inference_latency_ms: response.inference_latency_ms,
        total_latency_ms: response.total_latency_ms,
        created_at: response.created_at,
      };

      setMessages((prev) => [...prev, asstMsg]);
    } catch (err: any) {
      console.error('Chat error:', err);
      setError(err?.message || 'Failed to communicate with AI Assistant. Please retry.');
      setLastFailedQuery(query);
    } finally {
      sendingRef.current = false;
      setLoading(false);
      // Refocus input
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleClearHistory = async () => {
    if (confirm('Clear chat history for this session?')) {
      try {
        await api.clearAssistantChatHistory(sessionId);
        conversationVersion.current += 1;
        setMessages([]);
        setError(null);
        setLastFailedQuery(null);
      } catch (err: any) {
        console.error('Failed to clear history:', err);
      }
    }
  };

  const toggleSourceExpand = (msgId: string) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const quickPrompts = [
    currentInstrument ? `Technical setup on ${currentInstrument.symbol}` : 'Technical setup on RELIANCE',
    'What is my paper portfolio equity?',
    'Check NIFTY 50 trend and RSI',
    'Is EUR/USD in a bullish or bearish regime?',
  ];

  return (
    <>
      {/* 1. Floating Toggle Button (Always visible bottom-right) */}
      {!isOpen && (
        <button
          onClick={() => {
            setIsOpen(true);
            setIsMinimized(false);
          }}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 text-white rounded-full shadow-xl shadow-indigo-500/25 border border-indigo-400/30 hover:scale-105 active:scale-95 transition-all group font-medium text-xs tracking-wide"
          title="Open AI Market Copilot"
        >
          <div className="relative">
            <Sparkles className="w-4 h-4 text-indigo-200 group-hover:rotate-12 transition-transform" />
            <span
              className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full ${
                status?.status === 'ONLINE' ? 'bg-emerald-400 ring-2 ring-indigo-900' : 'bg-amber-400'
              }`}
            />
          </div>
          <span>AI Market Copilot</span>
          <span className="text-[10px] bg-white/15 px-1.5 py-0.5 rounded-full font-mono">
            {status?.status === 'ONLINE' ? 'Qwen' : 'Fallback'}
          </span>
        </button>
      )}

      {/* 2. Floating Chat Window */}
      {isOpen && (
        <div
          className={`fixed bottom-6 right-6 z-50 bg-[#0B101D]/95 backdrop-blur-2xl border border-indigo-500/30 shadow-2xl shadow-black/80 rounded-2xl flex flex-col overflow-hidden transition-all duration-200 ${
            isMinimized
              ? 'w-80 h-14'
              : 'w-[440px] max-w-[calc(100vw-2rem)] h-[600px] max-h-[calc(100vh-5rem)]'
          }`}
        >
          {/* Header */}
          <div className="px-4 py-3 bg-gradient-to-r from-[#0E1528] to-[#121A33] border-b border-white/[0.08] flex items-center justify-between gap-3 shrink-0">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-xs font-bold text-white tracking-wide truncate">
                    AI Market Copilot
                  </h3>
                  <span
                    className={`inline-flex items-center gap-1 text-[9px] px-1.5 py-0.2 rounded font-mono border ${
                      status?.status === 'ONLINE'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        status?.status === 'ONLINE' ? 'bg-emerald-400' : 'bg-amber-400'
                      }`}
                    />
                    {status?.status === 'ONLINE' ? 'Local Qwen' : 'Fallback'}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 truncate">
                  Advisory Quantitative Research Assistant
                </p>
              </div>
            </div>

            {/* Header Action Buttons */}
            <div className="flex items-center gap-1 shrink-0 text-slate-400">
              <button
                onClick={handleClearHistory}
                className="p-1.5 hover:text-rose-400 hover:bg-white/[0.06] rounded-lg transition-colors"
                title="Clear Chat History"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={fetchStatus}
                className="p-1.5 hover:text-slate-200 hover:bg-white/[0.06] rounded-lg transition-colors"
                title="Refresh Status"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1.5 hover:text-slate-200 hover:bg-white/[0.06] rounded-lg transition-colors"
                title={isMinimized ? 'Expand' : 'Minimize'}
              >
                {isMinimized ? <Maximize2 className="w-3.5 h-3.5" /> : <Minimize2 className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:text-rose-400 hover:bg-white/[0.06] rounded-lg transition-colors"
                title="Close"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Main Body (Collapsed when minimized) */}
          {!isMinimized && (
            <>
              {/* Context Pill Bar */}
              <div className="px-4 py-1.5 bg-[#070B16] border-b border-white/[0.04] flex items-center justify-between text-[10px] font-mono text-slate-400">
                <div className="flex items-center gap-1.5 truncate">
                  <span className="text-slate-500">Active Context:</span>
                  {currentInstrument ? (
                    <span className="text-cyan-400 font-semibold truncate">
                      {currentInstrument.symbol} ({timeframe}, {currentInstrument.market})
                    </span>
                  ) : (
                    <span className="text-slate-400 italic">No instrument selected</span>
                  )}
                </div>
                <span className="text-indigo-400/80 bg-indigo-500/10 px-1.5 py-0.5 rounded text-[9px] border border-indigo-500/20">
                  Paper Trading Only
                </span>
              </div>

              {/* Message List */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
                {messages.length === 0 && (
                  <div className="py-6 text-center space-y-3">
                    <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
                      <Sparkles className="w-6 h-6" />
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-semibold text-white text-sm">
                        Welcome to Vibe Market Copilot
                      </h4>
                      <p className="text-slate-400 text-xs max-w-xs mx-auto leading-relaxed">
                      Ask general questions, retrieve recent news with sources, or explore saved market data, strategy signals, and your paper portfolio.
                      </p>
                    </div>

                    {/* Quick prompts */}
                    <div className="pt-2 text-left space-y-1.5">
                      <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold px-1">
                        Suggested Inquiries:
                      </p>
                      <div className="flex flex-col gap-1.5">
                        {quickPrompts.map((q, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSendMessage(q)}
                            className="text-left text-xs bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.06] hover:border-indigo-500/30 text-slate-300 hover:text-white px-3 py-2 rounded-xl transition-all"
                          >
                            💬 {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-[92%] rounded-2xl p-3.5 space-y-2 leading-relaxed ${
                        m.role === 'user'
                          ? 'bg-indigo-600/90 text-white rounded-tr-none shadow-md shadow-indigo-600/10'
                          : 'bg-[#121A2F]/90 text-slate-200 border border-white/[0.08] rounded-tl-none shadow-md shadow-black/20'
                      }`}
                    >
                      {/* Role Header (for Assistant) */}
                      {m.role === 'assistant' && (
                        <div className="flex items-center justify-between gap-2 border-b border-white/[0.06] pb-1.5 mb-1.5 text-[10px] font-mono flex-wrap">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {m.is_fallback ? (
                              <span className="flex items-center gap-1.5 text-amber-400 font-semibold bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                                <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />
                                <span>Deterministic Fallback</span>
                              </span>
                            ) : m.model_name?.includes('qwen') ? (
                              <span className="flex items-center gap-1.5 text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                                <Sparkles className="w-3 h-3 text-emerald-400 shrink-0" />
                                <span>Local Qwen AI</span>
                              </span>
                            ) : (
                              <span className="flex items-center gap-1.5 text-indigo-300 font-semibold bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                                <Bot className="w-3 h-3 text-indigo-400 shrink-0" />
                                <span>Built-in Assistant</span>
                              </span>
                            )}

                            {m.detected_intent && (
                              <span className="text-[9px] bg-slate-800 text-indigo-300 px-1.5 py-0.5 rounded font-mono border border-slate-700/60 font-semibold">
                                {m.detected_intent}
                              </span>
                            )}

                            {m.total_latency_ms !== undefined && m.total_latency_ms > 0 && (
                              <span
                                className="text-[9px] text-slate-400 font-mono bg-slate-800/60 px-1.5 py-0.5 rounded border border-slate-700/40"
                                title={`Route: ${m.routing_time_ms || 0}ms | Tools: ${m.tool_latency_ms || 0}ms | Infer: ${m.inference_latency_ms || 0}ms`}
                              >
                                ⏱️ {Math.round(m.total_latency_ms)}ms
                              </span>
                            )}
                          </div>

                          <span className="text-slate-400 text-[9px]">
                            {new Date(m.created_at).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                      )}

                      {/* Content with Safe Markdown */}
                      <div className="text-xs sm:text-[13px] leading-relaxed break-words font-sans">
                        {m.role === 'assistant' ? (
                          <SafeMarkdown content={m.content} />
                        ) : (
                          <div className="whitespace-pre-wrap">{m.content}</div>
                        )}
                      </div>

                      {/* Sources Accordion (Assistant only) */}
                      {m.news && <NewsSources news={m.news} />}
                      {m.sources && m.sources.some(src => src.tool_name !== 'NewsTool') && (
                        <div className="mt-2 pt-2 border-t border-white/[0.06]">
                          <button
                            onClick={() => toggleSourceExpand(m.id)}
                            className="flex items-center gap-1.5 text-[10px] font-mono text-indigo-400 hover:text-indigo-300 transition-colors"
                          >
                            <Database className="w-3 h-3" />
                            <span>
                              Retrieved Grounding Sources ({m.sources.filter(src => src.tool_name !== 'NewsTool').length})
                            </span>
                            {expandedSources[m.id] ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )}
                          </button>

                          {expandedSources[m.id] && (
                            <div className="mt-2 space-y-1.5 pl-2 border-l border-indigo-500/20">
                              {m.sources.filter(src => src.tool_name !== 'NewsTool').map((src, sIdx) => (
                                <div
                                  key={sIdx}
                                  className="text-[10px] bg-[#070B16]/80 p-2 rounded-lg border border-white/[0.04] space-y-0.5"
                                >
                                  <div className="flex items-center justify-between text-slate-400 font-mono font-semibold">
                                    <span className="text-cyan-400">{src.tool_name}</span>
                                    <span>{src.timestamp || 'Timestamp unavailable'}</span>
                                  </div>
                                  <p className="text-slate-300 font-sans">{src.summary}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Fallback Warning Flag */}
                      {m.is_fallback && (
                        <div className="mt-1 flex items-center gap-1 text-[10px] text-amber-400 font-mono bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                          <AlertTriangle className="w-3 h-3 shrink-0" />
                          <span>Fallback response — local AI answer unavailable.</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {/* Loading Indicator */}
                {loading && (() => {
                  const details = getLoadingDetails(activeQuery);
                  return (
                    <div className="flex items-start gap-2.5">
                      <div className="w-6 h-6 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                        <Bot className="w-3.5 h-3.5 animate-pulse" />
                      </div>
                      <div className="bg-[#121A2F]/90 border border-white/[0.08] rounded-2xl rounded-tl-none p-3 space-y-1 text-slate-300 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
                          <span className="font-mono text-[11px] text-indigo-300 font-semibold">
                            {details.title}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-400">
                          {details.subtitle}
                        </p>
                      </div>
                    </div>
                  );
                })()}

                {/* Error Banner with Retry */}
                {error && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/25 rounded-xl space-y-2 text-xs text-rose-300">
                    <div className="flex items-center gap-2 font-semibold">
                      <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                      <span>{error}</span>
                    </div>
                    {lastFailedQuery && (
                      <button
                        onClick={() => handleSendMessage(lastFailedQuery)}
                        className="px-2.5 py-1 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-white rounded-lg text-[11px] font-mono transition-colors flex items-center gap-1.5"
                      >
                        <RefreshCw className="w-3 h-3" />
                        Retry Last Message
                      </button>
                    )}
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area & Safety Footer */}
              <div className="p-3 bg-[#0B101D] border-t border-white/[0.08] space-y-2">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-center gap-2"
                >
                  <textarea
                    ref={inputRef}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                  placeholder="Ask about price, indicators, news, strategy, or portfolio..."
                    rows={1}
                    className="flex-1 bg-[#121A2F]/90 border border-white/[0.1] rounded-xl px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/20 resize-none font-sans"
                    disabled={loading}
                  />

                  <button
                    type="submit"
                    disabled={!inputText.trim() || loading}
                    className="p-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl transition-all shadow-md shadow-indigo-600/20 shrink-0"
                    title="Send message"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>

                <div className="flex items-center justify-between text-[9px] text-slate-400 px-1 font-mono">
                  <span className="flex items-center gap-1">
                    <ShieldAlert className="w-3 h-3 text-amber-400" />
                    Advisory Only • Zero Real Orders
                  </span>
                  <span>Press Enter ↵</span>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
};
