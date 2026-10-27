"""The card image on the Examples page, in the style of the other case studies: navy and gold, 640 x 480 webp."""
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

GOLD, NAVY = "#B3A369", "#191345"
LABELS = {"1": "One", "2": "Two", "3-5": "Three to five", "6+": "Six or more"}
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": NAVY, "ytick.color": NAVY, "axes.edgecolor": NAVY})


def make(findings, path):
    """findings: numbers.json's findings. A bar per bucket of peers per funder; the one-peer bar is navy."""
    n = findings["peers_per_funder"]
    tot = sum(n.values())
    vals = [(LABELS[k], 100 * v / tot, NAVY if k == "1" else GOLD) for k, v in n.items()]
    fig, ax = plt.subplots(figsize=(4, 3))
    y = np.arange(len(vals))[::-1]
    for yi, (lab, v, col) in zip(y, vals):
        ax.barh(yi, v, color=col, height=0.7)
        ax.text(v + 2, yi, f"{v:.0f}%", va="center", fontsize=12, fontweight="bold")
    ax.set_yticks(y, [v[0] for v in vals], fontsize=11)
    ax.set_xlim(0, 85)
    ax.set_xticks([])
    for sp in ("bottom", "top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.suptitle("Funders by how many clinics\nlike yours they fund", x=0.03, ha="left", fontsize=12.5, fontweight="bold", y=0.97)
    fig.subplots_adjust(top=0.78, bottom=0.04, left=0.33, right=0.97)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    Image.open(buf).convert("RGB").save(path, "WEBP", quality=85, method=6)
