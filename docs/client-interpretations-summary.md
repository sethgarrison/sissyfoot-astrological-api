# Client guide: reading UI from `interpretation` + `chart_data`

How to build the natal-chart reading UI from **`GET /chart`** and **`POST /chart`** (and saved readings), which return **`ChartAPIResponse`**: top-level metadata, **`chart_data`** (drawing only), and **`interpretation`** (all interpretive copy).

TypeScript types: [`types/api.ts`](../types/api.ts) (`ChartAPIResponse`, `ChartData`, `ChartInterpretation`, nested types).

---

## Where the data lives

| Path | Purpose |
|------|---------|
| **`chart_data`** | Aspects, planet positions, nodes, houses, element/quality counts, lunar phase. **Use only** to draw the chart — do not drive reading copy from raw placements here. |
| **`interpretation`** | Big three, chart context, **house_groups** (planets + nested aspects + long texts), retrograde lists. **Use this** for the reading UI. |

---

## 1. House sections (`interpretation.house_groups`)

The API returns **only houses that contain at least one planet**. Empty houses are omitted.

For each **`house_group`**:

| Field | Use |
|-------|-----|
| `house` | House number (1–12). |
| `house_keyword` | Theme for the section header (from DB). May be empty. |
| `sign_on_cusp` | Zodiac sign on that house cusp. |
| `interpretation.house_in_sign` | Long text for sign on the cusp (incl. rising / house 1 when applicable). |

**Suggested heading**

- `House {house}: {house_keyword}` when `house_keyword` is present.
- Otherwise: `House {house}` or `House {house} · {sign_on_cusp}`.

---

## 2. Planet rows (`house_groups[].planets`)

Each object is one **chart planet** (Sun through Chiron) in that house.

| Field | Use |
|-------|-----|
| `body` | Planet name (e.g. `Sun`, `Moon`). |
| `synthesis` | Short line: **`{planet_keyword} {sign_adverb}`** only (no house theme). |
| `planet_keyword` | From reference data. |
| `sign`, `sign_adverb` | Sign and its adverb. |
| `retrograde` | If `true`, show e.g. “Rx” next to the name. |

**Suggested line**

```text
{body}: {synthesis}
```

**Long prose**

- `interpretation.planet_in_sign` — planet-in-sign text.
- `interpretation.planet_in_house` — planet-in-house text.

---

## 3. Aspects under each planet (`planets[].aspects`)

Each list includes **every chart aspect that involves this planet**. The same logical aspect may appear **twice** (once under each endpoint).

| Field | Use |
|-------|-----|
| `aspect` | Aspect name from the ephemeris (e.g. `Trine`, `Conjunction`). |
| `synthesis` | **Short** line for the summary list. |
| `interpretation` | **Long** text; use for “read more”, modal, or tooltip. |
| `aspect_keyphrase` | `null` for conjunctions; otherwise the phrase used in building `synthesis`. |
| `other_body`, `other_sign` | Partner planet and sign. |
| `is_placeholder` | If `true`, treat as draft / missing real copy. |

**Server rules**

- **Conjunction:** `aspect_keyphrase` is `null`. `synthesis` matches the **other planet’s placement synthesis**.
- **Other aspects:** `synthesis` is assembled from keyphrase + other planet keyword + other sign adverb.

Drawing metadata for aspects (type, DB vs default, placeholders) also appears on **`chart_data.aspects`** for the wheel; keep interpretation copy under **`interpretation`** only.

---

## 4. Chart context (`interpretation.context`)

| Path | Content |
|------|---------|
| `shape.key` / `shape.interpretation` | Chart shape id and paragraph. |
| `spatial_distribution` | Combined hemisphere/quadrant emphasis (`key` + `interpretation` string). |
| `quality_distribution` | Dominant modality / balanced copy (`key` + `interpretation`). |
| `modality_distribution` | Element emphasis (`key` + `interpretation`). |

Render as separate blocks after the house list.

---

## 5. Big three (`interpretation.big_three`)

Rich objects for **Sun**, **Moon**, and **Ascendant**. There is **no** synthetic Ascendant row in `house_groups`; rising meaning is here and in house 1’s `house_in_sign` when provided.

---

## 6. Data quality and admin

- **Sign adverbs** (`adverb`) and **aspect summary phrases** (`summary_keyphrase`) are editable via **`/data/signs`** and **`/data/aspects`**.
- If lexicon fetch fails server-side, the API still returns charts using **built-in defaults**.

---

## 7. Example layout (outline)

```text
[context: shape, spatial, quality, modality]

For each house_group:
  Heading: House N: house_keyword
  Sub: house_in_sign (optional block)

  For each planet:
    • body: synthesis   [Rx if retrograde]
    planet_in_sign / planet_in_house (expand)
    For each aspect:
      – aspect: synthesis   (tap → interpretation)

[Big three: sun / moon / ascendant]
[Retrogrades: retrograde_planets + retrograde_interpretations]
```

---

## Related server code

- Wire response: [`chart_pipeline.py`](../chart_pipeline.py) (`build_chart_api_response`)
- Internal summary builder: [`interpretations/summary.py`](../interpretations/summary.py)
- DB + lexicon: [`interpretations/lookup.py`](../interpretations/lookup.py)
- Defaults: [`interpretations/lexicons.py`](../interpretations/lexicons.py)
