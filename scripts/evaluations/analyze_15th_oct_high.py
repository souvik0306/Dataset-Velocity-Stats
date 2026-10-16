#!/usr/bin/env python3
"""Evaluate the configured 15 October high-motion flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "15th_Oct_High"
OUTPUT_FOLDER = "15th_Oct_High"

WINDOWS = {
    "AI": (
        (38.85, 58.85),
        (39.79, 59.79),
        (40.53, 60.53),
    ),
    "RAW": (
        (44.00, 64.00),
        (37.66, 57.66),
        (44.20, 64.20),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
