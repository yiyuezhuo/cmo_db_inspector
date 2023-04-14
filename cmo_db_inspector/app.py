
import gradio as gr
from pathlib import Path
from .selector import SelectorTab
from .sensor import SensorRawTab, RadarSearchTrack
from .aircraft import AircraftRawTab, AircraftTab
from .utils import merge_update

css = """
#first-page-button, #prev-page-button, #next-page-button, #end-page-button {
    min-width: min(50px,100%)
}
"""

class App:
    def __init__(self, cmo_db_root: Path):
        self.cmo_db_root = cmo_db_root
        self.demo = None

    def build(self):
        with gr.Tabs() as tabs:
            with gr.TabItem("Selector", id=0):
                self.selector_tab = SelectorTab(self.cmo_db_root).build()
            with gr.TabItem("Aircraft Raw", id=1):
                self.aircraft_raw_tab = AircraftRawTab(self.selector_tab).build()
            with gr.TabItem("Sensor Raw", id=2):
                self.sensor_raw_tab = SensorRawTab(self.selector_tab).build()
            with gr.TabItem("Aircraft", id=3):
                self.aircraft_tab = AircraftTab(self.selector_tab).build()
            with gr.TabItem("Radar (Search & Track)", id=4):
                self.radar_search_track = RadarSearchTrack(self.selector_tab).build()
            with gr.TabItem("Radar Equation", id=5):
                pass

        return self

    def bind(self):
        gr_df_select_output = set()

        self.aircraft_tab.register_outputs(gr_df_select_output)
        self.aircraft_raw_tab.register_outputs(gr_df_select_output)
        self.sensor_raw_tab.register_outputs(gr_df_select_output)
        self.radar_search_track.register_outputs(gr_df_select_output)
        
        # self.selector_tab.selected_events["Aircraft"].return_update = self.aircraft_raw_tab.updates
        self.selector_tab.selected_events["Aircraft"].return_update = merge_update(self.aircraft_tab.updates, self.aircraft_raw_tab.updates)
        self.selector_tab.selected_events["Sensor"].return_update = merge_update(self.sensor_raw_tab.updates, self.radar_search_track.updates)
        # self.selector_tab.selected_events["Sensor"].return_update = self.sensor_raw_tab.updates

        self.selector_tab.bind(gr_df_select_output)
        # self.sensor_raw_tab.bind()

        return self

    def create(self):
        with gr.Blocks(analytics_enabled=False, theme=gr.themes.Default(), css=css) as demo:
            self.build()
            self.bind()

            demo.load(lambda: "", [], [self.selector_tab.class_text])
        
        self.demo = demo
        return self
