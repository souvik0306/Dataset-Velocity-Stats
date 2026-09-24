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


BAGS_DIR = Path(__file__).resolve().parents[2] / "data" / "22nd_Sept_Hover_RC_hovering"

FLIGHTS = {
    "AI": {
        1: {"bag": "flight_2026-07-01-14-59-51.bag", "start": 36.31},
        2: {"bag": "flight_2026-07-01-15-02-42.bag", "start": 34.62},
        3: {"bag": "flight_2026-07-01-15-05-13.bag", "start": 35.69},
    },
    "RAW": {
        1: {"bag": "flight_2026-07-01-14-28-47.bag", "start": 43.42},
        2: {"bag": "flight_2026-07-01-14-31-33.bag", "start": 39.91},
        3: {"bag": "flight_2026-07-01-14-34-13.bag", "start": 38.23},
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
    parser.add_argument("-o", "--output-dir", default="results/RC-Hovering")
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
        include_yaw=False,
        extra_selected_metrics=HOVER_EXTRA_SELECTED_METRICS,
        extra_metric_definitions=HOVER_EXTRA_METRIC_DEFINITIONS,
        extra_metric_methods=HOVER_EXTRA_METRIC_METHODS,
    )


if __name__ == "__main__":
    main()
