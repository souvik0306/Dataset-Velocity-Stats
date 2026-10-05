#!/usr/bin/env python3
"""Evaluate the configured 2 October yaw flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "2nd_Oct_Yaw"
OUTPUT_FOLDER = "2nd_Oct_Yaw"

WINDOWS = {
    "AI": (
        (124.54, 144.54),
        (44.24, 64.24),
        (40.37, 60.37),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
