#!/usr/bin/env python3
"""Run Medium Motion Metrics for the configured AI and RAW flight windows."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation_common import run_group


# Window starts are seconds since bag start, in sorted bag filename order.
DATASETS = {
    "AI": {
        "folder": "AI",
        "window_starts_s": (34.43, 41.62, 35.62),
    },
    "RAW": {
        "folder": "RAW",
        "window_starts_s": (38.48, 34.54, 36.91),
    },
}

DEFAULT_DURATIONS_S = (20,)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default='data/Medium')
    parser.add_argument("-o", "--output-dir", default='results/Medium')
    parser.add_argument("--durations", nargs="+", type=int, choices=DEFAULT_DURATIONS_S,
                        default=list(DEFAULT_DURATIONS_S), metavar="SECONDS")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    run_group(Path(args.root).expanduser().resolve(),
              Path(args.output_dir).expanduser().resolve(),
              DATASETS, args.durations, make_plots=not args.no_plots,
              title='Medium Motion Metrics', include_yaw=False)


if __name__ == "__main__":
    main()
