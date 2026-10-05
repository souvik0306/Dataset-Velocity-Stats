#!/usr/bin/env python3
"""Evaluate the configured less-RC hover flight windows."""

from evaluation_common import run_evaluation


DATA_FOLDER = "22nd_Sept_Hover_less_RC"
OUTPUT_FOLDER = "Less-RC-Hovering"

WINDOWS = {
    "AI": (
        (45.05, 65.05),
        (37.39, 57.39),
        (36.06, 56.06),
        (37.28, 57.28),
        (34.52, 54.52),
    ),
    "RAW": (
        (113.37, 133.37),
        (33.27, 53.27),
        (38.22, 58.22),
        (36.97, 56.97),
    ),
}


if __name__ == "__main__":
    run_evaluation(
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER,
        windows=WINDOWS,
    )
