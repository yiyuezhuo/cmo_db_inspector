from contextlib import contextmanager
from dataclasses import dataclass
import sqlite3
from pathlib import Path
import gradio as gr
import math

import pandas as pd # Gradio force pandas usage anyway.

from .utils import connect

@dataclass
class TableInfo:
    name: str
    table_name: str
    select_command_root: str
    headers: list[str]
        
    @property
    def select_command_free(self) -> str:
        return self.select_command_root + " WHERE Name LIKE '%' || ? || '%'"
    
    @property
    def select_command_ranged(self) -> str:
        return self.select_command_free + " LIMIT ? OFFSET ?"
    
table_info_map = {
    "Aircraft": TableInfo(
        name="Aircraft", table_name="DataAircraft", 
        select_command_root="SELECT DataAircraft.ID, Name, Comments, EnumOperatorCountry.Description, YearCommissioned FROM DataAircraft INNER JOIN EnumOperatorCountry ON DataAircraft.OperatorCountry=EnumOperatorCountry.ID",
        headers=["ID", "Name", "Comments", "Country", "Year Commissioned"]
    ),
    "Sensor": TableInfo(
        name="Sensor", table_name="DataSensor",
        select_command_root="SELECT DataSensor.ID, Name, Comments, EnumSensorRole.Description, EnumSensorGeneration.Description FROM DataSensor INNER JOIN EnumSensorRole ON DataSensor.Role=EnumSensorRole.ID INNER JOIN EnumSensorGeneration on Generation=EnumSensorGeneration.ID",
        headers=["ID", "Name", "Comments", "Role", "Generation"]
    )
}

# data_type = ['Aircraft', 'Ship', 'Submarine', 'Facility', 'Ground Unit', 'Satellite', 'Weapon', 'Sensor']

def pick_default_db(db_list: list[Path]):
    if len(db_list) == 0:
        return None
    elif len(db_list) == 1:
        return db_list[0]
    
    db_list_sorted = sorted(db_list, key=lambda p:p.stat().st_ctime)
    if db_list_sorted[-1].stat().st_size >= db_list_sorted[-2].stat().st_size:
        return db_list_sorted[-1]
    return db_list_sorted[-2]

class SelectedEvent:
    def __init__(self):
        self.return_update = None

class SelectorTab:
    def __init__(self, cmo_db_root: Path, row_per_page=20):
        self.cmo_db_root = cmo_db_root
        self.row_per_page = row_per_page
        
        self.db_list = list(cmo_db_root.glob("*.db3"))
        self.db_list.sort(key=lambda p:p.stat().st_ctime)
        
        self.default_db = pick_default_db(self.db_list)

        self.selected_events = {
            "Aircraft": SelectedEvent(),
            "Sensor": SelectedEvent()
        }
    
    def build(self):
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    self.cmo_dababase_dropdown = gr.Dropdown([p.name for p in self.db_list], label="CMO Database", value=self.default_db.name)
                    self.type_dropdown = gr.Dropdown(list(table_info_map), label="Type", value="Aircraft")
                with gr.Row():
                    # gr.Text("F/A", label="Class")
                    self.class_text = gr.Text("initial class", label="Class") # The value will be override by load event and trigger a change handler
                with gr.Row().style(equal_height=True):
                    #with gr.Column(min_width=100):
                    self.first_page_button = gr.Button("First", elem_id="first-page-button").style(size="sm") # gr.Button("First Page")
                    self.prev_page_button = gr.Button("Prev", elem_id="prev-page-button").style(size="sm") # gr.Button("Prev Page")
                    with gr.Column(min_width=100):
                        self.page_index_number = gr.Number(1, label="Page Index")
                    with gr.Column(min_width=100):
                        self.page_count_number = gr.Number(1, label="Page Count")
                    self.next_page_button = gr.Button("Next", elem_id="next-page-button").style(size="sm") # gr.Button("Next Page")
                    self.end_page_button = gr.Button("End", elem_id="end-page-button").style(size="sm") # gr.Button("End Page")
            with gr.Column():
                self.gr_df = gr.DataFrame([[]], interactive=False) #, datatype=["str", "str"])
                # self.gr_df = gr.DataFrame([[]], headers=["ID", "Name", "Comments", "Country/Role", "Year/Generation"]) #, datatype=["str", "str"])
                # self.gr_df = gr.DataFrame([[]])#, headers=["ID", "Name"]), datatype=["str", "str"])
            
        return self
    
    def bind(self, gr_df_select_output: set):
        inputs = {self.cmo_dababase_dropdown, self.type_dropdown, self.page_index_number, self.class_text}
        
        outputs = [self.gr_df, self.page_index_number, self.page_count_number]
        
        self.first_page_button.click(lambda data: self.update(data, page_target=1), inputs, outputs)
        self.prev_page_button.click(lambda data: self.update(data, page_offset=-1), inputs, outputs)
        self.next_page_button.click(lambda data: self.update(data, page_offset=1), inputs, outputs)
        self.end_page_button.click(lambda data: self.update(data, page_target=-1), inputs, outputs)

        for component in [self.type_dropdown, self.cmo_dababase_dropdown, self.class_text]:
            component.change(lambda data: self.update(data), inputs, outputs)

        self.gr_df.select(self.select, {self.gr_df, self.type_dropdown, self.cmo_dababase_dropdown}, gr_df_select_output)

        self.gr_df_select_output = gr_df_select_output

        return self
    
    def get_db_path(self, data):
        db_name = data[self.cmo_dababase_dropdown]
        db_path = self.cmo_db_root / db_name
        return db_path
    
    def get_init_db_path(self):
        return self.default_db
    
    def get_db_inputs(self):
        return {self.cmo_dababase_dropdown}
            
    def get_current_page_index(self, data):
        page_index = data[self.page_index_number]
        assert page_index.is_integer()
        return int(page_index)
    
    def select(self, data, evt: gr.SelectData):
        # evt.value
        # print(f"Select -> evt={evt}, evt.value={evt.value}")

        self.selected_any = True

        i, _ = evt.index

        df: pd.DataFrame = data[self.gr_df]
        _id = df.iloc[i]["ID"]

        type_name = data[self.type_dropdown]
        event = self.selected_events[type_name]

        ret = {component: gr.update() for component in self.gr_df_select_output}
        if event.return_update is not None:
            ret.update(event.return_update(data, _id))

        return ret
    
    def update(self, data, page_target=None, page_offset=None):

        db_path = self.get_db_path(data)

        type_name = data[self.type_dropdown]
        table_info = table_info_map[type_name]
        match_str = data[self.class_text]

        with connect(db_path) as conn:

            cur = conn.execute(f"SELECT COUNT(*) FROM {table_info.table_name} WHERE Name LIKE '%' || ? || '%'", (match_str,))
            n = cur.fetchone()[0]
            page_count = math.ceil(n / self.row_per_page)
            current_page_index = self.get_current_page_index(data)

            if page_offset is None and page_target is None:
                page_offset = 0

            if page_offset is not None and page_target is None:
                page_target = current_page_index + page_offset
            
            if page_target is not None:
                if page_target < 0:
                    page_target = page_count + page_target + 1
                elif page_target == 0:
                    page_target = 1
                elif page_target > page_count:
                    page_target = page_count
                page_index = page_target
            
            limit = self.row_per_page
            offset = (page_index-1) * self.row_per_page
            cur = conn.execute(table_info.select_command_ranged, (match_str, limit, offset))
            res = cur.fetchall()

        df = pd.DataFrame(res, columns=table_info.headers)
        ret = {self.gr_df: df, self.page_index_number: page_index, self.page_count_number: page_count}
        # print(f"ret={ret}")
        return ret

        # return {self.gr_df: res, self.page_index_number: page_index, self.page_count_number: page_count}
        
        # Gradio doesn't support pandas-free header setting at this point. Though we can hack (show/hide multiple dataframe, wrap it in a dataframe), it's decided that just leave it statically.
        # https://github.com/gradio-app/gradio/issues/2358
        # headers = [d[0] for d in cur.description]
        # return {self.gr_df: gr.update(value=res, headers=headers), self.page_index_number: page_index, self.page_count_number: page_count}
    
                    