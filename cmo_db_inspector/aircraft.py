
import gradio as gr
from .interfaces import DbPathProvider
from .utils import connect, text_grid, tags

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

    def build(self):
        for name in ["Loadouts", "Sensors", "Comms", "Codes"]:
            self.name_to_component[name] = tags([], label=name)
        return self

    def bind(self):
        return self
        
    def updates(self, data, _id):
        _id = int(_id)

        command_map = {
            "Loadouts": "SELECT Name FROM DataAircraftLoadouts INNER JOIN DataLoadout ON DataAircraftLoadouts.ComponentID = DataLoadout.ID WHERE DataAircraftLoadouts.ID = ?",
            "Sensors": "SELECT DataSensor.Name FROM DataAircraftSensors INNER JOIN DataSensor ON ComponentID=DataSensor.ID WHERE DataAircraftSensors.ID = ?",
            "Comms": "SELECT Name FROM DataAircraftComms INNER JOIN DataComm ON ComponentID = DataComm.ID WHERE DataAircraftComms.ID= ?",
            "Codes": "SELECT Description FROM DataAircraftCodes INNER JOIN EnumAircraftCode ON DataAircraftCodes.CodeID=EnumAircraftCode.ID WHERE DataAircraftCodes.ID = ?"
        }
        rd = {}
        with connect(self.db_path_provider.get_db_path(data)) as conn:
            for name, command in command_map.items():
                cur = conn.execute(command, (_id,))
                res = cur.fetchall()

                rl = [r[0] for r in res]
                rd[self.name_to_component[name]] = gr.update(value=rl, choices=rl)

        return rd

    def register_outputs(self, outputs: set):
        for component in self.name_to_component.values():
            outputs.add(component)
