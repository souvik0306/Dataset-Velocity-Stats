#!/usr/bin/env python3
"""Run 2 October less-RC hover metrics for the configured AI flights."""

from __future__ import annotations

import argparse
from pathlib import Path

from analyze_hover import (
    HOVER_EXTRA_METRIC_DEFINITIONS,
    HOVER_EXTRA_METRIC_METHODS,
    HOVER_EXTRA_SELECTED_METRICS,
)
from evaluation_common import run_group


BAGS_DIR = Path(__file__).resolve().parents[2] / "data" / "2nd_Oct_Hover_less_RC"

# Each 20-second evaluation starts 5 seconds after the Vicon cutoff.
FLIGHTS = {
    1: {"bag": "flight_1.bag", "start": 56.24, "end": 76.24},
    2: {"bag": "flight_2.bag", "start": 39.81, "end": 59.81},
    3: {"bag": "flight_3.bag", "start": 37.99, "end": 57.99},
}

DATASETS = {
    "AI": {
        "folder": ".",
        "window_starts_s": tuple(flight["start"] for flight in FLIGHTS.values()),
    }
}

DEFAULT_DURATIONS_S = (20,)


def validate_flights(root: Path) -> None:
    """Ensure bag discovery and configured 20-second windows are exact."""
    expected = [flight["bag"] for flight in FLIGHTS.values()]
    discovered = sorted(
        (path.name for path in root.glob("flight_*.bag")),
        key=lambda name: int(Path(name).stem[len("flight_") :]),
    )
    if discovered != expected:
        raise ValueError(
            "Bag order does not match FLIGHTS: "
            f"expected {expected}, found {discovered}"
        )

    for flight_number, flight in FLIGHTS.items():
        duration_s = float(flight["end"]) - float(flight["start"])
        if abs(duration_s - DEFAULT_DURATIONS_S[0]) > 1e-9:
            raise ValueError(
                f"Flight {flight_number} window is {duration_s:g} s; expected 20 s"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=BAGS_DIR)
    parser.add_argument("-o", "--output-dir", default="results/2nd_Oct_hover_less_rc")
    parser.add_argument(
        "--durations",
        nargs="+",
        type=int,
        choices=DEFAULT_DURATIONS_S,
        default=list(DEFAULT_DURATIONS_S),
        metavar="SECONDS",
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    validate_flights(root)
    run_group(
        root,
        Path(args.output_dir).expanduser().resolve(),
        DATASETS,
        args.durations,
        make_plots=not args.no_plots,
        title="2 October Less-RC Hover Motion Metrics",
        make_pitch_rate_time_series=True,
        pitch_rate_time_series_title="2 October Less-RC Hover",
        include_yaw=False,
        extra_selected_metrics=HOVER_EXTRA_SELECTED_METRICS,
        extra_metric_definitions=HOVER_EXTRA_METRIC_DEFINITIONS,
        extra_metric_methods=HOVER_EXTRA_METRIC_METHODS,
    )


if __name__ == "__main__":
    main()
