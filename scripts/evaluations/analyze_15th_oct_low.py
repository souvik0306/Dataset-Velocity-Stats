#!/usr/bin/env python3
"""Evaluate the configured 15 October low-motion flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "15th_Oct_Low"
OUTPUT_FOLDER = "15th_Oct_Low"

WINDOWS = {
    "AI": (
        (42.03, 62.03),
        (38.28, 58.28),
        (55.69, 75.69),
    ),
    "RAW": (
        (38.70, 58.70),
        (41.77, 61.77),
        (39.39, 59.39),
        (42.76, 62.76),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
