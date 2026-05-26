export type Suit = 'major' | 'cups' | 'wands' | 'swords' | 'pentacles';

export interface TarotCard {
  slug: string;
  suit: Suit;
  number: number;
  name_ru: string;
  name_en: string;
  upright_meaning_ru: string;
  upright_meaning_en: string;
  reversed_meaning_ru: string;
  reversed_meaning_en: string;
  keywords_ru: string[];
  keywords_en: string[];
  image_url: string;
}

export interface SpreadPosition {
  index: number;
  label_ru: string;
  label_en: string;
  meaning_ru: string;
  meaning_en: string;
}

export interface DrawnCard {
  position_index: number;
  is_reversed: boolean;
  card: TarotCard;
}

export interface ReadingResponse {
  id: number;
  question: string;
  locale: string;
  created_at: string;
  spread_type: { slug: string; positions: SpreadPosition[] };
  cards: DrawnCard[];
}
