#!/usr/bin/env python3
"""Evaluate the configured RC-hovering flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "22nd_Sept_Hover_RC_hovering"
OUTPUT_FOLDER = "RC-Hovering"

WINDOWS = {
    "AI": (
        (36.31, 56.31),
        (34.62, 54.62),
        (35.69, 55.69),
    ),
    "RAW": (
        (43.42, 63.42),
        (39.91, 59.91),
        (38.23, 58.23),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
