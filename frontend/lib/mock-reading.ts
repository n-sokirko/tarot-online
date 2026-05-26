import type { ReadingResponse } from './types';

export const mockReading: ReadingResponse = {
  id: 1,
  question: '',
  locale: 'ru',
  created_at: new Date().toISOString(),
  spread_type: {
    slug: 'three-card',
    positions: [
      {
        index: 0,
        label_ru: 'Прошлое',
        label_en: 'Past',
        meaning_ru: 'То, что сформировало текущую ситуацию',
        meaning_en: 'What shaped the current situation',
      },
      {
        index: 1,
        label_ru: 'Настоящее',
        label_en: 'Present',
        meaning_ru: 'То, что происходит прямо сейчас',
        meaning_en: 'What is happening right now',
      },
      {
        index: 2,
        label_ru: 'Будущее',
        label_en: 'Future',
        meaning_ru: 'Куда ведёт этот путь',
        meaning_en: 'Where this path leads',
      },
    ],
  },
  cards: [
    {
      position_index: 0,
      is_reversed: false,
      card: {
        slug: 'the-fool',
        suit: 'major',
        number: 0,
        name_ru: 'Дурак',
        name_en: 'The Fool',
        upright_meaning_ru:
          'Начало нового пути, спонтанность, свобода, невинность и открытость новому',
        upright_meaning_en:
          'New beginnings, spontaneity, freedom, innocence, and openness to the unknown',
        reversed_meaning_ru:
          'Безрассудство, наивность, риск без подготовки, упущенные возможности',
        reversed_meaning_en:
          'Recklessness, naivety, risk without preparation, missed opportunities',
        keywords_ru: ['начало', 'свобода', 'приключение', 'доверие'],
        keywords_en: ['beginning', 'freedom', 'adventure', 'trust'],
        image_url: '/cards/rider-waite/00-fool.jpg',
      },
    },
    {
      position_index: 1,
      is_reversed: false,
      card: {
        slug: 'the-high-priestess',
        suit: 'major',
        number: 2,
        name_ru: 'Верховная Жрица',
        name_en: 'The High Priestess',
        upright_meaning_ru:
          'Интуиция, тайное знание, внутренний голос, связь с подсознанием',
        upright_meaning_en:
          'Intuition, hidden knowledge, inner voice, connection to the subconscious',
        reversed_meaning_ru:
          'Игнорирование интуиции, скрытые секреты, поверхностность',
        reversed_meaning_en:
          'Ignoring intuition, hidden secrets, superficiality',
        keywords_ru: ['интуиция', 'тайна', 'мудрость', 'внутренний мир'],
        keywords_en: ['intuition', 'mystery', 'wisdom', 'inner world'],
        image_url: '/cards/rider-waite/02-high-priestess.jpg',
      },
    },
    {
      position_index: 2,
      is_reversed: false,
      card: {
        slug: 'the-star',
        suit: 'major',
        number: 17,
        name_ru: 'Звезда',
        name_en: 'The Star',
        upright_meaning_ru:
          'Надежда, вдохновение, обновление, исцеление и вера в лучшее',
        upright_meaning_en:
          'Hope, inspiration, renewal, healing, and faith in the future',
        reversed_meaning_ru:
          'Потеря веры, разочарование, ощущение покинутости',
        reversed_meaning_en: 'Loss of faith, disappointment, feeling abandoned',
        keywords_ru: ['надежда', 'вдохновение', 'исцеление', 'свет'],
        keywords_en: ['hope', 'inspiration', 'healing', 'light'],
        image_url: '/cards/rider-waite/17-star.jpg',
      },
    },
  ],
};
