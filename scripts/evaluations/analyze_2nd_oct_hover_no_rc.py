#!/usr/bin/env python3
"""Evaluate the configured 2 October no-RC hover flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "2nd_Oct_Hover_no_RC"
OUTPUT_FOLDER = "2nd_Oct_hover_no_rc"

WINDOWS = {
    "AI": (
        (63.96, 83.96),
        (36.37, 56.37),
        (41.80, 61.80),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
