#!/usr/bin/env python3
"""Evaluate the configured super-high-motion flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "Super-High"
OUTPUT_FOLDER = "Super-High"

WINDOWS = {
    "AI": (
        (41.14, 61.14),
        (40.24, 60.24),
        (37.50, 57.50),
        (38.23, 58.23),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
