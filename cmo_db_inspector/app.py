
import gradio as gr
from pathlib import Path
from .selector import SelectorTab
from .sensor import SensorRawTab

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
                pass
            with gr.TabItem("Sensor Raw", id=2):
                self.sensor_raw_tab = SensorRawTab(self.selector_tab).build()

        return self

    def bind(self):
        gr_df_select_output = set()

        sensor_event = self.selector_tab.selected_events["Sensor"]
        self.sensor_raw_tab.register_outputs(gr_df_select_output)
        sensor_event.return_update = self.sensor_raw_tab.updates

        self.selector_tab.bind(gr_df_select_output)
        self.sensor_raw_tab.bind()

        return self

    def create(self):
        with gr.Blocks(analytics_enabled=False, theme=gr.themes.Default(), css=css) as demo:
            self.build()
            self.bind()
        
        self.demo = demo
        return self
