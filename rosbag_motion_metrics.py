#!/usr/bin/env python3
"""Compute flight motion metrics from ROS1 bag files.

DATA SOURCE PATHS
-----------------
Horizontal velocity:
- X: /vrpn_client_node/AIIMU1/twist/twist/linear/x
- Y: /vrpn_client_node/AIIMU1/twist/twist/linear/y

Vicon GT orientation used for roll, pitch, and yaw:
- X: /vrpn_client_node/AIIMU1/pose/pose/orientation/x
- Y: /vrpn_client_node/AIIMU1/pose/pose/orientation/y
- Z: /vrpn_client_node/AIIMU1/pose/pose/orientation/z
- W: /vrpn_client_node/AIIMU1/pose/pose/orientation/w
- Timestamp: /vrpn_client_node/AIIMU1/pose/header/stamp

The Vicon quaternion fields are converted to Euler roll, pitch, and yaw.
Pitch rate is derived from retained Vicon pitch samples after rejecting burst intervals,
resampling at the median interval, and applying an 11-point cubic Savitzky-Golay derivative.
Yaw rate is derived by unwrapping retained Vicon yaw samples and taking finite differences.

Metrics:
- peak/mean/median/RMS/P95 horizontal velocity magnitude and the percentage of
  samples below 0.1 m/s from /vrpn_client_node/AIIMU1/twist
- maximum/P99 absolute pitch rate derived from retained Vicon pose samples
- P99 absolute yaw rate in degrees/s derived from retained Vicon pose samples
- roll, relative pitch, absolute pitch angle, and unwrapped relative yaw from /vrpn_client_node/AIIMU1/pose
"""

from __future__ import annotations

import csv
import importlib.util
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import rosbag
from scipy.signal import savgol_filter


TWIST_TOPIC = "/vrpn_client_node/AIIMU1/twist"
POSE_TOPIC = "/vrpn_client_node/AIIMU1/pose"
CLEANER_PATH = Path(__file__).with_name("3_vel_csv_dataset_cleaner.py")
CLEANER_WINDOW = 9
CLEANER_FILL = "linear"
VELOCITY_COMPONENT_BOUNDS = (-8.0, 8.0)

METRIC_DEFINITIONS = [
    {
        "metric": "Peak horizontal velocity",
        "value_key": "peak_horizontal_velocity_m_s",
        "count_key": "velocity_sample_count",
        "unit": "m/s",
        "topic": TWIST_TOPIC,
        "fields": "cleaned twist.linear.x, cleaned twist.linear.y",
    },
    {
        "metric": "RMS horizontal velocity",
        "value_key": "rms_horizontal_velocity_m_s",
        "count_key": "velocity_sample_count",
        "unit": "m/s",
        "topic": TWIST_TOPIC,
        "fields": "cleaned twist.linear.x, cleaned twist.linear.y",
        "highlight": True,
    },
    {
        "metric": "Peak absolute X velocity",
        "value_key": "peak_absolute_x_velocity_m_s",
        "count_key": "velocity_x_sample_count",
        "unit": "m/s",
        "topic": TWIST_TOPIC,
        "fields": "cleaned twist.linear.x",
    },
    {
        "metric": "Peak absolute Y velocity",
        "value_key": "peak_absolute_y_velocity_m_s",
        "count_key": "velocity_y_sample_count",
        "unit": "m/s",
        "topic": TWIST_TOPIC,
        "fields": "cleaned twist.linear.y",
    },
    {
        "metric": "Maximum absolute pitch rate",
        "value_key": "maximum_absolute_pitch_rate_rad_s",
        "count_key": "pitch_rate_sample_count",
        "unit": "rad/s",
        "topic": POSE_TOPIC,
        "fields": "pose.orientation quaternion -> pitch; retained header.stamp resampling; 11-point cubic Savitzky-Golay derivative",
    },
    {
        "metric": "P99 absolute pitch rate",
        "value_key": "p99_absolute_pitch_rate_rad_s",
        "count_key": "pitch_rate_sample_count",
        "unit": "rad/s",
        "topic": POSE_TOPIC,
        "fields": "pose.orientation quaternion -> pitch; retained header.stamp resampling; 11-point cubic Savitzky-Golay derivative",
    },
    {
        "metric": "P99 absolute yaw rate",
        "value_key": "p99_absolute_yaw_rate_deg_s",
        "count_key": "yaw_rate_sample_count",
        "unit": "degrees/s",
        "topic": POSE_TOPIC,
        "fields": "pose.orientation quaternion -> unwrapped yaw; retained header.stamp finite-difference derivative",
    },
    {
        "metric": "Minimum roll angle",
        "value_key": "minimum_roll_deg",
        "count_key": "pose_sample_count",
        "unit": "degrees",
        "topic": POSE_TOPIC,
        "fields": "pose.orientation quaternion -> roll",
    },
    {
        "metric": "Maximum roll angle",
        "value_key": "maximum_roll_deg",
        "count_key": "pose_sample_count",
        "unit": "degrees",
        "topic": POSE_TOPIC,
        "fields": "pose.orientation quaternion -> roll",
    },
    {
        "metric": "Peak absolute roll angle",
        "value_key": "peak_absolute_roll_deg",
        "count_key": "pose_sample_count",
        "unit": "degrees",
        "topic": POSE_TOPIC,
        "fields": "pose.orientation quaternion -> roll",
        "highlight": True,
    },
    {
        "metric": "Minimum relative pitch angle",
        "value_key": "minimum_pitch_deg",
        "count_key": "pose_sample_count",
        "unit": "degrees",
        "topic": POSE_TOPIC,
        "fields": "pose.orientation quaternion -> pitch, relative to initial pitch",
    },
    {
        "metric": "Maximum relative pitch angle",
        "value_key": "maximum_pitch_deg",
        "count_key": "pose_sample_count",
        "unit": "degrees",
        "topic": POSE_TOPIC,
        "fields": "pose.orientation quaternion -> pitch, relative to initial pitch",
    },
    {
        "metric": "Maximum absolute pitch angle",
        "value_key": "maximum_absolute_pitch_angle_deg",
        "count_key": "pose_sample_count",
        "unit": "degrees",
        "topic": POSE_TOPIC,
        "fields": "abs(pitch from pose.orientation quaternion)",
        "highlight": True,
    },
    {
        "metric": "Maximum absolute yaw excursion",
        "value_key": "maximum_absolute_yaw_excursion_deg",
        "count_key": "pose_sample_count",
        "unit": "degrees",
        "topic": POSE_TOPIC,
        "fields": "abs(unwrapped yaw - initial unwrapped yaw)",
    },
    {
        "metric": "Yaw range",
        "value_key": "yaw_range_deg",
        "count_key": "pose_sample_count",
        "unit": "degrees",
        "topic": POSE_TOPIC,
        "fields": "maximum relative unwrapped yaw - minimum relative unwrapped yaw",
    },
]


@dataclass
class MagnitudeStats:
    count: int = 0
    peak: Optional[float] = None
    total: float = 0.0
    total_square: float = 0.0
    # Keep cleaned magnitudes so percentile-based hover metrics use the same
    # samples as the existing peak and RMS metrics.
    values: List[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        self.count += 1
        self.peak = value if self.peak is None else max(self.peak, value)
        self.total += value
        self.total_square += value * value
        self.values.append(value)

    @property
    def mean(self) -> Optional[float]:
        return None if self.count == 0 else self.total / self.count

    @property
    def rms(self) -> Optional[float]:
        return None if self.count == 0 else math.sqrt(self.total_square / self.count)

    @property
    def median(self) -> Optional[float]:
        return None if self.count == 0 else float(np.median(self.values))

    @property
    def p95(self) -> Optional[float]:
        return None if self.count == 0 else float(np.percentile(self.values, 95))

    def percentage_below(self, threshold: float) -> Optional[float]:
        if self.count == 0:
            return None
        return 100.0 * sum(value < threshold for value in self.values) / self.count


@dataclass
class ComponentStats:
    count: int = 0
    peak_abs: Optional[float] = None
    total: float = 0.0

    def add(self, value: float) -> None:
        self.count += 1
        abs_value = abs(value)
        self.peak_abs = abs_value if self.peak_abs is None else max(self.peak_abs, abs_value)
        self.total += value

    @property
    def mean(self) -> Optional[float]:
        return None if self.count == 0 else self.total / self.count


@dataclass
class RangeStats:
    count: int = 0
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    peak_abs: Optional[float] = None

    def add(self, value: float) -> None:
        self.count += 1
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)
        abs_value = abs(value)
        self.peak_abs = abs_value if self.peak_abs is None else max(self.peak_abs, abs_value)

    @property
    def range(self) -> Optional[float]:
        if self.minimum is None or self.maximum is None:
            return None
        return self.maximum - self.minimum


def load_velocity_cleaner():
    spec = importlib.util.spec_from_file_location("vel_csv_dataset_cleaner", CLEANER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load velocity cleaner from {CLEANER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clean_xy_samples(
    samples: List[Tuple[float, float, float]],
    component_bounds: Optional[Tuple[Optional[float], Optional[float]]],
) -> Tuple[pd.DataFrame, Dict[str, int], Dict[str, int]]:
    if not samples:
        return pd.DataFrame(columns=["time", "vel_x", "vel_y"]), {}, {}

    cleaner = load_velocity_cleaner()
    df = pd.DataFrame(samples, columns=["time", "vel_x", "vel_y"])
    bound_overrides = []
    if component_bounds is not None:
        lower, upper = component_bounds
        bound_overrides.append(("vel_*", lower, upper))
    else:
        bound_overrides.append(("vel_*", None, None))

    return cleaner.clean_dataframe(
        df,
        window=CLEANER_WINDOW,
        median_tol_override=None,
        bound_overrides=bound_overrides,
        fill=CLEANER_FILL,
        savgol_window=None,
    )


def stats_from_cleaned_xy(cleaned: pd.DataFrame) -> Tuple[MagnitudeStats, ComponentStats, ComponentStats]:
    magnitude = MagnitudeStats()
    x_stats = ComponentStats()
    y_stats = ComponentStats()
    for x, y in zip(cleaned["vel_x"], cleaned["vel_y"]):
        if pd.isna(x) or pd.isna(y):
            continue
        x = float(x)
        y = float(y)
        magnitude.add(math.sqrt(x * x + y * y))
        x_stats.add(x)
        y_stats.add(y)
    return magnitude, x_stats, y_stats


def quaternion_to_roll_pitch_yaw_radians(
    x: float, y: float, z: float, w: float
) -> tuple[float, float, float]:
    """Convert a ROS geometry quaternion to roll, pitch, and yaw in radians."""
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        pitch = math.copysign(math.pi / 2.0, sinp)
    else:
        pitch = math.asin(sinp)

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def normalize_quaternion(
    quaternion: Tuple[float, float, float, float],
) -> Tuple[float, float, float, float]:
    """Normalize an XYZW quaternion."""
    norm = math.sqrt(sum(component * component for component in quaternion))
    if norm <= 1e-12:
        raise ValueError("Cannot normalize a zero-length quaternion")
    return tuple(component / norm for component in quaternion)


def pitch_rate_from_pose_samples(
    samples: List[Tuple[float, Tuple[float, float, float, float]]],
) -> Tuple[Optional[float], Optional[float], int, int, Optional[float], List[Tuple[float, float]]]:
    """Return maximum and P99 absolute pitch rate using the Vicon SG derivative."""
    retained, skipped, minimum_interval_s = retain_pose_samples(samples)
    if len(retained) < 3:
        return None, None, 0, skipped, minimum_interval_s, []

    times = np.array([time_s for time_s, _ in retained])
    pitches = np.array([
        quaternion_to_roll_pitch_yaw_radians(*quaternion)[1]
        for _, quaternion in retained
    ])
    dt = float(np.median(np.diff(times)))
    uniform_times = times[0] + np.arange(int((times[-1] - times[0]) / dt) + 1) * dt
    uniform_pitch = np.interp(uniform_times, times, pitches)

    window_length = min(11, len(uniform_times) if len(uniform_times) % 2 else len(uniform_times) - 1)
    polyorder = min(3, window_length - 1)
    absolute_rates = np.abs(savgol_filter(
        uniform_pitch,
        window_length=window_length,
        polyorder=polyorder,
        deriv=1,
        delta=dt,
        mode="interp",
    ))
    rate_samples = list(zip(uniform_times.tolist(), absolute_rates.tolist()))
    return (
        float(absolute_rates.max()),
        float(np.percentile(absolute_rates, 99)),
        len(rate_samples),
        skipped,
        minimum_interval_s,
        rate_samples,
    )


def plot_absolute_pitch_rate_time_series(
    rate_samples: Sequence[Tuple[float, float]],
    *,
    p99_rad_s: float,
    maximum_rad_s: float,
    window_duration_s: float,
    title: str,
    output_path: Path,
) -> Path:
    """Plot absolute pitch rate with its P99 and maximum reference lines."""
    if not rate_samples:
        raise ValueError("Cannot plot an empty pitch-rate time series")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sample_time = np.array([time_s for time_s, _ in rate_samples])
    time_from_window_start = sample_time - sample_time[0]
    absolute_pitch_rate = np.array([rate for _, rate in rate_samples])

    fig, axis = plt.subplots(figsize=(14, 7.5))
    axis.plot(
        time_from_window_start,
        absolute_pitch_rate,
        color="#1f77b4",
        linewidth=1.6,
        label="Absolute pitch rate",
    )
    axis.axhline(
        p99_rad_s,
        color="#e69f00",
        linewidth=2.2,
        linestyle="--",
        label=f"P99 ≈ {p99_rad_s:.1f} rad/s",
    )
    axis.axhline(
        maximum_rad_s,
        color="#d62728",
        linewidth=2.2,
        linestyle=":",
        label=f"Maximum = {maximum_rad_s:.1f} rad/s",
    )
    axis.set_xlim(0.0, window_duration_s)
    axis.set_ylim(bottom=0.0)
    axis.set_xlabel("Time from evaluation-window start (s)", fontsize=14)
    axis.set_ylabel("Absolute pitch rate (rad/s)", fontsize=14)
    axis.set_title(title, fontsize=18)
    axis.grid(alpha=0.3)
    axis.tick_params(labelsize=12)
    axis.legend(loc="upper right", fontsize=12)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def retain_pose_samples(
    samples: List[Tuple[float, Tuple[float, float, float, float]]],
) -> Tuple[
    List[Tuple[float, Tuple[float, float, float, float]]], int, Optional[float]
]:
    """Reject timestamp bursts using half the median positive sample interval."""
    intervals = [
        current[0] - previous[0]
        for previous, current in zip(samples, samples[1:])
        if current[0] > previous[0]
    ]
    if not intervals:
        return [], 0, None

    minimum_interval_s = 0.5 * float(np.median(intervals))
    retained = [samples[0]]
    skipped = 0
    for sample in samples[1:]:
        if sample[0] - retained[-1][0] < minimum_interval_s:
            skipped += 1
        else:
            retained.append(sample)
    return retained, skipped, minimum_interval_s


def p99_absolute_yaw_rate_from_pose_samples(
    samples: List[Tuple[float, Tuple[float, float, float, float]]],
) -> Tuple[Optional[float], int]:
    """Return P99 absolute finite-difference yaw rate and its sample count."""
    retained, _, _ = retain_pose_samples(samples)
    if len(retained) < 2:
        return None, 0

    times = np.array([time_s for time_s, _ in retained])
    yaw_rad = np.array([
        quaternion_to_roll_pitch_yaw_radians(*quaternion)[2]
        for _, quaternion in retained
    ])
    yaw_rate_deg_s = np.degrees(np.diff(np.unwrap(yaw_rad)) / np.diff(times))
    return float(np.percentile(np.abs(yaw_rate_deg_s), 99)), len(yaw_rate_deg_s)


def unwrap_angle_radians(current: float, previous: float, previous_unwrapped: float) -> float:
    """Continue a wrapped angle series across the +/-pi boundary."""
    delta = (current - previous + math.pi) % (2.0 * math.pi) - math.pi
    return previous_unwrapped + delta


def _fmt(value: Optional[float]) -> str:
    return "" if value is None else f"{value:.9g}"


def compute_metrics_for_time_window(
    bag_path: Path,
    *,
    dataset: str,
    window_key: str,
    window_start_s: float,
    window_end_s: float,
) -> Dict[str, object]:
    """Compute metrics for one bag inside an explicitly supplied time window."""
    if window_start_s < 0:
        raise ValueError(f"Window start must be non-negative, got {window_start_s}")
    if window_end_s <= window_start_s:
        raise ValueError(f"Invalid evaluation window for {window_key}: {window_start_s} to {window_end_s}")

    velocity_samples: List[Tuple[float, float, float]] = []
    pose_samples: List[Tuple[float, Tuple[float, float, float, float]]] = []
    roll = RangeStats()
    pitch = RangeStats()
    absolute_pitch = RangeStats()
    yaw = RangeStats()
    initial_pitch_rad: Optional[float] = None
    initial_yaw_unwrapped_rad: Optional[float] = None
    previous_yaw_rad: Optional[float] = None
    previous_yaw_unwrapped_rad: Optional[float] = None

    bag_path = bag_path.expanduser()
    with rosbag.Bag(str(bag_path), "r") as bag:
        start_time = bag.get_start_time()
        end_time = bag.get_end_time()

        for topic, msg, stamp in bag.read_messages(topics=[TWIST_TOPIC, POSE_TOPIC]):
            elapsed_s = stamp.to_sec() - start_time
            if elapsed_s < window_start_s or elapsed_s > window_end_s:
                continue

            if topic == TWIST_TOPIC:
                x = msg.twist.linear.x
                y = msg.twist.linear.y
                velocity_samples.append((elapsed_s, x, y))
            elif topic == POSE_TOPIC:
                q = msg.pose.orientation
                current_quaternion = normalize_quaternion((q.x, q.y, q.z, q.w))
                pose_time_s = msg.header.stamp.to_sec()
                pose_samples.append((pose_time_s, current_quaternion))

                roll_rad, pitch_rad, yaw_rad = quaternion_to_roll_pitch_yaw_radians(
                    *current_quaternion
                )
                roll.add(math.degrees(roll_rad))

                if initial_pitch_rad is None:
                    initial_pitch_rad = pitch_rad
                pitch.add(math.degrees(pitch_rad - initial_pitch_rad))
                absolute_pitch.add(math.degrees(pitch_rad))

                if previous_yaw_rad is None:
                    yaw_unwrapped_rad = yaw_rad
                    initial_yaw_unwrapped_rad = yaw_unwrapped_rad
                else:
                    assert previous_yaw_unwrapped_rad is not None
                    yaw_unwrapped_rad = unwrap_angle_radians(
                        yaw_rad, previous_yaw_rad, previous_yaw_unwrapped_rad
                    )
                assert initial_yaw_unwrapped_rad is not None
                yaw.add(math.degrees(yaw_unwrapped_rad - initial_yaw_unwrapped_rad))
                previous_yaw_rad = yaw_rad
                previous_yaw_unwrapped_rad = yaw_unwrapped_rad

    maximum_pitch_rate, p99_pitch_rate, pitch_rate_count, pitch_rate_skipped, pitch_rate_minimum_interval_s, _pitch_rate_samples = (
        pitch_rate_from_pose_samples(pose_samples)
    )
    p99_absolute_yaw_rate_deg_s, yaw_rate_sample_count = (
        p99_absolute_yaw_rate_from_pose_samples(pose_samples)
    )

    cleaned_velocity, velocity_pruned_counts, velocity_filtered_counts = clean_xy_samples(
        velocity_samples,
        component_bounds=VELOCITY_COMPONENT_BOUNDS,
    )
    velocity, velocity_x, velocity_y = stats_from_cleaned_xy(cleaned_velocity)

    return {
        "bag_path": str(bag_path),
        "bag_name": bag_path.name,
        "dataset": dataset,
        
        "evaluation_window": window_key,
        "window_start_s": window_start_s,
        "window_end_s": window_end_s,
        "window_duration_s": window_end_s - window_start_s,
        "start_time_epoch": start_time,
        "end_time_epoch": end_time,
        "duration_s": end_time - start_time,
        
        "velocity_sample_count": velocity.count,
        "velocity_raw_sample_count": len(velocity_samples),
        "velocity_pruned_sample_count": sum(velocity_pruned_counts.values()),
        "velocity_filtered_sample_count": sum(velocity_filtered_counts.values()),
        
        "peak_horizontal_velocity_m_s": velocity.peak,
        "mean_horizontal_velocity_m_s": velocity.mean,
        "median_horizontal_velocity_m_s": velocity.median,
        "rms_horizontal_velocity_m_s": velocity.rms,
        "p95_horizontal_velocity_m_s": velocity.p95,
        "percentage_time_horizontal_velocity_below_0_1_m_s": velocity.percentage_below(0.1),
        
        "velocity_x_sample_count": velocity_x.count,
        "peak_absolute_x_velocity_m_s": velocity_x.peak_abs,
        "mean_x_velocity_m_s": velocity_x.mean,
        "velocity_y_sample_count": velocity_y.count,
        "peak_absolute_y_velocity_m_s": velocity_y.peak_abs,
        "mean_y_velocity_m_s": velocity_y.mean,
        
        "pitch_rate_sample_count": pitch_rate_count,
        "pitch_rate_skipped_pose_sample_count": pitch_rate_skipped,
        "pitch_rate_minimum_interval_s": pitch_rate_minimum_interval_s,
        "maximum_absolute_pitch_rate_rad_s": maximum_pitch_rate,
        "p99_absolute_pitch_rate_rad_s": p99_pitch_rate,
        "_pitch_rate_samples": _pitch_rate_samples,
        "yaw_rate_sample_count": yaw_rate_sample_count,
        "p99_absolute_yaw_rate_deg_s": p99_absolute_yaw_rate_deg_s,
        
        "pose_sample_count": roll.count,
        "minimum_roll_deg": roll.minimum,
        "maximum_roll_deg": roll.maximum,
        "roll_range_deg": roll.range,
        "peak_absolute_roll_deg": roll.peak_abs,
        
        "minimum_pitch_deg": pitch.minimum,
        "maximum_pitch_deg": pitch.maximum,
        "pitch_range_deg": pitch.range,
        "maximum_absolute_pitch_angle_deg": absolute_pitch.peak_abs,
        
        "minimum_yaw_deg": yaw.minimum,
        "maximum_yaw_deg": yaw.maximum,
        "yaw_range_deg": yaw.range,
        "maximum_absolute_yaw_excursion_deg": yaw.peak_abs,
    }


def metric_rows(
    wide_row: Dict[str, object],
    metric_definitions: Sequence[Dict[str, object]] = METRIC_DEFINITIONS,
) -> List[Dict[str, object]]:
    """Reshape one bag's metrics into one row per metric."""
    bag_columns = {
        "evaluation_window": wide_row["evaluation_window"],
        "window_start_s": wide_row["window_start_s"],
        "window_end_s": wide_row["window_end_s"],
        "window_duration_s": wide_row["window_duration_s"],
    }

    rows = []
    for definition in metric_definitions:
        rows.append(
            {
                **bag_columns,
                "metric": definition["metric"],
                "value": wide_row[definition["value_key"]],
                "unit": definition["unit"],
                "sample_count": wide_row[definition["count_key"]],
                "topic": definition["topic"],
                "fields": definition["fields"],
            }
        )
    return rows


def flatten_metric_rows(
    wide_rows: Iterable[Dict[str, object]],
    metric_definitions: Sequence[Dict[str, object]] = METRIC_DEFINITIONS,
) -> List[Dict[str, object]]:
    rows = []
    for wide_row in wide_rows:
        rows.extend(metric_rows(wide_row, metric_definitions))
    return rows


def write_csv(
    rows: Iterable[Dict[str, object]],
    output_path: Path,
    wide: bool = False,
    metric_definitions: Sequence[Dict[str, object]] = METRIC_DEFINITIONS,
) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError("No rows to write.")

    output_rows = rows if wide else flatten_metric_rows(rows, metric_definitions)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(output_rows[0].keys())
    with output_path.open("w", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow({key: _fmt(value) if isinstance(value, float) else value for key, value in row.items()})
