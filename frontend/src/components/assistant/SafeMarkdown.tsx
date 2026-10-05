import React from 'react';

interface SafeMarkdownProps {
  content: string;
  className?: string;
}

/**
 * Parses inline formatting: **bold**, *italic*, `code`.
 * Returns array of React nodes. Completely XSS-safe (uses React JSX, no dangerouslySetInnerHTML).
 */
function renderInlineTokens(text: string): React.ReactNode[] {
  const tokens: React.ReactNode[] = [];
  // Regex to match `code`, **bold**, or *italic*
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    // Add plain text before match
    if (match.index > lastIndex) {
      tokens.push(text.substring(lastIndex, match.index));
    }

    const token = match[0];
    if (token.startsWith('`') && token.endsWith('`')) {
      tokens.push(
        <code
          key={`c-${match.index}`}
          className="px-1.5 py-0.5 rounded bg-black/40 border border-white/10 text-cyan-300 font-mono text-[11px]"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith('**') && token.endsWith('**')) {
      tokens.push(
        <strong key={`b-${match.index}`} className="font-semibold text-white">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith('*') && token.endsWith('*')) {
      tokens.push(
        <em key={`i-${match.index}`} className="italic text-slate-300">
          {token.slice(1, -1)}
        </em>
      );
    }

    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < text.length) {
    tokens.push(text.substring(lastIndex));
  }

  return tokens.length > 0 ? tokens : [text];
}

export const SafeMarkdown: React.FC<SafeMarkdownProps> = ({ content, className = '' }) => {
  if (!content) return null;

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let currentList: React.ReactNode[] = [];
  let currentQuote: string[] = [];
  let codeLines: string[] | null = null;
  let tableRows: string[][] = [];
  const flushTable = (key: number) => {
    if (!tableRows.length) return;
    const [header, ...body] = tableRows;
    elements.push(<div key={`table-${key}`} className="overflow-x-auto"><table className="text-xs border-collapse w-full"><thead><tr>{header.map((cell, i) => <th key={i} className="border border-white/10 p-2 text-left">{renderInlineTokens(cell)}</th>)}</tr></thead><tbody>{body.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j} className="border border-white/10 p-2">{renderInlineTokens(cell)}</td>)}</tr>)}</tbody></table></div>);
    tableRows = [];
  };

  const flushList = (key: number) => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`ul-${key}`} className="space-y-1 my-1.5 pl-1">
          {currentList}
        </ul>
      );
      currentList = [];
    }
  };

  const flushQuote = (key: number) => {
    if (currentQuote.length > 0) {
      const quoteText = currentQuote.join(' ');
      const isNote = quoteText.includes('[!NOTE]');
      const cleanQuote = quoteText.replace(/\[!NOTE\]/g, '').trim();

      elements.push(
        <div
          key={`quote-${key}`}
          className={`my-2 p-2.5 rounded-xl border text-xs leading-relaxed ${
            isNote
              ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-200'
              : 'bg-slate-800/50 border-slate-700/60 text-slate-300 italic'
          }`}
        >
          {renderInlineTokens(cleanQuote)}
        </div>
      );
      currentQuote = [];
    }
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (trimmed.startsWith('```')) {
      flushList(idx); flushQuote(idx); flushTable(idx);
      if (codeLines !== null) {
        elements.push(<pre key={`code-${idx}`} className="overflow-x-auto p-2 bg-black/40 rounded"><code>{codeLines.join('\n')}</code></pre>);
        codeLines = null;
      } else codeLines = [];
      return;
    }
    if (codeLines !== null) { codeLines.push(line); return; }
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      flushList(idx); flushQuote(idx);
      const cells = trimmed.slice(1, -1).split('|').map(cell => cell.trim());
      if (!cells.every(cell => /^:?-{3,}:?$/.test(cell))) tableRows.push(cells);
      return;
    }
    flushTable(idx);
    const ordered = trimmed.match(/^\d+\.\s+(.*)$/);
    if (ordered) {
      flushList(idx); flushQuote(idx);
      elements.push(<ol key={`ordered-${idx}`} start={Number(trimmed.split('.')[0])} className="list-decimal pl-5"><li>{renderInlineTokens(ordered[1])}</li></ol>);
      return;
    }

    // Check if line is blockquote
    if (trimmed.startsWith('>')) {
      flushList(idx);
      currentQuote.push(trimmed.replace(/^>\s*/, ''));
      return;
    } else {
      flushQuote(idx);
    }

    // Check if line is a list item
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const itemContent = trimmed.substring(2);
      currentList.push(
        <li key={`li-${idx}`} className="flex items-start gap-2 text-slate-200">
          <span className="text-indigo-400 select-none mt-0.5">•</span>
          <span className="flex-1">{renderInlineTokens(itemContent)}</span>
        </li>
      );
      return;
    } else {
      flushList(idx);
    }

    // Empty line
    if (!trimmed) {
      elements.push(<div key={`space-${idx}`} className="h-1.5" />);
      return;
    }

    // Headings
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={`h3-${idx}`} className="text-xs sm:text-[13px] font-bold text-white mt-2.5 mb-1 tracking-wide flex items-center gap-1.5">
          {renderInlineTokens(trimmed.substring(4))}
        </h4>
      );
      return;
    }
    if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={`h2-${idx}`} className="text-sm font-bold text-white mt-3 mb-1.5 tracking-wide">
          {renderInlineTokens(trimmed.substring(3))}
        </h3>
      );
      return;
    }
    if (trimmed.startsWith('# ')) {
      elements.push(
        <h2 key={`h1-${idx}`} className="text-base font-bold text-white mt-3 mb-1.5 tracking-wide">
          {renderInlineTokens(trimmed.substring(2))}
        </h2>
      );
      return;
    }

    // Regular paragraph
    elements.push(
      <p key={`p-${idx}`} className="text-slate-200 leading-relaxed">
        {renderInlineTokens(trimmed)}
      </p>
    );
  });

  // Flush any remaining
  flushList(lines.length);
  flushQuote(lines.length);
  flushTable(lines.length);
  if (codeLines !== null) elements.push(<pre key="unfinished-code" className="overflow-x-auto p-2"><code>{(codeLines as string[]).join('\n')}</code></pre>);

  return <div className={`space-y-1 ${className}`}>{elements}</div>;
};

export default SafeMarkdown;
