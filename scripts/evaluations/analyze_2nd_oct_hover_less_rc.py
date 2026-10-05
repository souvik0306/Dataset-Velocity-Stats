#!/usr/bin/env python3
"""Evaluate the configured 2 October less-RC hover flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "2nd_Oct_Hover_less_RC"
OUTPUT_FOLDER = "2nd_Oct_hover_less_rc"

WINDOWS = {
    "AI": (
        (56.24, 76.24),
        (39.81, 59.81),
        (37.99, 57.99),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
