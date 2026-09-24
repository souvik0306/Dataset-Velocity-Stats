## ROS Bag Motion Metrics Report

### Processing Notes

- Metrics are computed only inside the evaluation windows from Vicon Cutoff+5s until Landing.
- Horizontal velocity is cleaned before peak/RMS calculation using x/y component bounds of -8 to +8 m/s, then computed from cleaned x/y components.
- X and Y velocity component plots use cleaned x/y values directly.
- Horizontal acceleration is cleaned before peak/RMS calculation using x/y component bounds of -8 to +8 m/s^2, then computed from cleaned x/y components.
- Savitzky-Golay smoothing is disabled for cleaned velocity and acceleration so peak metrics are not smoothed down.
- Angular rate magnitude uses raw x/y/z components.
- Roll and pitch are converted from ROS quaternion fields x/y/z/w to degrees.

### Formulas

- Horizontal velocity magnitude: `sqrt(vx^2 + vy^2)`
- Peak horizontal velocity: `max(sqrt(vx^2 + vy^2))`
- RMS horizontal velocity: `sqrt(mean(vx^2 + vy^2))`
- Peak absolute X velocity: `max(abs(vx))`
- Peak absolute Y velocity: `max(abs(vy))`
- Horizontal acceleration magnitude: `sqrt(ax^2 + ay^2)`
- Peak acceleration magnitude: `max(sqrt(ax^2 + ay^2))`
- RMS acceleration magnitude: `sqrt(mean(ax^2 + ay^2))`
- Angular rate magnitude: `sqrt(wx^2 + wy^2 + wz^2)`
- Peak angular rate magnitude: `max(sqrt(wx^2 + wy^2 + wz^2))`
- RMS angular rate magnitude: `sqrt(mean(wx^2 + wy^2 + wz^2))`
- Peak absolute roll angle: `max(abs(roll))`
- Peak absolute pitch angle: `max(abs(pitch))`

### Highlighted New Plots

- RMS horizontal velocity
- Peak absolute roll angle
- Peak absolute pitch angle

### UN

- Flights processed: 8

#### Metric 1: Peak horizontal velocity

![UN Peak horizontal velocity](UN/plots/metric_01_peak_horizontal_velocity.png)

#### Metric 2: RMS horizontal velocity - **NEW**

![UN RMS horizontal velocity](UN/plots/metric_02_rms_horizontal_velocity.png)

#### Metric 3: Peak absolute X velocity

![UN Peak absolute X velocity](UN/plots/metric_03_peak_absolute_x_velocity.png)

#### Metric 4: Peak absolute Y velocity

![UN Peak absolute Y velocity](UN/plots/metric_04_peak_absolute_y_velocity.png)

#### Metric 5: Peak acceleration magnitude

![UN Peak acceleration magnitude](UN/plots/metric_05_peak_acceleration_magnitude.png)

#### Metric 6: RMS acceleration magnitude

![UN RMS acceleration magnitude](UN/plots/metric_06_rms_acceleration_magnitude.png)

#### Metric 7: Peak angular rate magnitude

![UN Peak angular rate magnitude](UN/plots/metric_07_peak_angular_rate_magnitude.png)

#### Metric 8: RMS angular rate magnitude

![UN RMS angular rate magnitude](UN/plots/metric_08_rms_angular_rate_magnitude.png)

#### Metric 9: Minimum roll angle

![UN Minimum roll angle](UN/plots/metric_09_minimum_roll_angle.png)

#### Metric 10: Maximum roll angle

![UN Maximum roll angle](UN/plots/metric_10_maximum_roll_angle.png)

#### Metric 11: Peak absolute roll angle - **NEW**

![UN Peak absolute roll angle](UN/plots/metric_11_peak_absolute_roll_angle.png)

#### Metric 12: Minimum pitch angle

![UN Minimum pitch angle](UN/plots/metric_12_minimum_pitch_angle.png)

#### Metric 13: Maximum pitch angle

![UN Maximum pitch angle](UN/plots/metric_13_maximum_pitch_angle.png)

#### Metric 14: Peak absolute pitch angle - **NEW**

![UN Peak absolute pitch angle](UN/plots/metric_14_peak_absolute_pitch_angle.png)

### RAW

- Flights processed: 10

#### Metric 1: Peak horizontal velocity

![RAW Peak horizontal velocity](RAW/plots/metric_01_peak_horizontal_velocity.png)

#### Metric 2: RMS horizontal velocity - **NEW**

![RAW RMS horizontal velocity](RAW/plots/metric_02_rms_horizontal_velocity.png)

#### Metric 3: Peak absolute X velocity

![RAW Peak absolute X velocity](RAW/plots/metric_03_peak_absolute_x_velocity.png)

#### Metric 4: Peak absolute Y velocity

![RAW Peak absolute Y velocity](RAW/plots/metric_04_peak_absolute_y_velocity.png)

#### Metric 5: Peak acceleration magnitude

![RAW Peak acceleration magnitude](RAW/plots/metric_05_peak_acceleration_magnitude.png)

#### Metric 6: RMS acceleration magnitude

![RAW RMS acceleration magnitude](RAW/plots/metric_06_rms_acceleration_magnitude.png)

#### Metric 7: Peak angular rate magnitude

![RAW Peak angular rate magnitude](RAW/plots/metric_07_peak_angular_rate_magnitude.png)

#### Metric 8: RMS angular rate magnitude

![RAW RMS angular rate magnitude](RAW/plots/metric_08_rms_angular_rate_magnitude.png)

#### Metric 9: Minimum roll angle

![RAW Minimum roll angle](RAW/plots/metric_09_minimum_roll_angle.png)

#### Metric 10: Maximum roll angle

![RAW Maximum roll angle](RAW/plots/metric_10_maximum_roll_angle.png)

#### Metric 11: Peak absolute roll angle - **NEW**

![RAW Peak absolute roll angle](RAW/plots/metric_11_peak_absolute_roll_angle.png)

#### Metric 12: Minimum pitch angle

![RAW Minimum pitch angle](RAW/plots/metric_12_minimum_pitch_angle.png)

#### Metric 13: Maximum pitch angle

![RAW Maximum pitch angle](RAW/plots/metric_13_maximum_pitch_angle.png)

#### Metric 14: Peak absolute pitch angle - **NEW**

![RAW Peak absolute pitch angle](RAW/plots/metric_14_peak_absolute_pitch_angle.png)
