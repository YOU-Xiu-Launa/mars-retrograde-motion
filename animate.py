
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pillow"]
# ///

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import Normalize

from plot import rows, ra_to_degrees, dec_to_degrees, parse_date


HERE = Path(__file__).parent
DATA = HERE / "data" / "horizons_results.txt"
OUT = HERE / "out"


def main():
    # Read the same original JPL Horizons data as plot.py
    table = rows(DATA)

    if not table:
        raise ValueError("No observations were found in the data file.")

    dates = [parse_date(row[0]) for row in table]
    ra = [ra_to_degrees(row[1]) for row in table]
    dec = [dec_to_degrees(row[2]) for row in table]

    count = len(table)
    progress = [i / (count - 1) for i in range(count)]

    background = "#050812"
    foreground = "#dce8ff"
    muted = "#71809c"

    fig, ax = plt.subplots(figsize=(10, 7), facecolor=background)
    ax.set_facecolor(background)

    x_min, x_max = min(ra), max(ra)
    y_min, y_max = min(dec), max(dec)

    x_pad = (x_max - x_min) * 0.12
    y_pad = (y_max - y_min) * 0.16

    # Keep the same sky-chart orientation as the static image
    ax.set_xlim(x_max + x_pad, x_min - x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    # Background stars
    import random
    rng = random.Random(12)

    star_x = [
        rng.uniform(x_min - x_pad, x_max + x_pad)
        for _ in range(220)
    ]
    star_y = [
        rng.uniform(y_min - y_pad, y_max + y_pad)
        for _ in range(220)
    ]
    star_sizes = [rng.choice([1, 2, 3]) for _ in range(220)]

    ax.scatter(
        star_x,
        star_y,
        s=star_sizes,
        color="#9db7e8",
        alpha=0.22,
        linewidths=0,
        zorder=1,
    )

    # The complete route stays faintly visible in the background
    ax.plot(
        ra,
        dec,
        color="#71809c",
        linewidth=0.8,
        alpha=0.20,
        zorder=2,
    )

    # The trail grows as the animation progresses
    path, = ax.plot(
        [ra[0]],
        [dec[0]],
        color="#24cfff",
        linewidth=1.4,
        alpha=0.8,
        zorder=3,
    )

    # Coloured particles show the observations revealed so far
    trail = ax.scatter(
        [ra[0]],
        [dec[0]],
        c=[0],
        cmap="turbo",
        norm=Normalize(0, 1),
        s=20,
        alpha=0.95,
        linewidths=0,
        zorder=4,
    )

    # Glow and marker for Mars' current observed position
    glow = ax.scatter(
        [ra[0]],
        [dec[0]],
        s=260,
        color="#168cff",
        alpha=0.12,
        linewidths=0,
        zorder=5,
    )

    planet = ax.scatter(
        [ra[0]],
        [dec[0]],
        s=65,
        color="#ffb36b",
        edgecolors="#fff0d8",
        linewidths=0.8,
        zorder=6,
    )

    date_label = ax.text(
        0.03,
        0.94,
        "",
        transform=ax.transAxes,
        color=foreground,
        fontsize=12,
        ha="left",
        va="top",
    )

    ax.set_title(
        "MARS  /  APPARENT RETROGRADE MOTION",
        color=foreground,
        fontsize=15,
        pad=20,
    )

    ax.set_xlabel(
        "RIGHT ASCENSION  /  degrees",
        color=muted,
        labelpad=10,
    )
    ax.set_ylabel(
        "DECLINATION  /  degrees",
        color=muted,
        labelpad=10,
    )

    ax.tick_params(colors=muted, labelsize=9, length=0)
    ax.grid(color="#71809c", alpha=0.15, linewidth=0.6)

    for spine in ax.spines.values():
        spine.set_color("#34415c")
        spine.set_linewidth(0.7)

    def update(frame):
        end = frame + 1

        path.set_data(ra[:end], dec[:end])

        trail.set_offsets(list(zip(ra[:end], dec[:end])))
        trail.set_array(progress[:end])

        current_x = ra[frame]
        current_y = dec[frame]

        glow.set_offsets([(current_x, current_y)])
        planet.set_offsets([(current_x, current_y)])

        date_label.set_text(
            "OBSERVATION DATE   "
            + dates[frame].strftime("%d %b %Y")
        )

        return path, trail, glow, planet, date_label

    movie = animation.FuncAnimation(
        fig,
        update,
        frames=count,
        interval=50,
        blit=False,
        repeat=True,
    )

    OUT.mkdir(exist_ok=True)
    output_path = OUT / "animation.gif"

    print(f"Creating animation from {count} observations...")

    movie.save(
        output_path,
        writer=animation.PillowWriter(fps=20),
        dpi=100,
    )

    plt.close(fig)
    print(f"Saved {output_path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
