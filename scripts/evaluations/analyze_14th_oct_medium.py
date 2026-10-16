#!/usr/bin/env python3
"""Evaluate the configured 14 October medium-motion flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "14th_Oct_Medium"
OUTPUT_FOLDER = "14th_Oct_Medium"

WINDOWS = {
    "AI": (
        (39.65, 59.65),
        (45.39, 65.39),
        (45.11, 65.11),
        (41.84, 61.84),
        (37.04, 57.04),
    ),
    "RAW": (
        (38.71, 58.71),
        (36.80, 56.80),
        (36.60, 56.60),
        (36.99, 56.99),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
