# Evaluation runners

Run one script per motion group from the workspace root. Each script contains the configured AI and RAW start times and writes to `results/<group>/`.

| Group | Script | Default durations |
|---|---|---|
| Low-Dynamic | `analyze_low.py` | 20 s |
| Medium | `analyze_medium.py` | 20 s |
| High | `analyze_high.py` | 20 s |
| Super-High | `analyze_super_high.py` | 20 s; AI only |
| Hover | `analyze_hover.py` | 20 s |
| RC Hovering | `analyze_rc_hovering.py` | 20 s |
| Yaw | `analyze_yaw.py` | 20 s |

Use `--durations 20` to run only a 20-second window, `--no-plots` for CSV-only output, and `--help` for path overrides.
