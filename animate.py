# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pillow"]
# ///

from pathlib import Path
import random

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import Normalize

from plot import rows, ra_to_degrees, dec_to_degrees, parse_date


HERE = Path(__file__).parent
DATA = HERE / "data" / "horizons_results.txt"
OUT = HERE / "out"


def main():
    # Read the original JPL Horizons data.
    table = rows(DATA)

    if not table:
        raise ValueError("No observations were found in the data file.")

    dates = [parse_date(row[0]) for row in table]
    ra = [ra_to_degrees(row[1]) for row in table]
    dec = [dec_to_degrees(row[2]) for row in table]

    count = len(table)

    if count < 2:
        raise ValueError("At least two observations are needed.")

    # Z represents elapsed time, not physical distance.
    elapsed_days = [
        (date - dates[0]).total_seconds() / 86400
        for date in dates
    ]

    progress = [i / (count - 1) for i in range(count)]

    background = "#050812"
    foreground = "#dce8ff"
    muted = "#71809c"

    fig = plt.figure(figsize=(12, 9), facecolor=background)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(background)

    # Calculate the plotting limits.
    x_min, x_max = min(ra), max(ra)
    y_min, y_max = min(dec), max(dec)
    z_min, z_max = min(elapsed_days), max(elapsed_days)

    x_pad = max((x_max - x_min) * 0.16, 0.5)
    y_pad = max((y_max - y_min) * 0.20, 0.5)
    z_pad = max((z_max - z_min) * 0.04, 1)

    # Keep the same sky-chart orientation as the static image.
    ax.set_xlim(x_max + x_pad, x_min - x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.set_zlim(z_min - z_pad, z_max + z_pad)

    # Create a reproducible 3D star field.
    rng = random.Random(12)

    star_count = 450
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
        rng.choice([2, 3, 4, 5])
        for _ in range(star_count)
    ]

    ax.scatter(
        star_x,
        star_y,
        star_z,
        s=star_sizes,
        color="#9db7e8",
        alpha=0.30,
        linewidths=0,
        depthshade=False,
    )

    # Show the complete route faintly in the background.
    ax.plot(
        ra,
        dec,
        elapsed_days,
        color="#71809c",
        linewidth=1.0,
        alpha=0.22,
    )

    # The bright route grows as the animation progresses.
    path, = ax.plot(
        [ra[0]],
        [dec[0]],
        [elapsed_days[0]],
        color="#24cfff",
        linewidth=2.2,
        alpha=0.95,
    )

    # Observations revealed so far.
    trail = ax.scatter(
        [ra[0]],
        [dec[0]],
        [elapsed_days[0]],
        c=[0],
        cmap="turbo",
        norm=Normalize(0, 1),
        s=42,
        alpha=0.95,
        linewidths=0,
        depthshade=False,
    )

    # A soft glow around Mars.
    glow = ax.scatter(
        [ra[0]],
        [dec[0]],
        [elapsed_days[0]],
        s=500,
        color="#168cff",
        alpha=0.13,
        linewidths=0,
        depthshade=False,
    )

    # Mars at the current observation date.
    planet = ax.scatter(
        [ra[0]],
        [dec[0]],
        [elapsed_days[0]],
        s=105,
        color="#ffb36b",
        edgecolors="#fff0d8",
        linewidths=1.0,
        depthshade=False,
    )

    date_label = ax.text2D(
        0.04,
        0.94,
        "",
        transform=ax.transAxes,
        color=foreground,
        fontsize=13,
        ha="left",
        va="top",
    )

    ax.set_title(
        "MARS  /  APPARENT RETROGRADE MOTION",
        color=foreground,
        fontsize=17,
        pad=24,
    )

    ax.set_xlabel(
        "RIGHT ASCENSION / degrees",
        color=muted,
        labelpad=12,
    )
    ax.set_ylabel(
        "DECLINATION / degrees",
        color=muted,
        labelpad=12,
    )
    ax.set_zlabel(
        "ELAPSED TIME / days",
        color=muted,
        labelpad=12,
    )

    ax.tick_params(colors=muted, labelsize=8, pad=2)

    # Style the 3D panes and grid.
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((0.03, 0.05, 0.10, 1.0))
        axis.pane.set_edgecolor("#34415c")
        axis._axinfo["grid"]["color"] = (0.25, 0.32, 0.45, 0.25)
        axis._axinfo["grid"]["linewidth"] = 0.6

    # Set a clear viewing angle.
    ax.view_init(elev=25, azim=-58)
    ax.set_box_aspect((1.2, 1.0, 1.6))

    # Keep the plot large within the figure.
    fig.subplots_adjust(
        left=0.01,
        right=0.99,
        top=0.90,
        bottom=0.08,
    )
    ax.set_position([0.02, 0.08, 0.94, 0.82])

    fig.text(
        0.97,
        0.025,
        "DATA: NASA/JPL HORIZONS  ·  Z = ELAPSED TIME",
        color=muted,
        fontsize=8,
        ha="right",
    )

    def update(frame):
        end = frame + 1

        # Extend the 3D trajectory.
        path.set_data_3d(
            ra[:end],
            dec[:end],
            elapsed_days[:end],
        )

        # Update the coloured observation trail.
        trail._offsets3d = (
            ra[:end],
            dec[:end],
            elapsed_days[:end],
        )
        trail.set_array(progress[:end])

        # Update the current position.
        current_x = ra[frame]
        current_y = dec[frame]
        current_z = elapsed_days[frame]

        glow._offsets3d = (
            [current_x],
            [current_y],
            [current_z],
        )
        planet._offsets3d = (
            [current_x],
            [current_y],
            [current_z],
        )

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

    print(f"Creating 3D animation from {count} observations...")

    movie.save(
        output_path,
        writer=animation.PillowWriter(fps=20),
        dpi=100,
    )

    plt.close(fig)
    print(f"Saved {output_path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
