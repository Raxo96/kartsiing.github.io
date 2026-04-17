"""Generate a line chart showing driver ranking changes across all races."""
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

csv_path = sys.argv[1] if len(sys.argv) > 1 else 'klasyfikacja_generalna.csv'
raw = pd.read_csv(csv_path, encoding='utf-8-sig')
df = raw.drop(columns=['Pozycja', 'Suma_Punktów']).set_index('Zawodnik')
races = list(df.columns)

cumsum = df.cumsum(axis=1)

# Only drivers with >0 cumulative points at end of season
active = cumsum[cumsum.iloc[:, -1] > 0]

ranks = pd.DataFrame(index=active.index, columns=races)
for col in races:
    mask = active[col] > 0
    ranks.loc[mask, col] = active.loc[mask, col].rank(ascending=False, method='min').astype(int)

# Limit to drivers with 2+ race appearances for readability
show = ranks[ranks.notna().sum(axis=1) >= 2]

x = range(len(races))
fig, ax = plt.subplots(figsize=(14, 9))
colors = plt.cm.tab20(np.linspace(0, 1, len(show)))

for i, (driver, row) in enumerate(show.iterrows()):
    vals = row.values.astype(float)
    mask = ~np.isnan(vals)
    if mask.sum() == 0:
        continue
    xs, ys = np.array(x)[mask], vals[mask]
    ax.plot(xs, ys, 'o-', label=f"{driver} ({int(active.loc[driver].iloc[-1])} pts)",
            color=colors[i], linewidth=2.5, markersize=9)
    ax.annotate(driver, (xs[-1], ys[-1]), textcoords="offset points", xytext=(8, 0),
                fontsize=8, color=colors[i], fontweight='bold', va='center')

# Annotate each point with cumulative score
for i, (driver, row) in enumerate(show.iterrows()):
    vals = row.values.astype(float)
    for j, col in enumerate(races):
        if not np.isnan(vals[j]):
            ax.annotate(f"{int(active.loc[driver, col])}", (j, vals[j]),
                        textcoords="offset points", xytext=(0, 12),
                        fontsize=7, color=colors[i], ha='center', alpha=0.7)

max_rank = int(np.nanmax(show.values.astype(float)))
ax.set_yticks(range(1, max_rank + 1))
ax.set_xticks(list(x))
ax.set_xticklabels([f"After {r}" for r in races], fontsize=12)
ax.invert_yaxis()
ax.set_ylabel('Championship position (1 = leader)', fontsize=12)
ax.set_xlabel('Standing after each race', fontsize=12)
ax.set_title(
    'Championship standings – driver position changes\n(ranked by cumulative points)',
    fontsize=14, fontweight='bold',
)
ax.legend(loc='center left', bbox_to_anchor=(1.15, 0.5), fontsize=9, title='Driver (total pts)')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('ranking_general.png', dpi=150, bbox_inches='tight')
print("Saved: ranking_general.png")
