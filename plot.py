
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///

import random
import re
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize


# ----------------------------
# File locations
# ----------------------------

FILE = "horizons_results.txt"
PICTURE = "plot.png"

HERE = Path(__file__).parent
DATA = HERE / "data" / FILE
OUT = HERE / "out"


# ----------------------------
# Read the original data
# ----------------------------

def rows(path):
    kept = []
    in_data = False

    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()

            if line == "$$SOE":
                in_data = True
                continue

            if line == "$$EOE":
                break

            if not in_data or not line:
                continue

            parts = line.split(",")

            if len(parts) < 5:
                continue

            date = parts[0].strip()
            ra = parts[3].strip()
            dec = parts[4].strip()

            if date and ra and dec:
                kept.append((date, ra, dec))

    return kept


def ra_to_degrees(ra):
    h, m, s = map(float, ra.split())
    return (h + m / 60 + s / 3600) * 15


def dec_to_degrees(dec):
    match = re.fullmatch(
        r"([+-])(\d+)\s+(\d+)\s+([\d.]+)", dec
    )

    if not match:
        raise ValueError(f"Cannot read declination: {dec}")

    sign, d, m, s = match.groups()
    value = float(d) + float(m) / 60 + float(s) / 3600

    if sign == "-":
        value = -value

    return value


def parse_date(date):
    return datetime.strptime(date[:11], "%Y-%b-%d")


# ----------------------------
# Draw the visualization
# ----------------------------

def main():
    table = rows(DATA)

    if not table:
        raise ValueError("No observations were found in the data file.")

    dates = [parse_date(row[0]) for row in table]
    ra_values = [ra_to_degrees(row[1]) for row in table]
    dec_values = [dec_to_degrees(row[2]) for row in table]

    count = len(table)
    progress = [i / (count - 1) for i in range(count)]

    print(f"{DATA.name}: {count} observations")
    print(f"First observation: {table[0][0]}")
    print(f"Last observation:  {table[-1][0]}")
    print(f"RA range: {min(ra_values):.2f}° to {max(ra_values):.2f}°")
    print(f"Dec range: {min(dec_values):.2f}° to {max(dec_values):.2f}°")

    # Deep-space colour palette
    background = "#050812"
    foreground = "#dce8ff"
    muted = "#71809c"

    fig, ax = plt.subplots(figsize=(12, 9), facecolor=background)
    ax.set_facecolor(background)

    # Set the viewing area with a little breathing room
    x_min, x_max = min(ra_values), max(ra_values)
    y_min, y_max = min(dec_values), max(dec_values)

    x_pad = (x_max - x_min) * 0.12
    y_pad = (y_max - y_min) * 0.16

    ax.set_xlim(x_max + x_pad, x_min - x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    # Background stars, placed reproducibly
    rng = random.Random(12)
    star_x = [rng.uniform(x_min - x_pad, x_max + x_pad) for _ in range(240)]
    star_y = [rng.uniform(y_min - y_pad, y_max + y_pad) for _ in range(240)]
    star_sizes = [rng.choice([1, 2, 3, 4]) for _ in range(240)]

    ax.scatter(
        star_x,
        star_y,
        s=star_sizes,
        color="#9db7e8",
        alpha=0.24,
        linewidths=0,
        zorder=1,
    )

    # A subtle line connects the real observations in time order
    ax.plot(
        ra_values,
        dec_values,
        color="#8ba4d8",
        linewidth=1.0,
        alpha=0.42,
        zorder=2,
    )

    # Soft glow behind the observed positions
    ax.scatter(
        ra_values,
        dec_values,
        s=100,
        color="#168cff",
        alpha=0.035,
        linewidths=0,
        zorder=3,
    )

    ax.scatter(
        ra_values,
        dec_values,
        s=42,
        color="#24cfff",
        alpha=0.07,
        linewidths=0,
        zorder=3,
    )

    # Main particles: colour represents time
    points = ax.scatter(
        ra_values,
        dec_values,
        c=progress,
        cmap="turbo",
        norm=Normalize(0, 1),
        s=[12 + 15 * p for p in progress],
        alpha=0.96,
        edgecolors="none",
        zorder=4,
    )

    # Highlight the first and last observed positions
    ax.scatter(
        ra_values[0],
        dec_values[0],
        s=105,
        facecolors="none",
        edgecolors="#f4f7ff",
        linewidths=1.3,
        zorder=5,
    )

    ax.scatter(
        ra_values[-1],
        dec_values[-1],
        s=145,
        facecolors="none",
        edgecolors="#ffb36b",
        linewidths=1.5,
        zorder=5,
    )

    ax.annotate(
        "START  ·  " + dates[0].strftime("%d %b %Y"),
        (ra_values[0], dec_values[0]),
        xytext=(10, 12),
        textcoords="offset points",
        color="#e8f0ff",
        fontsize=9,
        fontweight="medium",
    )

    ax.annotate(
        "END  ·  " + dates[-1].strftime("%d %b %Y"),
        (ra_values[-1], dec_values[-1]),
        xytext=(10, -20),
        textcoords="offset points",
        color="#ffbd83",
        fontsize=9,
        fontweight="medium",
    )

    # Title and explanatory text
    fig.text(
        0.08,
        0.92,
        "MARS",
        color="#f2f5ff",
        fontsize=27,
        fontweight="bold",
        ha="left",
    )

    fig.text(
        0.082,
        0.885,
        "THE APPARENT RETROGRADE MOTION",
        color="#91a8d2",
        fontsize=10,
        ha="left",
        tracking=2,
    )

    fig.text(
        0.92,
        0.92,
        f"{dates[0]:%b %Y} — {dates[-1]:%b %Y}",
        color="#dce8ff",
        fontsize=10,
        ha="right",
    )

    # Scientific coordinate axes
    ax.set_xlabel(
        "RIGHT ASCENSION  /  degrees",
        color=muted,
        labelpad=14,
        fontsize=9,
    )
    ax.set_ylabel(
        "DECLINATION  /  degrees",
        color=muted,
        labelpad=14,
        fontsize=9,
    )

    ax.tick_params(colors=muted, labelsize=9, length=0, pad=8)

    ax.grid(
        color="#71809c",
        alpha=0.16,
        linewidth=0.65,
    )

    for spine in ax.spines.values():
        spine.set_color("#34415c")
        spine.set_linewidth(0.7)

    # Colour key for the passage of time
    colorbar = fig.colorbar(
        points,
        ax=ax,
        orientation="horizontal",
        pad=0.13,
        fraction=0.045,
        aspect=35,
    )

    colorbar.set_ticks([0, 1])
    colorbar.set_ticklabels(
        [dates[0].strftime("%b %Y"), dates[-1].strftime("%b %Y")]
    )
    colorbar.ax.tick_params(colors=muted, labelsize=8, length=0)
    colorbar.outline.set_visible(False)
    colorbar.set_label(
        "TIME  →",
        color=muted,
        fontsize=8,
        labelpad=7,
    )

    # Small footer
    fig.text(
        0.08,
        0.035,
        "182 DAILY OBSERVATIONS  ·  GEOCENTRIC SKY POSITIONS",
        color="#53617c",
        fontsize=8,
    )

    fig.text(
        0.92,
        0.035,
        "DATA: NASA/JPL HORIZONS",
        color="#53617c",
        fontsize=8,
        ha="right",
    )

    fig.subplots_adjust(
        left=0.12,
        right=0.94,
        top=0.82,
        bottom=0.19,
    )

    OUT.mkdir(exist_ok=True)
    output_path = OUT / PICTURE

    fig.savefig(
        output_path,
        dpi=240,
        facecolor=fig.get_facecolor(),
    )

    print(f"Saved {output_path.relative_to(HERE)}")

    plt.show()


if __name__ == "__main__":
    main()
