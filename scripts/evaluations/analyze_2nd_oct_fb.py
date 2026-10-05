#!/usr/bin/env python3
"""Run 2 October FB motion metrics for the configured AI flights."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation_common import run_group


BAGS_DIR = Path(__file__).resolve().parents[2] / "data" / "2nd_Oct_FB"

# Each 20-second evaluation starts 5 seconds after the Vicon cutoff.
FLIGHTS = {
    1: {"bag": "flight_1.bag", "start": 42.77, "end": 62.77},
    2: {"bag": "flight_2.bag", "start": 34.51, "end": 54.51},
    3: {"bag": "flight_3.bag", "start": 44.93, "end": 64.93},
    4: {"bag": "flight_4.bag", "start": 40.11, "end": 60.11},
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
    parser.add_argument("-o", "--output-dir", default="results/2nd_Oct_FB")
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
        title="2 October FB Motion Metrics",
        make_pitch_rate_time_series=True,
        pitch_rate_time_series_title="2 October FB",
        include_yaw=False,
    )


if __name__ == "__main__":
    main()
