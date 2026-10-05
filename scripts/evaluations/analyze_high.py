#!/usr/bin/env python3
"""Evaluate the configured high-motion flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "High"
OUTPUT_FOLDER = "High"

WINDOWS = {
    "AI": (
        (41.07, 61.07),
        (39.10, 59.10),
        (39.65, 59.65),
        (43.22, 63.22),
    ),
    "RAW": (
        (36.19, 56.19),
        (37.10, 57.10),
        (37.42, 57.42),
        (31.98, 51.98),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
