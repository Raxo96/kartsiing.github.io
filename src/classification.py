"""Race result assembly and master classification management."""
import pandas as pd
from pathlib import Path
from src.points import calculate_race_points

# Chronological order for Polish month filenames (no diacritics, lower-case)
MONTH_ORDER: dict[str, int] = {
    'styczen':    1,
    'luty':       2,
    'marzec':     3,
    'kwiecien':   4,
    'maj':        5,
    'czerwiec':   6,
    'lipiec':     7,
    'sierpien':   8,
    'wrzesien':   9,
    'pazdziernik': 10,
    'listopad':   11,
    'grudzien':   12,
}

_DIACRITICS = str.maketrans('ąęóśźżćńł', 'aeoszzncl')


def race_sort_key(csv_path: Path) -> int:
    """Return chronological index for a race CSV path; unknown names sort last."""
    stem = csv_path.stem.lower().translate(_DIACRITICS)
    return MONTH_ORDER.get(stem, 99)


def assign_positions(raw_drivers: list[dict]) -> list[dict]:
    """
    Sort into overall finishing positions: Final A before B before C (etc.),
    then within each group by laps descending, adjusted gap ascending.
    Returns new list with 'position' key added.
    """
    finals_present = sorted({d['final'] for d in raw_drivers})
    final_order = [f for f in ['A', 'B', 'C', 'D'] if f in finals_present]
    for f in finals_present:
        if f not in final_order:
            final_order.append(f)

    ordered: list[dict] = []
    for f in final_order:
        group = [d for d in raw_drivers if d['final'] == f]
        if any(d.get('final_pos') is not None for d in group):
            group = sorted(group, key=lambda d: d['final_pos'] if d['final_pos'] is not None else 9999)
        else:
            group = sorted(group, key=lambda d: (-d['laps'], d['gap'] + d['penalty']))
        ordered.extend(group)

    return [{**d, 'position': idx} for idx, d in enumerate(ordered, start=1)]


def build_race_results(
    raw_drivers: list[dict],
    override_fastest_lap_driver: str | None = None,
) -> list[dict]:
    """Full pipeline: assign positions then calculate championship points."""
    return calculate_race_points(assign_positions(raw_drivers), override_fastest_lap_driver)


def load_classification(csv_path: str) -> pd.DataFrame:
    """Load existing classification CSV with normalized (English) column names."""
    if not Path(csv_path).exists():
        return pd.DataFrame(columns=['driver', 'total_points'])
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df = df.rename(columns={'Zawodnik': 'driver', 'Suma_Punktów': 'total_points', 'Pozycja': 'position'})
    return df.drop(columns=['position'], errors='ignore')


def update_classification(df: pd.DataFrame, race_results: list[dict], race_name: str) -> pd.DataFrame:
    """Merge race results into the classification DataFrame. Returns updated DataFrame."""
    df = df.drop(columns=['position'], errors='ignore')

    if race_name not in df.columns:
        df[race_name] = 0

    for result in race_results:
        driver, points = result['driver'], result['points']
        if driver in df['driver'].values:
            df.loc[df['driver'] == driver, race_name] = points
        else:
            new_row: dict = {'driver': driver, race_name: points}
            for col in df.columns:
                if col not in new_row:
                    new_row[col] = 0
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    race_columns = [c for c in df.columns if c not in ('driver', 'total_points', 'position')]
    df['total_points'] = df[race_columns].sum(axis=1)
    df = df.sort_values('total_points', ascending=False).reset_index(drop=True)
    df.insert(0, 'position', range(1, len(df) + 1))
    return df


def save_classification(df: pd.DataFrame, csv_path: str) -> None:
    """Write classification back to CSV using original Polish column names."""
    out = df.rename(columns={'driver': 'Zawodnik', 'total_points': 'Suma_Punktów', 'position': 'Pozycja'})
    out.to_csv(csv_path, index=False, encoding='utf-8-sig')
