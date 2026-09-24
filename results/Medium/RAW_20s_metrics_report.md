# Medium Motion Metrics: RAW 20-second metrics

## Metric Formulas and Sources

Velocity formulas use cleaned X/Y samples. For pitch rate, Vicon pose samples with intervals shorter than half the median positive pose interval are skipped. Pitch is interpolated onto a uniform grid at the retained median interval, then differentiated with an 11-point cubic Savitzky-Golay filter (or the largest valid odd window for short series). Maximum and linearly interpolated P99 use absolute rates in rad/s. Roll, pitch, and yaw are derived from the Vicon quaternion and reported in degrees. In angle formulas, t=0 means the first Vicon pose sample inside the evaluation window, not the start of the bag. Angle extrema use all in-window pose samples without Savitzky-Golay smoothing or burst-sample rejection; those steps apply only to pitch rate. For the Yaw selected CSV, max_absolute_yaw_deg is the largest absolute unwrapped yaw change from the first in-window pose, and yaw_range_deg is the maximum minus minimum unwrapped yaw in the window. Unwrapping removes jumps at the ±180-degree boundary.

| Metric | Formula | Source fields |
|---|---|---|
| Peak horizontal velocity | `max(sqrt(vx^2 + vy^2))` | `/vrpn_client_node/AIIMU1/twist/twist/linear/x`<br>`/vrpn_client_node/AIIMU1/twist/twist/linear/y` |
| RMS horizontal velocity | `sqrt(mean(vx^2 + vy^2))` | `/vrpn_client_node/AIIMU1/twist/twist/linear/x`<br>`/vrpn_client_node/AIIMU1/twist/twist/linear/y` |
| Peak absolute X velocity | `max(abs(vx))` | `/vrpn_client_node/AIIMU1/twist/twist/linear/x` |
| Peak absolute Y velocity | `max(abs(vy))` | `/vrpn_client_node/AIIMU1/twist/twist/linear/y` |
| Maximum absolute pitch rate | `max(abs(SG_derivative(pitch_uniform, 11, 3)))` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w`<br>`/vrpn_client_node/AIIMU1/pose/header/stamp` |
| P99 absolute pitch rate | `P99(abs(SG_derivative(pitch_uniform, 11, 3)))` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w`<br>`/vrpn_client_node/AIIMU1/pose/header/stamp` |
| Minimum roll angle | `min(roll)` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w` |
| Maximum roll angle | `max(roll)` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w` |
| Peak absolute roll angle | `max(abs(roll))` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w` |
| Minimum relative pitch angle | `min(pitch(t) - pitch(0))` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w` |
| Maximum relative pitch angle | `max(pitch(t) - pitch(0))` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w` |
| Pitch range | `max(pitch(t)) - min(pitch(t))` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w` |
| Maximum absolute pitch angle | `max(abs(pitch(t)))` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w` |
| Maximum absolute yaw excursion | `max(abs(unwrap(yaw(t)) - unwrap(yaw(0))))` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w` |
| Yaw range | `max(unwrap(yaw(t))) - min(unwrap(yaw(t)))` | `/vrpn_client_node/AIIMU1/pose/pose/orientation/x`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/y`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/z`<br>`/vrpn_client_node/AIIMU1/pose/pose/orientation/w` |

[Full metrics](20s/RAW/metrics.csv)  
[Selected metrics](20s/RAW/selected_metrics.csv)  
[Flight-to-bag mapping](20s/RAW/flight_bag_mapping.csv)
