# /// script
# requires-python = ">=3.10"
# dependencies = ["plotly"]
# ///

import csv
import json
import re
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio


# --------------------------------------------------
# FILE LOCATIONS
# --------------------------------------------------

HERE = Path(__file__).parent
DATA = HERE / "data" / "horizons_results.txt"
OUT = HERE / "out"
OUTPUT = OUT / "interactive.html"


# --------------------------------------------------
# READ NASA/JPL HORIZONS DATA
# --------------------------------------------------

def read_observations(path):
    """Read the original Horizons data without changing the source file."""

    observations = []
    inside_data = False

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as handle:

        for line in handle:
            line = line.strip()

            if line == "$$SOE":
                inside_data = True
                continue

            if line == "$$EOE":
                break

            if not inside_data or not line:
                continue

            parts = next(csv.reader([line]))

            if len(parts) < 5:
                continue

            date_text = parts[0].strip()
            ra_text = parts[3].strip()
            dec_text = parts[4].strip()

            if not date_text or not ra_text or not dec_text:
                continue

            date = datetime.strptime(
                date_text[:11],
                "%Y-%b-%d"
            )

            ra = ra_to_degrees(ra_text)
            dec = dec_to_degrees(dec_text)

            observations.append({
                "date": date,
                "ra": ra,
                "dec": dec,
            })

    if not observations:
        raise ValueError(
            "No observations found. Check data/horizons_results.txt."
        )

    observations.sort(key=lambda item: item["date"])

    return observations


def ra_to_degrees(value):
    """Convert right ascension from hours to degrees."""

    hours, minutes, seconds = map(
        float,
        value.split()
    )

    return (
        hours
        + minutes / 60
        + seconds / 3600
    ) * 15


def dec_to_degrees(value):
    """Convert declination from sexagesimal notation to degrees."""

    match = re.fullmatch(
        r"\s*([+-])\s*(\d+)\s+(\d+)\s+([\d.]+)\s*",
        value
    )

    if not match:
        raise ValueError(
            f"Cannot read declination: {value}"
        )

    sign, degrees, minutes, seconds = match.groups()

    result = (
        float(degrees)
        + float(minutes) / 60
        + float(seconds) / 3600
    )

    return -result if sign == "-" else result


# --------------------------------------------------
# BUILD THE 3D FIGURE
# --------------------------------------------------

def build_figure(observations):

    dates = [
        item["date"].strftime("%Y-%m-%d")
        for item in observations
    ]

    ra = [item["ra"] for item in observations]
    dec = [item["dec"] for item in observations]

    first_date = observations[0]["date"]

    elapsed = [
        (item["date"] - first_date).days
        for item in observations
    ]

    progress = [
        i / max(len(observations) - 1, 1)
        for i in range(len(observations))
    ]

    # The initial view shows the complete trajectory.
    fig = go.Figure()

    # Trace 0: the trajectory line.
    fig.add_trace(
        go.Scatter3d(
            x=ra,
            y=dec,
            z=elapsed,
            mode="lines",
            name="Trajectory",
            line=dict(
                color="#55DDF5",
                width=5,
            ),
            connectgaps=False,
            hoverinfo="skip",
        )
    )

    # Trace 1: all daily observations.
    fig.add_trace(
        go.Scatter3d(
            x=ra,
            y=dec,
            z=elapsed,
            mode="markers",
            name="Daily observations",
            marker=dict(
                size=3.5,
                color=progress,
                colorscale="Turbo",
                cmin=0,
                cmax=1,
                opacity=0.95,
                colorbar=dict(
                    title=dict(
                        text="Elapsed<br>days",
                        font=dict(color="#AAB9D5"),
                    ),
                    tickfont=dict(color="#AAB9D5"),
                    thickness=12,
                    len=0.55,
                    bgcolor="rgba(8,17,34,0.65)",
                    outlinewidth=0,
                ),
            ),
            customdata=[
                [date, day]
                for date, day in zip(dates, elapsed)
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Right ascension: %{x:.3f}°<br>"
                "Declination: %{y:.3f}°<br>"
                "Elapsed days: %{z}<br>"
                "<extra></extra>"
            ),
        )
    )

    # Trace 2: the currently selected observation.
    fig.add_trace(
        go.Scatter3d(
            x=[ra[0]],
            y=[dec[0]],
            z=[elapsed[0]],
            mode="markers",
            name="Selected observation",
            marker=dict(
                size=9,
                color="#FFFFFF",
                line=dict(
                    color="#55DDF5",
                    width=3,
                ),
            ),
            text=[dates[0]],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Right ascension: %{x:.3f}°<br>"
                "Declination: %{y:.3f}°<br>"
                "Elapsed days: %{z}<br>"
                "<extra></extra>"
            ),
        )
    )

    # Start and end markers.
    fig.add_trace(
        go.Scatter3d(
            x=[ra[0], ra[-1]],
            y=[dec[0], dec[-1]],
            z=[elapsed[0], elapsed[-1]],
            mode="markers+text",
            name="Start / End",
            text=["START", "END"],
            textposition="top center",
            textfont=dict(
                color="#C5D5F0",
                size=10,
            ),
            marker=dict(
                size=[5, 6],
                color=["#FFFFFF", "#FFB77A"],
                symbol="circle",
            ),
            hovertemplate=(
                "%{text}<br>"
                "%{x:.3f}°, %{y:.3f}°<br>"
                "Elapsed days: %{z}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#081426",
        plot_bgcolor="#081426",
        margin=dict(
            l=0,
            r=0,
            t=10,
            b=0,
        ),
        showlegend=False,
        scene=dict(
            bgcolor="#081426",
            xaxis=dict(
                title="RIGHT ASCENSION · degrees",
                autorange="reversed",
                color="#91A8D2",
                gridcolor="rgba(115,150,195,0.15)",
                zerolinecolor="rgba(115,150,195,0.18)",
                showbackground=True,
                backgroundcolor="#0B192D",
            ),
            yaxis=dict(
                title="DECLINATION · degrees",
                color="#91A8D2",
                gridcolor="rgba(115,150,195,0.15)",
                zerolinecolor="rgba(115,150,195,0.18)",
                showbackground=True,
                backgroundcolor="#0B192D",
            ),
            zaxis=dict(
                title="ELAPSED TIME · days",
                color="#91A8D2",
                gridcolor="rgba(115,150,195,0.15)",
                zerolinecolor="rgba(115,150,195,0.18)",
                showbackground=True,
                backgroundcolor="#0B192D",
            ),
            camera=dict(
                eye=dict(
                    x=1.65,
                    y=1.65,
                    z=1.25,
                )
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=1.2,
                y=1.0,
                z=1.15,
            ),
        ),
        font=dict(
            family="Arial, sans-serif",
            color="#E8F0FF",
        ),
    )

    return fig, dates, ra, dec, elapsed


# --------------------------------------------------
# BUILD THE WEB PAGE
# --------------------------------------------------

def build_page(fig, dates, ra, dec, elapsed):

    plot_html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=True,
        div_id="mars-plot",
        config={
            "responsive": True,
            "displaylogo": False,
            "scrollZoom": True,
            "modeBarButtonsToRemove": [
                "lasso3d",
                "select3d",
            ],
        },
    )

    browser_data = json.dumps({
        "dates": dates,
        "ra": ra,
        "dec": dec,
        "elapsed": elapsed,
    })

    page = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Mars in Retrograde | Data Explorer</title>

<style>
:root {
    --bg: #081426;
    --panel: #101F35;
    --panel-light: #142640;
    --line: #263A56;
    --text: #F0F5FF;
    --muted: #91A8D2;
    --cyan: #75D8F5;
    --orange: #FFB77A;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background:
        radial-gradient(
            ellipse at 50% -20%,
            #183455 0%,
            var(--bg) 55%
        );
    color: var(--text);
    font-family: Arial, Helvetica, sans-serif;
    min-height: 100vh;
}

.page {
    max-width: 1500px;
    margin: 0 auto;
    padding: 34px 36px 24px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 24px;
    margin-bottom: 26px;
}

.eyebrow {
    color: var(--cyan);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2.4px;
    margin-bottom: 12px;
}

h1 {
    margin: 0;
    font-size: clamp(28px, 4vw, 48px);
    letter-spacing: 1.5px;
    line-height: 1.08;
}

.subtitle {
    margin-top: 12px;
    color: var(--muted);
    font-size: 14px;
    letter-spacing: 0.3px;
}

.data-badge {
    border: 1px solid #29435F;
    border-radius: 999px;
    padding: 10px 15px;
    color: var(--cyan);
    font-size: 11px;
    letter-spacing: 1px;
    white-space: nowrap;
    background: rgba(16,31,53,0.7);
}

.card {
    background: rgba(16,31,53,0.92);
    border: 1px solid rgba(91,125,166,0.18);
    border-radius: 18px;
    box-shadow: 0 14px 40px rgba(0,0,0,0.12);
}

.timeline-card {
    padding: 23px 26px 20px;
    margin-bottom: 18px;
}

.section-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 10px;
}

.section-label {
    color: var(--muted);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.8px;
}

.current-date {
    color: var(--cyan);
    font-size: 22px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
}

#timeline {
    width: 100%;
    margin: 14px 0 7px;
    accent-color: var(--cyan);
    cursor: pointer;
    height: 7px;
}

.timeline-ends {
    display: flex;
    justify-content: space-between;
    color: #7086A9;
    font-size: 11px;
    font-variant-numeric: tabular-nums;
}

.controls-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.5fr) minmax(260px, 0.8fr);
    gap: 18px;
    margin-bottom: 18px;
}

.range-card {
    padding: 23px 26px;
}

.range-card h2 {
    font-size: 13px;
    margin: 0 0 7px;
    letter-spacing: 1.3px;
}

.description {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.6;
    margin: 0 0 21px;
}

.date-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.date-field label {
    display: block;
    color: var(--muted);
    font-size: 10px;
    letter-spacing: 1.4px;
    margin-bottom: 9px;
}

.date-field input {
    display: block;
    width: 100%;
    min-width: 0;
    padding: 13px 12px;
    color: var(--text);
    background: #0A1729;
    border: 1px solid #2A405E;
    border-radius: 9px;
    font-family: inherit;
    font-size: 14px;
    color-scheme: dark;
    outline: none;
}

.date-field input:focus {
    border-color: var(--cyan);
    box-shadow: 0 0 0 2px rgba(117,216,245,0.12);
}

.range-hint {
    color: #7187A8;
    font-size: 11px;
    line-height: 1.6;
    margin-top: 14px;
}

.play-card {
    padding: 23px 26px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.play-card h2 {
    font-size: 13px;
    margin: 0 0 7px;
    letter-spacing: 1.3px;
}

.button-row {
    display: flex;
    gap: 10px;
    margin-top: 12px;
}

button {
    border: 0;
    border-radius: 10px;
    padding: 13px 18px;
    font-family: inherit;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.15s, background 0.15s;
}

button:hover {
    transform: translateY(-1px);
}

.primary {
    color: #071426;
    background: var(--cyan);
    flex: 1;
}

.secondary {
    color: var(--text);
    background: #20344F;
    border: 1px solid #344B69;
    flex: 1;
}

.plot-card {
    overflow: hidden;
    padding: 10px 10px 0;
    min-height: 560px;
}

.plot-heading {
    padding: 14px 18px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
}

.plot-heading strong {
    font-size: 11px;
    letter-spacing: 1.5px;
}

.plot-heading span {
    color: var(--muted);
    font-size: 11px;
}

#mars-plot {
    width: 100%;
    height: min(68vw, 760px);
    min-height: 500px;
}

footer {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    padding: 20px 4px 0;
    color: #657A9B;
    font-size: 10px;
    letter-spacing: 0.8px;
    line-height: 1.6;
}

@media (max-width: 800px) {
    .page {
        padding: 22px 15px;
    }

    header {
        flex-direction: column;
        margin-bottom: 20px;
    }

    .controls-grid {
        grid-template-columns: 1fr;
    }

    .timeline-card,
    .range-card,
    .play-card {
        padding: 19px;
    }

    .date-grid {
        grid-template-columns: 1fr;
        gap: 14px;
    }

    .plot-card {
        min-height: 440px;
    }

    #mars-plot {
        height: 500px;
        min-height: 420px;
    }

    .current-date {
        font-size: 18px;
    }

    .data-badge {
        white-space: normal;
    }
}
</style>
</head>

<body>
<div class="page">

    <header>
        <div>
            <div class="eyebrow">CELESTIAL MOTION / DATA EXPLORATION</div>
            <h1>MARS IN RETROGRADE</h1>
            <div class="subtitle">
                Earth's view · September 2024 — March 2025
            </div>
        </div>

        <div class="data-badge">
            182 DAILY OBSERVATIONS
        </div>
    </header>

    <section class="card timeline-card">
        <div class="section-heading">
            <div class="section-label">SELECTED OBSERVATION</div>
            <div class="current-date" id="current-date"></div>
        </div>

        <input
            id="timeline"
            type="range"
            min="0"
            max="181"
            value="0"
            step="1"
            aria-label="Selected observation date"
        >

        <div class="timeline-ends">
            <span id="timeline-first"></span>
            <span id="timeline-last"></span>
        </div>
    </section>

    <div class="controls-grid">

        <section class="card range-card">
            <h2>VISIBLE TRAJECTORY RANGE</h2>
            <p class="description">
                Enter a date or use the calendar picker.
                This changes the visible path, not the selected observation.
            </p>

            <div class="date-grid">
                <div class="date-field">
                    <label for="range-start">START DATE</label>
                    <input
                        id="range-start"
                        type="date"
                    >
                </div>

                <div class="date-field">
                    <label for="range-end">END DATE</label>
                    <input
                        id="range-end"
                        type="date"
                    >
                </div>
            </div>

            <div class="range-hint" id="range-hint"></div>
        </section>

        <section class="card play-card">
            <div>
                <h2>TIME PLAYBACK</h2>
                <p class="description">
                    Play through the selected date range.
                    Pause at any time or reset the view.
                </p>
            </div>

            <div class="button-row">
                <button class="primary" id="play">▶ Play</button>
                <button class="secondary" id="reset">↺ Reset</button>
            </div>
        </section>

    </div>

    <section class="card plot-card">
        <div class="plot-heading">
            <strong>THREE-DIMENSIONAL TRAJECTORY</strong>
            <span>Drag to rotate · Scroll to zoom</span>
        </div>

        __PLOT__
    </section>

    <footer>
        <span>NASA/JPL HORIZONS · GEOCENTRIC APPARENT POSITIONS</span>
        <span>Z = ELAPSED DAYS · NOT PHYSICAL DISTANCE</span>
    </footer>

</div>

<script>
const DATA = __DATA__;

const dates = DATA.dates;
const ra = DATA.ra;
const dec = DATA.dec;
const elapsed = DATA.elapsed;

const last = dates.length - 1;

const plot = document.getElementById("mars-plot");
const timeline = document.getElementById("timeline");

const startControl = document.getElementById("range-start");
const endControl = document.getElementById("range-end");

const currentLabel = document.getElementById("current-date");
const firstLabel = document.getElementById("timeline-first");
const lastLabel = document.getElementById("timeline-last");
const rangeHint = document.getElementById("range-hint");
const playButton = document.getElementById("play");

let current = 0;
let playing = false;
let timer = null;


// --------------------------------------------------
// DATE HELPERS
// --------------------------------------------------

function dateIndex(dateString) {
    const index = dates.indexOf(dateString);

    if (index !== -1) {
        return index;
    }

    // For dates between observations, choose the nearest
    // observation on or before the selected date.
    let result = 0;

    for (let i = 0; i < dates.length; i++) {
        if (dates[i] <= dateString) {
            result = i;
        } else {
            break;
        }
    }

    return result;
}

function getRange() {
    return {
        start: dateIndex(startControl.value),
        end: dateIndex(endControl.value)
    };
}

function updateLabels() {
    currentLabel.textContent = dates[current];

    firstLabel.textContent = dates[0];
    lastLabel.textContent = dates[last];

    const range = getRange();

    rangeHint.textContent =
        dates[range.start] + "  →  " +
        dates[range.end] + "  ·  " +
        (range.end - range.start + 1) +
        " observations";
}


// --------------------------------------------------
// UPDATE THE VISIBLE TRAJECTORY ONLY
// This function never changes the current observation.
// --------------------------------------------------

function updateRange() {
    const range = getRange();
    const start = range.start;
    const end = range.end;

    const visibleX = ra.map((value, i) =>
        i >= start && i <= end ? value : null
    );

    const visibleY = dec.map((value, i) =>
        i >= start && i <= end ? value : null
    );

    const visibleZ = elapsed.map((value, i) =>
        i >= start && i <= end ? value : null
    );

    // Trace 0: visible trajectory line.
    Plotly.restyle(plot, {
        x: [visibleX],
        y: [visibleY],
        z: [visibleZ]
    }, [0]);

    // Trace 1: visible daily observations.
    Plotly.restyle(plot, {
        x: [visibleX],
        y: [visibleY],
        z: [visibleZ]
    }, [1]);

    updateLabels();
}


// --------------------------------------------------
// UPDATE THE SELECTED OBSERVATION ONLY
// This function never changes the date range.
// --------------------------------------------------

function updateCurrent() {
    timeline.value = current;

    Plotly.restyle(plot, {
        x: [[ra[current]]],
        y: [[dec[current]]],
        z: [[elapsed[current]]],
        text: [[dates[current]]]
    }, [2]);

    updateLabels();
}


// --------------------------------------------------
// TIMELINE: controls the current observation only.
// --------------------------------------------------

timeline.max = last;
timeline.value = 0;

timeline.addEventListener("input", () => {
    stopPlaying();

    current = Number(timeline.value);
    updateCurrent();
});


// --------------------------------------------------
// DATE INPUTS: control the visible range only.
// They do not change current or timeline.value.
// --------------------------------------------------

startControl.min = dates[0];
startControl.max = dates[last];
startControl.value = dates[0];

endControl.min = dates[0];
endControl.max = dates[last];
endControl.value = dates[last];

startControl.addEventListener("change", () => {
    stopPlaying();

    if (startControl.value > endControl.value) {
        endControl.value = startControl.value;
    }

    endControl.min = startControl.value;
    startControl.max = endControl.value;

    updateRange();
});

endControl.addEventListener("change", () => {
    stopPlaying();

    if (endControl.value < startControl.value) {
        startControl.value = endControl.value;
    }

    startControl.max = endControl.value;
    endControl.min = startControl.value;

    updateRange();
});


// --------------------------------------------------
// PLAYBACK
// --------------------------------------------------

function stopPlaying() {
    playing = false;

    if (timer !== null) {
        clearInterval(timer);
        timer = null;
    }

    playButton.textContent = "▶ Play";
}

playButton.addEventListener("click", () => {
    if (playing) {
        stopPlaying();
        return;
    }

    const range = getRange();
    const start = range.start;
    const end = range.end;

    // If the selected observation is outside the playback
    // range, begin playback at the range's first observation.
    if (current < start || current > end) {
        current = start;
        updateCurrent();
    }

    if (current >= end) {
        current = start;
        updateCurrent();
    }

    playing = true;
    playButton.textContent = "Ⅱ Pause";

    timer = setInterval(() => {
        const latestRange = getRange();

        if (current >= latestRange.end) {
            stopPlaying();
            return;
        }

        current += 1;
        updateCurrent();
    }, 160);
});


// --------------------------------------------------
// RESET
// --------------------------------------------------

document.getElementById("reset").addEventListener("click", () => {
    stopPlaying();

    startControl.value = dates[0];
    endControl.value = dates[last];

    startControl.min = dates[0];
    startControl.max = dates[last];

    endControl.min = dates[0];
    endControl.max = dates[last];

    current = 0;

    updateRange();
    updateCurrent();

    Plotly.relayout(plot, {
        "scene.camera": {
            eye: {
                x: 1.65,
                y: 1.65,
                z: 1.25
            }
        }
    });
});


// --------------------------------------------------
// INITIAL STATE
// --------------------------------------------------

updateLabels();
</script>

</body>
</html>
"""

    page = page.replace("__PLOT__", plot_html)
    page = page.replace("__DATA__", browser_data)

    return page


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    observations = read_observations(DATA)

    fig, dates, ra, dec, elapsed = build_figure(
        observations
    )

    page = build_page(
        fig,
        dates,
        ra,
        dec,
        elapsed
    )

    OUT.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        page,
        encoding="utf-8"
    )

    print(f"Loaded {len(observations)} observations")
    print(f"From {dates[0]} to {dates[-1]}")
    print(f"Saved interactive page: {OUTPUT.relative_to(HERE)}")


if __name__ == "__main__":
    main()
