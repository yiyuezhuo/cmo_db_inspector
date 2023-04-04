import gradio as gr
from pathlib import Path
import sqlite3
import math
from dataclasses import dataclass
from typing import Union

data_type = ['Aircraft', 'Ship', 'Submarine', 'Facility', 'Ground Unit', 'Satellite', 'Weapon', 'Sensor']

@dataclass
class PageManager:
    row_list: list
    row_per_page: int

    def sub_page(self, idx: int) -> list:
        i = idx - 1
        return self.row_list[i*self.row_per_page:(i+1)*self.row_per_page]
    
    def get_max_page_count(self):
        return math.ceil(len(self.row_list) / self.row_per_page)
    
    def goto_sub_page(self, idx: int) -> tuple[int, list]:
        idx = min(max(1, idx), self.get_max_page_count())
        return idx, self.sub_page(idx)
    
    def gen_goto_sub_page(self, *, offset=0, set_to=None):
        def f(prev_page_idx: float):
            assert prev_page_idx.is_integer()
            prev_page_idx = int(prev_page_idx)
            if set_to is not None:
                return self.goto_sub_page(set_to)
            return self.goto_sub_page(prev_page_idx + offset)
        return f
    
    def update_row_list(self, row_list: list):
        self.row_list = row_list


class CMODatabase:
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path
        # self.db = sqlite3.connect(db_path)

    def select_id_name_from_data_aircraft(self, pattern: str) -> list:
        db = sqlite3.connect(self.db_path)
        parameters = (pattern,)
        cursor = db.execute(r"SELECT ID, Name from DataAircraft WHERE Name LIKE '%' || ? || '%'", parameters)
        ret = cursor.fetchall()
        db.close()
        return ret
    
def make_demo(cmo_db_root: str, results_per_page = 20):
    db_list = list(Path(cmo_db_root).glob("*.db3"))
    
    # db = sqlite3.connect(db_list[-1])
    # cursor = db.execute(r"SELECT ID, Name from DataAircraft WHERE Name LIKE '%F/A%'")
    db = CMODatabase(db_list[-1])

    # rl = db.select_id_name_from_data_aircraft("F/A")
    rl: list = []
    page_manager = PageManager(rl, results_per_page)

    with gr.Blocks(theme=gr.themes.Default()) as demo:
        with gr.Row():
            cmd_dababase_dropdown = gr.Dropdown([p.name for p in db_list], label="CMO Database")
            type_dropdown = gr.Dropdown(data_type, label="Type")
        with gr.Row():
            # gr.Text("F/A", label="Class")
            class_text = gr.Text(label="Class")
        with gr.Row():
            first_page_button = gr.Button("First Page")
            prev_page_button = gr.Button("Prev Page")
            page_index_number = gr.Number(1, label="Page Index")
            next_page_button = gr.Button("Next Page")
            end_page_button = gr.Button("End Page")
        # gr_df = gr.DataFrame(page_manager.sub_page(1), headers=["ID", "Name"], datatype=["str", "str"])
        gr_df = gr.DataFrame([[]], headers=["ID", "Name"], datatype=["str", "str"])
        
        first_page_button.click(page_manager.gen_goto_sub_page(set_to=1), [page_index_number], [page_index_number, gr_df])
        prev_page_button.click(page_manager.gen_goto_sub_page(offset=-1), [page_index_number], [page_index_number, gr_df])
        next_page_button.click(page_manager.gen_goto_sub_page(offset=1), [page_index_number], [page_index_number, gr_df])
        end_page_button.click(page_manager.gen_goto_sub_page(set_to=page_manager.get_max_page_count()), [page_index_number], [page_index_number, gr_df])

        def text_changed(s):
            # print(s)
            rl = db.select_id_name_from_data_aircraft(s)
            page_manager.update_row_list(rl)

            return page_manager.goto_sub_page(1)

        class_text.change(text_changed, class_text, [page_index_number, gr_df])
        
    # demo.launch()
    return demo
