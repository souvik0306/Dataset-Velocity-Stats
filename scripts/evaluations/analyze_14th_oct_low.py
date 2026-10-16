#!/usr/bin/env python3
"""Evaluate the configured 14 October low-motion flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "14th_Oct_Low"
OUTPUT_FOLDER = "14th_Oct_Low"

WINDOWS = {
    "AI": (
        (46.39, 66.39),
        (41.23, 61.23),
        (38.41, 58.41),
        (59.76, 79.76),
    ),
    "RAW": (
        (37.88, 57.88),
        (39.02, 59.02),
        (44.80, 64.80),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
