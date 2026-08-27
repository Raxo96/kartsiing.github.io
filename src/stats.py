"""Per-driver and season-wide statistics derived from race results."""
import math


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return round(math.sqrt(sum((v - mean) ** 2 for v in values) / len(values)), 2)


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
        'consistency_score':   _stdev(positions),  # lower = more consistent
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
    lap_counts:      dict[str, int]   = {}
    track_time:      dict[str, float] = {}
    driver_positions: dict[str, list[int]] = {}

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
            laps = r.get('laps') or 0
            lap_counts[d]         = lap_counts.get(d, 0) + laps
            best_lap = r.get('best_lap')
            if best_lap and laps:
                track_time[d]     = track_time.get(d, 0.0) + best_lap * laps
            driver_positions.setdefault(d, []).append(r['position'])

    standing_pos = {s['driver']: s['position'] for s in standings}

    def _top(counts: dict) -> tuple:
        if not counts:
            return None, 0
        best_val = max(counts.values())
        candidates = [d for d, v in counts.items() if v == best_val]
        # tiebreak by current championship ranking (lower pos = better)
        d = min(candidates, key=lambda x: standing_pos.get(x, 9999))
        return d, counts[d]

    wins_driver,     wins_n     = _top(win_counts)
    podiums_driver,  podiums_n  = _top(podium_counts)
    fl_driver,       fl_n       = _top(fl_counts)
    pen_driver,      pen_total  = _top(penalty_totals)

    # Most Consistent: lowest position stdev, min 3 races, tiebreak by ranking
    eligible = {d: _stdev(pos) for d, pos in driver_positions.items() if len(pos) >= 3}
    if eligible:
        best_stdev = min(eligible.values())
        consistent_candidates = [d for d, s in eligible.items() if s == best_stdev]
        consistent_driver = min(consistent_candidates, key=lambda x: standing_pos.get(x, 9999))
        consistent_score  = best_stdev
    else:
        consistent_driver, consistent_score = None, None

    # Track Veteran: most laps, tiebreak by current ranking position
    if lap_counts:
        max_laps = max(lap_counts.values())
        veteran_candidates = [d for d, l in lap_counts.items() if l == max_laps]
        veteran_driver = min(veteran_candidates, key=lambda d: standing_pos.get(d, 9999))
        veteran_laps   = max_laps
        veteran_time   = round(track_time.get(veteran_driver, 0.0), 1)
    else:
        veteran_driver, veteran_laps, veteran_time = None, 0, 0.0

    # Top Gainer / Top Loser: compare first-race position to current position
    # Build per-race cumulative standings snapshots
    driver_race_pts: dict[str, list[int]] = {}
    for driver_row in standings:
        d = driver_row['driver']
        cumulative = 0
        pts_list = []
        for race in races:
            cumulative += driver_row.get(race, 0) if isinstance(driver_row, dict) else 0
            pts_list.append(cumulative)
        driver_race_pts[d] = pts_list

    # Rank drivers after each race
    snapshots: list[dict[str, int]] = []
    for race_idx in range(len(races)):
        snapshot_pts = {d: pts[race_idx] for d, pts in driver_race_pts.items()}
        sorted_drivers = sorted(snapshot_pts.keys(), key=lambda d: -snapshot_pts[d])
        rank_map = {}
        for rank, drv in enumerate(sorted_drivers, 1):
            if snapshot_pts[drv] > 0 or race_idx == 0:
                rank_map[drv] = rank
        snapshots.append(rank_map)

    # For each driver who appears in standings, track best and worst rank across all snapshots
    gainer_driver, gainer_delta, gainer_worst, gainer_current = None, 0, None, None
    loser_driver,  loser_delta,  loser_best,   loser_current  = None, 0, None, None

    for driver_row in standings:
        d = driver_row['driver']
        driver_ranks = [s[d] for s in snapshots if d in s]
        if len(driver_ranks) < 2:
            continue
        best_rank  = min(driver_ranks)
        worst_rank = max(driver_ranks)
        current    = standing_pos.get(d, worst_rank)
        gain = worst_rank - current
        loss = best_rank - current  # negative means dropped from best

        if gain > gainer_delta:
            gainer_delta   = gain
            gainer_driver  = d
            gainer_worst   = worst_rank
            gainer_current = current
        if loss < loser_delta:
            loser_delta   = loss
            loser_driver  = d
            loser_best    = best_rank
            loser_current = current

    leader = standings[0] if standings else None
    leader_pts = int(leader.get('top8_points', leader['total_points'])) if leader else 0

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
                'gap_to_leader': leader_pts - int(s.get('top8_points', s['total_points'])),
            }
            for s in standings
        ],
        'records': {
            'most_wins':         {'driver': wins_driver,    'wins':            wins_n},
            'most_podiums':      {'driver': podiums_driver, 'podiums':         podiums_n},
            'most_fastest_laps': {'driver': fl_driver,      'count':           fl_n},
            'most_penalties':    {'driver': pen_driver,     'penalty_seconds': round(pen_total, 2)},
            'most_consistent':   {'driver': consistent_driver, 'stdev': consistent_score},
            'track_veteran':     {'driver': veteran_driver, 'laps': veteran_laps, 'track_time_s': veteran_time},
            'top_gainer':        {'driver': gainer_driver,  'positions_gained': gainer_delta,
                                   'worst_rank': gainer_worst, 'current_rank': gainer_current},
            'top_loser':         {'driver': loser_driver,   'positions_lost': abs(loser_delta),
                                   'best_rank': loser_best,   'current_rank': loser_current},
        },
    }
