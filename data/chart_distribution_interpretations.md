# Chart Distribution Interpretations

Interpretations for hemisphere and quadrant (quarter) distribution are stored in `chart_distribution_interpretations` and returned under `interpretations.chart_shape.distribution` in the API response.

## Key Scheme

Based on **planetary placements by house** (which houses contain planets).

### Hemisphere emphasis (>50% in one half)
| Key | When it applies |
|-----|-----------------|
| `hemisphere_northern` | More than half of planets in houses 7–12 (above horizon) |
| `hemisphere_southern` | More than half of planets in houses 1–6 (below horizon) |
| `hemisphere_eastern` | More than half of planets in houses 10–12, 1–3 (ascendant side) |
| `hemisphere_western` | More than half of planets in houses 4–9 (descendant side) |

### Hemisphere spread (balanced distribution)
| Key | When it applies |
|-----|-----------------|
| `hemisphere_spread_north_south` | Planets in both N and S hemispheres, neither has a majority |
| `hemisphere_spread_east_west` | Planets in both E and W hemispheres, neither has a majority |

### Quadrant/quarter emphasis (>50% in one quarter)
| Key | When it applies |
|-----|-----------------|
| `quadrant_1` | More than half of planets in houses 1–3 |
| `quadrant_2` | More than half of planets in houses 4–6 |
| `quadrant_3` | More than half of planets in houses 7–9 |
| `quadrant_4` | More than half of planets in houses 10–12 |

### Quadrant/quarter spread
| Key | When it applies |
|-----|-----------------|
| `quadrant_spread` | No single quadrant has a majority; planets span 2+ quadrants |

## Running the seed

```bash
python -m database.seed
```

Creates placeholder rows for all keys. For spread keys, the placeholder uses "(planets distributed across regions)"; for emphasis keys, it uses "emphasis".
