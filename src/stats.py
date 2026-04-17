"""Per-driver and season-wide statistics derived from race results."""


def compute_driver_stats(driver: str, race_results_by_race: dict[str, list[dict]]) -> dict:
    """Compute all-time stats for a single driver."""
    history = [
        r for results in race_results_by_race.values()
        for r in results
        if r['driver'] == driver
    ]

    if not history:
        return {
            'races_entered': 0, 'wins': 0, 'podiums': 0, 'fastest_laps': 0,
            'total_penalties': 0.0, 'total_points': 0,
            'avg_finish_position': None, 'best_finish': None, 'worst_finish': None,
        }

    positions = [h['position'] for h in history]
    return {
        'races_entered':       len(history),
        'wins':                sum(1 for p in positions if p == 1),
        'podiums':             sum(1 for p in positions if p <= 3),
        'fastest_laps':        sum(1 for h in history if h.get('has_fastest_lap')),
        'total_penalties':     round(sum(h.get('penalty', 0) for h in history), 2),
        'total_points':        sum(h['points'] for h in history),
        'avg_finish_position': round(sum(positions) / len(positions), 2),
        'best_finish':         min(positions),
        'worst_finish':        max(positions),
    }


def compute_season_stats(
    standings: list[dict],
    race_results_by_race: dict[str, list[dict]],
) -> dict:
    """Compute season-wide records and summary statistics."""
    races = list(race_results_by_race.keys())

    win_counts:      dict[str, int]   = {}
    podium_counts:   dict[str, int]   = {}
    fl_counts:       dict[str, int]   = {}
    penalty_totals:  dict[str, float] = {}

    for results in race_results_by_race.values():
        for r in results:
            d = r['driver']
            if r['position'] == 1:
                win_counts[d]     = win_counts.get(d, 0) + 1
            if r['position'] <= 3:
                podium_counts[d]  = podium_counts.get(d, 0) + 1
            if r.get('has_fastest_lap'):
                fl_counts[d]      = fl_counts.get(d, 0) + 1
            penalty_totals[d]     = penalty_totals.get(d, 0.0) + r.get('penalty', 0)

    def _top(counts: dict) -> tuple:
        if not counts:
            return None, 0
        d = max(counts, key=lambda k: counts[k])
        return d, counts[d]

    wins_driver,     wins_n     = _top(win_counts)
    podiums_driver,  podiums_n  = _top(podium_counts)
    fl_driver,       fl_n       = _top(fl_counts)
    pen_driver,      pen_total  = _top(penalty_totals)

    leader = standings[0] if standings else None
    leader_pts = int(leader['total_points']) if leader else 0

    return {
        'total_races':   len(races),
        'total_drivers': len(standings),
        'leader':        leader['driver'] if leader else None,
        'leader_points': leader_pts,
        'points_table':  {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1},
        'fastest_lap_bonus': 1,
        'points_gaps': [
            {
                'position': s['position'],
                'driver':   s['driver'],
                'gap_to_leader': leader_pts - int(s['total_points']),
            }
            for s in standings
        ],
        'records': {
            'most_wins':         {'driver': wins_driver,    'wins':            wins_n},
            'most_podiums':      {'driver': podiums_driver, 'podiums':         podiums_n},
            'most_fastest_laps': {'driver': fl_driver,      'count':           fl_n},
            'most_penalties':    {'driver': pen_driver,     'penalty_seconds': round(pen_total, 2)},
        },
    }
