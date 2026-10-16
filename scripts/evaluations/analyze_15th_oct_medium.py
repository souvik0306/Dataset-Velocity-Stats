#!/usr/bin/env python3
"""Evaluate the configured 15 October medium-motion flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "15th_Oct_Medium"
OUTPUT_FOLDER = "15th_Oct_Medium"

WINDOWS = {
    "AI": (
        (40.05, 60.05),
        (39.13, 59.13),
        (40.87, 60.87),
        (39.10, 59.10),
    ),
    "RAW": (
        (40.99, 60.99),
        (49.39, 69.39),
        (45.42, 65.42),
        (42.41, 62.41),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
