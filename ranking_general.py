import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys

csv_path = sys.argv[1] if len(sys.argv) > 1 else 'klasyfikacja_generalna.csv'
raw = pd.read_csv(csv_path, encoding='utf-8-sig')
df = raw.drop(columns=['Pozycja', 'Suma_Punktów']).set_index('Zawodnik')
months = list(df.columns)

# Suma kumulatywna
cumsum = df.cumsum(axis=1)

# Ranking generalny po każdym miesiącu (tylko zawodnicy z >0 pkt kumulatywnie)
# Uwzględniamy WSZYSTKICH którzy kiedykolwiek zdobyli punkty
active = cumsum[cumsum.iloc[:, -1] > 0]

ranks = pd.DataFrame(index=active.index, columns=months)
for col in months:
    mask = active[col] > 0
    ranks.loc[mask, col] = active.loc[mask, col].rank(ascending=False, method='min').astype(int)

# Filtruj do zawodników z >= 2 miesiącami aktywności dla czytelności
show = ranks[ranks.notna().sum(axis=1) >= 2]

x = range(len(months))
fig, ax = plt.subplots(figsize=(14, 9))

colors = plt.cm.tab20(np.linspace(0, 1, len(show)))
for i, (player, row) in enumerate(show.iterrows()):
    vals = row.values.astype(float)
    mask = ~np.isnan(vals)
    if mask.sum() == 0:
        continue
    xs = np.array(x)[mask]
    ys = vals[mask]
    ax.plot(xs, ys, 'o-', label=f"{player} ({int(active.loc[player].iloc[-1])} pkt)",
            color=colors[i], linewidth=2.5, markersize=9)
    ax.annotate(player, (xs[-1], ys[-1]), textcoords="offset points", xytext=(8, 0),
                fontsize=8, color=colors[i], fontweight='bold', va='center')

# Dodaj etykiety z kumulatywną sumą punktów przy każdym punkcie
for i, (player, row) in enumerate(show.iterrows()):
    vals = row.values.astype(float)
    for j, col in enumerate(months):
        if not np.isnan(vals[j]):
            ax.annotate(f"{int(active.loc[player, col])}", (j, vals[j]),
                        textcoords="offset points", xytext=(0, 12),
                        fontsize=7, color=colors[i], ha='center', alpha=0.7)

max_rank = int(np.nanmax(show.values.astype(float)))
ax.set_yticks(range(1, max_rank + 1))
ax.set_xticks(list(x))
ax.set_xticklabels([f"Po {m}" for m in months], fontsize=12)
ax.invert_yaxis()
ax.set_ylabel('Pozycja w klasyfikacji generalnej (1 = lider)', fontsize=12)
ax.set_xlabel('Klasyfikacja generalna po danym miesiącu', fontsize=12)
ax.set_title('Klasyfikacja generalna – zmiany pozycji zawodników\n(ranking na podstawie sumy kumulatywnej punktów)', fontsize=14, fontweight='bold')
ax.legend(loc='center left', bbox_to_anchor=(1.15, 0.5), fontsize=9, title='Zawodnik (suma pkt)')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('ranking_general.png', dpi=150, bbox_inches='tight')
print("Zapisano: ranking_general.png")
