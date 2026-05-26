# Database Schema

Owned by `database-agent`. Edit through migrations, never hot-patch production.

```mermaid
erDiagram
    User ||--o{ Reading : has
    SpreadType ||--o{ Reading : "shapes"
    Reading ||--o{ ReadingCard : "contains"
    Reading ||--|| Interpretation : "produces"
    Card ||--o{ ReadingCard : "appears in"

    User {
        bigint id PK
        string username
        string email UK
        string display_name
        string locale
        datetime date_joined
        datetime last_login
        datetime deleted_at
        bool is_active
        bool is_staff
        bool is_superuser
    }
    Card {
        bigint id PK
        string slug UK
        string suit
        smallint number
        string name_ru
        string name_en
        text upright_meaning_ru
        text upright_meaning_en
        text reversed_meaning_ru
        text reversed_meaning_en
        json keywords_ru
        json keywords_en
        string image_url
    }
    SpreadType {
        bigint id PK
        string slug UK
        string name_ru
        string name_en
        smallint positions_count
        json positions
    }
    Reading {
        bigint id PK
        bigint user_id FK
        bigint spread_type_id FK
        text question
        string locale
        datetime created_at
        datetime deleted_at
    }
    ReadingCard {
        bigint id PK
        bigint reading_id FK
        bigint card_id FK
        smallint position_index
        bool is_reversed
    }
    Interpretation {
        bigint id PK
        bigint reading_id FK
        text body_md
        string model_used
        string prompt_version
        datetime generated_at
        int token_count
    }
```

## Indexes (must exist)

- `User.email` — unique
- `Card.slug` — unique
- `Card(suit, number)` — composite, for browsing
- `Reading(created_at)` — descending, for history page
- `Reading(user_id, created_at)` — composite, for user history
- `ReadingCard(reading_id, position_index)` — unique together

## Migrations

| App | Migration | Description |
|-----|-----------|-------------|
| `users` | `0001_initial` | Custom User (extends AbstractUser), email as USERNAME_FIELD |
| `tarot` | `0001_initial` | Card (78-card deck) and SpreadType models |
| `readings` | `0001_initial` | Reading, ReadingCard, Interpretation |

To apply:
```bash
python manage.py migrate
```

## Seed Data

Load the Rider-Waite deck and spread types:
```bash
python manage.py seed_deck
```

This command is **idempotent** — safe to run multiple times. It uses `update_or_create` on `slug`.

Source files:
- `data/deck/rider-waite.json` — 78 cards (Major Arcana fully populated; Minor Arcana stubs pending `content-agent`)
- `data/deck/spread-positions.json` — spread type definitions
