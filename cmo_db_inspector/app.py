
import gradio as gr
from pathlib import Path
from .selector import SelectorTab
from .sensor import SensorRawTab, RadarSearchTrack, extract_Hz_value
from .aircraft import AircraftRawTab, AircraftTab
from .utils import merge_update
from .references import ReferencesTab
from .insights_tab import InsightsTab
from .radar_equation_tab import RadarEquationTab

css = """
#first-page-button, #prev-page-button, #next-page-button, #end-page-button {
    min-width: min(50px,100%)
}

div.math.block {
    fill: var(--body-text-color);
    display: inline-block;
    vertical-align: middle;
    padding: var(--size-1-5) -var(--size-1);
    color: var(--body-text-color);
}
"""

# `.math.inline` is set to change font color once light/dark mode is switched, however `.math.block` is not set. So I copy inline style to block.

class App:
    def __init__(self, cmo_db_root: Path):
        self.cmo_db_root = cmo_db_root
        self.demo = None
        self.tabs = None
        self.aircraft_tab_item = None
        self.radar_search_track_tab_item = None

    def build(self):
        with gr.Tabs() as tabs:
            with gr.TabItem("Selector", id=0):
                self.selector_tab = SelectorTab(self.cmo_db_root).build()
            with gr.TabItem("Aircraft Raw", id=1):
                self.aircraft_raw_tab = AircraftRawTab(self.selector_tab).build()
            with gr.TabItem("Sensor Raw", id=2):
                self.sensor_raw_tab = SensorRawTab(self.selector_tab).build()
            with gr.TabItem("Aircraft", id=3) as aircraft_tab_item:
                self.aircraft_tab = AircraftTab(self.selector_tab).build()
            with gr.TabItem("Radar (Search & Track)", id=4) as radar_search_track_tab_item:
                self.radar_search_track = RadarSearchTrack(self.selector_tab).build()
            with gr.TabItem("Radar Equation", id=5) as radar_equation_tab_item:
                self.radar_equation = RadarEquationTab().build()
            with gr.TabItem("Insights", id=6):
                self.insights_tab = InsightsTab(self.selector_tab).build()
            with gr.TabItem("References", id=7):
                self.references_tab = ReferencesTab().build()
            with gr.TabItem("Lua Generator", id=8):
                pass
            with gr.TabItem("Force Packages", id=9):
                pass
            
        self.tabs = tabs
        self.aircraft_tab_item = aircraft_tab_item
        self.radar_search_track_tab_item = radar_search_track_tab_item
        self.radar_equation_tab_item = radar_equation_tab_item

        return self

    def bind(self):
        gr_df_select_output = set()

        self.aircraft_tab.register_outputs(gr_df_select_output)
        self.aircraft_raw_tab.register_outputs(gr_df_select_output)
        self.sensor_raw_tab.register_outputs(gr_df_select_output)
        self.radar_search_track.register_outputs(gr_df_select_output)
        
        gr_df_select_output.add(self.tabs)
        
        self.selector_tab.selected_events["Aircraft"].return_update = merge_update(self.aircraft_tab.updates, self.aircraft_raw_tab.updates, self.switch_to_aircraft_tab)
        self.selector_tab.selected_events["Sensor"].return_update = merge_update(self.sensor_raw_tab.updates, self.radar_search_track.updates, self.switch_to_specialized_sensor_tab)
        # self.selector_tab.selected_events["Aircraft"].return_update = merge_update(self.aircraft_tab.updates, self.aircraft_raw_tab.updates)
        # self.selector_tab.selected_events["Sensor"].return_update = merge_update(self.sensor_raw_tab.updates, self.radar_search_track.updates)


        self.selector_tab.bind(gr_df_select_output)
        # self.sensor_raw_tab.bind()

        self.insights_tab.bind()
        self.radar_equation.bind()

        _input_s = ["FrequencySearchAndTrack", "RadarPeakPower", "RadarVerticalBeamwidth", "RadarHorizontalBeamwidth",
             "RadarPRF", "RadarSystemNoiseLevel", "RadarProcessingGainLoss"]
        _output_s = ["peak_power", "frequency", "vertical_beamwidth", "horizontal_beamwidth",
                      "pulse_repetition_frequency", "system_noise_level", "processing_gain_loss", "minimum_power"]
        self.radar_search_track.name_to_component["send_to_radar_equation"].click(
            self.send_radar_params_to_radar_equation,
            set(self.radar_search_track.name_to_component[s] for s in _input_s),
            set(self.radar_equation.ui[s] for s in _output_s) | {self.tabs}
        )

        self.aircraft_tab.name_to_component["send_to_radar_equation"].click(
            self.send_aircraft_params_to_radar_equation,
            {self.aircraft_tab.name_to_component["Signatures"]},
            {self.radar_equation.ui["radar_cross_section_3d"], self.tabs}
        )

        return self
    
    def switch_to_aircraft_tab(self, data, _id):
        return {self.tabs: gr.update(selected=self.aircraft_tab_item.id)}

    def switch_to_specialized_sensor_tab(self, data, _id):
        # TODO: Branch to ECM, FCR, ESM...
        return {self.tabs: gr.update(selected=self.radar_search_track_tab_item.id)}

    def create(self):
        with gr.Blocks(analytics_enabled=False, theme=gr.themes.Default(), css=css) as demo:
            self.build()
            self.bind()

            demo.load(lambda: "", [], [self.selector_tab.class_text])
        
        self.demo = demo
        return self
    
    def send_aircraft_params_to_radar_equation(self, data):
        signatures = data[self.aircraft_tab.name_to_component["Signatures"]]

        sdf = signatures.loc[signatures["Description"].str.contains("Radar"), ["Description", "Front", "Side", "Rear"]]

        return {
            self.radar_equation.ui["radar_cross_section_3d"]: sdf,

            self.tabs: gr.update(selected=self.radar_equation_tab_item.id)
        }

    def send_radar_params_to_radar_equation(self, data):
        src_ui = self.radar_search_track.name_to_component
        dst_ui = self.radar_equation.ui

        # print(data)
        freq_s_l = data[src_ui["FrequencySearchAndTrack"]]
        freq = min(extract_Hz_value(s) for s in freq_s_l)

        return {
            dst_ui["peak_power"]: data[src_ui["RadarPeakPower"]],
            dst_ui["frequency"]: freq,
            # dst_ui["minimum_power"]: 1e-15,
            dst_ui["vertical_beamwidth"]: data[src_ui["RadarVerticalBeamwidth"]],
            dst_ui["horizontal_beamwidth"]: data[src_ui["RadarHorizontalBeamwidth"]],
            dst_ui["pulse_repetition_frequency"]: data[src_ui["RadarPRF"]],
            dst_ui["system_noise_level"]: data[src_ui["RadarSystemNoiseLevel"]],
            dst_ui["processing_gain_loss"]: data[src_ui["RadarProcessingGainLoss"]],

            self.tabs: gr.update(selected=self.radar_equation_tab_item.id)
        }
