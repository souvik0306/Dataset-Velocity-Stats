#!/usr/bin/env python3
"""Run RC-hovering motion metrics for the configured AI and RAW flights."""

from __future__ import annotations

import argparse
from pathlib import Path

from analyze_hover import (
    HOVER_EXTRA_METRIC_DEFINITIONS,
    HOVER_EXTRA_METRIC_METHODS,
    HOVER_EXTRA_SELECTED_METRICS,
)
from evaluation_common import run_group


BAGS_DIR = Path(__file__).resolve().parents[2] / "data" / "22nd_Sept_Hover_less_RC"

FLIGHTS = {
    "AI": {
        1: {"bag": "flight_2026-07-01-14-41-46.bag", "start": 45.05},
        2: {"bag": "flight_2026-07-01-14-45-13.bag", "start": 37.39},
        3: {"bag": "flight_2026-07-01-14-47-42.bag", "start": 36.06},
        4: {"bag": "flight_2026-07-01-14-50-12.bag", "start": 37.28},
        5: {"bag": "flight_2026-07-01-14-53-18.bag", "start": 34.52},
    },
    "RAW": {
        1: {"bag": "flight_2026-07-01-14-11-04.bag", "start": 113.37},
        2: {"bag": "flight_2026-07-01-14-15-52.bag", "start": 33.27},
        3: {"bag": "flight_2026-07-01-14-18-56.bag", "start": 38.22},
        4: {"bag": "flight_2026-07-01-14-21-56.bag", "start": 36.97},
    },
}

DATASETS = {
    dataset: {
        "folder": dataset,
        "window_starts_s": tuple(flight["start"] for flight in flights.values()),
    }
    for dataset, flights in FLIGHTS.items()
}

DEFAULT_DURATIONS_S = (20,)


def validate_flight_order(root: Path) -> None:
    """Ensure sorted bag discovery matches the explicit flight configuration."""
    for dataset, flights in FLIGHTS.items():
        expected = [flight["bag"] for flight in flights.values()]
        discovered = sorted(path.name for path in (root / dataset).glob("flight_*.bag"))
        if discovered != expected:
            raise ValueError(
                f"{dataset} bag order does not match FLIGHTS: "
                f"expected {expected}, found {discovered}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=BAGS_DIR)
    parser.add_argument("-o", "--output-dir", default="results/Less-RC-Hovering")
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
    validate_flight_order(root)
    run_group(
        root,
        Path(args.output_dir).expanduser().resolve(),
        DATASETS,
        args.durations,
        make_plots=not args.no_plots,
        title="RC Hovering Motion Metrics",
        make_pitch_rate_time_series=True,
        pitch_rate_time_series_title="22 Sept Less-RC Hover",
        include_yaw=False,
        extra_selected_metrics=HOVER_EXTRA_SELECTED_METRICS,
        extra_metric_definitions=HOVER_EXTRA_METRIC_DEFINITIONS,
        extra_metric_methods=HOVER_EXTRA_METRIC_METHODS,
    )


if __name__ == "__main__":
    main()
