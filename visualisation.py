import numpy as np
import matplotlib.pyplot as plt

# Corrected runtime data
sizes = np.array([4, 16, 64, 128, 256])
V = sizes ** 2

# Times in seconds.
# EK at 256x256 is a lower bound because it was stopped after more than 6000s.
EK = np.array([0.001, 0.63, 20.22, 770.0, 8000.0])
BK = np.array([0.001, 0.19, 2.40, 160.0, 3203.0])

# Edmonds-Karp worst-case:
# O(VE^2), and for image grid graphs E = O(V), so O(V^3).
# We normalize the curve at the 16x16 EK measurement.
anchor = 1
EK_O_V3 = EK[anchor] * (V / V[anchor]) ** 3

fig, ax = plt.subplots(figsize=(8.2, 5.2))

ax.plot(V, EK, marker="o", linewidth=2.3, label="Edmonds-Karp empirical")
ax.plot(V, BK, marker="o", linewidth=2.3, label="Boykov-Kolmogorov empirical")

ax.plot(
    V,
    EK_O_V3,
    linestyle="--",
    linewidth=2.0,
    label=r"Edmonds-Karp worst-case reference $O(V^3)$",
)

# Mark EK 256x256 as a lower bound
ax.scatter([V[-1]], [EK[-1]], marker="^", s=95, zorder=5)
ax.annotate(
    "EK > 6000 s",
    xy=(V[-1], EK[-1]),
    xytext=(V[-1] * 0.32, EK[-1] * 1.8),
    arrowprops=dict(arrowstyle="->", lw=1),
    fontsize=10,
)

# Important note: no fake BK theoretical curve
note = (
    "BK worst-case depends on the min-cut capacity |C|,\n"
    "so it is not plotted as a pure function of V."
)

ax.text(
    0.03,
    0.05,
    note,
    transform=ax.transAxes,
    fontsize=9,
    bbox=dict(
        boxstyle="round,pad=0.35",
        facecolor="white",
        alpha=0.85,
        edgecolor="0.7",
    ),
)

ax.set_xscale("log")
ax.set_yscale("log")

ax.set_xlabel("Image size / number of pixels $V$")
ax.set_ylabel("Runtime (seconds, log scale)")
ax.set_title("Runtime comparison for image graph max-flow algorithms")

ax.set_xticks(V)
ax.set_xticklabels([f"{s}×{s}" for s in sizes], rotation=25)

ax.grid(True, which="both", linestyle=":", linewidth=0.7)
ax.legend(fontsize=9, loc="upper left")

fig.tight_layout()
fig.savefig("runtime_complexity_corrected.png", dpi=220)
plt.show()