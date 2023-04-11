
import gradio as gr

class AircraftTab:
    def __init__(self, init_ser):
        self.components_map = {}

    def build(self):
        with gr.Tab("Aircraft Raw"):
            pass