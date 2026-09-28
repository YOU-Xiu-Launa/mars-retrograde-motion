# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///

"""
Read Mars's apparent positions from the saved Horizons data,
plot its path across the sky, and save the picture to out/.

    uv run plot.py
"""

import re
from pathlib import Path

import matplotlib.pyplot as plt

FILE = "horizons_results.txt"
PICTURE = "plot.png"

HERE = Path(__file__).parent
DATA = HERE / "data" / FILE
OUT = HERE / "out"


def rows(path):
    """Read the observation rows between Horizons' data markers."""
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
    """Convert right ascension from hours, minutes, seconds to degrees."""
    h, m, s = map(float, ra.split())
    return (h + m / 60 + s / 3600) * 15


def dec_to_degrees(dec):
    """Convert declination from degrees, arcminutes, arcseconds to degrees."""
    match = re.fullmatch(
        r"([+-])(\d+)\s+(\d+)\s+([\d.]+)",
        dec
    )

    if not match:
        raise ValueError(f"Cannot read declination: {dec}")

    sign, d, m, s = match.groups()
    value = float(d) + float(m) / 60 + float(s) / 3600

    if sign == "-":
        value = -value

    return value


def main():
    table = rows(DATA)
    print(f"{DATA.name}: {len(table)} observations")
    print(f"First observation: {table[0]}")

    dates, ra_values, dec_values = [], [], []

    for date, ra, dec in table:
        dates.append(date)
        ra_values.append(ra_to_degrees(ra))
        dec_values.append(dec_to_degrees(dec))

    print(f"RA range: {min(ra_values):.2f}° to {max(ra_values):.2f}°")
    print(f"Dec range: {min(dec_values):.2f}° to {max(dec_values):.2f}°")

    fig, ax = plt.subplots(figsize=(9, 7))

    ax.plot(
        ra_values,
        dec_values,
        color="#d65f3e",
        linewidth=1.8,
        marker="o",
        markersize=2.5,
    )

    # In the usual sky-chart convention, right ascension increases to the left.
    ax.invert_xaxis()

    ax.set_xlabel("Right Ascension (degrees)")
    ax.set_ylabel("Declination (degrees)")
    ax.set_title("Mars Retrograde Motion\nSep 2024 – Mar 2025")
    ax.grid(alpha=0.25)

    fig.tight_layout()

    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / PICTURE, dpi=200)
    print(f"Saved out/{PICTURE}")

    plt.show()


if __name__ == "__main__":
    main()
