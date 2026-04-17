"""JSON data exporters for React frontend consumption."""
import json
from datetime import datetime
from pathlib import Path


def _write_json(data: dict, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Written: {path}")


def export_standings(df, race_results_by_race: dict, output_path: str = 'data/standings.json') -> None:
    races = list(race_results_by_race.keys())
    standings = []
    for _, row in df.iterrows():
        driver = row['driver']
        standings.append({
            'position':     int(row['position']),
            'driver':       driver,
            'total_points': int(row['total_points']),
            'race_points':  {race: int(row.get(race, 0) or 0) for race in races},
        })
    _write_json({
        'generated_at': datetime.now().isoformat(),
        'season':       2026,
        'races':        races,
        'standings':    standings,
    }, output_path)


def export_races(race_results_by_race: dict, output_path: str = 'data/races.json') -> None:
    races_out = []
    for race_name, results in race_results_by_race.items():
        fl_driver = next((r['driver']   for r in results if r.get('has_fastest_lap')), None)
        fl_time   = next((r['best_lap'] for r in results if r.get('has_fastest_lap')), None)
        races_out.append({
            'name':               race_name,
            'fastest_lap_driver': fl_driver,
            'fastest_lap_time':   fl_time,
            'results': [
                {
                    'position':       r['position'],
                    'driver':         r['driver'],
                    'kart':           r.get('kart'),
                    'laps':           r.get('laps'),
                    'gap':            r['gap'] if r['gap'] != float('inf') else None,
                    'best_lap':       r.get('best_lap'),
                    'penalty':        r.get('penalty', 0),
                    'final':          r.get('final'),
                    'points':         r['points'],
                    'has_fastest_lap': r.get('has_fastest_lap', False),
                }
                for r in results
            ],
        })
    _write_json({'races': races_out}, output_path)


def export_drivers(
    all_drivers: list[str],
    race_results_by_race: dict,
    stats_by_driver: dict,
    output_path: str = 'data/drivers.json',
) -> None:
    drivers_out = []
    for driver in all_drivers:
        history = []
        for race_name, results in race_results_by_race.items():
            match = next((r for r in results if r['driver'] == driver), None)
            if match:
                history.append({
                    'race':           race_name,
                    'position':       match['position'],
                    'points':         match['points'],
                    'best_lap':       match.get('best_lap'),
                    'penalty':        match.get('penalty', 0),
                    'final':          match.get('final'),
                    'has_fastest_lap': match.get('has_fastest_lap', False),
                })
        drivers_out.append({
            'name':         driver,
            'stats':        stats_by_driver.get(driver, {}),
            'race_history': history,
        })
    _write_json({'drivers': drivers_out}, output_path)


def export_season_stats(season_stats: dict, output_path: str = 'data/season_stats.json') -> None:
    _write_json(season_stats, output_path)
