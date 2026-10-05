#!/usr/bin/env python3
"""Evaluate the configured medium-motion flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "Medium"
OUTPUT_FOLDER = "Medium"

WINDOWS = {
    "AI": (
        (34.43, 54.43),
        (41.62, 61.62),
        (35.62, 55.62),
    ),
    "RAW": (
        (38.48, 58.48),
        (34.54, 54.54),
        (36.91, 56.91),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
