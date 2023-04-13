
from contextlib import contextmanager
import sqlite3
import gradio as gr
from typing import Optional

light_speed = 300_000_000 # 300_000_000 m/s

def inv_db(x):
    return 10 ** (x/10)

def chunks(arr, size):
    return (arr[idx:idx+size] for idx in range(0, len(arr), size))

def show(df):
    from IPython.display import display, HTML
    return display(HTML(df.to_html()))

@contextmanager
def connect(db_path):
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()

def text_grid(indexes, elements_per_row: int, info_map=None, value_map=None, value_list=None):
    info_map = {} if info_map is None else info_map

    if value_map is None:
        if value_list is not None:
            value_map = {idx:value for idx, value in zip(indexes, value_list)}
        else:
            value_map = {}

    name_to_component = {}

    for chunk in chunks(list(indexes), elements_per_row):
        with gr.Row():
            for index in chunk:
                info = info_map.get(index, None)
                text = gr.Text(value_map.get(index, ""), label=index, info=info)
                name_to_component[index] = text

    return name_to_component

def tags(names: list[str], label: Optional[str]=None):
    checkbox_group = gr.CheckboxGroup(choices=[], value=[], label=label, interactive=False)
    return checkbox_group
    """
    # `Dataset` can't be outputs
    dataset = gr.Dataset(components=[gr.Textbox(visible=False)],
        label=label,
        samples=[[name] for name in names],
    )
    return dataset
    """

def merge_update(*f_list):
    def g(*args, **kwargs):
        rd = {}
        for f in f_list:
            rd.update(f(*args, **kwargs))
        return rd
    return g

        