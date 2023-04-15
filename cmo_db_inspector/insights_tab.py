
import gradio as gr
import pandas as pd
import numpy as np

from .interfaces import DbPathProvider

country_map = {
    "United States": "USA",
    "Russia [1992-]": "Russia",
    "Soviet Union [-1991]": "Russia",
    "China": "China",
    "United Kingdom": "UK",
    "France": "France"
}

country_color_discrete_map = {
    "USA": "blue",
    "Russia": "green",
    "China": "red",
    "UK": "purple",
    "France": "pink",
    "Others": "grey"
}


class InsightsTab:
    def __init__(self, db_path_provider: DbPathProvider):
        self.db_path_provider = db_path_provider
        self.name_to_component: dict[str, gr.components.Component] = {}

    def build(self):
        with gr.Row():
            with gr.Column(scale = 1):
                with gr.Accordion("Agility vs Front dBsm (A-D Bands)"):
                    self.name_to_component["major_powers"] = gr.Checkbox(True, label="Major Power")
                    self.name_to_component["hover_check_box_group"] = gr.CheckboxGroup(
                        choices=["Comments", "Year", "Non-Jittering Agility"], 
                        value=["Comments", "Year", "Non-Jittering Agility"], label="Hover Info")
                    self.name_to_component["jittering"] = gr.Slider(0, 0.05, value=0.05, label="Jittering")
                    self.name_to_component["plot_agility_front"] = gr.Button("Plot")
                    # self.name_to_component["plot_agility_front_major_power"] = gr.Button("Major Power")
            with gr.Column(scale=4):
                self.name_to_component["plot"] = gr.Plot(show_label=False)

        return self

    def bind(self):
        
        inputs = self.db_path_provider.get_db_inputs() | {self.name_to_component[name] for name in ["major_powers", "jittering", "hover_check_box_group"]}
        self.name_to_component["plot_agility_front"].click(
            self.plot_agility_front, inputs, self.name_to_component["plot"])

        return self

    def plot_agility_front(self, data):
        import plotly.express as px

        df = pd.read_sql_query(
            "SELECT DataAircraft.ID, Name, Comments, YearCommissioned, Agility, DataAircraftSignatures.Front, Description AS Country FROM DataAircraft "
            "INNER JOIN DataAircraftSignatures ON DataAircraft.ID=DataAircraftSignatures.ID "
            "INNER JOIN EnumOperatorCountry ON OperatorCountry = EnumOperatorCountry.ID "
            "WHERE DataAircraftSignatures.Type = 5001",
            "sqlite:///" + str(self.db_path_provider.get_db_path(data)))

        color_discrete_map = None
        if data[self.name_to_component["major_powers"]]:
            df["Country"] = df.Country.map(lambda x: country_map.get(x, "Others"))
            color_discrete_map = country_color_discrete_map

        jittering = data[self.name_to_component["jittering"]]
        if jittering > 0:
            df["NonJitteringAgility"] = df["Agility"].copy()
            df["Agility"] = df["Agility"] + np.random.randn(df["Agility"].size) * jittering

        hover_options = set(data[self.name_to_component["hover_check_box_group"]])
        if "Comments" in hover_options:
            mask = df["Comments"] != "-"
            df.loc[mask, "Name"] = df.loc[mask, "Name"] + " (" + df.loc[mask, "Comments"] + ")"

        custom_data = ["Name"]
        if "Year" in hover_options:
            custom_data.append("YearCommissioned")
        if "Non-Jittering Agility" in hover_options:
            custom_data.append("NonJitteringAgility")

        hovertemplate = ",".join("%{customdata["+str(i)+"]}" for i in range(len(custom_data)))
        # print(hovertemplate)

        fig = px.scatter(df, x="Agility", y="Front", custom_data=custom_data, color="Country", color_discrete_map=color_discrete_map)
        fig.update_traces(hovertemplate=hovertemplate)

        return fig
