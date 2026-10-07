#!/usr/bin/env python3
"""Plot smoothed absolute pitch rate for 2 October less-RC AI flights 1 and 3.

The displayed traces are smoothed for readability.  The P99 and maximum
reference lines are calculated from the original (unsmoothed) pitch-rate
samples returned by the motion-metrics pipeline.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import median_filter

TICK_FONT_SIZE = 18
LEGEND_FONT_SIZE = 18
LABEL_FONT_SIZE = 18
SUBPLOT_TITLE_FONT_SIZE = 20
FIGURE_TITLE_FONT_SIZE = 18
DATA_LINE_WIDTH = 4

plt.rcParams.update({"font.size": TICK_FONT_SIZE})

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT))
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts" / "evaluations"))

from analyze_2nd_oct_hover_less_rc import DATA_FOLDER, OUTPUT_FOLDER, WINDOWS  # noqa: E402
from rosbag_motion_metrics import compute_metrics_for_time_window  # noqa: E402

FLIGHTS = (1, 3)
WINDOW_DURATION_S = 20.0
DEFAULT_SMOOTHING_MS = 150.0
DEFAULT_OUTPUT = (
    WORKSPACE_ROOT
    / "results"
    / OUTPUT_FOLDER
    / "20s"
    / "AI"
    / "plots"
    / "absolute_pitch_rate_flights_1_and_3_smoothed.png"
)
DEFAULT_ANGLE_OUTPUT = DEFAULT_OUTPUT.with_name(
    "pitch_angle_values_used_for_rate_flights_1_and_3.png"
)


def smooth_for_display(
    times_s: np.ndarray, values: np.ndarray, smoothing_ms: float
) -> Tuple[np.ndarray, int]:
    """Return a centered rolling median; do not use it for metric statistics."""
    if len(times_s) < 2:
        return values.copy(), 1

    median_dt_s = float(np.median(np.diff(times_s)))
    window_samples = max(1, int(round((smoothing_ms / 1000.0) / median_dt_s)))
    if window_samples % 2 == 0:
        window_samples += 1
    return median_filter(values, size=window_samples, mode="nearest"), window_samples


def load_flight(flight_number: int) -> Dict[str, object]:
    """Run the standard metrics pipeline for one configured 20-second window."""
    bag_path = WORKSPACE_ROOT / "data" / DATA_FOLDER / f"flight_{flight_number}.bag"
    if not bag_path.is_file():
        raise FileNotFoundError(f"Missing flight bag: {bag_path}")

    window_start_s, window_end_s = WINDOWS["AI"][flight_number - 1]
    if not np.isclose(window_end_s - window_start_s, WINDOW_DURATION_S):
        raise ValueError(
            f"Flight {flight_number} window is not {WINDOW_DURATION_S:g} s: "
            f"{window_start_s:.2f}-{window_end_s:.2f} s"
        )

    return compute_metrics_for_time_window(
        bag_path,
        dataset="AI",
        window_key=f"ai_flight_{flight_number}",
        window_start_s=window_start_s,
        window_end_s=window_end_s,
    )


def make_angle_plot(
    results: Dict[int, Dict[str, object]], smoothing_ms: float, output_path: Path
) -> Path:
    """Plot the unsmoothed, resampled pitch values supplied to the derivative."""
    fig, axes = plt.subplots(2, 1, figsize=(18, 11), sharex=True)
    colors = {1: "#1769c2", 3: "#7b2cbf"}

    for axis, flight_number in zip(axes, FLIGHTS):
        result = results[flight_number]
        angle_samples = result["_pitch_angle_samples_for_rate"]
        header_times_s = np.array([time_s for time_s, _ in angle_samples])
        angles_rad = np.array([angle_rad for _, angle_rad in angle_samples])
        relative_header_times_s = header_times_s - header_times_s[0]
        angle_min = float(angles_rad.min())
        angle_max = float(angles_rad.max())
        padding = max(0.03 * (angle_max - angle_min), 0.002)
        displayed_angles, _ = smooth_for_display(
            relative_header_times_s, angles_rad, smoothing_ms
        )

        axis.plot(
            relative_header_times_s,
            angles_rad,
            color=colors[flight_number],
            linewidth=1.2,
            alpha=0.40,
            label="Actual pitch values used for rate calculation",
        )
        axis.plot(
            relative_header_times_s,
            displayed_angles,
            color=colors[flight_number],
            linewidth=DATA_LINE_WIDTH,
            label=f"Smoothed pitch angle ({smoothing_ms:g} ms centered median)",
        )
        axis.axhline(0.0, color="#555555", linewidth=1.0, alpha=0.6)
        axis.set_title(
            f"AI Flight {flight_number}  |  source window "
            f"{float(result['window_start_s']):.2f}-{float(result['window_end_s']):.2f} s",
            fontsize=SUBPLOT_TITLE_FONT_SIZE,
            loc="left",
        )
        axis.set_xlim(0.0, WINDOW_DURATION_S)
        axis.set_ylim(angle_min - padding, angle_max + padding)
        axis.set_ylabel("Pitch angle (rad)", fontsize=LABEL_FONT_SIZE)
        axis.grid(which="major", alpha=0.30)
        axis.minorticks_on()
        axis.grid(which="minor", alpha=0.12)
        axis.tick_params(labelsize=TICK_FONT_SIZE)
        axis.legend(loc="upper left", fontsize=LEGEND_FONT_SIZE)

    axes[-1].set_xlabel(
        "Time from evaluation-window start, derived from pose header timestamp (s)",
        fontsize=LABEL_FONT_SIZE,
    )
    fig.suptitle(
        "2nd October Hover Less RC: Pitch Values Used for Rate Calculation",
        fontsize=FIGURE_TITLE_FONT_SIZE,
        fontweight="bold",
    )
    fig.subplots_adjust(top=0.91, bottom=0.09, left=0.10, right=0.98, hspace=0.22)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    print(f"Saved {output_path}")
    return output_path


def make_plot(
    smoothing_ms: float,
    output_path: Path,
    angle_output_path: Path = DEFAULT_ANGLE_OUTPUT,
) -> Path:
    if smoothing_ms <= 0:
        raise ValueError("Smoothing duration must be greater than zero")

    results = {flight_number: load_flight(flight_number) for flight_number in FLIGHTS}
    make_angle_plot(results, smoothing_ms, angle_output_path)
    fig, axes = plt.subplots(2, 1, figsize=(18, 11), sharex=True)
    colors = {1: "#1769c2", 3: "#7b2cbf"}

    for axis, flight_number in zip(axes, FLIGHTS):
        result = results[flight_number]
        rate_samples = result["_pitch_rate_samples"]
        sample_times_s = np.array([time_s for time_s, _ in rate_samples])
        raw_rates = np.array([rate for _, rate in rate_samples])
        relative_times_s = sample_times_s - sample_times_s[0]
        maximum_index = int(np.argmax(raw_rates))
        maximum_relative_time_s = float(relative_times_s[maximum_index])
        displayed_rates, window_samples = smooth_for_display(
            relative_times_s, raw_rates, smoothing_ms
        )

        p99 = float(result["p99_absolute_pitch_rate_rad_s"])
        maximum = float(result["maximum_absolute_pitch_rate_rad_s"])
        window_start_s = float(result["window_start_s"])
        window_end_s = float(result["window_end_s"])

        axis.plot(
            relative_times_s,
            raw_rates,
            color=colors[flight_number],
            linewidth=1.2,
            alpha=0.40,
            label="Actual absolute pitch rate",
        )
        axis.plot(
            relative_times_s,
            displayed_rates,
            color=colors[flight_number],
            linewidth=DATA_LINE_WIDTH,
            label=(
                f"Smoothed absolute pitch rate "
                f"({smoothing_ms:g} ms centered median)"
            ),
        )
        axis.axhline(
            p99,
            color="#e69f00",
            linewidth=2.2,
            linestyle="--",
            label=f"Actual P99 = {p99:.3f} rad/s",
        )
        axis.axhline(
            maximum,
            color="#d62728",
            linewidth=3.2,
            linestyle="--",
            label=f"Actual maximum = {maximum:.3f} rad/s",
        )
        axis.axvline(
            maximum_relative_time_s,
            color="#d62728",
            linewidth=2.0,
            linestyle=":",
        )
        axis.plot(
            maximum_relative_time_s,
            maximum,
            marker="o",
            markersize=8,
            color="#d62728",
            zorder=5,
        )
        axis.set_title(
            f"AI Flight {flight_number}  |  source window "
            f"{window_start_s:.2f}-{window_end_s:.2f} s",
            fontsize=SUBPLOT_TITLE_FONT_SIZE,
            loc="left",
        )
        axis.set_xlim(0.0, WINDOW_DURATION_S)
        axis.set_ylim(0.0, maximum * 1.10)
        axis.set_ylabel("Absolute pitch rate (rad/s)", fontsize=LABEL_FONT_SIZE)
        axis.grid(which="major", alpha=0.30)
        axis.minorticks_on()
        axis.grid(which="minor", alpha=0.12)
        axis.tick_params(labelsize=TICK_FONT_SIZE)
        axis.plot(
            [maximum_relative_time_s, maximum_relative_time_s],
            [0.0, -0.018],
            transform=axis.get_xaxis_transform(),
            color="#d62728",
            linewidth=2,
            clip_on=False,
        )
        axis.text(
            maximum_relative_time_s,
            -0.03,
            f"{maximum_relative_time_s:.2f} s\nmax",
            transform=axis.get_xaxis_transform(),
            ha="center",
            va="top",
            color="#d62728",
            fontsize=TICK_FONT_SIZE,
            clip_on=False,
        )
        axis.legend(loc="upper left", fontsize=LEGEND_FONT_SIZE)

        print(
            f"AI Flight {flight_number}: actual P99={p99:.6f} rad/s, "
            f"actual max={maximum:.6f} rad/s at {maximum_relative_time_s:.2f} s, "
            f"display median={window_samples} samples"
        )

    axes[-1].set_xlabel(
        "Time from evaluation-window start, derived from pose header timestamp (s)",
        fontsize=LABEL_FONT_SIZE,
        labelpad=28,
    )
    fig.suptitle(
        "2nd October Hover Less RC: Absolute Pitch Rate",
        fontsize=FIGURE_TITLE_FONT_SIZE,
        fontweight="bold",
    )
    fig.subplots_adjust(top=0.91, bottom=0.14, left=0.10, right=0.98, hspace=0.30)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    print(f"Saved {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoothing-ms",
        type=float,
        default=DEFAULT_SMOOTHING_MS,
        help=f"Centered-median width used only for display (default: {DEFAULT_SMOOTHING_MS:g})",
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
    make_plot(
        args.smoothing_ms,
        args.output.expanduser().resolve(),
        args.angle_output.expanduser().resolve(),
    )


if __name__ == "__main__":
    main()
