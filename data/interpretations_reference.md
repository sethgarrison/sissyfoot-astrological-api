# Complete Interpretation Models Reference

Full picture of all interpretation data for the natal chart API and reading UI.

---

## API Response: `interpretations` Object

All interpretations live under `chart.interpretations`:

```json
{
  "interpretations": {
    "planet_in_sign": { ... },
    "planet_in_house": { ... },
    "aspects": { ... },
    "chart_shape": { ... },
    "modality_element_distribution": { ... },
    "retrograde_planets": [ ... ],
    "retrograde_interpretations": { ... }
  }
}
```

---

## 1. Planet in Sign

**Path:** `interpretations.planet_in_sign`  
**Type:** `dict[str, str]`  
**Key format:** `"Planet in Sign"` (e.g. `"Sun in Aries"`, `"Moon in Cancer"`, `"Rising in Libra"`)

| Source | Table | Column |
|--------|-------|--------|
| Database | `planet_sign_interpretations` | `interpretation_text` |
| Fallback | Built-in defaults | Sun, Moon, Rising only |

**Planets:** Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron  
**Rising:** Uses `"Rising in {rising_sign}"` as key (rising sign is on House 1 cusp)

---

## 2. Planet in House

**Path:** `interpretations.planet_in_house`  
**Type:** `dict[str, str]`  
**Key format:** `"Planet in House N"` (e.g. `"Sun in House 1"`, `"Mercury in House 3"`)

| Source | Table | Column |
|--------|-------|--------|
| Database | `planet_house_interpretations` | `interpretation_text` |
| Fallback | Built-in defaults | All planet-house pairs |

---

## 3. Aspects

**Path:** `interpretations.aspects`  
**Type:** `dict[str, str]`  
**Key format:** `"Planet1 aspect_type Planet2"` (e.g. `"Sun square Moon"`, `"Venus trine Mars"`)

| Source | Table | Column |
|--------|-------|--------|
| Database | `aspect_interpretations` | `interpretation_text` (looked up by aspect type only) |
| Fallback | Built-in defaults | Conjunction, Opposition, Square, Trine, Sextile, Quincunx |

**Raw aspect data:** `chart.aspects` has full aspect list with `planet1`, `planet2`, `aspect`, `orbit`, `movement`.

---

## 4. Chart Shape

**Path:** `interpretations.chart_shape`  
**Type:** Object with `primary`, `interpretation`, `distribution`

```json
{
  "primary": "bundle",
  "interpretation": "The Bundle pattern: ...",
  "distribution": { "hemisphere_northern": "...", "quadrant_spread": "..." }
}
```

### 4a. Shape interpretation (`primary` + `interpretation`)

| Source | Table | Column |
|--------|-------|--------|
| Database | `chart_shape_interpretations` | `interpretation_text` |
| Detection | `interpretations/chart_shapes.py` | `detect_chart_shape()` |

**Shape keys:** `splash`, `splay`, `bundle`, `bowl`, `locomotive`, `bucket`, `see_saw`

### 4b. Distribution (`distribution` sub-dict)

| Source | Table | Column |
|--------|-------|--------|
| Database | `chart_distribution_interpretations` | `interpretation_text` |
| Detection | `interpretations/chart_shapes.py` | `detect_distributions()` |

**Keys (hemisphere/quadrant):**

| Key | Meaning |
|-----|---------|
| `hemisphere_northern` | >50% of planets in houses 7–12 |
| `hemisphere_southern` | >50% in 1–6 |
| `hemisphere_eastern` | >50% in 10–12, 1–3 |
| `hemisphere_western` | >50% in 4–9 |
| `quadrant_1` | >50% in 1–3 |
| `quadrant_2` | >50% in 4–6 |
| `quadrant_3` | >50% in 7–9 |
| `quadrant_4` | >50% in 10–12 |
| `hemisphere_spread_north_south` | Planets in both N & S, neither >50% |
| `hemisphere_spread_east_west` | Planets in both E & W, neither >50% |
| `quadrant_spread` | No quadrant >50%, planets in 2+ quadrants |

---

## 5. Modality & Element Distribution

**Path:** `interpretations.modality_element_distribution`  
**Type:** `dict[str, str]`  
**Key format:** `element_X_dominant`, `element_balanced`, `element_lacking_X`, `quality_X_dominant`, `quality_balanced`

| Source | Table | Column |
|--------|-------|--------|
| Database | `modality_element_distribution_interpretations` | `interpretation_text` |
| Detection | `interpretations/modality_element.py` | From `houses_overview.by_quality`, `by_element` |

**Keys:**

| Key | When it applies |
|-----|-----------------|
| `element_fire_dominant` | Fire has the most planets |
| `element_earth_dominant` | Earth has the most planets |
| `element_air_dominant` | Air has the most planets |
| `element_water_dominant` | Water has the most planets |
| `element_balanced` | No single element dominates |
| `element_lacking_fire` | 0 planets in fire signs |
| `element_lacking_earth` | 0 planets in earth signs |
| `element_lacking_air` | 0 planets in air signs |
| `element_lacking_water` | 0 planets in water signs |
| `quality_cardinal_dominant` | Cardinal has the most planets |
| `quality_fixed_dominant` | Fixed has the most planets |
| `quality_mutable_dominant` | Mutable has the most planets |
| `quality_balanced` | No single modality dominates |

**Supporting data:** `chart.houses_overview` has `by_quality`, `by_element` with `count`, `signs`, `planets` per category.

---

## 6. Retrograde

**Path:** `interpretations.retrograde_planets` and `interpretations.retrograde_interpretations`  
**Types:** `list[str]`, `dict[str, str]`

### 6a. Retrograde planets list

**Path:** `interpretations.retrograde_planets`  
**Type:** `list[str]`  
**Value:** Sorted list of planet names that are retrograde (e.g. `["Mercury", "Venus"]`)

**Source:** `chart.planets` where `retrograde === true`

### 6b. Retrograde interpretations

**Path:** `interpretations.retrograde_interpretations`  
**Type:** `dict[str, str]`  
**Key format:** Same as planet_in_sign and planet_in_house (e.g. `"Mercury in Gemini"`, `"Mercury in House 3"`)

| Source | Table | Column |
|--------|-------|--------|
| Database | `planet_sign_interpretations` | `retrograde_interpretation` |
| Database | `planet_house_interpretations` | `retrograde_interpretation` |

Only entries for retrograde planets with non-null `retrograde_interpretation` are returned.

---

## Supporting Chart Data (for UI context)

These are **not** interpretations but provide context for the reading:

| Path | Type | Description |
|------|------|-------------|
| `chart.planets` | `list[PlanetPosition]` | All planets with `name`, `sign`, `house`, `degree`, `retrograde`, etc. |
| `chart.houses_overview` | `SignPlacementOverview` | `signs_with_planets`, `by_quality`, `by_element` |
| `chart.aspects` | `list[AspectInfo]` | Full aspect list with planets, type, orbit |
| `chart.sun_sign` | `str` | Rising / Sun / Moon signs |
| `chart.moon_sign` | `str` | |
| `chart.rising_sign` | `str` | |
| `chart.lunar_phase` | `LunarPhase` | `phase_name`, `emoji`, `degrees_between` |
| `chart.lunar_nodes` | `list[LunarNodePosition]` | North & South Node positions |
| `chart.houses` | `list[HouseCusp]` | House cusps (sign, degree) |

---

## Database Tables Summary

| Table | Keyed by | Columns for interpretation |
|-------|----------|----------------------------|
| `planet_sign_interpretations` | planet_id, sign_id | `interpretation_text`, `retrograde_interpretation` |
| `planet_house_interpretations` | planet_id, house_id | `interpretation_text`, `retrograde_interpretation` |
| `aspect_interpretations` | aspect_id | `interpretation_text` |
| `chart_shape_interpretations` | shape_key | `interpretation_text` |
| `chart_distribution_interpretations` | distribution_key | `interpretation_text` |
| `modality_element_distribution_interpretations` | distribution_key | `interpretation_text` |

---

## Suggested Reading UI Sections

1. **Big Three** – Sun, Moon, Rising from `planet_in_sign`
2. **Planets in Signs** – All `planet_in_sign` (group by planet or by section)
3. **Planets in Houses** – All `planet_in_house`
4. **Retrograde** – If `retrograde_planets.length > 0`, show section with `retrograde_interpretations`
5. **Aspects** – `aspects` dict (or list from `chart.aspects` with interpretation text)
6. **Chart Shape** – `chart_shape.primary` + `chart_shape.interpretation`
7. **Hemisphere/Quadrant** – `chart_shape.distribution` (house distribution)
8. **Modality & Element** – `modality_element_distribution` (sign placement distribution)
