# Interpretation Flow — High-Level Overview

Documents how interpretations move from chart data → detection → lookup → API response. Use this to align before making changes.

---

## 1. The Pipeline (Order of Operations)

```
1. Chart computation (Kerykeion)
   → Raw positions: planets (sign, house, degree, retrograde), houses (cusps), aspects

2. Derived values
   → Big three: sun_sign, moon_sign, rising_sign (from House 1 cusp sign)
   → houses_overview: by_quality, by_element (from planetary placements in signs)

3. Detection (rule-based, no DB)
   → chart_shape: bundle, bowl, bucket, etc. (from planet longitudes)
   → distribution_keys: hemisphere_northern, quadrant_1, etc. (from house positions)
   → modality_element_keys: element_fire_dominant, quality_balanced, etc. (from houses_overview)

4. Lookup (DB)
   → Fetch interpretations for: planet+sign, planet+house, aspect, chart_shape, distribution, modality_element, rising_sign, retrograde

5. Merge (API layer)
   → DB result + built-in defaults (only fill gaps where DB is empty)
   → DB always wins when present

6. Response
   → chart.interpretations populated and returned
```

---

## 2. Interpretation Categories & Sources

| Category | What we look up | Detection / Input | Source (priority) |
|----------|-----------------|-------------------|-------------------|
| **Planet in sign** | Each planet's sign placement | `(planet.name, planet.sign)` for all planets | DB → built-in (Sun, Moon, Rising only) |
| **Planet in house** | Each planet's house placement | `(planet.name, planet.house)` for all planets | DB → built-in |
| **Aspects** | Each aspect in the chart | `planet1 aspect_type planet2` from Kerykeion aspects | Planet-pair DB → generic DB → built-in |
| **Rising sign** | Sign on House 1 cusp | `rising_sign` (house 1 cusp sign) | DB only (SignHouseInterpretation) |
| **Chart shape** | Geometric pattern of planet positions | `detect_chart_shape(planets)` | DB → none (no built-in) |
| **Distribution** | Hemisphere / quadrant emphasis | `detect_distributions(planets)` | DB → none |
| **Modality / element** | Sign element & quality emphasis | `detect_modality_element_keys(by_quality, by_element)` | DB → none |
| **Retrograde** | Extra meaning when planet is Rx | `planet.retrograde` for each planet | DB (retrograde_interpretation column) → none |

---

## 3. Fallback Behavior

- **DB first:** If the DB has an interpretation for a key, we use it.
- **Built-in defaults:** Only for planet-in-sign (Sun, Moon, Rising), planet-in-house (all pairs), and aspects. Applied only when DB returns nothing.
- **No fallback:** Chart shape, distribution, modality/element, rising sign, and retrograde have no built-in defaults. If DB is empty, we return nothing for those keys.

---

## 4. Special Cases

### Retrograde

- Retrograde planets are listed in `interpretations.retrograde_planets`.
- If a retrograde planet has a DB row for its planet+sign or planet+house, we also fetch `retrograde_interpretation` and add it to `interpretations.retrograde_interpretations`.
- Key format matches planet-in-sign and planet-in-house (e.g. `"Mercury in Gemini"`, `"Mercury in House 3"`).

### Rising sign

- **Planet-in-sign:** "Rising in {sign}" uses PlanetSignInterpretation with a special "Rising" concept (currently via built-in defaults; not a literal planet).
- **Rising-sign interpretation:** Full "you as an Aries Rising" style text comes from SignHouseInterpretation (house 1 + sign). This is the `rising_sign_interpretation` field.

### Aspects

- Prefer **planet-pair specific** (PlanetAspectInterpretation: Sun-Moon Conjunction).
- Fall back to **generic** (AspectInterpretation: Conjunction in general).
- Then to **built-in** (defaults module) if both DB layers are empty.

---

## 5. The Big Three (Sun, Moon, Ascendant) — New Model

Sun, Moon, and Ascendant/Rising each have their **own dedicated interpretation tables** with multiple columns. This replaces the old model (planet_sign_interpretations + built-in defaults for Big Three).

### 5a. Tables & Structure

| Luminary | Table | Keyed By | Columns (from data) |
|----------|-------|----------|----------------------|
| **Sun** | `sun_sign_interpretations` | sign | archetypes_balanced, archetypes_unbalanced, journey, gifts, challenges, interpretation |
| **Moon** | `moon_sign_interpretations` | sign | nature, sources_of_contentment, keywords, interpretation |
| **Ascendant** | `ascendant_sign_interpretations` | sign | impression, appearance, childhood, balance, interpretation |

### 5b. Lookup Flow

1. **Sun in {sign}**
   - Fetch row from `sun_sign_interpretations` for that sign (all columns).
   - **Consider consolidating** sun and signs data for simplicity (e.g. sun table includes sign_interpretation, or we join once at seed time).
   - For now: also attach `signs.interpretation` (broad sign meaning) when building the Sun object.

2. **Moon in {sign}**
   - Fetch row from `moon_sign_interpretations` for that sign.
   - API returns: all columns for that row.

3. **Ascendant/Rising in {sign}**
   - Fetch row from `ascendant_sign_interpretations` for that sign.
   - Big Three uses **only** ascendant_sign_interpretations (not SignHouseInterpretation).

### 5c. API Shape

`interpretations.big_three` is an object with three nested objects:

```json
{
  "big_three": {
    "sun": { "sign": "Aries", "archetypes_balanced": "...", "interpretation": "...", ... },
    "moon": { "sign": "Cancer", "nature": "...", "interpretation": "...", ... },
    "ascendant": { "sign": "Libra", "impression": "...", "interpretation": "...", ... }
  }
}
```

### 5d. Relationship to Other Interpretations

- **Big Three** = dedicated sun/moon/ascendant tables only. No planet_sign_interpretations for Sun, Moon, or Rising.
- **Other planets** (Mercury, Venus, Mars, etc.) still use `planet_sign_interpretations` (unchanged).
- **SignHouseInterpretation** (sign on each house cusp) will live in a separate, well-defined `house_interpretation` object (to be designed next). Not used for Big Three.

---

## 6. Data Flow Diagram (Conceptual)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  BIRTH DATA (date, time, place)                                         │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  KERYKEION                                                              │
│  Planets, houses, aspects, lunar phase, nodes                           │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ Direct use    │      │ Detection logic   │      │ houses_overview   │
│ planet.sign   │      │ chart_shapes.py   │      │ by_quality,       │
│ planet.house  │      │ modality_element  │      │ by_element        │
│ aspects list  │      │ .py               │      │                   │
└───────┬───────┘      └─────────┬──────────┘      └─────────┬──────────┘
        │                       │                           │
        └───────────────────────┼───────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  fetch_interpretations()                                                │
│  Build lookup keys → Query DB tables → Return raw dict                  │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  _enrich_with_interpretations()                                         │
│  Merge DB result + built-in defaults (DB wins)                           │
│  Attach to chart.interpretations                                         │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  API RESPONSE (NatalChart with interpretations populated)               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Open Questions / Possible Misalignments

1. **"Rising in X" vs `rising_sign_interpretation`:** Currently "Rising in Libra" (planet-in-sign style) comes from built-in defaults. The full rising-sign blurb comes from `rising_sign_interpretation` (SignHouseInterpretation). Should these be unified or kept separate?

2. **Chart shape when none detected:** If `detect_chart_shape` returns `None`, we never look up chart shape. Is that intended, or should we have a "no clear shape" interpretation?

3. **Modality/element multiple keys:** We can return several keys (e.g. `element_fire_dominant` and `element_lacking_earth`). All matching interpretations are included. Is that the desired behavior?

4. **Lunar nodes:** North/South Node positions are in the chart but excluded from aspects and chart shape. No interpretations for them. Confirm if that’s correct.

---


## 8. Aspect Interpretation — Type-Based (Pre-Model)

Aspects have two layers: **specific chart data** (useful for the chart) and **interpretation** (keyed by type, not by aspect name).

### Two Layers

1. **Aspect list (unchanged):** Full list of aspects with planet1, aspect type (name), planet2, degrees/orbit. This gives the specific chart data (e.g. "Sun Square Moon 8.2°").

2. **Interpretation layer:** For each aspect, classify it by **type** (easy, stressful, or conjunction). The interpretation is looked up by type, not by aspect name.

### Why Type Over Name

- **Aspect name** (Conjunction, Opposition, Square, Trine, Sextile, Quincunx) is less important for interpretation.
- **Type** (easy, stressful, conjunction) drives the meaning: how the energies blend or clash.
- The specific data (planet pair, exact aspect, degrees) remains useful for chart display and context.

### Type Mapping (from aspects table)

| Aspect Name | Type |
|-------------|------|
| Conjunction | conjunction |
| Opposition, Square, Quincunx | stressful |
| Trine, Sextile | easy-flowing |

### Interpretation Lookup

- `aspect_type_interpretations` (or similar) keyed by type: `conjunction`, `stressful`, `easy-flowing`.
- Each aspect in the list gets: full data (planet1, planet2, aspect, degrees) + interpretation for its type.

### API Shape (conceptual)

```json
{
  "aspects": [
    {
      "planet1": "Sun",
      "planet2": "Moon",
      "aspect": "Square",
      "aspect_degrees": 90,
      "orbit": 8.2,
      "type": "stressful",
      "interpretation": "Creative tension between identity and emotions..."
    }
  ]
}
```

### Relationship to Existing

- **PlanetAspectInterpretation** (planet-pair specific): Still used when available — e.g. "Sun Square Moon" has a specific row. Falls back to type-based interpretation when no planet-pair row exists.

---

## 9. House Interpretation — Concept (Pre-Model)

What the `house_interpretation` object needs to convey, before we define the model:

### Per House (1–12)

- **Planets in each house:** Which planets are in each house, plus the interpretation for each (planet-in-house).
- **Sign on each house cusp:** Which sign sits on each house cusp, plus the interpretation for that sign-on-house (e.g. SignHouseInterpretation).

### Shape

- **Distribution shape:** The geometric pattern (bundle, bowl, bucket, splash, etc.) that planets form in the chart.
- **Meaning:** The interpretation of that shape (from chart_shape_interpretations).

### Quadrant

- **Concentration:** Whether planets are concentrated in a particular quadrant (1–3, 4–6, 7–9, 10–12).
- **Meaning:** The interpretation of that quadrant emphasis (from chart_distribution_interpretations: quadrant_1, quadrant_2, etc.).

### Hemisphere

- **Concentration:** Whether planets are concentrated in a particular hemisphere (northern/southern, eastern/western).
- **Meaning:** The interpretation of that hemisphere emphasis (from chart_distribution_interpretations: hemisphere_northern, etc.).

---

*Use this doc to validate the flow before implementing changes. Update it when the flow changes.*
