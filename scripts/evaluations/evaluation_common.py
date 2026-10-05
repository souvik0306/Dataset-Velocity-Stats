"""Shared behavior for all motion-metric evaluation runners."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from generate_motion_metric_report import metric_methodology_lines, metric_slug, plot_metric  # noqa: E402
from rosbag_motion_metrics import (  # noqa: E402
    METRIC_DEFINITIONS,
    TWIST_TOPIC,
    compute_metrics_for_time_window,
    flatten_metric_rows,
    plot_absolute_pitch_rate_time_series,
    write_csv,
)

SELECTED_METRICS = (
    ("peak_horizontal_velocity_m_s", "peak_horizontal_velocity_m_s"),
    ("median_horizontal_velocity_m_s", "median_horizontal_velocity_m_s"),
    ("rms_horizontal_velocity_m_s", "rms_horizontal_velocity_m_s"),
    ("p95_horizontal_velocity_m_s", "p95_horizontal_velocity_m_s"),
    (
        "percentage_time_horizontal_velocity_below_0_1_m_s",
        "percentage_time_vxy_gt_below_0_1_m_s",
    ),
    ("maximum_absolute_pitch_rate_rad_s", "max_absolute_pitch_rate_rad_s"),
    ("p99_absolute_pitch_rate_rad_s", "p99_absolute_pitch_rate_rad_s"),
    ("pitch_range_deg", "pitch_range_deg"),
    ("maximum_absolute_pitch_angle_deg", "max_absolute_pitch_deg"),
    ("maximum_absolute_yaw_excursion_deg", "max_absolute_yaw_deg"),
    ("yaw_range_deg", "yaw_range_deg"),
    ("p99_absolute_yaw_rate_deg_s", "p99_absolute_yaw_rate_deg_s"),
)

EXTRA_METRIC_DEFINITIONS = (
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

EXTRA_METRIC_METHODS = (
    (
        "Median horizontal velocity",
        "`median(sqrt(vx^2 + vy^2))`",
        "cleaned Vicon GT twist X/Y",
    ),
    (
        "P95 horizontal velocity",
        "`P95(sqrt(vx^2 + vy^2))`",
        "cleaned Vicon GT twist X/Y",
    ),
    (
        "Percentage of time with horizontal velocity below 0.1 m/s",
        "`100 * count(vxy < 0.1) / count(vxy)`",
        "cleaned Vicon GT twist X/Y",
    ),
)

ALL_METRIC_DEFINITIONS = (*METRIC_DEFINITIONS, *EXTRA_METRIC_DEFINITIONS)


def find_flight_bags(dataset_dir: Path) -> List[Path]:
    """Return flight bags in natural filename order."""

    def natural_key(path: Path) -> List[str]:
        return [
            f"{int(part):020d}" if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", path.name)
        ]

    return sorted(dataset_dir.glob("flight_*.bag"), key=natural_key)


def validate_durations(durations: Iterable[int]) -> List[int]:
    normalized = sorted(set(durations))
    if not normalized or any(duration <= 0 for duration in normalized):
        raise ValueError("Durations must be positive whole seconds")
    return normalized


def analyze_dataset(
    root: Path,
    output_root: Path,
    dataset: str,
    duration_s: int,
    *,
    make_plots: bool,
    make_pitch_rate_time_series: bool = False,
    pitch_rate_time_series_title: str = "Absolute Pitch Rate",
    config: Optional[Dict[str, object]] = None,
    metric_definitions: Sequence[Dict[str, object]] = METRIC_DEFINITIONS,
) -> Dict[str, object]:
    if config is None:
        raise ValueError("Dataset configuration is required")
    dataset_dir = root / str(config["folder"])
    starts = tuple(float(value) for value in config["window_starts_s"])
    bags = find_flight_bags(dataset_dir)

    if len(bags) != len(starts):
        raise ValueError(
            f"Expected {len(starts)} bags in {dataset_dir}, but found {len(bags)}. "
            "The configured starts map to bags in sorted filename order."
        )

    output_dir = output_root / f"{duration_s}s" / dataset
    output_dir.mkdir(parents=True, exist_ok=True)

    wide_rows: List[Dict[str, object]] = []
    for flight_number, (bag_path, start_s) in enumerate(zip(bags, starts), start=1):
        end_s = start_s + duration_s
        print(
            f"[{duration_s}s {dataset} {flight_number}/{len(bags)}] "
            f"{bag_path.name}: {start_s:.2f}-{end_s:.2f} s"
        )
        wide_rows.append(
            compute_metrics_for_time_window(
                bag_path,
                dataset=dataset,
                window_key=f"{dataset.lower()}_flight_{flight_number}",
                window_start_s=start_s,
                window_end_s=end_s,
            )
        )

    csv_path = output_dir / "metrics.csv"
    write_csv(wide_rows, csv_path, wide=False, metric_definitions=metric_definitions)

    plot_paths = []
    if make_plots:
        plot_dir = output_dir / "plots"
        plot_dir.mkdir(parents=True, exist_ok=True)
        for stale_plot in plot_dir.glob("metric_*.png"):
            stale_plot.unlink()
        if make_pitch_rate_time_series:
            for stale_plot in plot_dir.glob("absolute_pitch_rate_time_series_flight_*.png"):
                stale_plot.unlink()
            for flight_number, row in enumerate(wide_rows, start=1):
                p99 = row["p99_absolute_pitch_rate_rad_s"]
                maximum = row["maximum_absolute_pitch_rate_rad_s"]
                if p99 is None or maximum is None:
                    continue
                plot_absolute_pitch_rate_time_series(
                    row["_pitch_rate_samples"],
                    p99_rad_s=float(p99),
                    maximum_rad_s=float(maximum),
                    window_duration_s=float(row["window_duration_s"]),
                    title=(
                        f"{pitch_rate_time_series_title} — "
                        f"{dataset} Flight {flight_number}"
                    ),
                    output_path=(
                        plot_dir
                        / f"absolute_pitch_rate_time_series_flight_{flight_number}.png"
                    ),
                )
        tidy_rows = flatten_metric_rows(wide_rows, metric_definitions)
        for metric_index, definition in enumerate(metric_definitions, start=1):
            metric_name = str(definition["metric"])
            plot_path = plot_dir / f"metric_{metric_index:02d}_{metric_slug(metric_name)}.png"
            plot_metric(
                dataset,
                metric_index,
                metric_name,
                tidy_rows,
                plot_path,
                highlighted=bool(definition.get("highlight", False)),
            )
            plot_paths.append((metric_index, metric_name, plot_path))

    return {
        "dataset": dataset,
        "duration_s": duration_s,
        "bag_count": len(bags),
        "csv_path": csv_path,
        "plot_paths": plot_paths,
        "wide_rows": wide_rows,
    }


def metric_averages(csv_path: Path) -> Dict[str, float]:
    values: Dict[str, List[float]] = {}
    with csv_path.open(newline="") as file_obj:
        for row in csv.DictReader(file_obj):
            if row["value"]:
                values.setdefault(row["metric"], []).append(float(row["value"]))
    return {metric: sum(items) / len(items) for metric, items in values.items() if items}


def write_comparison_csv(
    outputs: Sequence[Dict[str, object]],
    path: Path,
    metric_definitions: Sequence[Dict[str, object]] = METRIC_DEFINITIONS,
) -> None:
    by_dataset = {str(output["dataset"]): metric_averages(Path(output["csv_path"])) for output in outputs}
    with path.open("w", newline="") as file_obj:
        fieldnames = ["metric", "unit", "AI_average", "RAW_average", "RAW_minus_AI"]
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for definition in metric_definitions:
            metric = str(definition["metric"])
            ai_average = by_dataset.get("AI", {}).get(metric)
            raw_average = by_dataset.get("RAW", {}).get(metric)
            difference = None if ai_average is None or raw_average is None else raw_average - ai_average
            writer.writerow(
                {
                    "metric": metric,
                    "unit": definition["unit"],
                    "AI_average": "" if ai_average is None else f"{ai_average:.9g}",
                    "RAW_average": "" if raw_average is None else f"{raw_average:.9g}",
                    "RAW_minus_AI": "" if difference is None else f"{difference:.9g}",
                }
            )


def write_combined_csv(
    outputs: Sequence[Dict[str, object]],
    path: Path,
    metric_definitions: Sequence[Dict[str, object]] = METRIC_DEFINITIONS,
) -> None:
    rows: List[Dict[str, object]] = []
    for output in outputs:
        for wide_row in output["wide_rows"]:
            for row in flatten_metric_rows([wide_row], metric_definitions):
                rows.append(
                    {
                        "duration_label": f"{output['duration_s']}s",
                        "dataset": output["dataset"],
                        "bag_name": wide_row["bag_name"],
                        **row,
                    }
                )

    with path.open("w", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    outputs: Sequence[Dict[str, object]],
    output_root: Path,
    *,
    title: str = "High Motion Metrics",
    metric_definitions: Sequence[Dict[str, object]] = METRIC_DEFINITIONS,
    extra_metric_methods: Sequence[Tuple[str, str, str]] = (),
) -> Path:
    report_path = output_root / "metrics_report.md"
    lines = [
        f"# {title}",
        "",
        *metric_methodology_lines(extra_metric_methods),
        "Flights are evaluated over the configured time windows.",
        "Each configured start is Vicon cutoff + 5 s; each end is start + window duration.",
        "Velocity uses the cleaning and metric definitions in `rosbag_motion_metrics.py`.",
        "",
    ]

    for duration_s in sorted({int(output["duration_s"]) for output in outputs}):
        duration_outputs = [output for output in outputs if output["duration_s"] == duration_s]
        lines.extend([f"## {duration_s}-second window", ""])
        if {output["dataset"] for output in duration_outputs} == {"AI", "RAW"}:
            comparison_path = output_root / f"{duration_s}s" / "AI_RAW_average_comparison.csv"
            write_comparison_csv(duration_outputs, comparison_path, metric_definitions)
            lines.extend([f"[AI versus RAW averages]({comparison_path.relative_to(output_root).as_posix()})", ""])
        for output in duration_outputs:
            dataset = str(output["dataset"])
            csv_path = Path(output["csv_path"])
            selected_path = output_root / f"{duration_s}s" / dataset / "selected_metrics.csv"
            mapping_path = output_root / f"{duration_s}s" / dataset / "flight_bag_mapping.csv"
            lines.extend(
                [
                    f"### {dataset}",
                    "",
                    f"Flights processed: {output['bag_count']}  ",
                    f"[Metrics CSV]({csv_path.relative_to(output_root).as_posix()})",
                    "",
                ]
            )
            if selected_path.exists():
                lines.extend(
                    [f"[Selected metrics CSV]({selected_path.relative_to(output_root).as_posix()})", ""]
                )
            if mapping_path.exists():
                lines.extend(
                    [f"[Flight-to-bag mapping]({mapping_path.relative_to(output_root).as_posix()})", ""]
                )
            for _, metric_name, plot_path in output["plot_paths"]:
                relative_plot = Path(plot_path).relative_to(output_root).as_posix()
                lines.extend([f"#### {metric_name}", "", f"![{dataset} {metric_name}]({relative_plot})", ""])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def selected_metric_row(
    wide_row: Dict[str, object],
) -> Dict[str, object]:
    row = {"flight": str(wide_row["evaluation_window"]).replace("_", " ")}
    row.update({output_key: wide_row[source_key] for source_key, output_key in SELECTED_METRICS})
    return row


def write_selected_outputs(
    outputs: Sequence[Dict[str, object]],
    output_root: Path,
) -> None:
    for dataset in {str(output["dataset"]) for output in outputs}:
        combined_rows = []
        dataset_outputs = [output for output in outputs if output["dataset"] == dataset]
        for output in dataset_outputs:
            duration_s = int(output["duration_s"])
            rows = [
                selected_metric_row(row)
                for row in output["wide_rows"]
            ]
            combined_rows.extend({"duration_s": duration_s, **row} for row in rows)
            path = output_root / f"{duration_s}s" / dataset / "selected_metrics.csv"
            with path.open("w", newline="") as file_obj:
                writer = csv.DictWriter(file_obj, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)

            if dataset == "RAW":
                mapping = [
                    {
                        "flight": str(row["evaluation_window"]).replace("_", " "),
                        "bag_name": row["bag_name"],
                        "window_start_s": f"{float(row['window_start_s']):.2f}",
                        "window_end_s": f"{float(row['window_end_s']):.2f}",
                    }
                    for row in output["wide_rows"]
                ]
                mapping_path = path.with_name("flight_bag_mapping.csv")
                with mapping_path.open("w", newline="") as file_obj:
                    writer = csv.DictWriter(file_obj, fieldnames=list(mapping[0]))
                    writer.writeheader()
                    writer.writerows(mapping)

        suffix = "all_windows" if dataset == "AI" or len(dataset_outputs) > 1 else f"{dataset_outputs[0]['duration_s']}s"
        combined_path = output_root / f"{dataset}_selected_motion_metrics_{suffix}.csv"
        with combined_path.open("w", newline="") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=list(combined_rows[0]))
            writer.writeheader()
            writer.writerows(combined_rows)


def run_group(
    root: Path,
    output_root: Path,
    datasets: Dict[str, Dict[str, object]],
    durations: Iterable[int],
    *,
    make_plots: bool,
    title: str,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    title_suffix = " Motion Metrics"
    time_series_title = (
        title[: -len(title_suffix)] if title.endswith(title_suffix) else title
    )
    outputs = [
        analyze_dataset(
            root,
            output_root,
            dataset,
            duration_s,
            make_plots=make_plots,
            make_pitch_rate_time_series=True,
            pitch_rate_time_series_title=time_series_title,
            config=config,
            metric_definitions=ALL_METRIC_DEFINITIONS,
        )
        for duration_s in validate_durations(durations)
        for dataset, config in datasets.items()
        if duration_s in config.get("durations", durations)
    ]
    if not outputs:
        raise ValueError("No dataset is configured for the requested durations")
    combined_path = output_root / "all_windows_metrics.csv"
    write_combined_csv(outputs, combined_path, ALL_METRIC_DEFINITIONS)
    write_selected_outputs(outputs, output_root)
    report_path = write_report(
        outputs,
        output_root,
        title=title,
        metric_definitions=ALL_METRIC_DEFINITIONS,
        extra_metric_methods=EXTRA_METRIC_METHODS,
    )
    for output in outputs:
        if output["dataset"] == "RAW" and output["duration_s"] == 20:
            raw_csv = output_root / "RAW_all_metrics_20s.csv"
            write_combined_csv([output], raw_csv, ALL_METRIC_DEFINITIONS)
            raw_report = output_root / "RAW_20s_metrics_report.md"
            raw_report.write_text(
                f"# {title}: RAW 20-second metrics\n\n"
                + "\n".join(metric_methodology_lines(EXTRA_METRIC_METHODS))
                + "\n[Full metrics](20s/RAW/metrics.csv)  \n"
                + "[Selected metrics](20s/RAW/selected_metrics.csv)  \n"
                + "[Flight-to-bag mapping](20s/RAW/flight_bag_mapping.csv)\n",
                encoding="utf-8",
            )
    print(f"Wrote combined metrics: {combined_path}")
    print(f"Wrote report: {report_path}")


def _title_from_folder(output_folder: str) -> str:
    label = output_folder.replace("_", " ").replace("-", " ")
    label = re.sub(r"\s+", " ", label).strip()
    label = re.sub(r"^2nd Oct\b", "2 October", label, flags=re.IGNORECASE)
    return f"{label} Motion Metrics"


def _datasets_from_windows(
    root: Path,
    windows: Mapping[str, Sequence[Tuple[float, float]]],
) -> Tuple[Dict[str, Dict[str, object]], Tuple[int, ...]]:
    """Validate explicit windows and convert them to the shared runner format."""
    datasets: Dict[str, Dict[str, object]] = {}
    durations = set()

    for dataset, dataset_windows in windows.items():
        if not dataset_windows:
            raise ValueError(f"{dataset} must define at least one evaluation window")

        starts = []
        for flight_number, (start_s, end_s) in enumerate(dataset_windows, start=1):
            duration_s = float(end_s) - float(start_s)
            rounded_duration = round(duration_s)
            if duration_s <= 0 or abs(duration_s - rounded_duration) > 1e-9:
                raise ValueError(
                    f"{dataset} flight {flight_number} has invalid window "
                    f"{start_s:g}-{end_s:g} s"
                )
            starts.append(float(start_s))
            durations.add(rounded_duration)

        dataset_subdir = root / dataset
        folder = dataset if dataset_subdir.is_dir() else "."
        datasets[dataset] = {
            "folder": folder,
            "window_starts_s": tuple(starts),
        }

    if len(durations) != 1:
        raise ValueError(
            "All configured evaluation windows must use the same duration; "
            f"found {sorted(durations)} seconds"
        )
    return datasets, tuple(sorted(durations))


def run_evaluation(
    *,
    data_folder: str,
    output_folder: str,
    windows: Mapping[str, Sequence[Tuple[float, float]]],
) -> None:
    """Run a consistently configured evaluation from a minimal runner script."""
    default_root = WORKSPACE_ROOT / "data" / data_folder
    default_output = WORKSPACE_ROOT / "results" / output_folder
    title = _title_from_folder(output_folder)

    parser = argparse.ArgumentParser(description=f"Run {title}.")
    parser.add_argument("root", nargs="?", default=default_root)
    parser.add_argument("-o", "--output-dir", default=default_output)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    datasets, durations = _datasets_from_windows(root, windows)
    run_group(
        root,
        Path(args.output_dir).expanduser().resolve(),
        datasets,
        durations,
        make_plots=not args.no_plots,
        title=title,
    )
