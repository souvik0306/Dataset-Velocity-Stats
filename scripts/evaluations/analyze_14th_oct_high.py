#!/usr/bin/env python3
"""Evaluate the configured 14 October high-motion flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "14th_Oct_High"
OUTPUT_FOLDER = "14th_Oct_High"

WINDOWS = {
    "AI": (
        (51.08, 71.08),
        (41.44, 61.44),
        (38.30, 58.30),
        (39.35, 59.35),
    ),
    "RAW": (
        (38.97, 58.97),
        (43.61, 63.61),
        (34.50, 54.50),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
