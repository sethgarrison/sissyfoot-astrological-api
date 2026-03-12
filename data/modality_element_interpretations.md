# Modality & Element Distribution Interpretations

Interpretations for this chart are stored in `modality_element_distribution_interpretations` and keyed by `distribution_key`. Keys are determined from **planetary placements** (which signs have planets), not house cusps.

## Key Scheme

When adding interpretations manually, use these exact keys:

### Element (fire, earth, air, water)

| Key | When it applies |
|-----|-----------------|
| `element_fire_dominant` | Fire has the most planets (strictly more than earth, air, water) |
| `element_earth_dominant` | Earth has the most planets |
| `element_air_dominant` | Air has the most planets |
| `element_water_dominant` | Water has the most planets |
| `element_balanced` | No single element has the most (e.g., fire and air are tied for highest) |
| `element_lacking_fire` | Zero planets in fire signs |
| `element_lacking_earth` | Zero planets in earth signs |
| `element_lacking_air` | Zero planets in air signs |
| `element_lacking_water` | Zero planets in water signs |

### Quality / Modality (cardinal, fixed, mutable)

| Key | When it applies |
|-----|-----------------|
| `quality_cardinal_dominant` | Cardinal signs have the most planets |
| `quality_fixed_dominant` | Fixed signs have the most planets |
| `quality_mutable_dominant` | Mutable signs have the most planets |
| `quality_balanced` | No single modality has the most (tie for highest) |

## Multiple keys per chart

A chart can match several keys at once. For example:

- `element_fire_dominant` + `element_lacking_water` + `quality_cardinal_dominant`

All matching interpretations are returned under `interpretations.modality_element_distribution` in the API response.

## Running the seed

```bash
python -m database.seed
```

This creates placeholder rows for all keys. Replace `[Add your interpretation here]` with your content.
