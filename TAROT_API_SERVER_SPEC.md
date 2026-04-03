# Tarot API — server implementation spec

Copy this document into your API codebase. The Tarot React app calls these endpoints via `fetch` (base URL = `VITE_API_BASE` or same-origin). Paths below are **relative** to that base.

---

## Overview

- **Public routes**: JSON only, no auth.
- **Admin routes**: `Authorization: Bearer <ADMIN_API_KEY>` (same secret the admin UI stores after the user pastes it).
- **Errors**: Prefer HTTP 4xx/5xx with body `{ "error": "message" }`.
- **`lang`**: Query parameter (e.g. `en`, `es`). Resolve multilingual JSONB by `content[lang] ?? content.en` for string fields inside objects.

---

## Database (Postgres)

### `cards`

| Column         | Type    | Notes |
|----------------|---------|--------|
| `name_short`   | text    | Primary key |
| `name`         | jsonb   | `{ "en": string, "es"?: string }` |
| `value`        | jsonb   | same shape |
| `meaning_up`   | jsonb   | same |
| `meaning_rev`  | jsonb   | same |
| `description`  | jsonb   | same |
| `suit`         | jsonb   | optional; minor arcana |
| `type`         | text    | `major` or `minor` |
| `value_int`    | int     | sort / ordering |
| `image_path`   | text    | optional |

### `tutorials`

| Column         | Type    | Notes |
|----------------|---------|--------|
| `section_key`  | text    | primary key or unique |
| `title`        | jsonb   | multilingual |
| `content`      | jsonb   | multilingual; value may be string **or** nested JSON per locale |
| `is_active`    | boolean | |
| `order_index`  | int     | ascending sort for list |

---

## JSON models (TypeScript)

Use these shapes for responses / request bodies. Adjust naming to match your stack; **field names must match** what the client expects.

### Localized card (most public endpoints)

```typescript
interface TarotCardLocalized {
  name_short: string;
  name: string;        // localized for requested lang
  name_en?: string;    // always English display name (for image path logic)
  type: string;
  value: string;
  value_int: number;
  meaning_up: string;
  meaning_rev: string;
  desc: string;        // from description.*
  suit?: string;
  image_path?: string | null;
}
```

Build from a DB row by picking each JSONB field’s `lang` key, then `en`; set `name_en` from `name.en`.

### Admin: full card row (multilingual objects)

```typescript
interface MultilingualContent {
  en: string;
  es?: string;
}

interface DatabaseCard {
  name_short: string;
  name: MultilingualContent;
  type: string;
  value: MultilingualContent;
  value_int: number;
  meaning_up: MultilingualContent;
  meaning_rev: MultilingualContent;
  description: MultilingualContent;
  suit?: MultilingualContent;
  image_path?: string | null;
}
```

### Admin PATCH body

Only include keys being updated. Server should merge into existing JSONB columns.

```typescript
interface PatchCardBody {
  name?: MultilingualContent;
  value?: MultilingualContent;
  meaning_up?: MultilingualContent;
  meaning_rev?: MultilingualContent;
  description?: MultilingualContent;
  suit?: MultilingualContent;
}
```

### Tutorial section (after resolving lang)

```typescript
interface TutorialSectionResponse {
  section_key: string;
  title: string;
  content: unknown; // string | object | array depending on stored JSON
}
```

---

## HTTP routes

All `GET` requests use query params as listed. Path parameters must be URL-decoded.

| Method | Path | Query / body | Auth | Response |
|--------|------|----------------|------|----------|
| `GET` | `/api/cards` | `lang` (default `en`) | — | `TarotCardLocalized[]`, sort `name_short` ASC |
| `GET` | `/api/cards/by-name` | `name`, `lang` optional | — | `TarotCardLocalized` — where `name->>'en' = :name OR name->>'es' = :name` |
| `GET` | `/api/cards/by-name-lang` | `name`, `lang` | — | `TarotCardLocalized` — where `name->>'en' = :name` only |
| `GET` | `/api/cards/by-short/:nameShort` | `lang` | — | `TarotCardLocalized` — `name_short = :nameShort` |
| `GET` | `/api/cards/random` | `lang` | — | `TarotCardLocalized` — random row |
| `GET` | `/api/cards/random-many` | `count`, `lang` | — | `TarotCardLocalized[]` — shuffle deck, return min(count, deck size) |
| `GET` | `/api/cards/by-suit/:suit` | `lang` | — | `TarotCardLocalized[]` — **`suit->>'en' = :suit`**, sort `value_int` ASC |
| `GET` | `/api/cards/by-type/:type` | `lang` | — | `TarotCardLocalized[]` — `type IN ('major','minor')`, sort `value_int` ASC |
| `GET` | `/api/cards/search` | `q`, `lang` | — | `TarotCardLocalized[]` — ILIKE `%q%` on `name->>'en'`, `name->>'es'`, `description->>'en'`, `description->>'es'`; sort `name_short` |
| `GET` | `/api/tutorials` | `lang` | — | `TutorialSectionResponse[]` — `is_active = true`, order `order_index` |
| `GET` | `/api/tutorials/section/:sectionKey` | `lang` | — | `TutorialSectionResponse` — `section_key` + active |
| `GET` | `/api/admin/cards` | — | `Bearer` | `DatabaseCard[]`, order `value_int` ASC |
| `PATCH` | `/api/admin/cards/:nameShort` | JSON `PatchCardBody` | `Bearer` | `{ "ok": true }` or 404 |

### Optional

- `GET /api/health` — e.g. `{ "ok": true, "db": true }` for ops; client does not depend on it.

---

## Query semantics (reference)

- **Random-many**: Cap `count` at deck size (78 or whatever is in DB).
- **Search**: Empty `q` → return empty array `[]` (client may omit calls when query empty).
- **404**: Use when a single resource is missing (`by-short`, `by-name`, `tutorial section`).
- **PATCH**: Update only supplied JSONB keys; match `name_short = :nameShort`.

---

## CORS (if SPA is on another origin)

Allow the frontend origin, methods `GET`, `PATCH`, headers `Content-Type`, `Authorization`.

---

## Client configuration

The Tarot app sets `VITE_API_BASE` to your API origin (and optional path prefix). If you mount routes under e.g. `/v1/tarot`, either:

- Set `VITE_API_BASE=https://api.example.com/v1/tarot` **and** keep paths as `/api/cards`, **or**
- Expose routes without the `/api` prefix and update the client’s `backendApi.ts` paths once.

---

## Revision

Derived from the Tarot app `backendApi.ts` + `src/types/tarot.ts`. Keep in sync if you add endpoints.
