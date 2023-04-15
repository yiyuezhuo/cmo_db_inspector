
import gradio as gr

class ReferencesTab:
    def __init__(self):
        pass

    def build(self):
        gr.Markdown(r"""

This app uses following radar equationb:

$$
\begin{align*}
R_{max} &= \min(\R_{max,p},\R_{max,PRF}) \\
R_{max,p} &= \left( \frac{P_s G^2\lambda^2\sigma C_1}{P_{e_{min}}(4\pi)^3 C_2} \right)^{1/4} \\
R_{max,RPF} &= \frac{c}{2PRF} \\
G &= \frac{4 \pi}{\theta\phi} \\
\lambda &= \frac{c}{f}
\end{align*}
$$

- $R_{max}$: Maximum range to detect a target.
- $P_s$: Transmitted power. DB attribute: `DataSensor.RadarPeakPower`
- $\lambda$: wavelength
- $c$: the speed of light. $300,000,000 m/s$
- $f$: Frequency. Derived from `DataSensorFrequencySearchAndTrack.Frequency` and `EnumSensorFrequency.Description`
- $\sigma$: RCS (Radar cross-section), which is `1m^2` for the reference calulation. The value can be found in `DataAircraftSignatures`.
- PRF: Pulse Repetition Frequency, pps (Pulse per second). `DataSensor.RadarPRF`
- $\theta$: Horizontal beam-width (radius). `DataSensor.RadarHorizontalBeamwidth` (degree to radians)
- $\phi$: Vertical beam-width (radians). `DataSensor.RadarVerticalBeamwidth` (degree to radians)
- $C_1$: Constant. `DataSensor.RadarProcessingGainLoss` (db to linear)
- $C_2$: Constant. `DataSensor.RadarSystemNoiseLevel` (db to linear)
- $P_{e_{min}}$: Minimum energy to be detected. (10^{-15}). (Someone suggest $10^{-12}$ but I found $10^{-15}$ to be more close to CMO result).


Harpoon IV Signatures Definition:

| Contact Size | RCS Surf (db) | RCS Surf ($m^2$) | Sample Range $(nm)$ | RCS Air $(db)$ | RCS Air $m^2$ | Sample Range (nm) |
| ------------ | ------------- | ---------------- | ------------------- | -------------- | ------------- | ----------------- |
| Large        | 65            | 3,000,000        | 100                 | 18             | 63            | 100               |
| Medium       | 55            | 300,000          | 56                  | 10             | 10            | 63                |
| Small        | 45            | 30,000           | 32                  | 5              | 3.2           | 47                |
| Very Small   | 35            | 3,000            | 18                  | -10            | 0.1           | 20                |
| Stealthy     | 25            | 300              | 10                  | -30            | 0.001         | 6                  |

APG-65 (LD/SD) Harpoon data:

| Version    | Large | Medium | Small | Very Small | Stealthy |
|------------|-------|--------|-------|------------|----------|
| Harpoon IV | 160   | 101    | 75    |   32       | 10       |
| Harpoon V  | 160   | 112    | 80    |   32       | 10       |

""")
