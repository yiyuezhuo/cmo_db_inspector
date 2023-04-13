import re
import pandas as pd
import sqlite3
from typing import Protocol
import gradio as gr

from .utils import connect, text_grid
from .interfaces import DbPathProvider

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
    [27, "Radar"],
    [35, "Fire Control"],
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
                """
                for chunk in chunks(list(indexs), self.elements_per_row):
                    with gr.Row():
                        for index in chunk:
                            info = info_map.get(index, None)
                            text = gr.Text("", label=index, info=info)
                            self.name_to_component[index] = text
                """
        
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

"""
def split_ser(ser, section):
    for section_idx, section_config in enumerate(section_arr):
        left = section_arr[section_idx][0]
        right = section_arr[section_idx+1][0] if section_idx + 1 < len(section_arr) else None
        yield section_config[1], ser.index[left:right], ser.values[left:right]

class SensorTables:
    def __init__(self, conn_str: str): # 'sqlite:///DB3K_499.db3'
        self.conn_str = conn_str
        self.reload_tables()

    def reload_tables(self):
        conn_str = self.conn_str

        self.freq_desc = pd.read_sql_table("EnumSensorFrequency", conn_str)
        self.sensor = pd.read_sql_table('DataSensor', conn_str, index_col="ID")
        self.cap = pd.read_sql_table("DataSensorCapabilities", conn_str)
        self.freq = pd.read_sql_table("DataSensorFrequencySearchAndTrack", conn_str)

        df_freq_merged = self.df_freq.merge(self.df_freq_desc, left_on="Frequency", right_on="ID")
        df_freq_merged["freq"] = df_freq_merged["Description"].map(extract_Hz_value)

        self.df_freq_uniqued = df_freq_merged.groupby("ID_x").freq.min()

"""