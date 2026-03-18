# Natal Chart API — Full Models Report

Client reference for all database models, fields, relationships, and API mapping.

---

## Reference Tables (Base Data)

### Planet
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| name | String(50) | No | Unique (Sun, Moon, Mercury, etc.) |
| symbol | String(10) | Yes | Astrological symbol |
| description | Text | Yes | General description of planet energy |
| keywords | String(255) | Yes | Comma-separated keywords |

**Planets:** Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron

---

### Sign
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| name | String(50) | No | Unique (Aries, Taurus, … Pisces) |
| element | String(20) | Yes | fire, earth, air, water |
| modality | String(20) | Yes | cardinal, fixed, mutable |
| archetypes_balanced | String(200) | Yes | Healthy archetypal expression |
| archetypes_unbalanced | String(200) | Yes | Shadow/challenging expression |
| journey | String(100) | Yes | Developmental theme |
| gifts | Text | Yes | Natural strengths |
| challenges | Text | Yes | Growth areas |
| interpretation | Text | Yes | Full sign interpretation |

---

### House
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| number | Integer | No | 1–12 (unique) |
| type_ | String(20) | Yes | angular, succedent, cadent |
| description | Text | Yes | Life area description |
| subtitle | String(100) | Yes | Short label (e.g. "House of Self") |
| keywords | String(255) | Yes | Comma-separated keywords |

---

### Aspect
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| name | String(50) | No | Unique (Conjunction, Opposition, Square, Trine, Sextile, Quincunx) |
| angle_degrees | Integer | Yes | 0, 60, 90, 120, 150, 180 |
| symbol | String(10) | Yes | Astrological symbol |

---

## Interpretation Tables

### PlanetSignInterpretation
**Unique:** (planet_id, sign_id)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| planet_id | FK → planets.id | No | |
| sign_id | FK → signs.id | No | |
| interpretation_text | Text | No | Primary interpretation (used in API) |
| interpretation_long | Text | Yes | Extended text |
| interpretation_short | Text | Yes | Summary |
| keywords | String(500) | Yes | Comma-separated |
| retrograde_interpretation | Text | Yes | Meaning when planet is retrograde |

**API key format:** `"Planet in Sign"` (e.g. `"Sun in Aries"`)

---

### PlanetHouseInterpretation
**Unique:** (planet_id, house_id)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| planet_id | FK → planets.id | No | |
| house_id | FK → houses.id | No | |
| interpretation_text | Text | No | Primary interpretation |
| short_interpretation | Text | Yes | Condensed version |
| retrograde_interpretation | Text | Yes | Meaning when retrograde in this house |

**API key format:** `"Planet in House N"` (e.g. `"Sun in House 1"`)

---

### SignHouseInterpretation
**Unique:** (house_id, sign_id)

Interpretation for sign on house cusp (e.g. Aries on 1st = Aries Rising).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| house_id | FK → houses.id | No | 1–12 |
| sign_id | FK → signs.id | No | |
| interpretation_text | Text | No | Full interpretation |

**Lookup:** House 1 + rising sign → `rising_sign` interpretation.

---

### AspectInterpretation (Generic)
**Unique:** (aspect_id)

One generic interpretation per aspect type (Conjunction, Opposition, etc.).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| aspect_id | FK → aspects.id | No | |
| interpretation_text | Text | No | Generic meaning of aspect type |

---

### PlanetAspectInterpretation (Planet-Pair)
**Unique:** (planet_1_id, planet_2_id, aspect_id)

Specific interpretation per planet pair + aspect (e.g. Sun conjunct Moon).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| planet_1_id | FK → planets.id | No | |
| planet_2_id | FK → planets.id | No | |
| aspect_id | FK → aspects.id | No | |
| interpretation_text | Text | No | Planet-pair specific meaning |

**API key format:** `"Planet1 aspect Planet2"` (e.g. `"Sun Conjunction Moon"`). Lookup prefers this table when row exists; falls back to AspectInterpretation.

---

### ChartShapeInterpretation
**Unique:** shape_key

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| shape_key | String(50) | No | splash, splay, bundle, bowl, locomotive, bucket, see_saw |
| interpretation_text | Text | No | Shape pattern meaning |

---

### ChartDistributionInterpretation
**Unique:** distribution_key

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| distribution_key | String(50) | No | hemisphere_northern, quadrant_1, etc. |
| interpretation_text | Text | No | Hemisphere/quadrant meaning |

---

### ModalityElementDistributionInterpretation
**Unique:** distribution_key

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| distribution_key | String(50) | No | element_fire_dominant, quality_balanced, etc. |
| interpretation_text | Text | No | Element/modality emphasis meaning |

---

## Stored Readings

### Reading
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | Integer | PK | Auto-increment |
| identifier | String(255) | No | Unique: `name__birthdatetime__lat__lng` |
| chart_data | Text | No | JSON string (full NatalChart) |
| created_at | DateTime | Yes | Timestamp |

---

## API Response Mapping

| API Path | Source | Key Format |
|----------|--------|------------|
| `interpretations.planet_in_sign` | planet_sign_interpretations | "Planet in Sign" |
| `interpretations.planet_in_house` | planet_house_interpretations | "Planet in House N" |
| `interpretations.aspects` | planet_aspect_interpretations (prefer) or aspect_interpretations | "Planet1 Aspect Planet2" |
| `interpretations.chart_shape.primary` | Detection logic | shape_key |
| `interpretations.chart_shape.interpretation` | chart_shape_interpretations | shape_key |
| `interpretations.chart_shape.distribution` | chart_distribution_interpretations | distribution_key |
| `interpretations.modality_element_distribution` | modality_element_distribution_interpretations | distribution_key |
| `interpretations.retrograde_planets` | chart.planets where retrograde=true | — |
| `interpretations.retrograde_interpretations` | planet_sign/planet_house retrograde_interpretation | Same as planet_in_sign/house |
| `interpretations.rising_sign_interpretation` | sign_house_interpretations (house 1 + rising sign) | — |

---

## Data Not Yet Exposed in API

These DB columns exist but are not currently in the chart response:

- **PlanetSignInterpretation:** interpretation_long, interpretation_short, keywords
- **PlanetHouseInterpretation:** short_interpretation
- **Planet, Sign, House:** description, keywords, subtitle, gifts, challenges, etc.

Client can request API expansion to include these fields when needed.
