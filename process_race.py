#!/usr/bin/env python3
"""
Process a single new race CSV and update classification + JSON data.
Usage: python process_race.py wyniki/maj.csv
"""
import json
import sys
from pathlib import Path

from src.loader import parse_race_csv
from src.classification import (
    build_race_results, load_classification,
    update_classification, save_classification, race_sort_key,
)
from src.stats import compute_driver_stats, compute_season_stats
from src.exporter import export_standings, export_races, export_drivers, export_season_stats

CLASSIFICATION_CSV = 'klasyfikacja_generalna.csv'
RACES_DIR = Path('wyniki')
OVERRIDES_FILE = Path('race_overrides.json')


def _load_overrides() -> dict:
    if OVERRIDES_FILE.exists():
        with open(OVERRIDES_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def _load_all_race_results(overrides: dict) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for csv_file in sorted(RACES_DIR.glob('*.csv'), key=race_sort_key):
        race_name = csv_file.stem.capitalize()
        try:
            fl_override = overrides.get(race_name, {}).get('fastest_lap_driver')
            results[race_name] = build_race_results(parse_race_csv(csv_file), fl_override)
        except Exception as e:
            print(f"  WARNING: could not load {csv_file.name}: {e}")
    return results


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python process_race.py wyniki/<race>.csv")
        sys.exit(1)

    csv_file = Path(sys.argv[1])
    if not csv_file.exists():
        print(f"File not found: {csv_file}")
        sys.exit(1)

    race_name = csv_file.stem.capitalize()
    print(f"Processing: {csv_file}  (race: '{race_name}')")

    overrides = _load_overrides()
    fl_override = overrides.get(race_name, {}).get('fastest_lap_driver')
    raw = parse_race_csv(csv_file)
    race_results = build_race_results(raw, fl_override)

    print(f"\nResults ({len(race_results)} drivers):")
    for r in race_results:
        fl  = " [FASTEST LAP]" if r['has_fastest_lap'] else ""
        pen = f" (+{r['penalty']}s penalty)" if r.get('penalty', 0) > 0 else ""
        print(f"  {r['position']:2}. {r['driver']:<20} {r['points']:2} pts{fl}{pen}")

    df = load_classification(CLASSIFICATION_CSV)
    df = update_classification(df, race_results, race_name)
    save_classification(df, CLASSIFICATION_CSV)
    print(f"\nClassification updated: {CLASSIFICATION_CSV}")

    all_race_results = _load_all_race_results(overrides)
    all_drivers = df['driver'].tolist()
    stats_by_driver = {d: compute_driver_stats(d, all_race_results) for d in all_drivers}
    season_stats = compute_season_stats(df.to_dict('records'), all_race_results)

    print("\nExporting JSON:")
    export_standings(df, all_race_results)
    export_races(all_race_results)
    export_drivers(all_drivers, all_race_results, stats_by_driver)
    export_season_stats(season_stats)

    print(f"\nTop 5:")
    for _, row in df.head(5).iterrows():
        print(f"  {int(row['position'])}. {row['driver']:<20} {int(row['total_points'])} pts")


if __name__ == '__main__':
    main()
