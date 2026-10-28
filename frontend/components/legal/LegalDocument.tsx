import Link from 'next/link';
import type { LegalBlock, LegalDoc } from '@/lib/legal';

interface Props {
  doc: LegalDoc;
  /** Shown above the title when the visitor's language has no translation. */
  notice?: string;
  /** The other legal document, linked at the bottom. */
  other: { href: string; label: string };
}

const TEXT = 'rgba(242,237,228,0.82)';
const MUTED = 'rgba(242,237,228,0.5)';
const GOLD = '#E0B26C';
const LINE = 'rgba(224,178,108,0.18)';

function Block({ block }: { block: LegalBlock }) {
  if ('p' in block) {
    return (
      <p className="text-[15px] leading-relaxed" style={{ color: TEXT }}>
        {block.p}
      </p>
    );
  }
  if ('ul' in block) {
    return (
      <ul className="flex flex-col gap-1.5 pl-5 list-disc text-[15px] leading-relaxed" style={{ color: TEXT }}>
        {block.ul.map((item) => <li key={item}>{item}</li>)}
      </ul>
    );
  }
  const { head, rows } = block.table;
  return (
    <div className="overflow-x-auto rounded-xl" style={{ border: `1px solid ${LINE}` }}>
      <table className="w-full text-left text-sm" style={{ color: TEXT }}>
        <thead>
          <tr style={{ background: 'rgba(224,178,108,0.06)' }}>
            {head.map((h) => (
              <th key={h} className="px-3 py-2 font-semibold whitespace-nowrap" style={{ color: GOLD }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[0]} style={{ borderTop: `1px solid ${LINE}` }}>
              {row.map((cell, i) => (
                <td key={cell} className={`px-3 py-2 align-top ${i === 0 ? 'font-semibold whitespace-nowrap' : ''}`}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * A legal document as plain, readable text. Server-rendered: nothing here needs
 * the browser, and a search engine or a lawyer reading the page gets the full text.
 */
export default function LegalDocument({ doc, notice, other }: Props) {
  return (
    <main className="min-h-screen flex flex-col items-center px-4 py-10">
      <article className="w-full max-w-2xl flex flex-col gap-8">
        {notice && (
          <p className="text-xs rounded-xl px-3 py-2" style={{ color: MUTED, border: `1px solid ${LINE}` }}>
            {notice}
          </p>
        )}

        <header className="flex flex-col gap-3">
          <h1 className="font-serif text-3xl md:text-4xl" style={{ color: GOLD }}>{doc.title}</h1>
          <p className="text-sm leading-relaxed" style={{ color: MUTED }}>{doc.intro}</p>
        </header>

        {doc.sections.map((section) => (
          <section key={section.heading} className="flex flex-col gap-3">
            <h2 className="font-serif text-xl" style={{ color: GOLD }}>{section.heading}</h2>
            {section.blocks.map((block, i) => <Block key={i} block={block} />)}
          </section>
        ))}

        <footer className="pt-4" style={{ borderTop: `1px solid ${LINE}` }}>
          <Link href={other.href} className="text-sm underline underline-offset-4" style={{ color: GOLD }}>
            {other.label}
          </Link>
        </footer>
      </article>
    </main>
  );
}
