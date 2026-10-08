#!/usr/bin/env python3
"""Extract and plot 7 October yaw-flight EKF2 IMU process-noise values.

The evaluation windows are:

* AI flight 2: 31.34--51.34 s
* AI flight 4: 31.41--51.41 s

Window-only CSV files and raw/smoothed plots are written to
``7th_Oct_Yaw/output`` by default.  Plot time is rebased to 0--20 seconds.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pyulog import ULog


plt.rcParams.update(
    {
        "font.size": 14,
        "axes.titlesize": 16,
        "axes.labelsize": 14,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.fontsize": 14,
        "figure.titlesize": 18,
    }
)


TOPIC_NAME = "ekf2_imu_process_noise"
SMOOTHING_WINDOW_S = 1.0

EVALUATION_WINDOWS = {
    "AI flight 2": (31.34, 51.34),
    "AI flight 4": (31.41, 51.41),
}

# (CSV name, ULog array field, plot color)
CURVES: Sequence[Tuple[str, str, str]] = (
    ("ekf2_imu_process_noise/accel_var_uorb.01", "accel_var_uorb[1]", "#d62728"),
    ("ekf2_imu_process_noise/accel_var_uorb.00", "accel_var_uorb[0]", "#1f77b4"),
    ("ekf2_imu_process_noise/gyro_var_uorb.00", "gyro_var_uorb[0]", "#ff7f0e"),
    ("ekf2_imu_process_noise/gyro_var_uorb.01", "gyro_var_uorb[1]", "#f14cc1"),
)

ACCEL_X = CURVES[1]
ACCEL_Y = CURVES[0]
GYRO_X = CURVES[2]
GYRO_Y = CURVES[3]


@dataclass(frozen=True)
class LogSpec:
    label: str
    path: Path


@dataclass
class ExtractedLog:
    spec: LogSpec
    source_time_s: Optional[np.ndarray]
    values: Optional[Dict[str, np.ndarray]]
    error: Optional[str] = None


def extract_log(spec: LogSpec) -> ExtractedLog:
    """Read the selected topic and fields from one ULog."""
    if not spec.path.is_file():
        return ExtractedLog(spec, None, None, f"file not found: {spec.path}")

    try:
        ulog = ULog(str(spec.path), message_name_filter_list=[TOPIC_NAME])
        topic = next(
            (data for data in ulog.data_list if data.name == TOPIC_NAME and data.multi_id == 0),
            None,
        )
        if topic is None:
            return ExtractedLog(spec, None, None, f'topic "{TOPIC_NAME}" is not present')

        timestamp = np.asarray(topic.data["timestamp"], dtype=np.float64)
        if timestamp.size == 0:
            return ExtractedLog(spec, None, None, f'topic "{TOPIC_NAME}" has no samples')

        missing = [field for _, field, _ in CURVES if field not in topic.data]
        if missing:
            return ExtractedLog(
                spec,
                None,
                None,
                "missing field(s): " + ", ".join(missing),
            )

        source_time_s = (timestamp - timestamp[0]) * 1e-6
        values = {
            curve_name: np.asarray(topic.data[field], dtype=np.float64)
            for curve_name, field, _ in CURVES
        }
        return ExtractedLog(spec, source_time_s, values)
    except (KeyError, OSError, ValueError) as exc:
        return ExtractedLog(spec, None, None, str(exc))


def window_mask(extracted: ExtractedLog) -> np.ndarray:
    """Return the mask for this flight's configured 20-second window."""
    if extracted.source_time_s is None:
        return np.array([], dtype=bool)
    start_s, end_s = EVALUATION_WINDOWS[extracted.spec.label]
    return (extracted.source_time_s >= start_s) & (extracted.source_time_s <= end_s)


def write_window_csv(extracted: ExtractedLog, output_path: Path) -> None:
    """Write only the configured evaluation window to CSV."""
    if extracted.source_time_s is None or extracted.values is None:
        return

    start_s, _ = EVALUATION_WINDOWS[extracted.spec.label]
    mask = window_mask(extracted)
    source_time_s = extracted.source_time_s[mask]
    evaluation_time_s = source_time_s - start_s
    curve_names = [curve_name for curve_name, _, _ in CURVES]

    with output_path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["evaluation_time_s", "source_time_s", *curve_names])
        writer.writerows(
            zip(
                evaluation_time_s,
                source_time_s,
                *(extracted.values[curve_name][mask] for curve_name in curve_names),
            )
        )


def centered_moving_average(values: np.ndarray, window_samples: int) -> np.ndarray:
    """Return an edge-padded centered moving average with unchanged length."""
    if window_samples <= 1:
        return values.copy()
    left_pad = window_samples // 2
    right_pad = window_samples - 1 - left_pad
    padded = np.pad(values, (left_pad, right_pad), mode="edge")
    kernel = np.full(window_samples, 1.0 / window_samples)
    return np.convolve(padded, kernel, mode="valid")


def make_curve_plot(
    extracted_logs: Sequence[ExtractedLog],
    curve: Tuple[str, str, str],
    sensor_name: str,
    axis_name: str,
    output_path: Path,
    smoothing_window_s: Optional[float] = None,
) -> None:
    """Plot one sensor axis with flights 2 and 4 in separate subplots."""
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(14, 8),
        sharex=True,
        constrained_layout=True,
    )
    curve_name, _, color = curve

    for axis, extracted in zip(axes, extracted_logs):
        start_s, end_s = EVALUATION_WINDOWS[extracted.spec.label]
        axis.set_title(
            f"{extracted.spec.label} — evaluation window {start_s:.2f}–{end_s:.2f} s"
        )
        axis.set_ylabel("Value")
        axis.grid(True, alpha=0.3)
        axis.ticklabel_format(
            axis="y",
            style="sci",
            scilimits=(0, 0),
            useMathText=True,
        )
        axis.yaxis.get_offset_text().set_fontsize(14)

        if extracted.source_time_s is None or extracted.values is None:
            axis.text(
                0.5,
                0.5,
                "No data\n" + (extracted.error or "unknown error"),
                ha="center",
                va="center",
                transform=axis.transAxes,
                color="#8b0000",
            )
            continue

        mask = window_mask(extracted)
        plot_time = extracted.source_time_s[mask] - start_s
        plot_values = extracted.values[curve_name][mask]
        if plot_time.size == 0:
            raise ValueError(
                f"{extracted.spec.label} contains no samples in {start_s:.2f}–{end_s:.2f} s"
            )

        if smoothing_window_s is not None and plot_time.size > 1:
            sample_period_s = float(np.median(np.diff(plot_time)))
            window_samples = max(1, int(round(smoothing_window_s / sample_period_s)))
            plot_values = centered_moving_average(plot_values, window_samples)

        axis.plot(plot_time, plot_values, color=color, linewidth=2.2)
        axis.set_xlim(0.0, end_s - start_s)

    axes[-1].set_xlabel("Time within evaluation window (s)")
    title = f"PX4 EKF2 {sensor_name} {axis_name} process noise"
    if smoothing_window_s is not None:
        title += f" — {smoothing_window_s:g} s moving average"
    fig.suptitle(title)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    default_data_dir = script_dir / "7th_Oct_Yaw"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir,
        help="directory containing log_2.ulg and log_4.ulg (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_data_dir / "output",
        help="directory for CSV and PNG outputs (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = args.data_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    specs = (
        LogSpec("AI flight 2", data_dir / "log_2.ulg"),
        LogSpec("AI flight 4", data_dir / "log_4.ulg"),
    )
    extracted_logs = [extract_log(spec) for spec in specs]

    for extracted in extracted_logs:
        if extracted.error:
            print(f"WARNING: {extracted.spec.label}: {extracted.error}")
            continue
        csv_name = extracted.spec.label.lower().replace(" ", "_")
        csv_path = output_dir / f"{csv_name}_imu_process_noise_window.csv"
        write_window_csv(extracted, csv_path)
        print(f"Wrote {csv_path}")

    plot_specs = (
        ("accelerometer", "X", ACCEL_X, "ekf2_accel_x_process_noise.png"),
        ("accelerometer", "Y", ACCEL_Y, "ekf2_accel_y_process_noise.png"),
        ("gyroscope", "X", GYRO_X, "ekf2_gyro_x_process_noise.png"),
        ("gyroscope", "Y", GYRO_Y, "ekf2_gyro_y_process_noise.png"),
    )
    for sensor_name, axis_name, curve, filename in plot_specs:
        plot_path = output_dir / filename
        make_curve_plot(extracted_logs, curve, sensor_name, axis_name, plot_path)
        print(f"Wrote {plot_path}")

        smoothed_path = output_dir / filename.replace(".png", "_smoothed.png")
        make_curve_plot(
            extracted_logs,
            curve,
            sensor_name,
            axis_name,
            smoothed_path,
            smoothing_window_s=SMOOTHING_WINDOW_S,
        )
        print(f"Wrote {smoothed_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
