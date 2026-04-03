# Editing the Database Manually

**DB is the source of truth.** No CSV bulk updates—edit directly in the database.

---

## Quick reference

| Environment | Database | How to edit |
|-------------|----------|-------------|
| **Local** | SQLite `./natal_chart.db` | `sqlite3 natal_chart.db` or [DB Browser for SQLite](https://sqlitebrowser.org/) |
| **Production** | PostgreSQL (from `DATABASE_URL`) | `psql $DATABASE_URL` or Render Shell → `psql $DATABASE_URL` |

---

## Before you edit

1. **Backup** (local SQLite): `cp natal_chart.db natal_chart.db.backup`
2. **Backup** (PostgreSQL): Use your host’s backup tools or `pg_dump` before large changes.
3. Use `data/models_report.md` for table/column reference.

---

## SQLite (local)

```bash
# Open the DB
sqlite3 natal_chart.db

# List tables
.tables

# Describe a table
.schema sun_sign_interpretations

# Exit
.quit
```

---

## Lookup IDs (needed for FKs)

```sql
-- Signs (name → id)
SELECT id, name FROM signs;

-- Planets (name → id)
SELECT id, name FROM planets;

-- Houses (number → id)
SELECT id, number FROM houses;

-- Aspects (name → id)
SELECT id, name, type_ FROM aspects;
```

---

## Example edits

### Big Three: Sun in Aries

```sql
-- Get sign_id for Aries
SELECT id FROM signs WHERE name = 'Aries';  -- e.g. 1

-- Update Sun-in-Aries interpretation
UPDATE sun_sign_interpretations
SET interpretation = 'Your new interpretation here.',
    archetypes_balanced = '...',
    gifts = '...'
WHERE sign_id = (SELECT id FROM signs WHERE name = 'Aries');
```

### Big Three: Moon in Cancer

```sql
UPDATE moon_sign_interpretations
SET interpretation = 'Your Moon in Cancer text.',
    nature = '...',
    sources_of_contentment = '...'
WHERE sign_id = (SELECT id FROM signs WHERE name = 'Cancer');
```

### Big Three: Ascendant in Libra

```sql
UPDATE ascendant_sign_interpretations
SET interpretation = 'Your Ascendant in Libra text.',
    impression = '...',
    appearance = '...'
WHERE sign_id = (SELECT id FROM signs WHERE name = 'Libra');
```

### Planet in sign (e.g. Mercury in Gemini)

```sql
UPDATE planet_sign_interpretations
SET interpretation_text = 'Your interpretation.'
WHERE planet_id = (SELECT id FROM planets WHERE name = 'Mercury')
  AND sign_id = (SELECT id FROM signs WHERE name = 'Gemini');
```

### Planet in house (e.g. Venus in House 7)

```sql
UPDATE planet_house_interpretations
SET interpretation_text = 'Your interpretation.'
WHERE planet_id = (SELECT id FROM planets WHERE name = 'Venus')
  AND house_id = (SELECT id FROM houses WHERE number = 7);
```

### Sign on house cusp (e.g. Aries on 1st = Rising)

```sql
UPDATE sign_house_interpretations
SET interpretation_text = 'Your Aries Rising interpretation.'
WHERE house_id = (SELECT id FROM houses WHERE number = 1)
  AND sign_id = (SELECT id FROM signs WHERE name = 'Aries');
```

### Aspect type (conjunction / stressful / easy-flowing)

```sql
UPDATE aspect_type_interpretations
SET interpretation_text = 'Your interpretation for this aspect type.'
WHERE type_key = 'stressful';  -- or 'conjunction', 'easy-flowing'
```

### Chart shape (e.g. bowl)

```sql
UPDATE chart_shape_interpretations
SET interpretation_text = 'Your chart shape interpretation.'
WHERE shape_key = 'bowl';
```

---

## Adding a new row (if missing)

```sql
-- Example: add Sun-in-Aries row (normally exists after seed)
INSERT INTO sun_sign_interpretations (sign_id, interpretation, archetypes_balanced, archetypes_unbalanced, journey, gifts, challenges)
SELECT id, 'Your text', NULL, NULL, NULL, NULL, NULL
FROM signs WHERE name = 'Aries';
```

---

## PostgreSQL (production)

```bash
# From Render Shell or local with DATABASE_URL set:
psql "$DATABASE_URL"

# Same SQL as above; Postgres is case-sensitive for identifiers in quotes.
```

---

## Table summary

| Table | Lookup key | Main text column(s) |
|-------|------------|---------------------|
| `sun_sign_interpretations` | sign_id | interpretation, archetypes_*, gifts, challenges |
| `moon_sign_interpretations` | sign_id | interpretation, nature, sources_of_contentment |
| `ascendant_sign_interpretations` | sign_id | interpretation, impression, appearance |
| `planet_sign_interpretations` | planet_id, sign_id | interpretation_text |
| `planet_house_interpretations` | planet_id, house_id | interpretation_text |
| `sign_house_interpretations` | house_id, sign_id | interpretation_text |
| `aspect_type_interpretations` | type_key | interpretation_text |
| `planet_aspect_interpretations` | planet_1_id, planet_2_id, aspect_id | interpretation_text |
| `chart_shape_interpretations` | shape_key | interpretation_text |
| `chart_distribution_interpretations` | distribution_key | interpretation_text |
| `modality_element_distribution_interpretations` | distribution_key | interpretation_text |
