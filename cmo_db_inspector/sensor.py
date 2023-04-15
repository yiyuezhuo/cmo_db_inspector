import re
import pandas as pd
import sqlite3
from typing import Protocol
import gradio as gr
from itertools import chain

from .utils import connect, text_grid, add_text_rows, tags, inv_db, nmi
from .interfaces import DbPathProvider
from .radar_equation import IRadar

unit_map = {"":1, "K":1_000, "M": 1_000_000, "G": 1_000_000_000}
hz_map = {
    "Visual Light": 300e12,
    "Near IR (0.75-8 µm)": 30e12,
    "Far IR (8-1000 µm)": 3e12,
    "Laser": 300e9
}

section_arr = [
    [0, "General"],
    [14, "Misc"],
    [27, "Radar (Search & Track)"],
    [35, "Radar (Fire Control)"],
    [43, "ESM"],
    [46, "ECM"],
    [52, "Sonar"],
    [62, "Visual/IR Zoom"],
    [66, "Mine Sweep"],
    [70, "Other"]
]

info_map = {
    "RangeMin": "nmi",
    "RangeMax": "nmi",
    "RadarPRF": "pps",
    "RadarPeakPower": "W",
    "RadarHorizontalBeamwidth": "degree",
    "RadarVerticalBeamwidth": "degree"
}

def extract_Hz_value(s):
    if s in hz_map:
        return hz_map[s]
    left, right, unit = re.findall(r"(\d+)-(\d+) (K|M|G)?Hz", s)[0]
    return (int(left) + int(right)) / 2 * unit_map[unit]

def split_data(*args):
    for section_idx, section_config in enumerate(section_arr):
        left = section_arr[section_idx][0]
        right = section_arr[section_idx+1][0] if section_idx + 1 < len(section_arr) else None
        yield section_config[1], *(arg[left:right] for arg in args)

class SensorRawTab:
    def __init__(self, db_path_provider: DbPathProvider, elements_per_row = 5):
        self.db_path_provider = db_path_provider
        self.elements_per_row = elements_per_row
        self.name_to_component: dict[str, gr.components.Component] = {}
        
    def build(self):
        with connect(self.db_path_provider.get_init_db_path()) as conn:
            cur = conn.execute("PRAGMA table_info(DataSensor)")
            res = cur.fetchall()

        headers = [r[1] for r in res]
        types = [r[2] for r in res]
            
        for section_name, indexes in split_data(headers):
            with gr.Accordion(section_name):
                self.name_to_component.update(text_grid(indexes, self.elements_per_row, info_map))
        
        return self
    
    def bind(self):
        return self
    
    def updates(self, data, _id):
        # print(f"_id={_id}, type=>{type(_id)}")
        _id = int(_id)
        with connect(self.db_path_provider.get_db_path(data)) as conn:
            cur = conn.execute("SELECT * FROM DataSensor WHERE ID = ?", (int(_id),))
            res = cur.fetchone()
            # print(f"res={res}")
        return {component: res[idx] for idx, component in enumerate(self.name_to_component.values())}
    
    def register_outputs(self, outputs: set):
        for component in self.name_to_component.values():
            outputs.add(component)
    
    # Gradio's outputs is assumed to be immutable. 
    """
    def deregister_outputs(self, outputs: set):
        for component in self.name_to_component.values():
            outputs.remove(component)
    """

    # def transform_returns(self, returns: dict):
    #    returns.update(self.updates())

class RadarSearchTrack:
    def __init__(self, db_path_provider: DbPathProvider):
        self.db_path_provider = db_path_provider
        self.name_to_component: dict[str, gr.components.Component] = {}

    row_name_list_left = [
        ["Role"],
        ["Range", "Altitude", "Altitude_ASL"],
        ["ScanInterval", "DirectionFindingAccuracy"],
        ["ResolutionRange", "ResolutionHeight", "ResolutionAngle"],
        ["MaxContactsAir", "MaxContactsSurface", "MaxContactsSubmarine"]
    ]

    row_name_list_right = [
        ["RadarHorizontalBeamwidth", "RadarVerticalBeamwidth", "RadarSystemNoiseLevel"],
        ["RadarProcessingGainLoss", "RadarPeakPower", "RadarPulseWidth"],
        ["RadarBlindTime", "RadarPRF"]
    ]

    tags_command_map = {
        "Capabilities": 
            "SELECT Description FROM DataSensorCapabilities "
            "INNER JOIN EnumSensorCapability ON CodeID = EnumSensorCapability.ID "
            "WHERE DataSensorCapabilities.ID = ?",

        "FrequencySearchAndTrack": 
            "SELECT Description FROM DataSensorFrequencySearchAndTrack "
            "INNER JOIN EnumSensorFrequency ON Frequency=EnumSensorFrequency.ID "
            "WHERE DataSensorFrequencySearchAndTrack.ID = ?",     
               
        "Codes": 
            "SELECT Description FROM DataSensorCodes "
            "INNER JOIN EnumSensorCode ON CodeID = EnumSensorCode.ID "
            "WHERE DataSensorCodes.ID = ?"
    }

    dbsm_arr = [-30, -20, -10, 0, 10, 20, 30]

    def build(self):
        with gr.Row():
            with gr.Column():
                self.name_to_component["Name"] = gr.Text("", show_label=False)

                for name_list in self.row_name_list_left:
                    add_text_rows(self.name_to_component, name_list)

                with gr.Row():
                    gr.Button("Send to Radar Equatiobn")

            with gr.Column():
                for name_list in self.row_name_list_right:
                    add_text_rows(self.name_to_component, name_list)

                self.name_to_component["detection_range"] = gr.DataFrame([[]], label="Radar Equation", headers = ["dBsm"] + [str(n) for n in self.dbsm_arr])

                for name in ["Capabilities", "FrequencySearchAndTrack", "Codes"]:
                    self.name_to_component[name] = tags([], label=name)

        
        return self

    def updates(self, data, _id):
        _id = int(_id)

        with connect(self.db_path_provider.get_db_path(data)) as conn:
            cur = conn.execute(
                "SELECT DataSensor.ID, Name, Comments, EnumSensorType.Description AS Type, "
                "EnumSensorRole.Description as Role, EnumSensorGeneration.Description AS Generation, "
                "RangeMin, RangeMax, AltitudeMin, AltitudeMax, AltitudeMin_ASL, AltitudeMax_ASL, ScanInterval, "
                "ResolutionRange, ResolutionHeight, ResolutionAngle, DirectionFindingAccuracy, "
                "MaxContactsAir, MaxContactsSurface, MaxContactsSubmarine, "
                "RadarHorizontalBeamwidth, RadarVerticalBeamwidth, RadarSystemNoiseLevel, RadarProcessingGainLoss, "
                "RadarPeakPower, RadarPulseWidth, RadarBlindTime, RadarPRF "
                "FROM DataSensor "
                "INNER JOIN EnumSensorRole ON Role=EnumSensorRole.ID "
                "INNER JOIN EnumSensorType ON Type=EnumSensorType.ID "
                "INNER JOIN EnumSensorGeneration ON Generation=EnumSensorGeneration.ID "
                "WHERE DataSensor.ID = ?",
                (_id,))
            res = cur.fetchone()

            # print(f"res={res}, _id={_id}")
            d = {k[0]: v for k, v in zip(cur.description, res)}
            comments = "" if d["Comments"] == "-" else f"({d['Comments']})"
            name = f"#{d['ID']} {d['Name']} ({d['Type']}, {d['Generation']})"

            _rd = {
                "Name": name,
                "Range": f"{round(d['RangeMin'], 2)} nmi - {round(d['RangeMax'], 2)} nmi",
                "Altitude": f"{round(d['AltitudeMin'], 2)} m - {round(d['AltitudeMax'], 2)} m",
                "Altitude_ASL": f"{round(d['AltitudeMin_ASL'], 2)} m - {round(d['AltitudeMax_ASL'], 2)} m"
            }

            for name_list in chain(self.row_name_list_left, self.row_name_list_right):
                for name in name_list:
                    if name not in _rd:
                        _rd[name] = d[name]

            rl_map = {}
            for name, command in self.tags_command_map.items():
                cur = conn.execute(command, (_id,))
                res = cur.fetchall()
                rl = [r[0] for r in res]
                rl_map[name] = rl
                _rd[name] = gr.update(value=rl, choices=rl)

            freq_s_l = rl_map["FrequencySearchAndTrack"]
            radar_record = RadarRecord(d, freq_s_l)
            ranges_m = [radar_record.detection_range(inv_db(dbsm)) for dbsm in self.dbsm_arr]
            _rd["detection_range"] = [
                ["km"] + [round(r / 1000, 1) for r in ranges_m],
                ["nmi"] + [round(r / 1000 / nmi, 1) for r in ranges_m]
            ]

        return {self.name_to_component[name]: value for name, value in _rd.items()}

    def register_outputs(self, outputs: set):
        for component in self.name_to_component.values():
            outputs.add(component)


class RadarRecord(IRadar):
    def __init__(self, d: dict, freq_s_l: list[str], minimum_power=1e-15):
        self.d = d
        self._frequency = min(extract_Hz_value(s) for s in freq_s_l)
        self._minimum_power = minimum_power
    
    @property
    def peak_power(self):
        return self.d["RadarPeakPower"]
    
    @property
    def frequency(self):
        return self._frequency
    
    @property
    def minimum_power(self):
        return self._minimum_power
    
    @property
    def vertical_beamwidth(self):
        return self.d["RadarVerticalBeamwidth"]
    
    @property
    def horizontal_beamwidth(self):
        return self.d["RadarHorizontalBeamwidth"]
    
    @property
    def pulse_repetition_frequency(self):
        return self.d["RadarPRF"]
    
    @property
    def system_noise_level(self):
        return self.d["RadarSystemNoiseLevel"]
    
    @property
    def processing_gain_loss(self):
        return self.d["RadarProcessingGainLoss"]
