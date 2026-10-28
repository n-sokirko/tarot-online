export type LegalBlock =
  | { p: string }
  | { ul: string[] }
  | { table: { head: string[]; rows: string[][] } };

export interface LegalSection {
  heading: string;
  blocks: LegalBlock[];
}

export interface LegalDoc {
  title: string;
  /** Lead line shown under the title. {{DATE}} is filled in. */
  intro: string;
  sections: LegalSection[];
}

export type LegalKind = 'terms' | 'privacy';
