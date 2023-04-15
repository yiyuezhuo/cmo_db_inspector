
import gradio as gr
import pandas as pd
import numpy as np

from .radar_equation import IRadar
from .utils import nmi, inv_db

class RadarUI(IRadar):
    def __init__(self, ui, data):
        self.ui = ui
        self.data = data

    @property
    def peak_power(self):
        return self.data[self.ui["peak_power"]]

    @property
    def frequency(self):
        return self.data[self.ui["frequency"]]

    @property
    def minimum_power(self):
        return self.data[self.ui["minimum_power"]]

    @property
    def vertical_beamwidth(self):
        return self.data[self.ui["vertical_beamwidth"]]

    @property
    def horizontal_beamwidth(self):
        return self.data[self.ui["horizontal_beamwidth"]]

    @property
    def pulse_repetition_frequency(self):
        return self.data[self.ui["pulse_repetition_frequency"]]

    @property
    def system_noise_level(self):
        return self.data[self.ui["system_noise_level"]]

    @property
    def processing_gain_loss(self):
        return self.data[self.ui["processing_gain_loss"]]

class RadarEquationTab:
    def __init__(self):
        self.ui = {}

    def build(self):
        with gr.Row():
            with gr.Column():
                with gr.Accordion("Radar"):
                    with gr.Row():
                        self.ui["peak_power"] = gr.Number(25_000, label="peak power (W)")
                        self.ui["frequency"] = gr.Number(9_000_000_000, label="frequency (HZ)")
                    with gr.Row():
                        self.ui["vertical_beamwidth"] = gr.Number(3.3, label="vertical beamwidth (degree)")
                        self.ui["horizontal_beamwidth"] = gr.Number(3.3, label="horizontal beamwidth (degree)")
                    with gr.Row():
                        self.ui["pulse_repetition_frequency"] = gr.Number(500, label="pulse repetition frequency (HZ)")
                        self.ui["system_noise_level"] = gr.Number(3, label="system noise level (dB)")
                        self.ui["processing_gain_loss"] = gr.Number(-2.5, label="processing gain loss (dB)")
                    self.ui["minimum_power"] = gr.Number(1e-15, label="minimum power (W) [Assumed]")
                with gr.Accordion("Target"):
                    with gr.Row():
                        self.ui["radar_cross_section_single"] = gr.Number(0, label="radar cross section (dBsm)")
                        self.ui["calculate_single"] = gr.Button("Calculate")
                    self.ui["radar_cross_section_3d"] = gr.DataFrame([["Radar, A-D Band (30-2000 MHz)", 9.5, 11.7, 9.5], ["Radar, E-M Band (2-100 GHz)", 9.5, 11.7, 9.5]], 
                                                                     label="CMO style RCS", headers=["Description", "Front", "Side", "Rear"], datatype=["str", "number", "number", "number"])
                    self.ui["calculate_3d"] = gr.Button("Calculate for the table")
            with gr.Column():
                with gr.Accordion("Derived"):
                    with gr.Row():
                        self.ui["PRF_range"] = gr.Number(label="PRF range (m)")
                        self.ui["gain"] = gr.Number(label="gain")
                        self.ui["wavelength"] = gr.Number(label="wavelength")
                with gr.Row():
                    self.ui["result_single_km"] = gr.Number(label="range (km)")
                    self.ui["result_single_nmi"] = gr.Number(label="range (nmi)")
                self.ui["result_3d_df"] = gr.DataFrame([[]], label="Result", headers=["Description", "Front", "Side", "Rear"], datatype=["str", "number", "number", "number"])
                self.ui["result_3d_plot"] = gr.Plot()
        
        return self
    
    def bind(self):
        radar_inputs = {"peak_power", "frequency", "vertical_beamwidth", "horizontal_beamwidth", 
                    "pulse_repetition_frequency", "system_noise_level", "processing_gain_loss", "minimum_power"}
        single_inputs = {"radar_cross_section_single"}
        _3d_inputs = {"radar_cross_section_3d"}
        derived_outputs = {"PRF_range", "gain", "wavelength"}
        single_outputs = {"result_single_km", "result_single_nmi"}
        _3d_outputs = {"result_3d_df", "result_3d_plot"}

        def u(s):
            return {self.ui[name] for name in s}

        self.ui["calculate_single"].click(self.calculate_single, u(radar_inputs | single_inputs), u(derived_outputs | single_outputs))
        self.ui["calculate_3d"].click(self.calculate_3d, u(radar_inputs | _3d_inputs), u(derived_outputs | _3d_outputs))

        return self
    
    def calculate_base(self, data):
        radar = RadarUI(self.ui, data)
        _rd = {
            "PRF_range": round(radar.PRF_range, 2),
            "gain": round(radar.gain, 2),
            "wavelength": round(radar.wavelength, 2),
        }
        return radar, _rd

    def calculate_single(self, data):
        radar, _rd = self.calculate_base(data)
        rcs_m2 = inv_db(data[self.ui["radar_cross_section_single"]])
        result_single_m = radar.detection_range(rcs_m2)
        _rd.update({
            "result_single_km": round(result_single_m / 1000, 2),
            "result_single_nmi": round(result_single_m / 1000 / nmi, 2),
        })
        return {self.ui[name]: value for name, value in _rd.items()}

    def calculate_3d(self, data):
        radar, _rd = self.calculate_base(data)

        df = data[self.ui["radar_cross_section_3d"]].copy()
        for i in range(2):
            for j in range(1, 4):
                rcs_m2 = inv_db(df.iloc[i, j])
                df.iloc[i, j] = radar.detection_range(rcs_m2)
        
        num_headers = ["Front", "Side", "Rear"]
        df_num_km = np.round(df[num_headers] / 1000, 2)
        df_num_nmi = np.round(df[num_headers] / 1000 / nmi, 2)
        df_num_km.columns = [s + " (km)" for s in num_headers]
        df_num_nmi.columns = [s + " (nmi)" for s in num_headers]

        _rd["result_3d_df"] = pd.concat([df[["Description"]], df_num_km, df_num_nmi], axis=1)

        df_indexed = df.set_index("Description")

        sdf_list = []

        for idx, row in df_indexed.iterrows():
            sdf_list.append(pd.DataFrame({
                "Direction": ["Front", "Right", "Rear", "Left"],
                "Range": [row.Front, row.Side, row.Rear, row.Side],
                "Band": [idx] * 4
            }))

        df_pivoted = pd.concat(sdf_list) # TODO: There should be a pandas method to make it prettier.

        import plotly.express as px

        fig = px.line_polar(df_pivoted, r='Range', theta='Direction', line_close=True, color="Band", title="Detection Range (m)")
        _rd["result_3d_plot"] = fig

        return {self.ui[name]: value for name, value in _rd.items()}

    def updates(self, data):
        pass