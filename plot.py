
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

    return -value if sign == "-" else value


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
    ra = [ra_to_degrees(row[1]) for row in table]
    dec = [dec_to_degrees(row[2]) for row in table]

    count = len(table)
    start_date = dates[0]
    elapsed_days = [(d - start_date).days for d in dates]
    progress = [i / max(count - 1, 1) for i in range(count)]

    print(f"{DATA.name}: {count} observations")
    print(f"First observation: {table[0][0]}")
    print(f"Last observation:  {table[-1][0]}")

    # The third axis represents elapsed time, not physical distance.
    time_axis = elapsed_days

    background = "#050812"
    foreground = "#e5edff"
    muted = "#7d8eae"
    cyan = "#35d9ff"
    orange = "#ffad70"

    fig = plt.figure(figsize=(13, 10), facecolor=background)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(background)

    # Coordinate ranges
    x_min, x_max = min(ra), max(ra)
    y_min, y_max = min(dec), max(dec)
    z_min, z_max = min(time_axis), max(time_axis)

    x_pad = max((x_max - x_min) * 0.16, 0.2)
    y_pad = max((y_max - y_min) * 0.20, 0.2)
    z_pad = max((z_max - z_min) * 0.06, 2)

    # ----------------------------
    # Atmospheric particle field
    # ----------------------------

    rng = random.Random(12)
    star_count = 900

    star_x = [
        rng.uniform(x_min - x_pad, x_max + x_pad)
        for _ in range(star_count)
    ]
    star_y = [
        rng.uniform(y_min - y_pad, y_max + y_pad)
        for _ in range(star_count)
    ]
    star_z = [
        rng.uniform(z_min - z_pad, z_max + z_pad)
        for _ in range(star_count)
    ]

    star_sizes = [
        rng.choices([0.5, 1, 2, 3], weights=[5, 5, 2, 1])[0]
        for _ in range(star_count)
    ]

    ax.scatter(
        star_x, star_y, star_z,
        s=star_sizes,
        c="#91b7f5",
        alpha=0.22,
        linewidths=0,
        depthshade=False,
        zorder=1,
    )

    # A soft, wide glow along the observed path
    ax.plot(
        ra, dec, time_axis,
        color="#168cff",
        linewidth=8,
        alpha=0.045,
        zorder=2,
    )

    ax.plot(
        ra, dec, time_axis,
        color=cyan,
        linewidth=2.0,
        alpha=0.30,
        zorder=3,
    )

    # Main observations: colour encodes time
    points = ax.scatter(
        ra, dec, time_axis,
        c=progress,
        cmap="turbo",
        norm=Normalize(0, 1),
        s=[12 + 20 * p for p in progress],
        alpha=0.96,
        edgecolors="none",
        depthshade=False,
        zorder=4,
    )

    # Decorative particles around the real path.
    # These are generated for visual atmosphere, not observations.
    # ----------------------------
    # Generative particle field
    # Decorative particles only:
    # the real observations remain unchanged.
    # ----------------------------

    particle_count = 3200

    particle_x = []
    particle_y = []
    particle_z = []
    particle_size = []

    for _ in range(particle_count):
        i = rng.randrange(count)

        # Wider spread creates a visible cloud around the path
        spread = rng.uniform(0.08, 0.65)

        particle_x.append(
            ra[i] + rng.gauss(0, spread)
        )
        particle_y.append(
            dec[i] + rng.gauss(0, spread)
        )
        particle_z.append(
            time_axis[i] + rng.gauss(0, 12)
        )

        particle_size.append(
            rng.uniform(1.0, 9.0)
        )

    # A cool-coloured cloud surrounding the trajectory
    ax.scatter(
        particle_x,
        particle_y,
        particle_z,
        c=particle_z,
        cmap="winter",
        s=particle_size,
        alpha=0.32,
        linewidths=0,
        depthshade=False,
        zorder=2,
    )

    # A second, finer layer creates a dust-like atmosphere
    fine_count = 1800

    fine_x = []
    fine_y = []
    fine_z = []
    fine_size = []

    for _ in range(fine_count):
        i = rng.randrange(count)

        spread = rng.uniform(0.04, 0.42)

        fine_x.append(
            ra[i] + rng.gauss(0, spread)
        )
        fine_y.append(
            dec[i] + rng.gauss(0, spread)
        )
        fine_z.append(
            time_axis[i] + rng.gauss(0, 7)
        )
        fine_size.append(
            rng.uniform(0.5, 3.5)
        )

    ax.scatter(
        fine_x,
        fine_y,
        fine_z,
        c="#65cfff",
        s=fine_size,
        alpha=0.24,
        linewidths=0,
        depthshade=False,
        zorder=3,
    )

    # Start and end markers
    ax.scatter(
        [ra[0]], [dec[0]], [time_axis[0]],
        s=150,
        facecolors="none",
        edgecolors="#f0f5ff",
        linewidths=1.5,
        depthshade=False,
        zorder=6,
    )

    ax.scatter(
        [ra[-1]], [dec[-1]], [time_axis[-1]],
        s=190,
        facecolors="none",
        edgecolors=orange,
        linewidths=1.8,
        depthshade=False,
        zorder=6,
    )

    ax.text(
        ra[0], dec[0], time_axis[0],
        "  START",
        color=foreground,
        fontsize=9,
    )

    ax.text(
        ra[-1], dec[-1], time_axis[-1],
        "  END",
        color=orange,
        fontsize=9,
    )

    # ----------------------------
    # Titles and labels
    # ----------------------------

    fig.text(
        0.075, 0.94,
        "MARS",
        color=foreground,
        fontsize=28,
        fontweight="bold",
    )

    fig.text(
        0.078, 0.905,
        "A PASSAGE THROUGH TIME  /  APPARENT RETROGRADE MOTION",
        color="#91a8d2",
        fontsize=10,
    )

    fig.text(
        0.925, 0.94,
        f"{dates[0]:%b %Y} — {dates[-1]:%b %Y}",
        color=foreground,
        fontsize=10,
        ha="right",
    )

    ax.set_xlabel(
        "RIGHT ASCENSION  /  degrees",
        color=muted,
        labelpad=12,
    )
    ax.set_ylabel(
        "DECLINATION  /  degrees",
        color=muted,
        labelpad=12,
    )
    ax.set_zlabel(
        "ELAPSED TIME  /  days",
        color=muted,
        labelpad=10,
    )

    ax.set_xlim(x_max + x_pad, x_min - x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_zlim(z_min - z_pad, z_max + z_pad)

    ax.tick_params(
        colors=muted,
        labelsize=8,
        pad=2,
    )

    # Dark, translucent 3D panes and subtle grid
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((0.025, 0.045, 0.09, 0.85))
        axis.pane.set_edgecolor("#263653")
        axis._axinfo["grid"]["color"] = (0.35, 0.45, 0.65, 0.18)
        axis._axinfo["grid"]["linewidth"] = 0.6

    # A cinematic viewing angle
    ax.view_init(elev=25, azim=-58)
    ax.set_box_aspect((1.25, 1.0, 1.15))
        # Mouse-wheel zoom for the interactive Matplotlib window
    def zoom_3d(event):
        if event.inaxes != ax:
            return

        if event.button == "up":
            scale = 0.82
        elif event.button == "down":
            scale = 1.22
        else:
            return

        x_limits = ax.get_xlim3d()
        y_limits = ax.get_ylim3d()
        z_limits = ax.get_zlim3d()

        def zoom_limits(limits, factor):
            center = (limits[0] + limits[1]) / 2
            half_range = (limits[1] - limits[0]) / 2
            new_half_range = half_range * factor

            return (
                center - new_half_range,
                center + new_half_range,
            )

        ax.set_xlim3d(zoom_limits(x_limits, scale))
        ax.set_ylim3d(zoom_limits(y_limits, scale))
        ax.set_zlim3d(zoom_limits(z_limits, scale))

        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("scroll_event", zoom_3d)

    # Time colour key
    colorbar = fig.colorbar(
        points,
        ax=ax,
        orientation="horizontal",
        pad=0.08,
        fraction=0.035,
        aspect=40,
    )

    colorbar.set_ticks([0, 1])
    colorbar.set_ticklabels([
        dates[0].strftime("%b %Y"),
        dates[-1].strftime("%b %Y"),
    ])
    colorbar.ax.tick_params(
        colors=muted,
        labelsize=8,
        length=0,
    )
    colorbar.outline.set_visible(False)
    colorbar.set_label(
        "OBSERVATION TIME  →",
        color=muted,
        fontsize=8,
        labelpad=6,
    )

    fig.text(
        0.075, 0.035,
        "182 DAILY OBSERVATIONS  ·  GEOCENTRIC SKY POSITIONS",
        color="#64728e",
        fontsize=8,
    )

    fig.text(
        0.925, 0.035,
        "DATA: NASA/JPL HORIZONS  ·  Z = ELAPSED TIME",
        color="#64728e",
        fontsize=8,
        ha="right",
    )

    fig.subplots_adjust(
        left=0.01,
        right=0.99,
        top=0.88,
        bottom=0.14,
    )

    # Give the 3D plot more room in the figure
    ax.set_position([0.02, 0.13, 0.96, 0.74])

    OUT.mkdir(exist_ok=True)
    output_path = OUT / PICTURE

    fig.savefig(
        output_path,
        dpi=240,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
    )

    print(f"Saved {output_path.relative_to(HERE)}")

    plt.show()


if __name__ == "__main__":
    main()
