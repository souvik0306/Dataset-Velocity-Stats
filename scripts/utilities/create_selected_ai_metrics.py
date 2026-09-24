#!/usr/bin/env python3
"""Create compact AI motion-metric CSVs from existing result folders."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List


METRIC_COLUMNS = {
    "Peak horizontal velocity": "peak_horizontal_velocity_m_s",
    "Maximum absolute pitch rate": "max_absolute_pitch_rate_rad_s",
    "P99 absolute pitch rate": "p99_absolute_pitch_rate_rad_s",
    "Maximum absolute pitch angle": "max_absolute_pitch_deg",
    "Peak absolute pitch angle": "max_absolute_pitch_deg",
}
OUTPUT_COLUMNS = [
    "flight",
    "peak_horizontal_velocity_m_s",
    "max_absolute_pitch_rate_rad_s",
    "p99_absolute_pitch_rate_rad_s",
    "pitch_range_deg",
    "max_absolute_pitch_deg",
]


def flight_number(name: str) -> int:
    match = re.search(r"flight_(\d+)$", name)
    return int(match.group(1)) if match else 0


def compact_rows(metrics_path: Path) -> List[Dict[str, str]]:
    """Convert a tidy AI metrics CSV to one row per flight."""
    flights: Dict[str, Dict[str, str]] = {}
    with metrics_path.open(newline="") as file_obj:
        for source_row in csv.DictReader(file_obj):
            window = source_row["evaluation_window"]
            row = flights.setdefault(window, {"flight": window.replace("_", " ")})
            metric = source_row["metric"]
            if metric in METRIC_COLUMNS:
                row[METRIC_COLUMNS[metric]] = source_row["value"]
            elif metric in ("Minimum pitch angle", "Minimum relative pitch angle"):
                row["_minimum_pitch_deg"] = source_row["value"]
            elif metric in ("Maximum pitch angle", "Maximum relative pitch angle"):
                row["_maximum_pitch_deg"] = source_row["value"]

    output_rows: List[Dict[str, str]] = []
    for window in sorted(flights, key=flight_number):
        row = flights[window]
        missing = [
            column
            for column in (*OUTPUT_COLUMNS[1:4], *OUTPUT_COLUMNS[5:], "_minimum_pitch_deg", "_maximum_pitch_deg")
            if not row.get(column)
        ]
        if missing:
            raise ValueError(f"Missing required values for {window} in {metrics_path}: {', '.join(missing)}")
        row["pitch_range_deg"] = f"{float(row['_maximum_pitch_deg']) - float(row['_minimum_pitch_deg']):.9g}"
        output_rows.append({column: row[column] for column in OUTPUT_COLUMNS})
    return output_rows


def duration_seconds(duration_dir: Path) -> int:
    match = re.fullmatch(r"(\d+)s", duration_dir.name)
    if not match:
        raise ValueError(f"Invalid duration directory name: {duration_dir.name}")
    return int(match.group(1))


def write_csv(path: Path, rows: List[Dict[str, str]], *, include_duration: bool = False) -> None:
    fieldnames = (["duration_s"] if include_duration else []) + OUTPUT_COLUMNS
    with path.open("w", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def process_result_directory(result_dir: Path) -> Path:
    """Write compact per-duration and combined AI CSVs under a result directory."""
    metric_paths = sorted(
        result_dir.glob("*s/AI/metrics.csv"),
        key=lambda path: duration_seconds(path.parent.parent),
    )
    if not metric_paths:
        raise FileNotFoundError(f"No */AI/metrics.csv files found under {result_dir}")

    combined_rows: List[Dict[str, str]] = []
    for metrics_path in metric_paths:
        duration_s = duration_seconds(metrics_path.parent.parent)
        rows = compact_rows(metrics_path)
        selected_path = metrics_path.with_name("selected_metrics.csv")
        write_csv(selected_path, rows)
        combined_rows.extend({"duration_s": str(duration_s), **row} for row in rows)
        print(f"Wrote {selected_path}")

    combined_path = result_dir / "AI_selected_motion_metrics_all_windows.csv"
    write_csv(combined_path, combined_rows, include_duration=True)
    print(f"Wrote {combined_path}")
    return combined_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create compact AI metric CSVs from result directories.")
    parser.add_argument("result_dirs", nargs="+", type=Path, help="Result directories containing */AI/metrics.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for result_dir in args.result_dirs:
        process_result_directory(result_dir.expanduser().resolve())


if __name__ == "__main__":
    main()
