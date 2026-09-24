#!/usr/bin/env python3
"""Run Low-Dynamic Motion Metrics for the configured AI and RAW flight windows."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation_common import run_group


# Window starts are seconds since bag start, in sorted bag filename order.
DATASETS = {
    "AI": {
        "folder": "AI",
        "window_starts_s": (44.24, 32.99, 35.95, 41.47),
    },
    "RAW": {
        "folder": "RAW",
        "window_starts_s": (48.51, 33.29, 34.77, 39.63, 35.16),
    },
}

DEFAULT_DURATIONS_S = (20,)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default='data/Low-Dynamic')
    parser.add_argument("-o", "--output-dir", default='results/Low-Dynamic')
    parser.add_argument("--durations", nargs="+", type=int, choices=DEFAULT_DURATIONS_S,
                        default=list(DEFAULT_DURATIONS_S), metavar="SECONDS")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    run_group(Path(args.root).expanduser().resolve(),
              Path(args.output_dir).expanduser().resolve(),
              DATASETS, args.durations, make_plots=not args.no_plots,
              title='Low-Dynamic Motion Metrics', include_yaw=False)


if __name__ == "__main__":
    main()
