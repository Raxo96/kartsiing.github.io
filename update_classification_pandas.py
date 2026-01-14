#!/usr/bin/env python3
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime

def calculate_points(position, fastest_lap_time, all_times, driver_name, all_drivers_with_times):
    """Oblicza punkty za pozycję i najszybsze okrążenie"""
    # Punkty za pozycję (tylko top 10)
    points_table = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
    position_points = points_table.get(position, 0) if position <= 10 else 0
    
    # Bonus za najszybsze okrążenie (każdy zawodnik może go dostać)
    fastest_bonus = 0
    if fastest_lap_time and len(all_drivers_with_times) > 0:
        try:
            # Znajdź najszybszy czas spośród WSZYSTKICH zawodników (nie tylko top 10)
            valid_times = []
            for driver_data in all_drivers_with_times:
                time_val = driver_data['time']
                if pd.notna(time_val) and str(time_val).replace('.', '').replace(',', '').isdigit():
                    valid_times.append(float(str(time_val).replace(',', '.')))
            
            if valid_times:
                fastest_time = float(str(fastest_lap_time).replace(',', '.'))
                if fastest_time == min(valid_times):
                    fastest_bonus = 1
        except (ValueError, TypeError):
            pass
    
    return position_points + fastest_bonus

def read_race_results(csv_file):
    """Czyta wyniki wyścigu z pliku CSV i oblicza pozycje biorąc pod uwagę kary.
    Obsługuje dodatkową kolumnę 'Finał' (A/B) i opcjonalnie 'FinalPos' (pozycja wewnątrz finału).
    Zawodnicy z Finału A zawsze będą przed Finałem B (nie porównujemy czasów między finałami).
    """
    try:
        # Czytaj CSV z różnymi separatorami i kodowaniami
        df = pd.read_csv(csv_file, encoding='utf-8-sig')

        # Usuń puste wiersze
        df = df.dropna(how='all')

        # Znajdź kolumny (mogą mieć różne nazwy)
        position_col = None
        driver_col = None
        fastest_lap_col = None
        laps_col = None
        diff_col = None
        penalty_col = None
        final_col = None
        finalpos_col = None

        for col in df.columns:
            col_lower = str(col).lower().strip()
            if any(x in col_lower for x in ['rnk', 'pozycja', 'pos']) and position_col is None:
                position_col = col
            elif any(x in col_lower for x in ['kierowca', 'zawodnik', 'driver']) and driver_col is None:
                driver_col = col
            elif any(x in col_lower for x in ['najlepsze', 'fastest', 'best', 'okrążenie', 'najlepsze okrążenie']) and fastest_lap_col is None:
                fastest_lap_col = col
            elif any(x in col_lower for x in ['okr', 'okrążenia', 'okrążenie', 'laps', 'lap']) and laps_col is None:
                laps_col = col
            elif any(x in col_lower for x in ['różnic', 'roznica', 'diff', 'difference']) and diff_col is None:
                diff_col = col
            elif any(x in col_lower for x in ['kara', 'penalty', 'pen']) and penalty_col is None:
                penalty_col = col
            elif any(x in col_lower for x in ['fina', 'final', 'stage']) and final_col is None:
                final_col = col
            elif any(x in col_lower for x in ['finalpos', 'final_pos', 'final position', 'finalposition', 'finalpos']) and finalpos_col is None:
                finalpos_col = col

        if not driver_col:
            print(f"Nie można znaleźć kolumny z nazwiskami kierowców w pliku {csv_file}")
            print(f"Dostępne kolumny: {list(df.columns)}")
            return []

        # Zbierz surowe dane o wszystkich zawodnikach
        raw_drivers = []
        for _, row in df.iterrows():
            try:
                driver = row[driver_col]
                if pd.isna(driver):
                    continue
                driver = str(driver).strip()

                # Finał (A/B) - normalizuj
                final = None
                if final_col and pd.notna(row[final_col]):
                    final = str(row[final_col]).strip().upper()
                else:
                    final = 'A'  # domyślnie A jeśli brak kolumny

                # Pozycja wewnątrz finału
                finalpos = None
                if finalpos_col and pd.notna(row[finalpos_col]):
                    try:
                        finalpos = int(row[finalpos_col])
                    except (ValueError, TypeError):
                        finalpos = None

                # Okrążenia
                laps = None
                if laps_col and pd.notna(row[laps_col]):
                    try:
                        laps = int(row[laps_col])
                    except (ValueError, TypeError):
                        laps = None

                # Różnica (czas) - może być w formacie z przecinkiem; traktujemy jako różnica do lidera
                diff = None
                if diff_col and pd.notna(row[diff_col]):
                    try:
                        diff = float(str(row[diff_col]).replace(',', '.'))
                    except (ValueError, TypeError):
                        diff = None

                # Kara (sekundy)
                penalty = 0
                if penalty_col and pd.notna(row[penalty_col]):
                    try:
                        penalty = float(str(row[penalty_col]).replace(',', '.'))
                    except (ValueError, TypeError):
                        penalty = 0

                # Najlepsze okrążenie (może być potrzebne dla bonusu)
                fastest_lap = row[fastest_lap_col] if fastest_lap_col else None

                raw_drivers.append({
                    'orig_position': int(row[position_col]) if position_col and pd.notna(row[position_col]) else None,
                    'driver': driver,
                    'final': final,
                    'finalpos': finalpos,
                    'laps': laps if laps is not None else 0,
                    'diff': diff if diff is not None else float('inf'),
                    'penalty': penalty,
                    'fastest_lap': fastest_lap
                })
            except Exception:
                continue

        if not raw_drivers:
            return []

        # Oblicz rzeczywisty czas/gap jako diff do lidera + penalty
        for d in raw_drivers:
            if d['diff'] == float('inf'):
                d['gap'] = float('inf')
            else:
                d['gap'] = d['diff'] + (d['penalty'] if d['penalty'] else 0)

        # Podziel na grupy finałów i posortuj wewnątrz każdej grupy
        # Ustal kolejność grup: A przed B jeśli istnieją
        finals_present = sorted({d['final'] for d in raw_drivers if d.get('final') is not None})
        final_order = []
        if 'A' in finals_present:
            final_order.append('A')
        if 'B' in finals_present:
            final_order.append('B')
        # Dodaj pozostałe jeśli są (np. C) w porządku rosnącym
        for f in finals_present:
            if f not in final_order:
                final_order.append(f)

        grouped_sorted = []
        for f in final_order:
            group = [d for d in raw_drivers if d.get('final') == f]
            # Jeśli finalpos dostępny dla przynajmniej jednego, sortuj po finalpos
            if any(d.get('finalpos') is not None for d in group):
                group_sorted = sorted(group, key=lambda x: (x['finalpos'] if x['finalpos'] is not None else float('inf')))
            else:
                # Sortuj standardowo wewnątrz finału: najpierw po okrążeniach malejąco, potem po gapie
                group_sorted = sorted(group, key=lambda x: (-x['laps'], x['gap']))
            grouped_sorted.extend(group_sorted)

        # Teraz grouped_sorted ma A przed B; przypisz globalne pozycje i oblicz punkty
        results = []
        for idx, d in enumerate(grouped_sorted, start=1):
            try:
                points = calculate_points(idx, d.get('fastest_lap'), None, d['driver'], [{'driver': rd['driver'], 'time': rd.get('fastest_lap')} for rd in raw_drivers])
            except Exception:
                points = 0

            results.append({
                'driver': d['driver'],
                'position': idx,
                'points': points,
                'fastest_lap': d.get('fastest_lap'),
                'penalty': d.get('penalty', 0)
            })

        return results

    except Exception as e:
        print(f"Błąd podczas czytania pliku {csv_file}: {e}")
        return []

def update_general_classification(race_results, race_name, classification_file='klasyfikacja_generalna.csv'):
    """Aktualizuje klasyfikację generalną"""
    
    # Sprawdź czy plik klasyfikacji istnieje
    if os.path.exists(classification_file):
        df_general = pd.read_csv(classification_file, encoding='utf-8-sig')
        # Usuń kolumnę Pozycja jeśli istnieje (będzie dodana na końcu)
        if 'Pozycja' in df_general.columns:
            df_general = df_general.drop('Pozycja', axis=1)
    else:
        # Stwórz nowy plik klasyfikacji
        df_general = pd.DataFrame(columns=['Zawodnik', 'Suma_Punktów'])
    
    # Dodaj kolumnę dla tego wyścigu jeśli nie istnieje
    if race_name not in df_general.columns:
        df_general[race_name] = 0
    
    # Znajdź zawodników z najszybszym okrążeniem i zbierz kary
    fastest_lap_drivers = []
    race_penalties = {}
    if race_results:
        # Znajdź najszybszy czas
        valid_times = []
        for result in race_results:
            if result.get('fastest_lap') and pd.notna(result['fastest_lap']):
                try:
                    time_val = float(str(result['fastest_lap']).replace(',', '.'))
                    valid_times.append(time_val)
                except (ValueError, TypeError):
                    pass
        
        if valid_times:
            fastest_time = min(valid_times)
            for result in race_results:
                if result.get('fastest_lap') and pd.notna(result['fastest_lap']):
                    try:
                        time_val = float(str(result['fastest_lap']).replace(',', '.'))
                        if time_val == fastest_time:
                            fastest_lap_drivers.append(result['driver'])
                    except (ValueError, TypeError):
                        pass
        # Zbierz kary
        for result in race_results:
            p = result.get('penalty', 0) if result.get('penalty') is not None else 0
            if p and p > 0:
                race_penalties[result['driver']] = p

    # Aktualizuj punkty dla każdego zawodnika z wyścigu
    for result in race_results:
        driver = result['driver']
        points = result['points']
        
        # Znajdź zawodnika lub dodaj nowego
        if driver in df_general['Zawodnik'].values:
            # Aktualizuj istniejącego zawodnika
            idx = df_general[df_general['Zawodnik'] == driver].index[0]
            df_general.loc[idx, race_name] = points
        else:
            # Dodaj nowego zawodnika
            new_row = {'Zawodnik': driver, race_name: points}
            # Wypełnij pozostałe kolumny zerami
            for col in df_general.columns:
                if col not in new_row:
                    new_row[col] = 0
            df_general = pd.concat([df_general, pd.DataFrame([new_row])], ignore_index=True)
    
    # Przelicz sumę punktów
    race_columns = [col for col in df_general.columns if col not in ['Zawodnik', 'Suma_Punktów']]
    df_general['Suma_Punktów'] = df_general[race_columns].sum(axis=1)
    
    # Sortuj według sumy punktów (malejąco)
    df_general = df_general.sort_values('Suma_Punktów', ascending=False).reset_index(drop=True)
    
    # Dodaj pozycję na początku
    df_general.insert(0, 'Pozycja', range(1, len(df_general) + 1))
    
    # Zapisz zaktualizowaną klasyfikację
    df_general.to_csv(classification_file, index=False, encoding='utf-8-sig')
    
    return df_general, {race_name: fastest_lap_drivers}, {race_name: race_penalties}

def generate_readme_table(df_general, fastest_lap_data=None, penalty_data=None, output_file='README.md'):
    """Generuje README.md z tabelą wyników"""
    
    # Znajdź kolumny wyścigów
    race_columns = [col for col in df_general.columns if col not in ['Pozycja', 'Zawodnik', 'Suma_Punktów']]
    
    # Statystyki
    total_drivers = len(df_general)
    total_races = len(race_columns)
    leader = df_general.iloc[0]['Zawodnik'] if len(df_general) > 0 else "Brak"
    leader_points = df_general.iloc[0]['Suma_Punktów'] if len(df_general) > 0 else 0
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Nagłówek i informacje
    content = f"""# 🏁 Puchar Kartingu 2026

**Klasyfikacja Generalna - Sezon 2026**

## 📊 Statystyki Sezonu

- **Wyścigów:** {total_races}
- **Zawodników:** {total_drivers}
- **Punktów Lidera:** {leader_points}
- **Aktualny Lider:** 🏆 {leader}

## 🏆 System punktacji

**Pozycje:** 1° = 25pkt, 2° = 18pkt, 3° = 15pkt, 4° = 12pkt, 5° = 10pkt, 6° = 8pkt, 7° = 6pkt, 8° = 4pkt, 9° = 2pkt, 10° = 1pkt  
**Bonus:** +1 punkt za najszybsze okrążenie w wyścigu (każdy zawodnik może go zdobyć)

## 📋 Klasyfikacja Generalna

"""
    
    # Nagłówek tabeli
    header = "| Pozycja | Zawodnik |"
    separator = "| --- | --- |"
    
    for race in race_columns:
        header += f" {race} |"
        separator += " --- |"
    
    header += " Suma Punktów |"
    separator += " --- |"
    
    content += header + "\n" + separator + "\n"
    
    # Wiersze z danymi
    for _, row in df_general.iterrows():
        position = int(row['Pozycja'])
        driver = row['Zawodnik']
        total_points = int(row['Suma_Punktów'])
        
        # Emoji dla podium
        if position == 1:
            position_display = "🥇 1"
        elif position == 2:
            position_display = "🥈 2"
        elif position == 3:
            position_display = "🥉 3"
        else:
            position_display = str(position)
        
        row_data = f"| {position_display} | **{driver}** |"
        
        for race in race_columns:
            points = int(row[race]) if pd.notna(row[race]) and row[race] > 0 else 0
            display_points = points if points > 0 else "-"
            
            # Sprawdź czy zawodnik miał najszybsze okrążenie w tym wyścigu
            has_fastest_lap = (fastest_lap_data and 
                             race in fastest_lap_data and 
                             driver in fastest_lap_data[race] and 
                             points > 0)
            # Sprawdź czy zawodnik miał karę w tym wyścigu
            has_penalty = (penalty_data and race in penalty_data and driver in penalty_data[race] and penalty_data[race][driver] > 0)
            
            cell = str(display_points)
            if has_fastest_lap:
                # formatowanie LaTeX-like dla fastest lap
                cell = f"**$${{\\color{{purple}}{cell}}}$$**"
            elif has_penalty:
                # formatowanie LaTeX-like dla kary (czerwony)
                cell = f"**$${{\\color{{red}}{cell}}}$$**"
            
            row_data += f" {cell} |"
        
        row_data += f" **{total_points}** |"
        content += row_data + "\n"
    
    # Stopka
    content += f"\n---\n\n*Ostatnia aktualizacja: {current_time}*  \n*Wygenerowano automatycznie przez system Puchar Kartingu 2026*\n"
    
    # Zapisz do README.md
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"README.md zaktualizowany: {output_file}")

def generate_html_report(df_general, fastest_lap_data=None, penalty_data=None, output_file='index.html'):
    """Generuje ładny raport HTML z klasyfikacją"""
    
    # Znajdź kolumny wyścigów
    race_columns = [col for col in df_general.columns if col not in ['Pozycja', 'Zawodnik', 'Suma_Punktów']]
    
    # CSS style
    css_style = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 1.2em;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #e74c3c;
        }
        .stat-label {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }
        th, td {
            padding: 12px 8px;
            text-align: center;
            border: 1px solid #ddd;
        }
        th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
        }
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        tr:hover {
            background-color: #e8f4fd;
        }
        .position-1 { background-color: #ffd700 !important; font-weight: bold; }
        .position-2 { background-color: #c0c0c0 !important; font-weight: bold; }
        .position-3 { background-color: #cd7f32 !important; font-weight: bold; }
        .driver-name {
            text-align: left;
            font-weight: bold;
            color: #2c3e50;
        }
        .points-cell {
            font-weight: bold;
        }
        .zero-points {
            color: #bdc3c7;
        }
        .footer {
            margin-top: 30px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .points-legend {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .legend-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        .legend-content {
            font-size: 0.9em;
            color: #5d6d7e;
        }
        .fastest-lap {
            border: 3px solid #8e44ad !important;
        }
        .penalty {
            border: 3px solid #e74c3c !important;
        }
    </style>
    """
    
    # Statystyki
    total_drivers = len(df_general)
    total_races = len(race_columns)
    leader = df_general.iloc[0]['Zawodnik'] if len(df_general) > 0 else "Brak"
    leader_points = df_general.iloc[0]['Suma_Punktów'] if len(df_general) > 0 else 0
    
    # Generuj HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Puchar Kartingu 2026 - Klasyfikacja Generalna</title>
        {css_style}
    </head>
    <body>
        <div class="container">
            <h1>🏁 Puchar Kartingu 2026</h1>
            <div class="subtitle">Klasyfikacja Generalna - Sezon 2026</div>
            
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{total_races}</div>
                    <div class="stat-label">Wyścigów</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{total_drivers}</div>
                    <div class="stat-label">Zawodników</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{leader_points}</div>
                    <div class="stat-label">Punktów Lidera</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">🏆</div>
                    <div class="stat-label">{leader}</div>
                </div>
            </div>
            
            <div class="points-legend">
                <div class="legend-title">System punktacji:</div>
                <div class="legend-content">
                    <strong>Pozycje:</strong> 1° = 25pkt, 2° = 18pkt, 3° = 15pkt, 4° = 12pkt, 5° = 10pkt, 6° = 8pkt, 7° = 6pkt, 8° = 4pkt, 9° = 2pkt, 10° = 1pkt<br>
                    <strong>Bonus:</strong> +1 punkt za najszybsze okrążenie w wyścigu (każdy zawodnik może go zdobyć)
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Pozycja</th>
                        <th>Zawodnik</th>
    """
    
    # Dodaj nagłówki miesięcy
    for race in race_columns:
        html_content += f"<th>{race}</th>"
    
    html_content += """
                        <th>Suma Punktów</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Dodaj wiersze z danymi
    for _, row in df_general.iterrows():
        position = int(row['Pozycja'])
        driver = row['Zawodnik']
        total_points = int(row['Suma_Punktów'])
        
        # Klasa CSS dla podium
        row_class = ""
        if position == 1:
            row_class = "position-1"
        elif position == 2:
            row_class = "position-2"
        elif position == 3:
            row_class = "position-3"
        
        html_content += f"""
                    <tr class="{row_class}">
                        <td>{position}</td>
                        <td class="driver-name">{driver}</td>
        """
        
        # Dodaj punkty z każdego wyścigu
        for race in race_columns:
            points = int(row[race]) if pd.notna(row[race]) and row[race] > 0 else 0
            points_class = "zero-points" if points == 0 else "points-cell"
            display_points = points if points > 0 else "-"
            
            # Sprawdź czy zawodnik miał najszybsze okrążenie w tym wyścigu
            has_fastest_lap = (fastest_lap_data and 
                             race in fastest_lap_data and 
                             driver in fastest_lap_data[race] and 
                             points > 0)
            # Sprawdź czy zawodnik miał karę w tym wyścigu
            has_penalty = (penalty_data and race in penalty_data and driver in penalty_data[race] and penalty_data[race][driver] > 0)
            
            if has_fastest_lap:
                points_class += " fastest-lap"
            if has_penalty:
                points_class += " penalty"
            
            html_content += f'<td class="{points_class}">{display_points}</td>'
        
        html_content += f"""
                        <td class="points-cell">{total_points}</td>
                    </tr>
        """
    
    # Zakończ HTML
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    html_content += f"""
                </tbody>
            </table>
            
            <div class="footer">
                Ostatnia aktualizacja: {current_time}<br>
                Wygenerowano automatycznie przez system Puchar Kartingu 2026
            </div>
        </div>
    </body>
    </html>
    """
    
    # Zapisz plik HTML
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Raport HTML wygenerowany: {output_file}")

def main():
    if len(sys.argv) != 2:
        print("Użycie: python update_classification.py <plik_wyników.csv>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Plik {csv_file} nie istnieje!")
        sys.exit(1)
    
    # Nazwa wyścigu z nazwy pliku (bez rozszerzenia)
    race_name = Path(csv_file).stem.capitalize()
    
    print(f"Przetwarzanie wyników z pliku: {csv_file}")
    print(f"Nazwa wyścigu: {race_name}")
    
    # Czytaj wyniki wyścigu
    race_results = read_race_results(csv_file)
    
    if not race_results:
        print("Nie znaleziono prawidłowych wyników w pliku!")
        sys.exit(1)
    
    print(f"\nZnalezione wyniki ({len(race_results)} zawodników):")
    for result in race_results:
        points_table = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
        base_points = points_table.get(result['position'], 0) if result['position'] <= 10 else 0
        bonus = " (+1 za najszybsze okrążenie)" if result['points'] > base_points else ""
        print(f"  {result['position']}. {result['driver']} - {result['points']} pkt{bonus}")
    
    # Aktualizuj klasyfikację generalną
    df_updated, fastest_lap_data, penalty_data = update_general_classification(race_results, race_name)
    
    print(f"\nKlasyfikacja generalna zaktualizowana!")
    print(f"Zapisano do: klasyfikacja_generalna.csv")
    
    # Wygeneruj raport HTML
    generate_html_report(df_updated, fastest_lap_data, penalty_data)
    
    # Wygeneruj README.md z tabelą
    generate_readme_table(df_updated, fastest_lap_data, penalty_data)
    
    print(f"\nTop 10 klasyfikacji generalnej:")
    for i in range(min(10, len(df_updated))):
        row = df_updated.iloc[i]
        print(f"  {row['Pozycja']}. {row['Zawodnik']} - {row['Suma_Punktów']} pkt")

if __name__ == "__main__":
    main()
