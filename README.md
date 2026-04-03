# Natal Chart API

A REST API for generating natal (birth) charts, powered by the **Swiss Ephemeris** via [Kerykeion](https://github.com/g-battaglia/kerykeion).

Returns planetary positions, house cusps, aspects, lunar phase, the big three (sun/moon/rising), and **interpretations** stored in the database (planet-in-sign, planet-in-house, aspect type, chart shape, and hemisphere/quadrant emphasis).

## Endpoints

| Method | Path               | Description                         |
|--------|--------------------|-------------------------------------|
| GET    | `/locations`       | Search locations for birth place (autocomplete) |
| GET    | `/chart`           | Generate a natal chart (saves to DB)|
| POST   | `/chart`           | Generate a natal chart (saves to DB)|
| GET    | `/readings`        | List all saved readings              |
| GET    | `/readings/{id}`   | Fetch a saved reading by identifier  |
| GET    | `/data/planets`    | Raw planets table                    |
| PATCH  | `/data/planets/{id}` | Update planet by id                 |
| GET    | `/data/signs`      | Raw signs table (includes Sun-in-sign Big Three fields) |
| PATCH  | `/data/signs/{id}` | Update sign by id                   |
| GET    | `/data/houses`     | Raw houses table                     |
| PATCH  | `/data/houses/{id}` | Update house by id                  |
| GET    | `/data/aspects`    | Raw aspects table                    |
| PATCH  | `/data/aspects/{id}` | Update aspect by id                 |
| GET    | `/data/moon`       | **Big Three:** Moon in sign interpretations |
| PATCH  | `/data/moon/{id}`  | Update Moon sign interpretation      |
| GET    | `/data/ascendant`  | **Big Three:** Ascendant/Rising in sign interpretations |
| PATCH  | `/data/ascendant/{id}` | Update Ascendant sign interpretation |
| GET    | `/data/planet-sign` | Planet in sign interpretations       |
| PATCH  | `/data/planet-sign/{id}` | Update planet-sign interpretation |
| GET    | `/data/planet-house` | Planet in house interpretations     |
| PATCH  | `/data/planet-house/{id}` | Update planet-house interpretation |
| GET    | `/data/aspect-type` | Aspect type interpretations (conjunction, stressful, easy-flowing) |
| PATCH  | `/data/aspect-type/{id}` | Update aspect type interpretation |
| GET    | `/data/aspect-generic` | Generic aspect interpretations   |
| PATCH  | `/data/aspect-generic/{id}` | Update generic aspect interpretation |
| GET    | `/data/planet-aspect` | Planet-pair aspect interpretations |
| PATCH  | `/data/planet-aspect/{id}` | Update planet-aspect interpretation |
| GET    | `/data/sign-house` | Sign on house cusp interpretations   |
| PATCH  | `/data/sign-house/{id}` | Update sign-house interpretation |
| GET    | `/data/chart-shape` | Chart shape interpretations         |
| PATCH  | `/data/chart-shape/{id}` | Update chart shape interpretation |
| GET    | `/data/chart-distribution` | Hemisphere/quadrant interpretations |
| PATCH  | `/data/chart-distribution/{id}` | Update chart distribution interpretation |
| GET    | `/data/modality-element` | Modality/element distribution interpretations |
| PATCH  | `/data/modality-element/{id}` | Update modality-element interpretation |
| GET    | `/health`          | Health check                        |
| GET    | `/debug/interpretations` | Debug: interpretation table row counts |
| GET    | `/docs`            | Interactive Swagger UI              |

### Query parameters / body fields

You can provide location two ways:

1. **Direct coordinates** (no network calls): `lat`, `lng`, `tz_str`
2. **City geocoding** (requires GeoNames): `city`, `nation`

| Field    | Required | Description                             |
|----------|----------|-----------------------------------------|
| year     | yes      | Birth year                              |
| month    | yes      | Birth month (1-12)                      |
| day      | yes      | Birth day (1-31)                        |
| hour     | no       | Birth hour, 24h format (default: 12)    |
| minute   | no       | Birth minute (default: 0)               |
| time     | no       | Alternative: `HH:MM` or `HH:MM:SS` (overrides hour & minute) |
| lat      | *        | Latitude                                |
| lng      | *        | Longitude                               |
| tz_str   | *        | IANA timezone (e.g. `America/New_York`) |
| house_system | no    | `whole_sign` (default) or `placidus`    |
| city     | *        | Birth city name                         |
| nation   | *        | ISO 2-letter country code               |
| name     | no       | Optional label for the subject          |

### Example

```bash
# Using direct coordinates (no API key needed)
curl "http://localhost:8000/chart?year=1990&month=6&day=15&hour=12&minute=30&lat=40.7128&lng=-74.006&tz_str=America/New_York"
# Or use time=HH:MM
curl "http://localhost:8000/chart?year=1990&month=6&day=15&time=12:30&lat=40.7128&lng=-74.006&tz_str=America/New_York"

# Using city geocoding (needs GEONAMES_USERNAME)
curl "http://localhost:8000/chart?year=1990&month=6&day=15&hour=12&city=New+York&nation=US"
```

### Saved readings

Each chart is saved with identifier `name__birthdatetime__lat__lng`. The response includes `reading_id` — use it to fetch the reading later:

```bash
# Generate chart (returns reading_id in response)
curl "http://localhost:8000/chart?year=1990&month=6&day=15&name=Jane&lat=40.7128&lng=-74.006&tz_str=America/New_York"

# Fetch saved reading by identifier
curl "http://localhost:8000/readings/Jane__1990-06-15T12:00__40.7128__-74.006"
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://localhost:8000/docs for the interactive API docs.

### Optional: GeoNames for city lookup

If you want to use `city`+`nation` instead of raw coordinates, create a free account at https://www.geonames.org/login and set:

```bash
export GEONAMES_USERNAME=your_username
```

### Interpretations database

The chart response splits **`chart_data`** (positions, houses, aspects, distributions, lunar phase — for drawing only) from **`interpretation`** (big three, chart context, house-grouped readings, retrogrades). Interpretation copy is loaded from the database. **Client rendering guide:** [astrology/docs/client-interpretations-summary.md](astrology/docs/client-interpretations-summary.md).

Saved readings store the same JSON shape as `GET /chart` / `POST /chart` (`ChartAPIResponse`). Older rows saved in the previous `NatalChart` format will not validate until re-generated.

- **Local:** Without `DATABASE_URL`, the app uses SQLite (`natal_chart.db`) in the project directory.

**The database is the source of truth.** Interpretations are maintained on the server (or in your local DB). Use the **`/data/*`** GET and PATCH endpoints for structured edits, or **[astrology/docs/EDITING_DATABASE.md](astrology/docs/EDITING_DATABASE.md)** for direct SQL. Sun-in-sign (Big Three) fields live on the `signs` table.

## Deploy to Render (free)

1. Push this repo to GitHub
2. Go to https://render.com and create a new **Web Service**
3. Connect your GitHub repo
4. Render will auto-detect the `Dockerfile` — no config needed
5. **City geocoding setup** (required for `city`+`nation` lookups):
   - Create a free account at https://www.geonames.org/login
   - Confirm your email
   - Enable web services at https://www.geonames.org/manageaccount
   - In Render → your service → **Environment** → add: `GEONAMES_USERNAME` = your username

The included `render.yaml` also supports Render Blueprints for one-click deploy.

> **Note:** Without `GEONAMES_USERNAME`, use `lat`+`lng`+`tz_str` instead of `city`+`nation`.
