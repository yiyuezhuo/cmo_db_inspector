# CMO Db Inspector

This app is inspired by [cmo-db](https://cmano-db.com/), however it's not open source and some features I want doesn't exist yet. For example:

- Expose more sensor attributes instead of being a poor clone cat similar to the original CMO data viewer, which just provide some obscure values such as `RangeMax`.
- Do some simple calculations according to data. For example, it's insteresting to know a rough time when a sensor detects a target as target's signature is given. Also it would be useful to see the distance a missile is possible to hit its target (after the WarPlannar release) when target's auto-evading maneuver is considered.
- Prodive some statistics in additional to indivisual data.
- Interchangeability to Harpoon V.

## Radar

### Radar Detection Range

This app uses following radar equationb:

$$
\begin{align*}
R_{max} &= \min(\R_{max,p},\R_{max,PRF}) \\
R_{max,p} &= \left( \frac{P_s}{G^2\lambda^2\sigma C_1}{P_{e_{min}}(4\pi)^3 C_2} \right)^{1/4} \\
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
- `\sigma`: RCS (Radar cross-section), which is `1m^2` for the reference calulation. The value can be found in `DataAircraftSignatures`.
- PRF: Pulse Repetition Frequency, pps (Pulse per second). `DataSensor.RadarPRF`
- $\theta$: Horizontal beam-width (radius). `DataSensor.RadarHorizontalBeamwidth` (degree to radians)
- $\phi$: Vertical beam-width (radians). `DataSensor.RadarVerticalBeamwidth` (degree to radians)
- $C_1$: Constant. `DataSensor.RadarProcessingGainLoss` (db to linear)
- $C_2$: Constant. `DataSensor.RadarSystemNoiseLevel` (db to linear)
- $P_{e_{min}}$: Minimum energy to be detected. (10^{-15}). (Someone suggest $10^{-12}$ but I found $10^{-15}$ to be more close to CMO result).

## Missle

It would be useful to do non-escape zone like calculation outside CMO and its "simulation".

### Effective Range

### ATA Probability

## Performance

## Harpoon V Interchangeability

### Data Mapping

Some ML models are fitted to do the mapping (Source: CMO Database, target: Harpoon V data book).

## Tech Detail

The app is written in Gradio, as I love the design of Stable-Diffusion WebUI and developed a Harpoon V automation tool for company with it.

The project itself is a Python package so it can be installed from pip directly. Also it's deployed on HuggingFace using their free server. You can use it in Colab as well with some generic Colab tricks, however you should provide CMO databases for this way.

