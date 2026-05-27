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

export interface Interpretation {
  body_md: string;
  model_used: string;
  prompt_version: string;
  generated_at: string;
  token_count: number;
}

export interface ReadingResponse {
  id: number;
  question: string;
  locale: string;
  created_at: string;
  spread_type: { slug: string; positions: SpreadPosition[] };
  cards: DrawnCard[];
  interpretation: Interpretation | null;
}

// ---- Runes ----

export interface Rune {
  slug: string;
  number: number;
  aett: number;
  symbol: string;
  name_ru: string;
  name_en: string;
  meaning_ru: string;
  meaning_en: string;
  keywords_ru: string[];
  keywords_en: string[];
}

export interface RuneCastItem {
  position_index: number;
  rune: Rune;
}

export type RuneLayout = 'single' | 'three' | 'five';

export interface RuneCastPosition {
  label_ru: string;
  label_en: string;
}

export interface RuneCastResponse {
  id: number;
  layout: RuneLayout;
  question: string;
  locale: string;
  created_at: string;
  positions: RuneCastPosition[];
  items: RuneCastItem[];
  interpretation: Interpretation | null;
}

// ---- Billing ----

export type PlanKind = 'free' | 'subscription' | 'credits';

export interface Plan {
  slug: string;
  name_ru: string;
  name_en: string;
  description_ru: string;
  description_en: string;
  kind: PlanKind;
  price_usd_cents: number;
  tg_stars_price: number;
  monthly_included_credits: number;
  credits_granted: number;
  entitlement_keys: string[];
  paddle_price_id: string;
}

export interface PlansResponse {
  plans: Plan[];
  telegram_bot_username: string;
  paddle_client_token: string;
  paddle_env: 'sandbox' | 'production';
}

export interface TelegramCheckoutPayload {
  url: string;
  stars: number;
  plan: Plan;
}

export interface TelegramInvoicePayload {
  invoice_link: string;
  stars: number;
  plan: Plan;
}

export interface BillingMe {
  tier: 'free' | 'premium' | 'deep';
  credits: number;
  entitlements: string[];
  subscription: null | {
    plan_slug: string;
    status: string;
    current_period_start: string | null;
    current_period_end: string | null;
    canceled_at: string | null;
  };
}

export interface CheckoutPayload {
  paddle_client_token: string;
  paddle_env: 'sandbox' | 'production';
  price_id: string;
  plan_slug: string;
  customer_email: string;
  custom_data: { user_id: string; plan_slug: string };
}
