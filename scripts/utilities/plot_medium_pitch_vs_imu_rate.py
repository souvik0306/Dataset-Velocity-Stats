#!/usr/bin/env python3
"""Plot Vicon absolute pitch rate and IMU angular-rate magnitude for 9 Sept medium AI flights."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rosbag

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT))
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts" / "evaluations"))

from analyze_medium import DATASETS  # noqa: E402
from rosbag_motion_metrics import (  # noqa: E402
    POSE_TOPIC,
    normalize_quaternion,
    pitch_rate_from_pose_samples,
)

IMU_TOPIC = "/mavros/imu/data_raw"
BAG_DIR = WORKSPACE_ROOT / "data" / "Medium" / "AI"
OUTPUT_DIR = WORKSPACE_ROOT / "results" / "Medium" / "diagnostics"
WINDOW_STARTS_S = DATASETS["AI"]["window_starts_s"]
WINDOW_DURATION_S = 20


def smoothed(times: np.ndarray, values: np.ndarray, window: str = "150ms") -> np.ndarray:
    """Compute a rolling median for display only."""
    order = np.argsort(times)
    series = pd.Series(values[order], index=pd.to_datetime(times[order], unit="s"))
    result = series.rolling(window, center=True, min_periods=1).median().to_numpy()
    return result[np.argsort(order)]


def plot_flight(flight_number: int, bag_path: Path, start_s: float) -> Path:
    end_s = start_s + WINDOW_DURATION_S
    pose_samples = []
    imu_samples = []

    with rosbag.Bag(str(bag_path)) as bag:
        bag_start_s = bag.get_start_time()
        for topic, msg, bag_stamp in bag.read_messages(topics=[POSE_TOPIC, IMU_TOPIC]):
            bag_elapsed_s = bag_stamp.to_sec() - bag_start_s
            if not start_s <= bag_elapsed_s <= end_s:
                continue
            if topic == POSE_TOPIC:
                q = msg.pose.orientation
                pose_samples.append(
                    (msg.header.stamp.to_sec(), normalize_quaternion((q.x, q.y, q.z, q.w)))
                )
            else:
                w = msg.angular_velocity
                imu_time_s = (msg.header.stamp.to_sec() or bag_stamp.to_sec()) - bag_start_s
                imu_samples.append((imu_time_s, math.sqrt(w.x * w.x + w.y * w.y + w.z * w.z)))

    _, _, _, skipped, minimum_interval_s, pitch_samples = pitch_rate_from_pose_samples(pose_samples)
    if not pitch_samples or not imu_samples:
        raise ValueError(f"Missing Vicon pitch-rate or IMU samples in {bag_path}")
    assert minimum_interval_s is not None
    original_count = len(pose_samples)
    retained_count = original_count - skipped
    print(f"Flight {flight_number}:")
    print("Median Vicon dt:", 2 * minimum_interval_s)
    print("Minimum allowed dt:", minimum_interval_s)
    print("Original samples:", original_count)
    print("Retained samples:", retained_count)
    print("Skipped samples:", skipped)

    pitch_time = np.array([time_s - bag_start_s for time_s, _ in pitch_samples])
    pitch_rate = np.array([rate for _, rate in pitch_samples])
    imu_time, imu_rate = (np.array(values) for values in zip(*imu_samples))

    fig, axis = plt.subplots(figsize=(18, 9))
    axis.plot(pitch_time, pitch_rate, color="#1b6edb", alpha=0.20, linewidth=1.5)
    axis.plot(
        pitch_time, smoothed(pitch_time, pitch_rate, "75ms"),
        color="#1b6edb", linewidth=4.5,
        label=f"Vicon SG absolute pitch rate (raw max {pitch_rate.max():.2f} rad/s)",
    )
    axis.plot(imu_time, imu_rate, color="#2baf0ac8", alpha=0.24, linewidth=1.8)
    axis.plot(
        imu_time, smoothed(imu_time, imu_rate), color="#2baf0ac8", linewidth=4.5,
        label=f"MAVROS IMU angular-rate magnitude (raw max {imu_rate.max():.2f} rad/s)",
    )
    axis.set_ylabel("Rate (rad/s)", fontsize=22)
    axis.set_xlim(start_s - 1, end_s + 1)
    axis.set_xlabel("Seconds since bag start (message header time)", fontsize=22)
    axis.tick_params(labelsize=18)
    axis.grid(alpha=0.3)
    axis.legend(fontsize=18, loc="upper right")
    fig.suptitle(
        f"Medium AI flight {flight_number}: pitch rate vs IMU angular rate\n"
        f"Evaluation window {start_s:.2f}–{end_s:.2f} s (bag time)",
        fontsize=26,
    )
    fig.subplots_adjust(top=0.81, bottom=0.19, left=0.10, right=0.98)
    fig.text(
        0.10,
        0.035,
        "Vicon: 11-point cubic SG derivative after resampling. Faint lines: calculated rates. "
        "Solid lines: display medians (Vicon 75 ms; IMU 150 ms).\n"
        f"Vicon skips {skipped} burst samples (minimum interval {minimum_interval_s * 1000:.2f} ms). "
        "IMU is the 3-axis angular-rate magnitude.",
        fontsize=15,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"pitch_rate_vs_imu_angular_rate_ai_flight_{flight_number}.png"
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    print(f"Flight {flight_number}: Vicon pitch max {pitch_rate.max():.3f} rad/s, "
          f"IMU max {imu_rate.max():.3f} rad/s -> {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flights", nargs="+", type=int, help="Flight numbers; defaults to all three")
    args = parser.parse_args()
    bags = sorted(BAG_DIR.glob("flight_*.bag"))
    if len(bags) != len(WINDOW_STARTS_S):
        parser.error(f"Expected {len(WINDOW_STARTS_S)} bags in {BAG_DIR}, found {len(bags)}")
    flights = args.flights or range(1, len(bags) + 1)
    for flight_number in flights:
        if not 1 <= flight_number <= len(bags):
            parser.error(f"Flight {flight_number} is not configured")
        plot_flight(flight_number, bags[flight_number - 1], WINDOW_STARTS_S[flight_number - 1])


if __name__ == "__main__":
    main()
