#!/usr/bin/env python3
"""Evaluate the configured hover flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "9th_Sept_AI_Hover_Rosbags"
OUTPUT_FOLDER = "Hover"

WINDOWS = {
    "AI": (
        (55.15, 75.15),
        (54.92, 74.92),
        (42.06, 62.06),
    ),
    "RAW": (
        (44.32, 64.32),
        (39.75, 59.75),
        (30.71, 50.71),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
