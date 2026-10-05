#!/usr/bin/env python3
"""Evaluate the configured yaw flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "10th_Sept_AI_Yaw_Rosbags"
OUTPUT_FOLDER = "Yaw"

WINDOWS = {
    "AI": (
        (44.93, 64.93),
        (38.07, 58.07),
        (39.44, 59.44),
        (36.31, 56.31),
        (31.78, 51.78),
    ),
    "RAW": (
        (38.05, 58.05),
        (34.77, 54.77),
        (38.71, 58.71),
        (32.82, 52.82),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
