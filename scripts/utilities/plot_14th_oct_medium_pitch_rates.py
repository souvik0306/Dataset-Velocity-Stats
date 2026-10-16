#!/usr/bin/env python3
"""Plot smoothed absolute pitch rate for 14 October Medium AI flights 3 and 5.

This reuses the dedicated pitch-rate plotting workflow. The displayed traces
are smoothed for readability, while P99 and maximum reference lines come from
the original unsmoothed pitch-rate samples returned by the metrics pipeline.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT))
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts" / "evaluations"))
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts" / "utilities"))

import plot_2nd_oct_hover_less_rc_pitch_rates as pitch_plotter  # noqa: E402
from analyze_14th_oct_medium import DATA_FOLDER, OUTPUT_FOLDER, WINDOWS  # noqa: E402

FLIGHTS = (3, 5)
DEFAULT_OUTPUT = (
    WORKSPACE_ROOT
    / "results"
    / OUTPUT_FOLDER
    / "20s"
    / "AI"
    / "plots"
    / "absolute_pitch_rate_flights_3_and_5_smoothed.png"
)
DEFAULT_ANGLE_OUTPUT = DEFAULT_OUTPUT.with_name(
    "pitch_angle_values_used_for_rate_flights_3_and_5.png"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoothing-ms",
        type=float,
        default=pitch_plotter.DEFAULT_SMOOTHING_MS,
        help=(
            "Centered-median width used only for display "
            f"(default: {pitch_plotter.DEFAULT_SMOOTHING_MS:g})"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output PNG path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--angle-output",
        type=Path,
        default=DEFAULT_ANGLE_OUTPUT,
        help=f"Pitch-angle input plot path (default: {DEFAULT_ANGLE_OUTPUT})",
    )
    args = parser.parse_args()

    pitch_plotter.DATA_FOLDER = DATA_FOLDER
    pitch_plotter.OUTPUT_FOLDER = OUTPUT_FOLDER
    pitch_plotter.WINDOWS = WINDOWS
    pitch_plotter.FLIGHTS = FLIGHTS
    pitch_plotter.BAG_DIR = WORKSPACE_ROOT / "data" / DATA_FOLDER / "AI"
    pitch_plotter.PLOT_TITLE_PREFIX = "14th October Medium"
    pitch_plotter.make_plot(
        args.smoothing_ms,
        args.output.expanduser().resolve(),
        args.angle_output.expanduser().resolve(),
    )


if __name__ == "__main__":
    main()
