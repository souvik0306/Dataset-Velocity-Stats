#!/usr/bin/env python3
"""Plot the yaw-rate metric inputs for 7 October AI flights 2 and 5."""

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
FLIGHTS = (2, 5)
DEFAULT_OUTPUT = (
    WORKSPACE_ROOT
    / "results"
    / OUTPUT_FOLDER
    / "20s"
    / DATASET
    / "plots"
    / "yaw_rate_flights_2_and_5.png"
)


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
    unwrapped_yaw_deg = np.degrees(np.unwrap(wrapped_yaw_rad))
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
    filtered_yaw_deg = np.degrees(
        np.array([yaw_rad for _, yaw_rad in filtered_angle_samples])
    )
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
        "relative_yaw_deg": relative_yaw_deg,
        "filtered_angle_times_s": filtered_angle_times_s,
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


def make_plot(output_path: Path) -> Path:
    results = {flight: load_yaw_series(flight) for flight in FLIGHTS}
    colors = {2: "#1769c2", 5: "#7b2cbf"}
    fig, axes = plt.subplots(2, 2, figsize=(19, 11), sharex="col")

    for row, flight_number in enumerate(FLIGHTS):
        result = results[flight_number]
        color = colors[flight_number]
        angle_axis, rate_axis = axes[row]

        angle_axis.plot(
            result["angle_times_s"],
            result["relative_yaw_deg"],
            color=color,
            linewidth=1.0,
            alpha=0.35,
            label="Raw unwrapped yaw",
        )
        angle_axis.plot(
            result["filtered_angle_times_s"],
            result["filtered_relative_yaw_deg"],
            color=color,
            linewidth=2.2,
            label=(
                f"Filtered yaw ({result['median_window_samples']}-sample "
                "centered median)"
            ),
        )
        angle_axis.axhline(0.0, color="#555555", linewidth=1.0, alpha=0.6)
        angle_axis.set_ylabel("Yaw excursion (deg)", fontsize=13)
        angle_axis.set_title(
            f"AI Flight {flight_number}: raw and filtered yaw angle",
            fontsize=15,
            loc="left",
        )
        angle_axis.legend(loc="upper left", fontsize=10)

        rates = result["signed_yaw_rate_deg_s"]
        rate_times = result["rate_times_s"]
        maximum_index = result["maximum_index"]
        maximum_time = float(rate_times[maximum_index])
        maximum_signed_rate = float(rates[maximum_index])
        p99 = float(result["p99_absolute_yaw_rate_deg_s"])
        maximum = float(result["maximum_absolute_yaw_rate_deg_s"])

        rate_axis.plot(
            rate_times,
            rates,
            color=color,
            linewidth=1.4,
            label="Filtered signed yaw rate",
        )
        rate_axis.axhline(
            p99,
            color="#e69f00",
            linewidth=1.8,
            linestyle="--",
            label=f"±P99 absolute rate = {p99:.1f} deg/s",
        )
        rate_axis.axhline(
            -p99,
            color="#e69f00",
            linewidth=1.8,
            linestyle="--",
        )
        rate_axis.scatter(
            [maximum_time],
            [maximum_signed_rate],
            color="#d62728",
            s=55,
            zorder=5,
            label=f"Maximum absolute rate = {maximum:.1f} deg/s",
        )
        rate_axis.axvline(
            maximum_time, color="#d62728", linewidth=1.4, linestyle=":"
        )
        rate_axis.set_ylabel("Yaw rate (deg/s)", fontsize=13)
        rate_axis.set_title(
            f"AI Flight {flight_number}: exact samples used by metric",
            fontsize=15,
            loc="left",
        )
        rate_axis.legend(loc="upper right", fontsize=10)

        for axis in (angle_axis, rate_axis):
            axis.set_xlim(0.0, 20.0)
            axis.grid(which="major", alpha=0.30)
            axis.minorticks_on()
            axis.grid(which="minor", alpha=0.12)
            axis.tick_params(labelsize=11)

        print(
            f"AI flight {flight_number}: P99 absolute yaw rate={p99:.6f} deg/s, "
            f"maximum={maximum:.6f} deg/s at {maximum_time:.6f} s, "
            f"retained poses={result['retained_count']}, "
            f"skipped poses={result['skipped_count']}, "
            f"minimum interval={float(result['minimum_interval_s']):.9f} s, "
            f"median window={result['median_window_samples']} samples"
        )

    axes[-1, 0].set_xlabel("Time from evaluation-window start (s)", fontsize=13)
    axes[-1, 1].set_xlabel("Time from evaluation-window start (s)", fontsize=13)
    fig.suptitle(
        "7 October Yaw: AI Flights 2 and 5",
        fontsize=20,
        fontweight="bold",
    )
    fig.subplots_adjust(
        top=0.91, bottom=0.08, left=0.07, right=0.98, hspace=0.30, wspace=0.18
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    print(f"Saved {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output PNG path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    make_plot(args.output.expanduser().resolve())


if __name__ == "__main__":
    main()
