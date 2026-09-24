#!/usr/bin/env python3
"""Plotting helpers for the timestamp-aware evaluation scripts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


VELOCITY_X_SOURCE = "`/vrpn_client_node/AIIMU1/twist/twist/linear/x`"
VELOCITY_Y_SOURCE = "`/vrpn_client_node/AIIMU1/twist/twist/linear/y`"
VELOCITY_SOURCE = f"{VELOCITY_X_SOURCE}<br>{VELOCITY_Y_SOURCE}"
ORIENTATION_SOURCE = (
    "`/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>"
    "`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>"
    "`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>"
    "`/vrpn_client_node/AIIMU1/pose/pose/orientation/w`"
)
ORIENTATION_RATE_SOURCE = (
    f"{ORIENTATION_SOURCE}<br>"
    "`/vrpn_client_node/AIIMU1/pose/header/stamp`"
)

METRIC_METHODS = (
    ("Peak horizontal velocity", "`max(sqrt(vx^2 + vy^2))`", VELOCITY_SOURCE),
    ("RMS horizontal velocity", "`sqrt(mean(vx^2 + vy^2))`", VELOCITY_SOURCE),
    ("Peak absolute X velocity", "`max(abs(vx))`", VELOCITY_X_SOURCE),
    ("Peak absolute Y velocity", "`max(abs(vy))`", VELOCITY_Y_SOURCE),
    (
        "Maximum absolute pitch rate",
        "`max(abs(SG_derivative(pitch_uniform, 11, 3)))`",
        ORIENTATION_RATE_SOURCE,
    ),
    (
        "P99 absolute pitch rate",
        "`P99(abs(SG_derivative(pitch_uniform, 11, 3)))`",
        ORIENTATION_RATE_SOURCE,
    ),
    ("Minimum roll angle", "`min(roll)`", ORIENTATION_SOURCE),
    ("Maximum roll angle", "`max(roll)`", ORIENTATION_SOURCE),
    ("Peak absolute roll angle", "`max(abs(roll))`", ORIENTATION_SOURCE),
    ("Minimum relative pitch angle", "`min(pitch(t) - pitch(0))`", ORIENTATION_SOURCE),
    ("Maximum relative pitch angle", "`max(pitch(t) - pitch(0))`", ORIENTATION_SOURCE),
    ("Pitch range", "`max(pitch(t)) - min(pitch(t))`", ORIENTATION_SOURCE),
    (
        "Maximum absolute pitch angle",
        "`max(abs(pitch(t)))`",
        ORIENTATION_SOURCE,
    ),
    (
        "Maximum absolute yaw excursion",
        "`max(abs(unwrap(yaw(t)) - unwrap(yaw(0))))`",
        ORIENTATION_SOURCE,
    ),
    (
        "Yaw range",
        "`max(unwrap(yaw(t))) - min(unwrap(yaw(t)))`",
        ORIENTATION_SOURCE,
    ),
)


def metric_methodology_lines(
    extra_methods: Sequence[Tuple[str, str, str]] = (),
) -> List[str]:
    """Return the shared report section documenting every metric."""
    lines = [
        "## Metric Formulas and Sources",
        "",
        "Velocity formulas use cleaned X/Y samples. For pitch rate, Vicon pose samples with intervals "
        "shorter than half the median positive pose interval are skipped. Pitch is interpolated "
        "onto a uniform grid at the retained median interval, then differentiated with an "
        "11-point cubic Savitzky-Golay filter (or the largest valid odd window for short series). "
        "Maximum and linearly interpolated P99 use absolute rates in rad/s. "
        "Roll, pitch, and yaw are derived from the Vicon quaternion and reported in degrees. "
        "In angle formulas, t=0 means the first Vicon pose sample inside the evaluation window, "
        "not the start of the bag. Angle extrema use all in-window pose samples without "
        "Savitzky-Golay smoothing or burst-sample rejection; those steps apply only to pitch rate. "
        "For the Yaw selected CSV, max_absolute_yaw_deg is the largest absolute unwrapped yaw "
        "change from the first in-window pose, and yaw_range_deg is the maximum minus minimum "
        "unwrapped yaw in the window. Unwrapping removes jumps at the ±180-degree boundary.",
        "",
        "| Metric | Formula | Source fields |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {metric} | {formula} | {source} |"
        for metric, formula, source in (*METRIC_METHODS, *extra_methods)
    )
    lines.append("")
    return lines


def flight_number_from_window(evaluation_window: str) -> int:
    match = re.search(r"flight_(\d+)$", evaluation_window)
    if not match:
        return 0
    return int(match.group(1))


def metric_slug(metric: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", metric.lower()).strip("_")
    return slug or "metric"


def plot_metric(
    dataset_folder: str,
    metric_index: int,
    metric_name: str,
    rows: List[Dict[str, object]],
    output_path: Path,
    highlighted: bool = False,
) -> None:
    metric_rows = [row for row in rows if row["metric"] == metric_name]
    metric_rows.sort(key=lambda row: flight_number_from_window(str(row["evaluation_window"])))
    labels = [str(row["evaluation_window"]).replace("_flight_", " ") for row in metric_rows]
    values = [float(row["value"]) for row in metric_rows]
    unit = str(metric_rows[0]["unit"]) if metric_rows else ""
    average = sum(values) / len(values)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6.25))
    bar_color = "#bda4e4" if highlighted else "#8fb9d4"
    edge_color = "#6b4d18" if highlighted else "#27485a"
    bars = ax.bar(labels, values, color=bar_color, edgecolor=edge_color, linewidth=0.8)
    ax.axhline(average, color="#b8322b", linestyle="--", linewidth=1.8, label=f"Average: {average:.3g} {unit}")
    ax.set_title(f"{dataset_folder}: Metric {metric_index} - {metric_name}", pad=14)
    ax.set_ylabel(unit, fontsize=18)
    ax.set_xlabel("Flight")
    ax.tick_params(axis="x", rotation=35, labelsize=15)
    ax.tick_params(axis="y", labelsize=15)
    for tick in ax.get_xticklabels():
        tick.set_ha("right")
    ax.grid(axis="y", alpha=0.22)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=7))
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        fontsize=15,
        frameon=True,
        facecolor="white",
        edgecolor="#cccccc",
        framealpha=0.95,
    )

    data_min = min(values + [average])
    data_max = max(values + [average])
    data_span = data_max - data_min
    if data_span == 0:
        data_span = abs(data_max) if data_max else 1.0
    scale = max(abs(data_min), abs(data_max), 1.0)
    padding = max(data_span * 0.35, scale * 0.15)
    if data_min >= 0:
        ax.set_ylim(0, data_max + padding)
    elif data_max <= 0:
        ax.set_ylim(data_min - padding, 0)
    else:
        ax.set_ylim(data_min - padding, data_max + padding)

    y_min, y_max = ax.get_ylim()
    y_span = y_max - y_min

    for bar, value in zip(bars, values):
        if value >= 0:
            label_y = value + y_span * 0.015
            va = "bottom"
        else:
            label_y = value - y_span * 0.015
            va = "top"
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            label_y,
            f"{value:.3g}",
            ha="center",
            va=va,
            fontsize=15,
            color="#111111",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "none", "alpha": 0.82},
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close()
