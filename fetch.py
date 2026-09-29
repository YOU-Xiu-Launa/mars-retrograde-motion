# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
Fetch daily geocentric positions of Mars from NASA/JPL Horizons.

    uv run fetch.py

The raw Horizons response is saved to data/horizons_results.txt.
If the file already exists, it is kept to avoid unnecessary requests.
"""

from pathlib import Path

import requests


# ----------------------------
# Data source and settings
# ----------------------------

URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

PARAMS = {
    "format": "text",
    "COMMAND": "'499'",
    "OBJ_DATA": "'YES'",
    "MAKE_EPHEM": "'YES'",
    "EPHEM_TYPE": "'OBSERVER'",
    "CENTER": "'500@399'",
    "START_TIME": "'2024-09-01'",
    "STOP_TIME": "'2025-03-01'",
    "STEP_SIZE": "'1 d'",
    "QUANTITIES": "'1'",
    "CSV_FORMAT": "'YES'",
    "TIME_TYPE": "'UT'",
    "TIME_DIGITS": "'MINUTES'",
    "ANG_FORMAT": "'HMS'",
    "APPARENT": "'AIRLESS'",
}

HERE = Path(__file__).parent
DATA = HERE / "data"
FILE = "horizons_results.txt"
OUTPUT = DATA / FILE


# ----------------------------
# Fetch the data
# ----------------------------

def fetch(url, params, path):
    """Fetch the Horizons response once and save the raw text."""

    if path.exists():
        print(
            f"{path.relative_to(HERE)} already exists "
            f"({path.stat().st_size // 1024} KB)."
        )
        print("Delete the file if you want to fetch it again.")
        return path

    print("Requesting Mars ephemeris data from NASA/JPL Horizons...")

    response = requests.get(
        url,
        params=params,
        timeout=60,
        headers={"User-Agent": "Mars-Retrograde-Motion-Student-Project"},
    )
    response.raise_for_status()

    content = response.text

    if "$$SOE" not in content or "$$EOE" not in content:
        raise ValueError(
            "The Horizons response does not contain the expected "
            "observation table. The data file was not saved."
        )

    DATA.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    print(f"Saved {path.relative_to(HERE)}")
    print(f"File size: {path.stat().st_size // 1024} KB")

    return path


if __name__ == "__main__":
    fetch(URL, PARAMS, OUTPUT)
