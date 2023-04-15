
import gradio as gr
from .interfaces import DbPathProvider
from .utils import connect, text_grid, tags, add_text_rows

info_map:dict[str, str] = {}


class AircraftRawTab:
    def __init__(self, db_path_provider: DbPathProvider, elements_per_row = 5):
        self.db_path_provider = db_path_provider
        self.elements_per_row = elements_per_row
        self.name_to_component: dict[str, gr.components.Component] = {}

    def build(self):
        with connect(self.db_path_provider.get_init_db_path()) as conn:
            cur = conn.execute("PRAGMA table_info(DataAircraft)")
            res = cur.fetchall()

        headers = [r[1] for r in res]
        types = [r[2] for r in res]

        self.name_to_component.update(text_grid(headers, self.elements_per_row, info_map))
        """
        for chunk in chunks(list(headers), self.elements_per_row):
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
        _id = int(_id)
        with connect(self.db_path_provider.get_db_path(data)) as conn:
            cur = conn.execute("SELECT * FROM DataAircraft WHERE ID = ?", (_id,))
            res = cur.fetchone()
        return {component: res[idx] for idx, component in enumerate(self.name_to_component.values())}
    
    def register_outputs(self, outputs: set):
        for component in self.name_to_component.values():
            outputs.add(component)

class AircraftTab:
    def __init__(self, db_path_provider: DbPathProvider):
        self.db_path_provider = db_path_provider
        self.name_to_component: dict[str, gr.components.Component] = {}

    row_name_list = [
        ["Type", "DamagePoints"],
        ["Agility", "ClimbRate"],
        ["Length", "Span", "Height"],
        ["WeightEmpty", "WeightMax"]
    ]

    tags_command_map = {
        "Loadouts": "SELECT Name FROM DataAircraftLoadouts INNER JOIN DataLoadout ON DataAircraftLoadouts.ComponentID = DataLoadout.ID WHERE DataAircraftLoadouts.ID = ?",
        "Sensors": "SELECT DataSensor.Name FROM DataAircraftSensors INNER JOIN DataSensor ON ComponentID=DataSensor.ID WHERE DataAircraftSensors.ID = ?",
        "Comms": "SELECT Name FROM DataAircraftComms INNER JOIN DataComm ON ComponentID = DataComm.ID WHERE DataAircraftComms.ID= ?",
        "Codes": "SELECT Description FROM DataAircraftCodes INNER JOIN EnumAircraftCode ON DataAircraftCodes.CodeID=EnumAircraftCode.ID WHERE DataAircraftCodes.ID = ?"
    }

    def build(self):
        
        with gr.Row():
            with gr.Column():
                
                self.name_to_component["Name"] = gr.Text("", show_label=False)

                for name_list in self.row_name_list:
                    add_text_rows(self.name_to_component, name_list)

                with gr.Row():
                    self.name_to_component["send_to_radar_equation"] = gr.Button("Send to Radar Equation")
                
            with gr.Column():
                headers_map = {
                    "Signatures": ["Description", "Front", "Side", "Rear", "Top"],
                    "Performances": ["AltitudeBand", "Throttle", "Speed", "AltitudeMin", "AltitudeMax", "Consumption"]
                }

                for name, headers in headers_map.items():
                    self.name_to_component[name] = gr.DataFrame([[]], headers=headers, label=name)

                for name in ["Sensors", "Comms", "Codes", "Loadouts"]:
                    self.name_to_component[name] = tags([], label=name)

        return self

    def bind(self):
        return self
        
    def updates(self, data, _id):
        _id = int(_id)

        rd = {}

        with connect(self.db_path_provider.get_db_path(data)) as conn:

            cur = conn.execute(
                "SELECT DataAircraft.ID, EnumAircraftType.Description as Type, Name, Comments, EnumOperatorCountry.Description as Country, YearCommissioned, Agility, ClimbRate, DamagePoints, Length, Span, Height, WeightEmpty, WeightMax "
                "FROM DataAircraft INNER JOIN EnumAircraftType ON Type = EnumAircraftType.ID INNER JOIN EnumOperatorCountry ON OperatorCountry=EnumOperatorCountry.ID "
                "WHERE DataAircraft.ID = ?",
                (_id,))
            res = cur.fetchone()
            d = {k[0]: v for k, v in zip(cur.description, res)}
            comments = "" if d["Comments"] == "-" else f"({d['Comments']})"
            name = f"#{d['ID']} {d['Name']} {comments} ({d['Country']}, {d['YearCommissioned']})"

            rd[self.name_to_component["Name"]] = name
            for name_list in self.row_name_list:
                for name in name_list:
                    rd[self.name_to_component[name]] = d[name]

            cur = conn.execute(
                "SELECT Description, Front, Side, Rear, Top FROM DataAircraftSignatures INNER JOIN EnumSignatureType ON Type=EnumSignatureType.ID "
                "WHERE DataAircraftSignatures.ID = ?",
                (_id,))
            rd[self.name_to_component["Signatures"]] = cur.fetchall()

            cur = conn.execute("SELECT ComponentID FROM DataAircraftPropulsion WHERE DataAircraftPropulsion.ID = ?", (_id,))
            component_id = cur.fetchone()[0]
            cur = conn.execute(
                "SELECT AltitudeBand, Throttle, Speed, AltitudeMin, AltitudeMax, Consumption FROM DataPropulsionPerformance "
                "WHERE ID = ?", 
                (component_id,))
            rd[self.name_to_component["Performances"]] = cur.fetchall()

            for name, command in self.tags_command_map.items():
                cur = conn.execute(command, (_id,))
                res = cur.fetchall()

                rl = [r[0] for r in res]
                rd[self.name_to_component[name]] = gr.update(value=rl, choices=rl)

        return rd

    def register_outputs(self, outputs: set):
        for component in self.name_to_component.values():
            outputs.add(component)
