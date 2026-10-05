import { NewsResult } from '../../types/market';

const trustedHosts = ['reuters.com', 'cnbctv18.com', 'economictimes.indiatimes.com', 'moneycontrol.com', 'livemint.com', 'business-standard.com', 'rbi.org.in', 'cnbc.com', 'bbc.com', 'bbc.co.uk', 'financialexpress.com', 'thehindubusinessline.com'];
export function safeNewsUrl(value: string): string | undefined {
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password || (url.port && url.port !== '443')) return;
    if (!trustedHosts.some(host => url.hostname === host || url.hostname === `www.${host}`)) return;
    return url.href;
  } catch { return; }
}

export function NewsSources({ news }: { news: NewsResult }) {
  const status = { OK: 'Recent news excerpts', NO_RECENT_NEWS: 'No recent verified news', PROVIDER_ERROR: 'News provider unavailable', CLARIFICATION: 'News topic needed' }[news.status];
  return (
    <section aria-label="News sources" className="mt-3 pt-2 border-t border-white/[0.06] space-y-2 text-[10px]">
      <p className={news.status === 'OK' ? 'text-cyan-400' : 'text-amber-400'}>{status} · {news.provider}</p>
      <p className="text-slate-400">{!news.articles.length ? 'No verified recent evidence available.' : news.cache_hit ? 'Cached evidence; original retrieval times retained.' : news.context_reused ? 'Previous news evidence; freshness checked again.' : 'New search evidence.'} Freshness window: {news.max_age_hours} hours.</p>
      {news.articles.map((article, index) => {
        const href = safeNewsUrl(article.url);
        return (
          <article key={article.url} className="bg-[#070B16]/80 rounded-lg border border-white/[0.06] p-2 space-y-1">
            {href ? <a className="text-indigo-300 hover:underline break-words" href={href} target="_blank" rel="noopener noreferrer">[{index + 1}] {article.title}</a> : <span>{article.title} (source link unavailable)</span>}
            <p className="text-slate-300">{article.publisher}</p>
            <p className="text-slate-400">Published: <time dateTime={article.published_at}>{article.published_at}</time></p>
            <p className="text-slate-400">Retrieved: <time dateTime={article.retrieved_at}>{article.retrieved_at}</time></p>
            <p className="text-slate-500">Search excerpt; full article not independently verified.</p>
            {article.snippet && <details className="text-slate-400"><summary className="cursor-pointer">View retrieved excerpt</summary><p className="mt-1 whitespace-pre-wrap break-words">{article.snippet}</p></details>}
          </article>
        );
      })}
      <p className="text-slate-500">{news.notice}</p>
    </section>
  );
}
