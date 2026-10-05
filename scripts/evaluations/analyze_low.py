#!/usr/bin/env python3
"""Evaluate the configured low-dynamic flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "Low-Dynamic"
OUTPUT_FOLDER = "Low-Dynamic"

WINDOWS = {
    "AI": (
        (44.24, 64.24),
        (32.99, 52.99),
        (35.95, 55.95),
        (41.47, 61.47),
    ),
    "RAW": (
        (48.51, 68.51),
        (33.29, 53.29),
        (34.77, 54.77),
        (39.63, 59.63),
        (35.16, 55.16),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
