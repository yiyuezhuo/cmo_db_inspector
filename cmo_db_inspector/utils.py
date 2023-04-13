
from contextlib import contextmanager
import sqlite3

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
