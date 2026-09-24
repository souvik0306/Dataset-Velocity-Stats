# Motion Metrics Workspace

## Layout

- `data/Low-Dynamic`, `data/Medium`, `data/High`, and `data/Super-High` contain the dynamic flight bags. Each has `AI/` and `RAW/`; `Super-High/RAW` is currently empty.
- Hover, yaw, and July datasets remain in their separate folders under `data/`.
- `results/` contains current CSVs, plots, and reports under the same group names as the runners.
- `archive/legacy_results/` preserves older mixed-group and July outputs.
- `scripts/evaluations/` contains the dataset runners; see [runner guide](scripts/evaluations/README.md).
- `scripts/utilities/` contains diagnostic and post-processing tools.
- `rosbag_motion_metrics.py` computes shared ROS bag metrics.
- `generate_motion_metric_report.py` creates shared metric plots and methodology text.

## Dynamic groups

| Group | AI bags | RAW bags | Runner | Results |
|---|---:|---:|---|---|
| Low-Dynamic | 4 | 5 | `scripts/evaluations/analyze_low.py` | `results/Low-Dynamic` |
| Medium | 3 | 3 | `scripts/evaluations/analyze_medium.py` | `results/Medium` |
| High | 4 | 4 | `scripts/evaluations/analyze_high.py` | `results/High` |
| Super-High | 4 | 0 | `scripts/evaluations/analyze_super_high.py` | `results/Super-High` |

Run from the workspace root, for example:

```bash
python3 scripts/evaluations/analyze_low.py --durations 20
python3 scripts/evaluations/analyze_medium.py --durations 20
python3 scripts/evaluations/analyze_high.py --durations 20
python3 scripts/evaluations/analyze_super_high.py --durations 20
```

Hover, RC hovering, and yaw use `scripts/evaluations/analyze_hover.py`,
`scripts/evaluations/analyze_rc_hovering.py`, and `scripts/evaluations/analyze_yaw.py`.
Each group has one runner with its AI and RAW timing configuration.
