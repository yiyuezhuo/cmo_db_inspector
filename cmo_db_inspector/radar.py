import re
import pandas as pd
import sqlite3

unit_map = {"":1, "K":1_000, "M": 1_000_000, "G": 1_000_000_000}
hz_map = {
    "Visual Light": 300e12,
    "Near IR (0.75-8 µm)": 30e12,
    "Far IR (8-1000 µm)": 3e12,
    "Laser": 300e9
}

section_arr = [
    [0, "General"],
    [13, "Misc"],
    [26, "Radar"],
    [34, "Fire Control"],
    [42, "ESM"],
    [45, "ECM"],
    [51, "Sonar"],
    [61, "Visual/IR Zoom"],
    [65, "Mine Sweep"],
    [69, "Other"]
]

def extract_Hz_value(s):
    if s in hz_map:
        return hz_map[s]
    left, right, unit = re.findall(r"(\d+)-(\d+) (K|M|G)?Hz", s)[0]
    return (int(left) + int(right)) / 2 * unit_map[unit]

def split_data(headers, values):
    for section_idx, section_config in enumerate(section_arr):
        left = section_arr[section_idx][0]
        right = section_arr[section_idx+1][0] if section_idx + 1 < len(section_arr) else None
        yield section_config[1], headers[left:right], values[left:right]

class SensorTab:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def build(self):
        # example
        conn = sqlite3.connect(self.db_path)


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