"""Championship points: position table and fastest lap bonus."""

POINTS_TABLE: dict[int, int] = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6:  8, 7:  6, 8:  4, 9:  2, 10: 1,
}
FASTEST_LAP_BONUS = 1


def position_points(position: int) -> int:
    return POINTS_TABLE.get(position, 0)


def find_fastest_lap_driver(results: list[dict]) -> str | None:
    """Return the driver with the best (lowest) lap time across all finalists."""
    best_time: float | None = None
    best_driver: str | None = None
    for r in results:
        lap = r.get('best_lap')
        if lap is not None:
            if best_time is None or lap < best_time:
                best_time = lap
                best_driver = r['driver']
    return best_driver


def calculate_race_points(
    results: list[dict],
    override_fastest_lap_driver: str | None = None,
) -> list[dict]:
    """
    Add 'points' and 'has_fastest_lap' to each result entry (modifies in-place).
    Requires 'position' to already be set on each entry.
    override_fastest_lap_driver: use when lap times are absent from the CSV.
    """
    fastest_driver = override_fastest_lap_driver or find_fastest_lap_driver(results)
    for r in results:
        has_fl = fastest_driver is not None and r['driver'] == fastest_driver
        r['points'] = position_points(r['position']) + (FASTEST_LAP_BONUS if has_fl else 0)
        r['has_fastest_lap'] = has_fl
    return results
