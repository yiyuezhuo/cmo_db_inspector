
from typing import Protocol, Optional
from enum import Enum
from dataclasses import dataclass

class Proficiency(Enum):
    Novice: 1
    Cadet: 2
    Regular: 3
    Veteran: 4
    Ace: 5

class TerminalManeuver(Enum):
    PopUp: 1
    ZigZag: 2
    Random: 3

class GuidanceMode(Enum):
    Radar: 1
    IR: 2

class Missile(Protocol):
    PoH: float # Probability of Hit (base hit probability)
    max_target_speed: float
    is_rocket_booster_or_no_power: bool
    has_capable_vs_seaskimmer: bool # Weapon Code 2006
    range_max: float # nmi
    guidance_mode: GuidanceMode

class MissileTarget(Protocol):
    speed: float # kt
    agility: float # CMO Agility or Harpoon style Maneuverability Rating
    altitude: float
    has_supermanouverability: bool # Aircraft Code 4001
    experience: Proficiency
    weight_empty: float
    weight_payload: float
    weight_fuel: float
    weight_max: float
    damaged: float # 0%~100%, 0.0~1.0, if the feature of "Aircraft Damage" is enabled
    terminal_maneuver: Optional[TerminalManeuver]
    proficiency: Optional[Proficiency]
    rcs: float # m^2
    ir_detection_distance: float # nmi
    altitude_max: float
    is_missile: bool # missile or aircraft

class Environment:
    bearing: float # degree
    distance: float # nmi # "required" distance (or "elapsed" range when the missile touchs the target)
    on_sea: bool

proficiency_agility_coef_map = {
    Proficiency.Novice: 0.3,
    Proficiency.Cadet: 0.5,
    Proficiency.Regular: 0.8,
    Proficiency.Veteran: 1.0,
    Proficiency.Ace: 1.2
}

terminal_maneuver_coef_map = {
    TerminalManeuver.PoPUp: 3 / 4, # Weapon Code 6121
    TerminalManeuver.ZigZag: 2 / 3, # Weapon Code 6122
    TerminalManeuver.Random: 1 / 2 # Weapon Code 6123
}

@dataclass
class MissileHitProbilityCalculator:
    missile: Missile
    target: MissileTarget
    env: Environment

    @property
    def distance_coef(self) -> float:
        m, t, e = self.missile, self.target, self.env

        p = e.distance / m.range_max
        pf = 0.5 if m.is_rocket_booster_or_no_power else 0.75
        if p < pf:
            return 1
        return pf + (1-pf) * (1 - (p - pf)/(1 - pf))
    
    @property
    def speed_mod(self) -> float:
        m, t, e = self.missile, self.target, self.env
        p =t.speed / m.max_target_speed
        if p > 1.0:
            return -0.5
        elif p > 0.8:
            return -0.25
        elif p > 0.7:
            return -0.15
        elif p > 0.6:
            return -0.1
        elif p > 0.4:
            return -0.05
        return 0
    
    @property
    def agility_altitude_coef(self) -> float:
        m, t, e = self.missile, self.target, self.env
        p = t.altitude / t.altitude_max
        if t.has_supermanouverability:
            return max(0.5, 1 - 0.5 * p)
        else:
            return max(0.25, 1 - 0.75 * p)

    @property
    def agility_proficiency_coef(self) -> float:
        return proficiency_agility_coef_map[self.target.proficiency]
    
    @property
    def agility_weight_coef(self) -> float:
        m, t, e = self.missile, self.target, self.env
        weight_current = t.weight_empty + t.weight_payload + t.weight_fuel
        weight_valid = t.weight_max - (t.weight_empty + 0.6 * t.weight_fuel)
        loadout_coef = min(0.99, weight_current - (t.weight_empty+0.6*t.weight_fuel) / weight_valid)
        return 0.4 + 0.6 * (1-loadout_coef)
    
    @property
    def agility_damaged_coef(self) -> float:
        return 1 - self.t.damaged
    
    @property
    def agility_angle_coef(self) -> float:
        """
        
        ---missile--->   <---target---- => bearing=0 => Head-On Attack => 0.6

        <--target-----
            /\
            |
            |
         missile
            |
            |
        => bearing = 90 deg or 270 deg => Side Attack => 1
        """
        bearing = self.env.bearing % 360
        if 0 <= bearing < 15 or 345 < bearing <= 360:
            return 0.6
        elif 15 <= bearing < 60 or 300 < bearing <= 345:
            return 0.7
        elif 60 <= bearing < 110 or 250 < bearing <= 300:
            return 1.0
        elif  110 <= bearing < 165 or 195 < bearing <= 250:
            return 0.85
        # elif 165 <= bearing <= 195:
        else:
            return 0.5
        
    @property
    def modified_agility(self) -> float:
        return self.target.agility * self.agility_altitude_coef * self.agility_proficiency_coef * self.agility_weight_coef * self.agility_damaged_coef * self.agility_angle_coef
    
    @property
    def agility_mod(self) -> float:
        return -0.1 * self.modified_agility 

    @property
    def seaskimmer_mod(self) -> float:
        m, t, e = self.missile, self.target, self.env

        if not e.on_sea or m.has_capable_vs_seaskimmer or t.altitude > 91.44: # 91.44 m
            return 1.0
        
        if t.altitude > 60.96:
            return -0.05
        elif t.altitude > 30.48:
            return -0.15
        return -0.3
    
    @property
    def angle_coef(self) -> float:
        b = self.env.bearing % 360 # -360 ~ 360 => 0 ~ 360
        b = b - (b % 180) * (b // 180) # 0 ~ 360 => 0 ~ 180 ~ 0
        return 1 - b / 180
    
    @property
    def terminal_maneuver_coef(self) -> float:
        return terminal_maneuver_coef_map[self.target.terminal_maneuver]
    
    @property
    def signature_mod(self) -> float:
        if self.missile.guidance_mode == GuidanceMode.Radar:
            rcs = self.target.rcs
            if rcs >= 1:
                return -0
            elif rcs > 0.1:
                return -0.1
            elif rcs > 0.01:
                return -0.15
            else:
                return -0.2
        elif self.missile.guidance_mode == GuidanceMode.IR:
            ir_dist = self.target.ir_detection_distance
            if ir_dist > 1:
                return -0
            elif ir_dist > 0.5:
                return -0.1
            elif ir_dist > 0.25:
                return -0.15
            else:
                return -0.2
            
    def apply_mod(self, x, mod):
        return min(max(0, x + mod), 1.0)
            
    @property
    def probability_hit(self):
        m, t, e = self.missile, self.target, self.env

        ph = self.apply_mod(self.missile.PoH * self.distance_coef, self.speed_mod)
        if not t.is_missile: # aircraft
            ph = self.apply_mod(ph, self.agility_mod)
        else: # missile
            
            ph *= self.angle_coef
            ph *= self.terminal_maneuver_coef
            ph = self.apply_mod(ph, self.signature_mod)

        ph = self.apply_mod(ph, self.seaskimmer_mod)

        return ph
