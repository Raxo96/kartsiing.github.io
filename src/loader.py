"""CSV race result parser. Handles A/B finals, flexible column names, Polish/English headers."""
import pandas as pd
from pathlib import Path


COLUMN_ALIASES: dict[str, list[str]] = {
    'position':  ['rnk', 'pozycja', 'pos'],
    'driver':    ['kierowca', 'zawodnik', 'driver'],
    'kart':      ['gokart', 'kart', 'car'],
    'best_lap':  ['najlepsze', 'fastest', 'best'],
    'laps':      ['okrążenia', 'laps', 'lap'],
    'gap':       ['różnic', 'roznica', 'diff', 'difference'],
    'penalty':   ['kara', 'penalty', 'pen'],
    # final_pos must be listed before 'final' so more-specific aliases win
    'final_pos': ['finalpos', 'final_pos'],
    'final':     ['finał', 'final', 'stage', 'fina'],
}

# Detection priority: specific fields first to avoid alias collisions
_PRIORITY = ['final_pos', 'position', 'driver', 'kart', 'best_lap', 'laps', 'gap', 'penalty', 'final']


def _detect_columns(df_columns: list[str]) -> dict[str, str | None]:
    detected: dict[str, str | None] = {key: None for key in COLUMN_ALIASES}
    claimed: set[str] = set()
    for field in _PRIORITY:
        for col in df_columns:
            if col in claimed:
                continue
            if any(alias in str(col).lower().strip() for alias in COLUMN_ALIASES[field]):
                detected[field] = col
                claimed.add(col)
                break
    return detected


def _parse_float(value) -> float | None:
    if pd.isna(value):
        return None
    try:
        cleaned = str(value).replace(',', '.').strip()
        return float(cleaned) if cleaned and cleaned != '-' else None
    except (ValueError, TypeError):
        return None


def parse_race_csv(csv_file: str | Path) -> list[dict]:
    """
    Parse a race result CSV. Returns a list of raw driver entry dicts with keys:
    driver, kart, final, final_pos, laps, gap, penalty, best_lap
    """
    df = pd.read_csv(csv_file, encoding='utf-8-sig').dropna(how='all')
    cols = _detect_columns(list(df.columns))

    if not cols['driver']:
        raise ValueError(
            f"No driver column found in {csv_file}. Available: {list(df.columns)}"
        )

    drivers = []
    for _, row in df.iterrows():
        raw_driver = row[cols['driver']]
        if pd.isna(raw_driver):
            continue
        driver = str(raw_driver).strip()
        if not driver:
            continue

        final = 'A'
        if cols['final'] and pd.notna(row[cols['final']]):
            final = str(row[cols['final']]).strip().upper()

        final_pos = None
        if cols['final_pos'] and pd.notna(row[cols['final_pos']]):
            try:
                final_pos = int(row[cols['final_pos']])
            except (ValueError, TypeError):
                pass

        laps = 0
        if cols['laps'] and pd.notna(row[cols['laps']]):
            try:
                laps = int(row[cols['laps']])
            except (ValueError, TypeError):
                pass

        gap = _parse_float(row[cols['gap']]) if cols['gap'] else None
        if gap is None:
            gap = float('inf')

        penalty = _parse_float(row[cols['penalty']]) if cols['penalty'] else 0.0
        if penalty is None:
            penalty = 0.0

        best_lap = _parse_float(row[cols['best_lap']]) if cols['best_lap'] else None

        kart = None
        if cols['kart'] and pd.notna(row[cols['kart']]):
            kart = str(row[cols['kart']]).strip()

        drivers.append({
            'driver':    driver,
            'kart':      kart,
            'final':     final,
            'final_pos': final_pos,
            'laps':      laps,
            'gap':       gap,
            'penalty':   penalty,
            'best_lap':  best_lap,
        })

    return drivers
