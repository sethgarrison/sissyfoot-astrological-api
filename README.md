# Natal Chart API

A REST API for generating natal (birth) charts, powered by the **Swiss Ephemeris** via [Kerykeion](https://github.com/g-battaglia/kerykeion).

Returns planetary positions, house cusps, aspects, lunar phase, and the big three (sun/moon/rising) for any birth date, time, and location.

## Endpoints

| Method | Path      | Description                |
|--------|-----------|----------------------------|
| GET    | `/chart`  | Generate a natal chart     |
| POST   | `/chart`  | Generate a natal chart     |
| GET    | `/health` | Health check               |
| GET    | `/docs`   | Interactive Swagger UI     |

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
| lat      | *        | Latitude                                |
| lng      | *        | Longitude                               |
| tz_str   | *        | IANA timezone (e.g. `America/New_York`) |
| city     | *        | Birth city name                         |
| nation   | *        | ISO 2-letter country code               |
| name     | no       | Optional label for the subject          |

### Example

```bash
# Using direct coordinates (no API key needed)
curl "http://localhost:8000/chart?year=1990&month=6&day=15&hour=12&minute=0&lat=40.7128&lng=-74.006&tz_str=America/New_York"

# Using city geocoding (needs GEONAMES_USERNAME)
curl "http://localhost:8000/chart?year=1990&month=6&day=15&hour=12&city=New+York&nation=US"
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

## Deploy to Render (free)

1. Push this repo to GitHub
2. Go to https://render.com and create a new **Web Service**
3. Connect your GitHub repo
4. Render will auto-detect the `Dockerfile` — no config needed
5. (Optional) Add `GEONAMES_USERNAME` as an environment variable if you want city lookup

The included `render.yaml` also supports Render Blueprints for one-click deploy.
