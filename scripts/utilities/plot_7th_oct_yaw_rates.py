#!/usr/bin/env python3
"""Compare the yaw rates of 7 October AI flights 2 and 4."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Dict, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rosbag
from scipy.ndimage import median_filter

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT))
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts" / "evaluations"))

from analyze_7th_oct_yaw import DATA_FOLDER, OUTPUT_FOLDER, WINDOWS  # noqa: E402
from rosbag_motion_metrics import (  # noqa: E402
    POSE_TOPIC,
    TWIST_TOPIC,
    normalize_quaternion,
    quaternion_to_roll_pitch_yaw_radians,
    retain_pose_samples,
    yaw_rate_from_pose_samples,
)

DATASET = "AI"
FLIGHTS = (2, 4)
WINDOW_DURATION_S = 20.0
DEFAULT_SMOOTHING_MS = 150.0
TICK_FONT_SIZE = 18
LEGEND_FONT_SIZE = 16
LABEL_FONT_SIZE = 18
SUBPLOT_TITLE_FONT_SIZE = 20
FIGURE_TITLE_FONT_SIZE = 18
DATA_LINE_WIDTH = 4
DEFAULT_OUTPUT = (
    WORKSPACE_ROOT
    / "results"
    / OUTPUT_FOLDER
    / "20s"
    / DATASET
    / "plots"
    / "yaw_rate_flights_2_and_4_smoothed.png"
)
DEFAULT_ANGLE_OUTPUT = DEFAULT_OUTPUT.with_name(
    "unwrapped_yaw_values_flights_2_and_4.png"
)

plt.rcParams.update({"font.size": TICK_FONT_SIZE})


def smooth_for_display(
    times_s: np.ndarray, values: np.ndarray, smoothing_ms: float
) -> Tuple[np.ndarray, int]:
    """Return a centered rolling median used only for the thick display trace."""
    if len(times_s) < 2:
        return values.copy(), 1

    median_dt_s = float(np.median(np.diff(times_s)))
    window_samples = max(1, int(round((smoothing_ms / 1000.0) / median_dt_s)))
    if window_samples % 2 == 0:
        window_samples += 1
    return median_filter(values, size=window_samples, mode="nearest"), window_samples


def load_yaw_series(flight_number: int) -> Dict[str, object]:
    """Load the exact retained pose samples used by the yaw-rate metric."""
    bag_path = (
        WORKSPACE_ROOT
        / "data"
        / DATA_FOLDER
        / DATASET
        / f"flight_{flight_number}.bag"
    )
    if not bag_path.is_file():
        raise FileNotFoundError(f"Missing flight bag: {bag_path}")

    window_start_s, window_end_s = WINDOWS[DATASET][flight_number - 1]
    all_header_times = []
    raw_pose_samples = []
    with rosbag.Bag(str(bag_path), "r") as bag:
        for topic, message, _ in bag.read_messages(
            topics=[TWIST_TOPIC, POSE_TOPIC]
        ):
            header_time_s = message.header.stamp.to_sec()
            if not math.isfinite(header_time_s) or header_time_s <= 0.0:
                raise ValueError(
                    f"Invalid header timestamp {header_time_s!r} on {topic} in "
                    f"{bag_path}"
                )
            all_header_times.append(header_time_s)
            if topic == POSE_TOPIC:
                q = message.pose.orientation
                raw_pose_samples.append(
                    (header_time_s, normalize_quaternion((q.x, q.y, q.z, q.w)))
                )

    if not all_header_times:
        raise ValueError(f"No pose or twist messages found in {bag_path}")
    recording_start_s = min(all_header_times)
    pose_samples = [
        sample
        for sample in raw_pose_samples
        if window_start_s <= sample[0] - recording_start_s <= window_end_s
    ]
    retained, skipped, minimum_interval_s = retain_pose_samples(pose_samples)
    if len(retained) < 2:
        raise ValueError(f"Not enough retained pose samples in {bag_path}")

    header_times_s = np.array([time_s for time_s, _ in retained])
    wrapped_yaw_rad = np.array(
        [
            quaternion_to_roll_pitch_yaw_radians(*quaternion)[2]
            for _, quaternion in retained
        ]
    )
    unwrapped_yaw_rad = np.unwrap(wrapped_yaw_rad)
    unwrapped_yaw_deg = np.degrees(unwrapped_yaw_rad)
    relative_yaw_deg = unwrapped_yaw_deg - unwrapped_yaw_deg[0]
    time_from_window_start_s = (
        header_times_s - recording_start_s - window_start_s
    )

    (
        p99,
        _,
        _,
        _,
        median_window_samples,
        rate_samples,
        filtered_angle_samples,
    ) = yaw_rate_from_pose_samples(pose_samples)
    if p99 is None or not rate_samples or not filtered_angle_samples:
        raise ValueError(f"Not enough yaw-rate samples in {bag_path}")

    rate_header_times_s = np.array([time_s for time_s, _ in rate_samples])
    signed_yaw_rate_deg_s = np.array([rate for _, rate in rate_samples])
    rate_times_s = rate_header_times_s - recording_start_s - window_start_s
    filtered_angle_header_times_s = np.array(
        [time_s for time_s, _ in filtered_angle_samples]
    )
    filtered_yaw_rad = np.array(
        [yaw_rad for _, yaw_rad in filtered_angle_samples]
    )
    filtered_yaw_deg = np.degrees(filtered_yaw_rad)
    filtered_relative_yaw_deg = filtered_yaw_deg - filtered_yaw_deg[0]
    filtered_angle_times_s = (
        filtered_angle_header_times_s - recording_start_s - window_start_s
    )
    absolute_rates = np.abs(signed_yaw_rate_deg_s)

    return {
        "flight": flight_number,
        "window_start_s": window_start_s,
        "window_end_s": window_end_s,
        "angle_times_s": time_from_window_start_s,
        "unwrapped_yaw_rad": unwrapped_yaw_rad,
        "relative_yaw_deg": relative_yaw_deg,
        "filtered_angle_times_s": filtered_angle_times_s,
        "filtered_yaw_rad": filtered_yaw_rad,
        "filtered_relative_yaw_deg": filtered_relative_yaw_deg,
        "rate_times_s": rate_times_s,
        "signed_yaw_rate_deg_s": signed_yaw_rate_deg_s,
        "p99_absolute_yaw_rate_deg_s": p99,
        "maximum_absolute_yaw_rate_deg_s": float(absolute_rates.max()),
        "maximum_index": int(np.argmax(absolute_rates)),
        "median_window_samples": median_window_samples,
        "retained_count": len(retained),
        "skipped_count": skipped,
        "minimum_interval_s": minimum_interval_s,
    }


def plot_yaw_rate_subplot(
    axis: plt.Axes,
    result: Dict[str, object],
    *,
    color: str,
    smoothing_ms: float,
) -> Dict[str, float]:
    """Draw one flight's yaw-rate comparison subplot and return its key values."""
    rates = np.asarray(result["signed_yaw_rate_deg_s"], dtype=float)
    rate_times = np.asarray(result["rate_times_s"], dtype=float)
    displayed_rates, display_window_samples = smooth_for_display(
        rate_times, rates, smoothing_ms
    )
    maximum_index = int(result["maximum_index"])
    maximum_time = float(rate_times[maximum_index])
    maximum_signed_rate = float(rates[maximum_index])
    p99 = float(result["p99_absolute_yaw_rate_deg_s"])
    maximum = float(result["maximum_absolute_yaw_rate_deg_s"])
    flight_number = int(result["flight"])
    maximum_label_alignment = (
        "right" if maximum_time > 0.90 * WINDOW_DURATION_S else "center"
    )

    axis.plot(
        rate_times,
        rates,
        color=color,
        linewidth=1.2,
        alpha=0.40,
        label="Actual signed yaw rate used by metric",
    )
    axis.plot(
        rate_times,
        displayed_rates,
        color=color,
        linewidth=DATA_LINE_WIDTH,
        label=f"Smoothed yaw rate ({smoothing_ms:g} ms centered median)",
    )
    axis.axhline(
        p99,
        color="#e69f00",
        linewidth=2.2,
        linestyle="--",
        label=f"Actual ±P99 = {p99:.3f} deg/s",
    )
    axis.axhline(-p99, color="#e69f00", linewidth=2.2, linestyle="--")
    axis.axhline(
        maximum_signed_rate,
        color="#d62728",
        linewidth=3.2,
        linestyle="--",
        label=f"Actual |maximum| = {maximum:.3f} deg/s",
    )
    axis.axvline(
        maximum_time,
        color="#d62728",
        linewidth=2.0,
        linestyle=":",
    )
    axis.plot(
        maximum_time,
        maximum_signed_rate,
        marker="o",
        markersize=8,
        color="#d62728",
        zorder=5,
    )
    axis.set_title(
        f"AI Flight {flight_number}  |  source window "
        f"{float(result['window_start_s']):.2f}-{float(result['window_end_s']):.2f} s",
        fontsize=SUBPLOT_TITLE_FONT_SIZE,
        loc="left",
    )
    axis.set_xlim(0.0, WINDOW_DURATION_S)
    axis.set_ylim(-1.10 * maximum, 1.10 * maximum)
    axis.set_ylabel("Signed yaw rate (deg/s)", fontsize=LABEL_FONT_SIZE)
    axis.grid(which="major", alpha=0.30)
    axis.minorticks_on()
    axis.grid(which="minor", alpha=0.12)
    axis.tick_params(labelsize=TICK_FONT_SIZE)
    axis.plot(
        [maximum_time, maximum_time],
        [0.0, -0.018],
        transform=axis.get_xaxis_transform(),
        color="#d62728",
        linewidth=2,
        clip_on=False,
    )
    axis.text(
        maximum_time,
        -0.03,
        f"{maximum_time:.2f} s\nmax",
        transform=axis.get_xaxis_transform(),
        ha=maximum_label_alignment,
        va="top",
        color="#d62728",
        fontsize=TICK_FONT_SIZE,
        clip_on=False,
    )
    legend_location = (
        "upper right" if maximum_time < 0.5 * WINDOW_DURATION_S else "upper left"
    )
    axis.legend(loc=legend_location, fontsize=LEGEND_FONT_SIZE)
    return {
        "p99": p99,
        "maximum": maximum,
        "maximum_time": maximum_time,
        "display_window_samples": float(display_window_samples),
    }


def make_yaw_values_plot(
    results: Dict[int, Dict[str, object]],
    smoothing_ms: float,
    output_path: Path,
) -> Path:
    """Plot retained yaw samples immediately after angle unwrapping."""
    colors = {2: "#1769c2", 4: "#7b2cbf"}
    fig, axes = plt.subplots(2, 1, figsize=(18, 11), sharex=True)

    for axis, flight_number in zip(axes, FLIGHTS):
        result = results[flight_number]
        angle_times_s = np.asarray(result["angle_times_s"], dtype=float)
        yaw_rad = np.asarray(result["unwrapped_yaw_rad"], dtype=float)
        displayed_yaw_rad, _ = smooth_for_display(
            angle_times_s, yaw_rad, smoothing_ms
        )
        angle_min = float(yaw_rad.min())
        angle_max = float(yaw_rad.max())
        padding = max(0.03 * (angle_max - angle_min), 0.002)
        color = colors[flight_number]

        axis.plot(
            angle_times_s,
            yaw_rad,
            color=color,
            linewidth=1.2,
            alpha=0.40,
            label="Actual yaw values after unwrapping",
        )
        axis.plot(
            angle_times_s,
            displayed_yaw_rad,
            color=color,
            linewidth=DATA_LINE_WIDTH,
            label=f"Smoothed unwrapped yaw ({smoothing_ms:g} ms centered median)",
        )
        axis.set_title(
            f"AI Flight {flight_number}  |  source window "
            f"{float(result['window_start_s']):.2f}-{float(result['window_end_s']):.2f} s",
            fontsize=SUBPLOT_TITLE_FONT_SIZE,
            loc="left",
        )
        axis.set_xlim(0.0, WINDOW_DURATION_S)
        axis.set_ylim(angle_min - padding, angle_max + padding)
        axis.set_ylabel("Unwrapped yaw angle (rad)", fontsize=LABEL_FONT_SIZE)
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
        "7th October Yaw: Unwrapped Yaw Values",
        fontsize=FIGURE_TITLE_FONT_SIZE,
        fontweight="bold",
    )
    fig.subplots_adjust(
        top=0.91, bottom=0.09, left=0.10, right=0.98, hspace=0.22
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    print(f"Saved {output_path}")
    return output_path


def make_plot(
    output_path: Path,
    smoothing_ms: float = DEFAULT_SMOOTHING_MS,
    angle_output_path: Path = DEFAULT_ANGLE_OUTPUT,
) -> Path:
    if smoothing_ms <= 0:
        raise ValueError("Smoothing duration must be greater than zero")

    results = {flight: load_yaw_series(flight) for flight in FLIGHTS}
    make_yaw_values_plot(results, smoothing_ms, angle_output_path)
    colors = {2: "#1769c2", 4: "#7b2cbf"}
    fig, axes = plt.subplots(2, 1, figsize=(18, 11), sharex=True)

    for axis, flight_number in zip(axes, FLIGHTS):
        result = results[flight_number]
        summary = plot_yaw_rate_subplot(
            axis,
            result,
            color=colors[flight_number],
            smoothing_ms=smoothing_ms,
        )
        print(
            f"AI flight {flight_number}: P99 absolute yaw rate="
            f"{summary['p99']:.6f} deg/s, maximum={summary['maximum']:.6f} "
            f"deg/s at {summary['maximum_time']:.2f} s, "
            f"retained poses={result['retained_count']}, "
            f"skipped poses={result['skipped_count']}, "
            f"minimum interval={float(result['minimum_interval_s']):.9f} s, "
            f"metric median window={result['median_window_samples']} samples, "
            f"display median={int(summary['display_window_samples'])} samples"
        )

    axes[-1].set_xlabel(
        "Time from evaluation-window start, derived from pose header timestamp (s)",
        fontsize=LABEL_FONT_SIZE,
        labelpad=28,
    )
    fig.suptitle(
        "7th October Yaw: Signed Yaw Rate",
        fontsize=FIGURE_TITLE_FONT_SIZE,
        fontweight="bold",
    )
    fig.subplots_adjust(
        top=0.91, bottom=0.14, left=0.10, right=0.98, hspace=0.30
    )

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
        help=f"Unwrapped-yaw plot path (default: {DEFAULT_ANGLE_OUTPUT})",
    )
    args = parser.parse_args()
    make_plot(
        args.output.expanduser().resolve(),
        args.smoothing_ms,
        args.angle_output.expanduser().resolve(),
    )


if __name__ == "__main__":
    main()
