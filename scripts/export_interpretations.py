"""
Export interpretation data to CSV for editing in Google Sheets.
Usage: python -m scripts.export_interpretations
Writes to data/interpretations_*.csv
"""
import asyncio
import csv
from pathlib import Path

from sqlalchemy import select

from database.connection import AsyncSessionLocal, init_db
from database.models import (
    Planet,
    Sign,
    House,
    Aspect,
    PlanetSignInterpretation,
    PlanetHouseInterpretation,
    AspectInterpretation,
    ChartShapeInterpretation,
    ChartDistributionInterpretation,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"


async def export_all():
    await init_db()
    OUTPUT_DIR.mkdir(exist_ok=True)

    async with AsyncSessionLocal() as session:
        # Reference tables
        for model, path_name, cols, order_col in [
            (Planet, "planets", ["id", "name", "symbol"], Planet.name),
            (Sign, "signs", ["id", "name", "element", "modality"], Sign.name),
            (House, "houses", ["id", "number", "type_"], House.number),
            (Aspect, "aspects", ["id", "name", "angle_degrees", "symbol"], Aspect.name),
        ]:
            rows = (await session.execute(select(model).order_by(order_col))).scalars().all()
            path = OUTPUT_DIR / f"{path_name}.csv"
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                for r in rows:
                    w.writerow([getattr(r, c) for c in cols])
            print(f"Wrote {path} ({len(rows)} rows)")

        # Planet-Sign
        rows = (
            await session.execute(
                select(
                    PlanetSignInterpretation,
                    Planet.name.label("planet"),
                    Sign.name.label("sign"),
                )
                .join(Planet, PlanetSignInterpretation.planet_id == Planet.id)
                .join(Sign, PlanetSignInterpretation.sign_id == Sign.id)
                .order_by(Planet.name, Sign.name)
            )
        ).all()
        path = OUTPUT_DIR / "planet_sign_interpretations.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "planet", "sign", "interpretation_text"])
            for r in rows:
                w.writerow([r.PlanetSignInterpretation.id, r.planet, r.sign, r.PlanetSignInterpretation.interpretation_text])
        print(f"Wrote {path} ({len(rows)} rows)")

        # Planet-House
        rows = (
            await session.execute(
                select(
                    PlanetHouseInterpretation,
                    Planet.name.label("planet"),
                    House.number.label("house"),
                )
                .join(Planet, PlanetHouseInterpretation.planet_id == Planet.id)
                .join(House, PlanetHouseInterpretation.house_id == House.id)
                .order_by(Planet.name, House.number)
            )
        ).all()
        path = OUTPUT_DIR / "planet_house_interpretations.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "planet", "house", "interpretation_text"])
            for r in rows:
                w.writerow([r.PlanetHouseInterpretation.id, r.planet, r.house, r.PlanetHouseInterpretation.interpretation_text])
        print(f"Wrote {path} ({len(rows)} rows)")

        # Aspect
        rows = (
            await session.execute(
                select(
                    AspectInterpretation,
                    Aspect.name.label("aspect"),
                )
                .join(Aspect, AspectInterpretation.aspect_id == Aspect.id)
                .order_by(Aspect.name)
            )
        ).all()
        path = OUTPUT_DIR / "aspect_interpretations.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "aspect", "interpretation_text"])
            for r in rows:
                w.writerow([r.AspectInterpretation.id, r.aspect, r.AspectInterpretation.interpretation_text])
        print(f"Wrote {path} ({len(rows)} rows)")

        # Chart Shape
        rows = (
            await session.execute(
                select(ChartShapeInterpretation).order_by(ChartShapeInterpretation.shape_key)
            )
        ).scalars().all()
        path = OUTPUT_DIR / "chart_shape_interpretations.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "shape_key", "interpretation_text"])
            for r in rows:
                w.writerow([r.id, r.shape_key, r.interpretation_text])
        print(f"Wrote {path} ({len(rows)} rows)")

        # Chart Distribution
        rows = (
            await session.execute(
                select(ChartDistributionInterpretation).order_by(ChartDistributionInterpretation.distribution_key)
            )
        ).scalars().all()
        path = OUTPUT_DIR / "chart_distribution_interpretations.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "distribution_key", "interpretation_text"])
            for r in rows:
                w.writerow([r.id, r.distribution_key, r.interpretation_text])
        print(f"Wrote {path} ({len(rows)} rows)")

    print(f"\nAll CSVs written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    asyncio.run(export_all())
