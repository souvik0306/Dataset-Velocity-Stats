#!/usr/bin/env python3
"""Evaluate the configured 7 October yaw flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "7th_Oct_Yaw"
OUTPUT_FOLDER = "7th_Oct_Yaw"

WINDOWS = {
    "AI": (
        (37.77, 57.77),
        (43.85, 63.85),
        (38.33, 58.33),
        (36.86, 56.86),
        (37.49, 57.49),
    ),
    "RAW": (
        (50.12, 70.12),
        (36.87, 56.87),
        (36.16, 56.16),
        (34.98, 54.98),
        (39.10, 59.10),
        (39.31, 59.31),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
