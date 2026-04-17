#!/usr/bin/env python3
"""
Rebuild classification and all JSON data from every race CSV in wyniki/.
Run this after adding a new monthly CSV: python process_all.py
"""
import json
import sys
import pandas as pd
from pathlib import Path

from src.loader import parse_race_csv
from src.classification import build_race_results, update_classification, save_classification, race_sort_key
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


def main() -> None:
    csv_files = sorted(RACES_DIR.glob('*.csv'), key=race_sort_key)
    if not csv_files:
        print(f"No CSV files found in {RACES_DIR}/")
        sys.exit(1)

    df: pd.DataFrame = pd.DataFrame(columns=['driver', 'total_points'])
    race_results_by_race: dict[str, list[dict]] = {}

    overrides = _load_overrides()

    print("Processing races:")
    for csv_file in csv_files:
        race_name = csv_file.stem.capitalize()
        try:
            raw = parse_race_csv(csv_file)
            fl_override = overrides.get(race_name, {}).get('fastest_lap_driver')
            results = build_race_results(raw, fl_override)
            race_results_by_race[race_name] = results
            df = update_classification(df, results, race_name)
            fl = next((r['driver'] for r in results if r['has_fastest_lap']), 'none')
            print(f"  {race_name}: {len(results)} drivers  |  fastest lap: {fl}")
        except Exception as e:
            print(f"  WARNING: could not process {csv_file.name}: {e}")

    save_classification(df, CLASSIFICATION_CSV)
    print(f"\nClassification saved: {CLASSIFICATION_CSV}")

    all_drivers = df['driver'].tolist()
    stats_by_driver = {d: compute_driver_stats(d, race_results_by_race) for d in all_drivers}
    season_stats = compute_season_stats(df.to_dict('records'), race_results_by_race)

    print("\nExporting JSON:")
    export_standings(df, race_results_by_race)
    export_races(race_results_by_race)
    export_drivers(all_drivers, race_results_by_race, stats_by_driver)
    export_season_stats(season_stats)

    print(f"\nTop 5:")
    for _, row in df.head(5).iterrows():
        print(f"  {int(row['position'])}. {row['driver']:<20} {int(row['total_points'])} pts")


if __name__ == '__main__':
    main()
