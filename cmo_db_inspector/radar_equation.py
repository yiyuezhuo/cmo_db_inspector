import numpy as np
import numpy.typing as npt
from typing import Protocol, Union
from .utils import light_speed, inv_db

# T = Union[float, npt.ArrayLike, pd.DataFrame, pd.Series]
# T = npt.ArrayLike
T = Union[np.ndarray, float]

class IRadar(Protocol):
    @property
    def peak_power(self) -> T:
        ...

    @property
    def frequency(self) -> T:
        ...

    @property
    def minimum_power(self) -> T:
        ...

    @property
    def vertical_beamwidth(self) -> T:
        ...

    @property
    def horizontal_beamwidth(self) -> T:
        ...

    @property
    def pulse_repetition_frequency(self) -> T:
        ...

    @property
    def system_noise_level(self) -> T:
        ...

    @property
    def processing_gain_loss(self) -> T:
        ...

    @property
    def PRF_range(self) -> T:
        return light_speed / self.pulse_repetition_frequency / 2
    
    @property
    def gain(self) -> T:
        return 4 * np.pi / np.deg2rad(self.vertical_beamwidth) / np.deg2rad(self.horizontal_beamwidth)
    
    @property
    def wavelength(self) -> T:
        return light_speed / self.frequency
    
    def log_power_range(self, radar_cross_section: float) -> T:
        P_S = self.peak_power
        G = self.gain
        sigma = radar_cross_section
        lam = self.wavelength
        P_e = self.minimum_power

        return 1/4 * (np.log(P_S) + 2 * np.log(G) + 2 * np.log(lam) + np.log(sigma) - 3 * np.log(4*np.pi) - np.log(P_e))
    
    def adjusted_range(self, radar_cross_section: float) -> T:
        r = np.exp(self.log_power_range(radar_cross_section))
        return r / inv_db(self.system_noise_level)**0.25 * inv_db(self.processing_gain_loss)**0.25
    
    def detection_range(self, radar_cross_section: float) -> T:
        return np.minimum(self.adjusted_range(radar_cross_section), self.PRF_range)
