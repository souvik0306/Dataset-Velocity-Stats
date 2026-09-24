# Super-High Motion Metrics

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

Flights are evaluated over the configured time windows.
Each configured start is Vicon cutoff + 5 s; each end is start + window duration.
Velocity uses the cleaning and metric definitions in `rosbag_motion_metrics.py`.

## 10-second window

### AI

Flights processed: 4  
[Metrics CSV](10s/AI/metrics.csv)

[Selected metrics CSV](10s/AI/selected_metrics.csv)

#### Peak horizontal velocity

![AI Peak horizontal velocity](10s/AI/plots/metric_01_peak_horizontal_velocity.png)

#### RMS horizontal velocity

![AI RMS horizontal velocity](10s/AI/plots/metric_02_rms_horizontal_velocity.png)

#### Peak absolute X velocity

![AI Peak absolute X velocity](10s/AI/plots/metric_03_peak_absolute_x_velocity.png)

#### Peak absolute Y velocity

![AI Peak absolute Y velocity](10s/AI/plots/metric_04_peak_absolute_y_velocity.png)

#### Maximum absolute pitch rate

![AI Maximum absolute pitch rate](10s/AI/plots/metric_05_maximum_absolute_pitch_rate.png)

#### P99 absolute pitch rate

![AI P99 absolute pitch rate](10s/AI/plots/metric_06_p99_absolute_pitch_rate.png)

#### Minimum roll angle

![AI Minimum roll angle](10s/AI/plots/metric_07_minimum_roll_angle.png)

#### Maximum roll angle

![AI Maximum roll angle](10s/AI/plots/metric_08_maximum_roll_angle.png)

#### Peak absolute roll angle

![AI Peak absolute roll angle](10s/AI/plots/metric_09_peak_absolute_roll_angle.png)

#### Minimum relative pitch angle

![AI Minimum relative pitch angle](10s/AI/plots/metric_10_minimum_relative_pitch_angle.png)

#### Maximum relative pitch angle

![AI Maximum relative pitch angle](10s/AI/plots/metric_11_maximum_relative_pitch_angle.png)

#### Maximum absolute pitch angle

![AI Maximum absolute pitch angle](10s/AI/plots/metric_12_maximum_absolute_pitch_angle.png)

#### Maximum absolute yaw excursion

![AI Maximum absolute yaw excursion](10s/AI/plots/metric_13_maximum_absolute_yaw_excursion.png)

#### Yaw range

![AI Yaw range](10s/AI/plots/metric_14_yaw_range.png)

## 20-second window

### AI

Flights processed: 4  
[Metrics CSV](20s/AI/metrics.csv)

[Selected metrics CSV](20s/AI/selected_metrics.csv)

#### Peak horizontal velocity

![AI Peak horizontal velocity](20s/AI/plots/metric_01_peak_horizontal_velocity.png)

#### RMS horizontal velocity

![AI RMS horizontal velocity](20s/AI/plots/metric_02_rms_horizontal_velocity.png)

#### Peak absolute X velocity

![AI Peak absolute X velocity](20s/AI/plots/metric_03_peak_absolute_x_velocity.png)

#### Peak absolute Y velocity

![AI Peak absolute Y velocity](20s/AI/plots/metric_04_peak_absolute_y_velocity.png)

#### Maximum absolute pitch rate

![AI Maximum absolute pitch rate](20s/AI/plots/metric_05_maximum_absolute_pitch_rate.png)

#### P99 absolute pitch rate

![AI P99 absolute pitch rate](20s/AI/plots/metric_06_p99_absolute_pitch_rate.png)

#### Minimum roll angle

![AI Minimum roll angle](20s/AI/plots/metric_07_minimum_roll_angle.png)

#### Maximum roll angle

![AI Maximum roll angle](20s/AI/plots/metric_08_maximum_roll_angle.png)

#### Peak absolute roll angle

![AI Peak absolute roll angle](20s/AI/plots/metric_09_peak_absolute_roll_angle.png)

#### Minimum relative pitch angle

![AI Minimum relative pitch angle](20s/AI/plots/metric_10_minimum_relative_pitch_angle.png)

#### Maximum relative pitch angle

![AI Maximum relative pitch angle](20s/AI/plots/metric_11_maximum_relative_pitch_angle.png)

#### Maximum absolute pitch angle

![AI Maximum absolute pitch angle](20s/AI/plots/metric_12_maximum_absolute_pitch_angle.png)

#### Maximum absolute yaw excursion

![AI Maximum absolute yaw excursion](20s/AI/plots/metric_13_maximum_absolute_yaw_excursion.png)

#### Yaw range

![AI Yaw range](20s/AI/plots/metric_14_yaw_range.png)

## 30-second window

### AI

Flights processed: 4  
[Metrics CSV](30s/AI/metrics.csv)

[Selected metrics CSV](30s/AI/selected_metrics.csv)

#### Peak horizontal velocity

![AI Peak horizontal velocity](30s/AI/plots/metric_01_peak_horizontal_velocity.png)

#### RMS horizontal velocity

![AI RMS horizontal velocity](30s/AI/plots/metric_02_rms_horizontal_velocity.png)

#### Peak absolute X velocity

![AI Peak absolute X velocity](30s/AI/plots/metric_03_peak_absolute_x_velocity.png)

#### Peak absolute Y velocity

![AI Peak absolute Y velocity](30s/AI/plots/metric_04_peak_absolute_y_velocity.png)

#### Maximum absolute pitch rate

![AI Maximum absolute pitch rate](30s/AI/plots/metric_05_maximum_absolute_pitch_rate.png)

#### P99 absolute pitch rate

![AI P99 absolute pitch rate](30s/AI/plots/metric_06_p99_absolute_pitch_rate.png)

#### Minimum roll angle

![AI Minimum roll angle](30s/AI/plots/metric_07_minimum_roll_angle.png)

#### Maximum roll angle

![AI Maximum roll angle](30s/AI/plots/metric_08_maximum_roll_angle.png)

#### Peak absolute roll angle

![AI Peak absolute roll angle](30s/AI/plots/metric_09_peak_absolute_roll_angle.png)

#### Minimum relative pitch angle

![AI Minimum relative pitch angle](30s/AI/plots/metric_10_minimum_relative_pitch_angle.png)

#### Maximum relative pitch angle

![AI Maximum relative pitch angle](30s/AI/plots/metric_11_maximum_relative_pitch_angle.png)

#### Maximum absolute pitch angle

![AI Maximum absolute pitch angle](30s/AI/plots/metric_12_maximum_absolute_pitch_angle.png)

#### Maximum absolute yaw excursion

![AI Maximum absolute yaw excursion](30s/AI/plots/metric_13_maximum_absolute_yaw_excursion.png)

#### Yaw range

![AI Yaw range](30s/AI/plots/metric_14_yaw_range.png)
