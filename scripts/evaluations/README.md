# Evaluation runners

Run one script per motion group from the workspace root. Each script contains only
its explicit AI/RAW time windows and input/output folder names. CLI handling,
validation, metrics, plots, and reports are shared by `evaluation_common.py`.

| Group | Script | Default durations |
|---|---|---|
| Low-Dynamic | `analyze_low.py` | 20 s |
| Medium | `analyze_medium.py` | 20 s |
| High | `analyze_high.py` | 20 s |
| Super-High | `analyze_super_high.py` | 20 s; AI only |
| Hover | `analyze_hover.py` | 20 s |
| RC Hovering | `analyze_rc_hovering.py` | 20 s |
| 2 October No-RC Hover | `analyze_2nd_oct_hover_no_rc.py` | 20 s; AI only |
| 2 October FB | `analyze_2nd_oct_fb.py` | 20 s; AI only |
| 2 October Yaw | `analyze_2nd_oct_yaw.py` | 20 s; AI only |
| 7 October Yaw | `analyze_7th_oct_yaw.py` | 20 s |
| Yaw | `analyze_yaw.py` | 20 s |

Use `--no-plots` for CSV-only output and `--help` for input/output path overrides.
