'use client';

import { Fragment } from 'react';

/**
 * Minimal markdown renderer scoped to what our AI prompts actually produce:
 * paragraphs separated by blank lines, **bold**, and plain prose.
 * Intentionally no headings/lists/links — we control the output and keep it lean.
 */
export function MarkdownProse({ body, className }: { body: string; className?: string }) {
  const paragraphs = body
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean);

  return (
    <div className={className}>
      {paragraphs.map((p, i) => (
        <p key={i} className="mb-4 last:mb-0 leading-relaxed">
          {renderInline(p)}
        </p>
      ))}
    </div>
  );
}

function renderInline(text: string) {
  // Split on **...** keeping the captures.
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} style={{ color: '#d4af37', fontWeight: 600 }}>
          {part.slice(2, -2)}
        </strong>
      );
    }
    // Preserve single line breaks inside paragraphs.
    const lines = part.split('\n');
    return (
      <Fragment key={i}>
        {lines.map((line, li) => (
          <Fragment key={li}>
            {line}
            {li < lines.length - 1 ? <br /> : null}
          </Fragment>
        ))}
      </Fragment>
    );
  });
}
