import React from 'react';

/**
 * Simple markdown renderer for panel text.
 * Handles: **bold**, *italic*, `code`, ```blocks```, ## headings,
 * - lists, 1. numbered lists, > blockquotes, [links](url), newlines
 */
export function renderMarkdown(text: string): React.ReactNode {
  if (!text) return null;

  // Split by code blocks first
  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="panel-markdown">
      {parts.map((part, i) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          const code = part.slice(3, -3).replace(/^\w*\n/, '');
          return (
            <pre key={i} className="text-xs bg-bg p-2 overflow-x-auto my-1">
              <code>{code}</code>
            </pre>
          );
        }
        return <span key={i}>{renderInline(part)}</span>;
      })}
    </div>
  );
}

function renderInline(text: string): React.ReactNode[] {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let inList = false;
  let listItems: React.ReactNode[] = [];

  lines.forEach((line, i) => {
    const trimmed = line.trim();

    // Flush list if we exit list context
    if (inList && !trimmed.startsWith('- ') && !trimmed.match(/^\d+\. /)) {
      elements.push(<ul key={`list-${i}`}>{listItems}</ul>);
      listItems = [];
      inList = false;
    }

    if (!trimmed) {
      elements.push(<br key={`br-${i}`} />);
    } else if (trimmed.startsWith('### ')) {
      elements.push(<h3 key={i}>{formatInline(trimmed.slice(4))}</h3>);
    } else if (trimmed.startsWith('## ')) {
      elements.push(<h2 key={i}>{formatInline(trimmed.slice(3))}</h2>);
    } else if (trimmed.startsWith('# ')) {
      elements.push(<h2 key={i}>{formatInline(trimmed.slice(2))}</h2>);
    } else if (trimmed.startsWith('> ')) {
      elements.push(
        <blockquote key={i}>{formatInline(trimmed.slice(2))}</blockquote>,
      );
    } else if (trimmed.startsWith('- ')) {
      inList = true;
      listItems.push(<li key={i}>{formatInline(trimmed.slice(2))}</li>);
    } else if (trimmed.match(/^\d+\. /)) {
      inList = true;
      listItems.push(
        <li key={i}>{formatInline(trimmed.replace(/^\d+\. /, ''))}</li>,
      );
    } else {
      elements.push(<p key={i}>{formatInline(trimmed)}</p>);
    }
  });

  // Flush remaining list
  if (inList && listItems.length > 0) {
    elements.push(<ul key="list-end">{listItems}</ul>);
  }

  return elements;
}

function formatInline(text: string): React.ReactNode {
  // Process inline markdown: **bold**, *italic*, `code`, [link](url)
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let keyIdx = 0;

  while (remaining.length > 0) {
    // Bold
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
    // Italic
    const italicMatch = remaining.match(/(?<!\*)\*([^*]+?)\*(?!\*)/);
    // Code
    const codeMatch = remaining.match(/`([^`]+?)`/);
    // Link
    const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);

    // Find earliest match
    const matches = [
      boldMatch ? { type: 'bold', match: boldMatch } : null,
      italicMatch ? { type: 'italic', match: italicMatch } : null,
      codeMatch ? { type: 'code', match: codeMatch } : null,
      linkMatch ? { type: 'link', match: linkMatch } : null,
    ]
      .filter(Boolean)
      .sort((a, b) => (a!.match.index || 0) - (b!.match.index || 0));

    if (matches.length === 0) {
      parts.push(remaining);
      break;
    }

    const first = matches[0]!;
    const idx = first.match.index || 0;

    if (idx > 0) {
      parts.push(remaining.slice(0, idx));
    }

    if (first.type === 'bold') {
      parts.push(<strong key={keyIdx++}>{first.match[1]}</strong>);
    } else if (first.type === 'italic') {
      parts.push(<em key={keyIdx++}>{first.match[1]}</em>);
    } else if (first.type === 'code') {
      parts.push(<code key={keyIdx++}>{first.match[1]}</code>);
    } else if (first.type === 'link') {
      parts.push(
        <a
          key={keyIdx++}
          href={first.match[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-c-blue hover:underline"
        >
          {first.match[1]}
        </a>,
      );
    }

    remaining = remaining.slice(idx + first.match[0].length);
  }

  return <>{parts}</>;
}
