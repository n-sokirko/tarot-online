import { describe, expect, it } from 'vitest';
import { fill, getLegalDoc, isLegalFallback, legalLanguage } from './index';
import type { LegalDoc, LegalKind } from './index';

const KINDS: LegalKind[] = ['terms', 'privacy'];

function allText(doc: LegalDoc): string[] {
  const out = [doc.title, doc.intro];
  for (const s of doc.sections) {
    out.push(s.heading);
    for (const b of s.blocks) {
      if ('p' in b) out.push(b.p);
      else if ('ul' in b) out.push(...b.ul);
      else out.push(...b.table.head, ...b.table.rows.flat());
    }
  }
  return out;
}

describe('legal documents', () => {
  for (const kind of KINDS) {
    for (const locale of ['ru', 'en']) {
      it(`${kind}/${locale}: every placeholder is filled in`, () => {
        for (const text of allText(getLegalDoc(kind, locale))) {
          expect(text).not.toMatch(/\{\{|\}\}/);
        }
      });

      it(`${kind}/${locale}: no doubled full stops`, () => {
        for (const text of allText(getLegalDoc(kind, locale))) {
          expect(text).not.toMatch(/\.\./);
        }
      });

      it(`${kind}/${locale}: no long dashes and no square-bracket blanks`, () => {
        for (const text of allText(getLegalDoc(kind, locale))) {
          expect(text).not.toMatch(/[—–]/);
          expect(text).not.toMatch(/\[[^\]]*\]/);       // a visitor must never see "[ФИО]"
        }
      });
    }

    it(`${kind}: Russian and English have the same structure`, () => {
      const ru = getLegalDoc(kind, 'ru');
      const en = getLegalDoc(kind, 'en');
      expect(en.sections.length).toBe(ru.sections.length);
      ru.sections.forEach((s, i) => {
        expect(en.sections[i].blocks.length).toBe(s.blocks.length);
        // the section number leads each heading, so the two stay aligned
        expect(en.sections[i].heading.split('.')[0]).toBe(s.heading.split('.')[0]);
      });
    });

    it(`${kind}: other languages read the English text`, () => {
      expect(getLegalDoc(kind, 'de')).toEqual(getLegalDoc(kind, 'en'));
      expect(isLegalFallback('de')).toBe(true);
      expect(isLegalFallback('ru')).toBe(false);
      expect(legalLanguage('uk')).toBe('en');
    });
  }

  it('the terms promise what the bot really does (16+, Stars only, no card payments)', () => {
    const ru = allText(getLegalDoc('terms', 'ru')).join('\n');
    expect(ru).toContain('от 16 лет');
    expect(ru).toContain('Telegram Stars');
    expect(ru).not.toMatch(/Paddle|банковск/i);
  });

  it('the privacy policy says what is really sent to the neural network', () => {
    const ru = allText(getLegalDoc('privacy', 'ru')).join('\n');
    expect(ru).toContain('Telegram ID, ник и e-mail нейросети не передаются');
    expect(ru).toContain('Для нумерологии это имя и дата рождения');
  });

  it('while the operator and contacts are empty the pages say so plainly', () => {
    expect(fill('{{OPERATOR}}', 'ru')).toMatch(/будет указан/);
    expect(fill('{{CONTACTS}}', 'en')).toMatch(/will be added/);
  });

  it('the effective date is rendered in the visitor language', () => {
    expect(fill('{{DATE}}', 'ru')).toMatch(/2026/);
    expect(fill('{{DATE}}', 'ru')).toMatch(/октября/);
    expect(fill('{{DATE}}', 'en')).toMatch(/October/);
  });
});
