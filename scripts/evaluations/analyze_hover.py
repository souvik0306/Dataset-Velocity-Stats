#!/usr/bin/env python3
"""Run Hover Motion Metrics for the configured AI and RAW flight windows."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation_common import run_group
from rosbag_motion_metrics import TWIST_TOPIC


# Window starts are seconds since bag start, in sorted bag filename order.
DATASETS = {
    "AI": {
        "folder": "AI",
        "window_starts_s": (55.15, 54.92, 42.06),
    },
    "RAW": {
        "folder": "RAW",
        "window_starts_s": (44.32, 39.75, 30.71),
    },
}

DEFAULT_DURATIONS_S = (20,)

# Hover-specific additions to the compact selected-metrics CSV. RMS and P99
# pitch rate are already computed by the shared pipeline; listing RMS here
# makes it available beside the new hover metrics.
HOVER_EXTRA_SELECTED_METRICS = (
    ("median_horizontal_velocity_m_s", "median_horizontal_velocity_m_s"),
    ("rms_horizontal_velocity_m_s", "rms_horizontal_velocity_m_s"),
    ("p95_horizontal_velocity_m_s", "p95_horizontal_velocity_m_s"),
    (
        "percentage_time_horizontal_velocity_below_0_1_m_s",
        "percentage_time_vxy_gt_below_0_1_m_s",
    ),
)

HOVER_EXTRA_METRIC_DEFINITIONS = (
    {
        "metric": "Median horizontal velocity",
        "value_key": "median_horizontal_velocity_m_s",
        "count_key": "velocity_sample_count",
        "unit": "m/s",
        "topic": TWIST_TOPIC,
        "fields": "cleaned twist.linear.x, cleaned twist.linear.y",
    },
    {
        "metric": "P95 horizontal velocity",
        "value_key": "p95_horizontal_velocity_m_s",
        "count_key": "velocity_sample_count",
        "unit": "m/s",
        "topic": TWIST_TOPIC,
        "fields": "cleaned twist.linear.x, cleaned twist.linear.y",
    },
    {
        "metric": "Percentage of time with horizontal velocity below 0.1 m/s",
        "value_key": "percentage_time_horizontal_velocity_below_0_1_m_s",
        "count_key": "velocity_sample_count",
        "unit": "%",
        "topic": TWIST_TOPIC,
        "fields": "cleaned twist.linear.x, cleaned twist.linear.y",
    },
)

HOVER_EXTRA_METRIC_METHODS = (
    ("Median horizontal velocity", "`median(sqrt(vx^2 + vy^2))`", "cleaned Vicon GT twist X/Y"),
    ("P95 horizontal velocity", "`P95(sqrt(vx^2 + vy^2))`", "cleaned Vicon GT twist X/Y"),
    (
        "Percentage of time with horizontal velocity below 0.1 m/s",
        "`100 * count(vxy < 0.1) / count(vxy)`",
        "cleaned Vicon GT twist X/Y",
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default='data/9th_Sept_AI_Hover_Rosbags')
    parser.add_argument("-o", "--output-dir", default='results/Hover')
    parser.add_argument("--durations", nargs="+", type=int, choices=DEFAULT_DURATIONS_S,
                        default=list(DEFAULT_DURATIONS_S), metavar="SECONDS")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    run_group(Path(args.root).expanduser().resolve(),
              Path(args.output_dir).expanduser().resolve(),
              DATASETS, args.durations, make_plots=not args.no_plots,
              title='Hover Motion Metrics', include_yaw=False,
              extra_selected_metrics=HOVER_EXTRA_SELECTED_METRICS,
              extra_metric_definitions=HOVER_EXTRA_METRIC_DEFINITIONS,
              extra_metric_methods=HOVER_EXTRA_METRIC_METHODS)


if __name__ == "__main__":
    main()
